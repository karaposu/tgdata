"""Test-only Gate C instrumentation. Importing this module never connects."""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location('stage4_receiver',
    HERE.parent/'stage-4-completion'/'prebuild_probe.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
p = base.p
from tgdata import TgData, ReadBudget
from tgdata.history_window import _encode_date

ROOT = Path('/private/tmp/tgdata19-gate-c-live-20261007')
CHAT = base.CHAT


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())


def read(path):
    return json.loads(Path(path).read_text())


def account():
    return int(read(base.OLD/'login-status.json')['verified_account_id'])


def allocate(root, name, slots):
    """One sequential owner; allocate before launch, never reclaim a crash's cap."""
    root = Path(root)
    root.mkdir(mode=0o700, exist_ok=True)
    assert root.stat().st_mode & 0o077 == 0
    assert type(slots) is int and 0 < slots <= 1000
    path = root/'allocations.jsonl'
    old = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    assert name not in [v['name'] for v in old], 'allocation cannot be reused'
    assert sum(v['slots'] for v in old) + slots <= 1000, 'stage traffic cap exhausted'
    row = dict(name=name, slots=slots, at=_encode_date(datetime.now(timezone.utc)))
    with path.open('a') as stream:
        stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(str(root), os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return slots


def begin_worker(root, name):
    rows = [json.loads(line) for line in (root/'allocations.jsonl').read_text().splitlines()]
    row = next(v for v in rows if v['name'] == name)
    save(root/(name+'.started.json'), dict(pid=os.getpid(), allocation=row))
    return row['slots']


@dataclass(frozen=True)
class CompositeReservation:
    primary: object
    test: object

    def __post_init__(self):
        assert self.primary.amount == self.test.amount

    @property
    def amount(self):
        return self.primary.amount


class RestrictiveBudget:
    """Enforce both real ledgers; this is not a production policy abstraction."""
    def __init__(self, primary, test):
        self.primary, self.test = primary, test

    def status(self, ident):
        one, two = self.primary.status(ident), self.test.status(ident)
        return one if one.remaining <= two.remaining else two

    def _reserve(self, ident, amount):
        one = self.primary._reserve(ident, amount)
        # If this fails, the conservative first charge is deliberately retained.
        two = self.test._reserve(ident, amount)
        return CompositeReservation(one, two)

    def _settle(self, claim, actual):
        self.primary._settle(claim.primary, actual)
        self.test._settle(claim.test, actual)


class DurableGuard(p.ReadOnlyGuard):
    def __init__(self, root, name, slots, media=False):
        super().__init__(CHAT, dict(max_rpc_requests=160, max_history_requests=20,
            max_requested_slots=slots, max_media_bytes=4*1024*1024 if media else 0),
            allow_media=media)
        self.trace = root/(name+'.sends.jsonl')

    def before_send(self, request):
        entry = super().before_send(request)
        # A crash after enqueue cannot hide this admitted diagnostic request.
        with self.trace.open('a') as stream:
            stream.write(json.dumps(entry, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
        return entry


async def source(root, name, budget, media=False):
    slots = begin_worker(root, name)
    guard = DurableGuard(root, name, slots, media)
    tg = TgData(str(base.CONFIG), connection_pool_size=1, interactive_login=False, read_budget=budget)
    factory = tg.connection_engine._new_client
    def instrumented(*args, **kwargs):
        client = factory(*args, **kwargs); guard.instrument(client)
        client.flood_sleep_threshold = 0; client._request_retries = 0; client._connection_retries = 1
        return client
    tg.connection_engine._new_client = instrumented
    try:
        client = await tg.connection_engine.get_client()
        assert (await client.get_me(input_peer=False)).id == account(), 'selected identity changed'
        return tg, client, guard
    except BaseException:
        await tg.close()
        raise


async def wait_until_ready(engine, status):
    from tgdata.backfill import BackfillPrepareContext
    while True:
        turn = await engine.prepare(BackfillPrepareContext.from_status(status))
        if turn.wait_seconds is None:
            return turn
        await asyncio.sleep(turn.wait_seconds + 0.02)
