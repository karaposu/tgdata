"""Targeted #7 fidelity checks; real SDK/SQLite with synthetic transport/faults.

These supplement the recorded regression run without touching runtime code.
"""
import asyncio
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from telethon import errors
from tgdata import AuthRequiredError, JoinBudgetConfigError, JoinBudgetStorageError, ReadBudget
from tgdata import health
from tgdata.smoke_tests import test_20_group_operations as g


async def immediate(_):
    pass


async def probe_history_retry():
    read = ReadBudget(g.TMP / 'merge_read.sqlite', clock=g.f.Clock())
    read.configure(g.f.ACCOUNT, 3)
    sender = g.Sender()
    sender.script = [errors.ServerError(None, 'synthetic retry'), g.f.response([])]
    with g.rig(read=read, senders=[sender]) as r, patch('telethon.client.users.asyncio.sleep', immediate):
        result = await r.tg.check_group_access('synthetic_room')
    assert result.readable is True
    assert len(sender.reads) == 2 and all(item[1] == 1 for item in sender.reads)
    assert read.status(g.f.ACCOUNT).used == 1  # Uncertain first attempt retained; empty reply settles to0.
    print('PASS history: one logical probe, two real SDK sends, each bounded and metered')


async def probe_account_and_wait_recovery():
    logged_out = g.Sender()
    logged_out.state_error = errors.AuthKeyUnregisteredError(None)
    with g.rig(senders=[logged_out, g.Sender()]) as r:
        await g.expect(AuthRequiredError, r.tg.lookup_group('synthetic_room'))
        assert r.tg._health.snapshot()['verdict'] == health.LOGGED_OUT
        await r.tg.lookup_group('synthetic_room')
        assert r.tg._health.snapshot()['verdict'] == health.OK
        assert any(e['scope'] == 'account' and e['verdict'] == health.OK for e in r.events)

    waiting = g.Sender()
    def one_wait(request):
        waiting.state_error = None
        return errors.FloodWaitError(request, capture=1)
    waiting.state_error = one_wait
    with g.rig(senders=[waiting]) as r, patch('telethon.client.users.asyncio.sleep', immediate):
        await r.tg.lookup_group('synthetic_room')
        assert any(e['verdict'] == health.WAITING for e in r.events)
        assert any(e['scope'] == 'request' and e['verdict'] == health.OK for e in r.events)
        assert r.tg._health.snapshot()['waiting'] == {}
    print('PASS health: metadata retains account and authorization-wait recovery')


def probe_storage_cleanup():
    budget, _ = g.ledger()
    connect = sqlite3.connect

    class FailingClose(sqlite3.Connection):
        def close(self):
            super().close()
            raise sqlite3.OperationalError('synthetic close failure')

    def fault_connection(*args, **kwargs):
        return connect(*args, factory=FailingClose, **kwargs)

    with patch('tgdata.join_budget.sqlite3.connect', fault_connection):
        primary = g.reject(JoinBudgetConfigError, lambda: budget._claim(99999))
        assert health.classify(primary) is None
        cleanup_only = g.reject(JoinBudgetStorageError, lambda: budget.status(g.f.ACCOUNT))
        assert 'cleanup failed' in str(cleanup_only) and health.classify(cleanup_only) is None

    def readonly(*args, **kwargs):
        return connect('file:' + budget.path + '?mode=ro', uri=True, **kwargs)

    with patch('tgdata.join_budget.sqlite3.connect', readonly):
        g.reject(JoinBudgetStorageError, lambda: budget._claim(g.f.ACCOUNT))
    assert budget.status(g.f.ACCOUNT).used == 0
    print('PASS storage: primary failure survives close fault; read-only refusal remains uncharged')


async def main():
    await probe_history_retry()
    await probe_account_and_wait_recovery()
    probe_storage_cleanup()


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp, patch.object(
            socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
        g.TMP = g.f.TMP = Path(tmp)
        asyncio.run(main())
