"""Fresh PR #14 probes; temporary SQLite and real SDK flows, no Telegram sockets.

Run from the repository: .venv/bin/python devdocs/work/9-account-read-budget/probe_pr_budget.py
Scripted replies do not establish live Telegram behavior.
"""
import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
import random
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import telethon
from telethon import errors
from telethon.tl import functions, types
from tgdata import ReadBudget, ReadBudgetExceeded, UnsupportedBudgetRequest, health
from tgdata.read_budget import WINDOW_SECONDS as DAY
from tgdata.smoke_tests import test_18_read_budget as f


def oracle_ledger():
    operations = 0
    for seed in range(8):
        rng = random.Random(seed)
        budget, clock = f.ledger(30)
        start, observed, maximum, curve = clock(), clock(), 30, []
        claims = {}
        tokens = []

        def cap(at):
            eligible = [value for day, value in curve if start + day * DAY <= at]
            return eligible[-1] if eligible else maximum

        def used(at):
            return sum(row[1] for row in claims.values() if at - row[0] < DAY)

        def retry(requested):
            times = {row[0] + DAY for row in claims.values() if row[0] + DAY > observed}
            times.update(start + day * DAY for day, _ in curve if start + day * DAY > observed)
            return next((at for at in sorted(times) if cap(at) - used(at) >= requested), None)

        for _ in range(120):
            choice = rng.randrange(5)
            observed = max(observed, clock())
            if choice == 0:
                amount = rng.randint(1, 15)
                if amount > max(0, cap(observed) - used(observed)):
                    error = f.rejected(ReadBudgetExceeded, lambda: budget._reserve(f.ACCOUNT, amount))
                    assert error.next_available_at == retry(amount)
                else:
                    token = budget._reserve(f.ACCOUNT, amount)
                    tokens.append(token)
                    claims[token.token] = [observed, amount, False]
            elif choice == 1 and tokens:
                token = rng.choice(tokens)
                actual = rng.randint(0, token.amount + 2)
                budget._settle(token, actual)
                row = claims[token.token]
                if not row[2] and observed - row[0] < DAY:
                    row[1], row[2] = actual, True
            elif choice == 2:
                maximum = rng.randint(0, 60)
                curve = [(0, maximum // 3), (1, maximum // 2), (3, maximum)] if rng.randrange(2) else []
                budget.configure(f.ACCOUNT, maximum, curve)
            elif choice == 3:
                clock.value += rng.choice([-500, 0, 3600, DAY, 2 * DAY])
            else:
                budget = ReadBudget(budget.path, clock=clock)
            observed = max(observed, clock())
            status = budget.status(f.ACCOUNT)
            assert status.used == used(observed), (seed, status, claims)
            assert status.limit == cap(observed)
            assert status.remaining == max(0, cap(observed) - used(observed))
            assert status.reserved == sum(row[1] for row in claims.values()
                                          if not row[2] and observed - row[0] < DAY)
            assert status.started_at == start and status.observed_at == observed
            operations += 1
    print(f'Ledger oracle: {operations} randomized transitions match independent accounting, including restart and rollback')


async def inflight_policy_and_expiry():
    budget, clock = f.ledger(10)
    _, client, sender = f.instance(budget)
    sender.script = [f.PENDING]
    pending = asyncio.create_task(client(f.history(8)))
    await asyncio.sleep(0)
    assert budget.status(f.ACCOUNT).reserved == 8
    budget.configure(f.ACCOUNT, 0)
    sender.pending.pop().set_result(f.response([f.message(1000)]))
    await pending
    status = budget.status(f.ACCOUNT)
    assert (status.used, status.reserved, status.remaining) == (1, 0, 0)
    await f.expect(ReadBudgetExceeded, client(f.history(1)))
    budget.configure(f.ACCOUNT, 10)
    sender.script = [f.PENDING]
    pending = asyncio.create_task(client(f.history(9)))
    await asyncio.sleep(0)
    clock.value += DAY
    await client(f.history(7))
    sender.pending.pop().set_result(f.response([f.message(800)]))
    await pending
    assert budget.status(f.ACCOUNT).used == 7
    print('In-flight policy/expiry: lowering the cap stops sends; an old reply cannot refund seven new-window units')


async def sender_refetch():
    budget, _ = f.ledger(2)
    events = []
    tg, _, sender = f.instance(budget, events=events)
    answer = f.response([f.message(1000), f.message(999)])
    answer.users = []
    sender.script = [answer]
    error = await f.expect(ReadBudgetExceeded, tg.get_messages(7, limit=2))
    assert error.partial_result.empty and len(sender.reads) == 1
    assert budget.status(f.ACCOUNT).used == 2 and not events
    assert health.classify(error) is None
    print('Missing sender: real Message.get_sender re-fetch is refused, its budget error propagates, two slots stay charged')


async def media_refetch():
    budget, _ = f.ledger(1)
    events = []
    tg, client, _ = f.instance(budget, events=events)

    class MediaSender(f.Sender):
        file_calls = 0

        def send(self, request, ordered=False):
            raw = f.unwrap(request)
            if isinstance(raw, functions.upload.GetFileRequest):
                self.file_calls += 1
                future = asyncio.get_running_loop().create_future()
                # Both supported probe versions re-fetch on this error.
                # 1.33.1 does not yet retry FileReferenceExpiredError.
                future.set_exception(errors.FilerefUpgradeNeededError(request=raw))
                return future
            return super().send(request, ordered=ordered)

    client._sender = sender = MediaSender()
    client.session.set_dc(2, '149.154.167.51', 443)  # identity only; sockets remain forbidden
    message = f.message(1000)
    message.media = types.MessageMediaDocument(document=types.Document(
        id=55, access_hash=55, file_reference=b'synthetic',
        date=datetime.fromtimestamp(f.NOW, timezone.utc), mime_type='application/octet-stream',
        size=32, dc_id=2, attributes=[]))
    sender.script = [f.response([message])]
    error = await f.expect(ReadBudgetExceeded, tg.get_messages(7, limit=1, include_media=True))
    assert sender.file_calls == 1 and len(sender.reads) == 1
    assert error.partial_result.empty and budget.status(f.ACCOUNT).used == 1
    assert not events and health.classify(error) is None
    print('Expired media: real SDK download/refetch stops at quota; one file request, one charged message, no health verdict')


async def discovery_network_partial():
    budget, _ = f.ledger(6)
    tg, _, sender = f.instance(budget)
    sender.script = [f.response([f.message(mid, f'https://t.me/room_{mid}')
                                 for mid in range(1005, 1000, -1)]),
                     ConnectionError('synthetic dropped connection')]
    error = await f.expect(ReadBudgetExceeded, tg.linked_groups(7, posts=100, pace=0))
    assert len(error.partial_result) == 5 and len(sender.reads) == 2
    assert [row[1] for row in sender.reads] == [6, 1]
    assert budget.status(f.ACCOUNT).used == 6
    print('Discovery reconnect: five mined links survive a failed second read and exhausted retry; six units charged')


async def cursors_and_wrapper_guards():
    budget, clock = f.ledger(3)
    _, client, sender = f.instance(budget)
    iterator = client.iter_messages(types.InputPeerChannel(7, 7), limit=10)
    first = [(await iterator.__anext__()).id for _ in range(3)]
    await f.expect(ReadBudgetExceeded, iterator.__anext__())
    clock.value += DAY
    budget.configure(f.ACCOUNT, 7)
    later = [(await iterator.__anext__()).id for _ in range(7)]
    assert first + later == list(range(1000, 990, -1))
    assert sender.reads[-1][1:] == (7, 998, 0)
    before = len(sender.reads)
    wrapped = functions.InvokeWithLayerRequest(1, functions.InvokeWithoutUpdatesRequest(f.history(1)))
    await f.expect(ReadBudgetExceeded, client(wrapped))
    await f.expect(UnsupportedBudgetRequest, client([
        functions.updates.GetStateRequest(), wrapped]))
    await f.expect(UnsupportedBudgetRequest, client(
        functions.InvokeWithoutUpdatesRequest(functions.messages.GetScheduledHistoryRequest(
            types.InputPeerChannel(7, 7), 0))))
    assert len(sender.reads) == before
    print('Forward resume/wrappers: ten consecutive IDs, correct resized cursor; nested and batched guards prevent sends')


async def main():
    print(f'PR #14 adversarial probes — Telethon {telethon.__version__}; runtime code unchanged')
    logging.getLogger('tgdata').addHandler(logging.NullHandler())
    with tempfile.TemporaryDirectory(prefix='tgdata_pr14_probe_') as root, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP = Path(root)
        try:
            oracle_ledger()
            for probe in (inflight_policy_and_expiry, sender_refetch, media_refetch,
                          discovery_network_partial, cursors_and_wrapper_guards):
                await asyncio.wait_for(probe(), 30)
        finally:
            for client in f.CLIENTS:
                await client.disconnect()
            f.CLIENTS.clear()
    print('All six adversarial probe groups passed')


if __name__ == '__main__':
    asyncio.run(main())
