"""Fresh PR25 probes: delivered facade/SDK/SQLite, synthetic wire, sockets blocked.

Run from the repository using the selected Telethon1.45 environment. Faults are
injected at real boundaries; the product implementation is never replaced.
"""
import asyncio
from contextlib import ExitStack
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import telethon
from telethon import errors
from telethon.network.mtprotosender import MTProtoSender
from telethon.tl import functions, types

from tgdata import JoinBudget, JoinBudgetExceeded, JoinBudgetStorageError
from tgdata.group_operations import GroupJoin
from tgdata.smoke_tests import test_36_group_join as t


def environment(root):
    stack = ExitStack()
    t.fx.TMP = Path(root)
    for name in ('connect', 'connect_ex'):
        stack.enter_context(patch.object(socket.socket, name, side_effect=AssertionError('network forbidden')))
    for name in ('start', 'send_code_request'):
        stack.enter_context(patch.object(telethon.TelegramClient, name, side_effect=AssertionError('login forbidden')))
    stack.enter_context(patch.object(t.fx.Wire, 'send', t.send))
    return stack


def leaf(request):
    while isinstance(request, functions.InvokeWithoutUpdatesRequest):
        request = request.query
    return request


async def policy_changed_during_proof():
    entered, release = asyncio.Event(), asyncio.Event()
    def resolve(wire, request):
        wire.script['GetUsersRequest'] = [t.g.Reply(t.UserVector(), entered=entered, release=release)]
        return t.g.resolved(t.g.channel(left=True))
    tg, fixture, budget = t.setup(limit=2, responses={'ResolveUsernameRequest': resolve})
    task = t.start(tg.join_group('synthetic_room', account_id=222))
    try:
        await entered.wait()
        other = JoinBudget(budget.path, clock=lambda: 1000)
        assert other.status(222).remaining == 2
        other.configure(222, 0)
        release.set()
        await t.fx.expect(JoinBudgetExceeded, task)
        assert budget.status(222).used == 0 and not t.requests(fixture)
        assert fixture.wire.closed and tg.get_account_health(222)['events'] == 0
        return dict(observed_before=2, cap_at_claim=0, enqueued=0, charged=0, health_events=0)
    finally:
        release.set()


async def different_facades_share_one_cap():
    number = 8
    all_entered, release = asyncio.Event(), asyncio.Event()
    reached = []
    class Held(t.g.Reply):
        def send(self, wire, request, ordered=False):
            reached.append(wire)
            if len(reached) == number:
                all_entered.set()
            return super().send(wire, request, ordered)
    def resolve(wire, request):
        obj = (types.contacts.ResolvedPeer(types.PeerChannel(7), [t.g.channel(left=True)], [])
               if isinstance(request, functions.contacts.ResolveUsernameRequest) else t.preview())
        return Held(obj, release=release)
    replies = dict(ResolveUsernameRequest=resolve, CheckChatInviteRequest=resolve)
    a, fa, budget = t.setup(limit=2, responses=replies)
    b, fb, _ = t.setup(responses=replies)
    b._join_budget = JoinBudget(budget.path, clock=lambda: 1000)
    tasks = [t.start((a if i % 2 else b).join_group(
        'synthetic_room' if i % 3 else 't.me/+token', account_id=222)) for i in range(number)]
    try:
        await all_entered.wait()
        assert budget.status(222).used == 0
        release.set()
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        joined = sum(isinstance(value, GroupJoin) and value.status == 'joined' for value in answers)
        refused = sum(isinstance(value, JoinBudgetExceeded) for value in answers)
        sends = len(t.requests(fa)) + len(t.requests(fb))
        assert (joined, refused, sends, budget.status(222).used) == (2, 6, 2, 2)
        assert all(client._sender.closed for client in fa.clients + fb.clients)
        assert fa.budget.status(222).used == fb.budget.status(222).used == 0
        return dict(facades=2, held_preflights=number, joined=joined, refused=refused,
                    enqueued=sends, persisted_charge=budget.status(222).used)
    finally:
        release.set()


async def database_failures():
    records = []
    for mode in ('native_commit_denied', 'lost_commit_reply', 'close_error', 'close_cancel'):
        tg, fixture, budget = t.setup()
        active = [False]
        original_connect, original_claim = sqlite3.connect, budget._claim
        class Connection:
            def __init__(self, db):
                self.db = db
            def __getattr__(self, name):
                return getattr(self.db, name)
            def commit(self):
                if active[0] and mode == 'native_commit_denied':
                    self.db.set_authorizer(lambda action, one, two, db, source:
                        sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_TRANSACTION and one == 'COMMIT'
                        else sqlite3.SQLITE_OK)
                self.db.commit()
                if active[0] and mode == 'lost_commit_reply':
                    raise sqlite3.OperationalError('synthetic lost commit reply')
            def close(self):
                self.db.close()
                if active[0] and mode == 'close_error':
                    raise OSError('synthetic close failure')
                if active[0] and mode == 'close_cancel':
                    raise asyncio.CancelledError('synthetic close cancellation')
        def connect(*args, **kwargs):
            db = original_connect(*args, **kwargs)
            return Connection(db) if str(args[0]).startswith(Path(budget.path).as_uri()) else db
        def claim(owner):
            active[0] = True
            try:
                return original_claim(owner)
            finally:
                active[0] = False
        with patch('tgdata.join_budget.sqlite3.connect', connect), patch.object(budget, '_claim', claim):
            kind = asyncio.CancelledError if mode == 'close_cancel' else JoinBudgetStorageError
            error = await t.fx.expect(kind, tg.join_group('synthetic_room', account_id=222))
        used = JoinBudget(budget.path, clock=lambda: 1000).status(222).used
        assert used == (0 if mode == 'native_commit_denied' else 1)
        assert not t.requests(fixture) and fixture.wire.closed
        assert tg.get_account_health(222)['events'] == 0
        records.append(dict(fault=mode, error=type(error).__name__, charged=used,
                            enqueued=0, health_events=0))
    return records


async def serialized_local_faults_and_rpc_origins():
    rows = []
    # A real SDK serializer failure happens after admission but before enqueue.
    original = functions.channels.JoinChannelRequest._bytes
    problem = OSError('synthetic serializer failure')
    def broken(request):
        raise problem
    tg, fixture, budget = t.setup()
    enqueued = []
    original_send = MTProtoSender.send
    def track(sender, request, ordered=False):
        result = original_send(sender, request, ordered=ordered)
        if isinstance(leaf(request), t.MUTATIONS):
            enqueued.append(request)
        return result
    with patch.object(functions.channels.JoinChannelRequest, '_bytes', broken), \
         patch.object(MTProtoSender, 'send', track):
        assert await t.fx.expect(OSError, tg.join_group('synthetic_room', account_id=222)) is problem
    assert not enqueued and budget.status(222).used == 1 and fixture.wire.closed
    rows.append(dict(case='serialization', original_error=True, actual_sdk_enqueues=0, charged=1))

    # A generated proof error has its actual request; nesting it under an unrelated
    # handled RPC must not turn it into a join outcome or legacy health event.
    for name in ('USER_ALREADY_PARTICIPANT', 'INVITE_REQUEST_SENT', 'STARS_PAYMENT_REQUIRED'):
        source = t.h.RPCReply(400, name)
        def resolve(wire, request):
            wire.script['GetUsersRequest'] = [source]
            return t.g.resolved(t.g.channel(left=True))
        tg, fixture, budget = t.setup(responses={'ResolveUsernameRequest': resolve})
        try:
            raise errors.ChannelPrivateError(t.fx.history())
        except errors.ChannelPrivateError:
            async with tg._health.call('legacy_parent', 99):
                error = await t.fx.expect(errors.RPCError, tg.join_group('synthetic_room', account_id=222))
        assert error is source.error and not t.requests(fixture) and budget.status(222).used == 0
        assert tg._health.snapshot()['events'] == 0 and tg.get_account_health(222)['events'] == 0
        rows.append(dict(case=name, original_error=True, actual_sdk_enqueues=0, charged=0,
                         legacy_events=0, owner_events=0))
    return rows


async def cancel_after_identity_change_in_held_proof():
    entered, release = asyncio.Event(), asyncio.Event()
    def resolve(wire, request):
        wire.account = 333
        class OtherUser:
            def __bytes__(self):
                import struct
                return struct.pack('<Ii', 0x1cb5c415, 1) + bytes(t.fx.user(333))
        wire.script['GetUsersRequest'] = [t.g.Reply(OtherUser(), entered=entered, release=release)]
        return t.g.resolved(t.g.channel(left=True))
    tg, fixture, budget = t.setup(responses={'ResolveUsernameRequest': resolve})
    task = t.start(tg.join_group('synthetic_room', account_id=222))
    try:
        await entered.wait()
        task.cancel()
        release.set()
        await t.fx.expect(asyncio.CancelledError, task)
        assert not t.requests(fixture) and budget.status(222).used == budget.status(333).used == 0
        assert fixture.wire.closed and fixture.clients[0]._tgdata_join_budget is None
        return dict(caller='CancelledError', charged_expected=0, charged_other=0, enqueued=0, closed=True)
    finally:
        release.set()


async def wrapped_result_cache_and_reply_failure():
    rows = []
    for use_file in (False, True):
        tg, fixture, budget = t.setup(store=None if use_file else t.fx.Store(), responses={
            'ImportChatInviteRequest': t.acknowledged(types.Updates([], [], [t.g.channel(99, access_hash=77)], t.DATE, 1))})
        value = await tg.join_group('t.me/+token', account_id=222)
        assert value.status == 'joined' and value.group.id is None
        later = fixture.engine._new_client()
        assert later.session.get_entity_rows_by_id(-1000000000099, exact=True) is None
        assert budget.status(222).used == 1
        rows.append(dict(session='file' if use_file else 'store', status=value.status,
                         preflight_id=value.group.id, nested_cached=False, charged=1))
    return rows


async def protocol_repair_retains_one_admission():
    observed = {}
    class Repair(t.g.Reply):
        def send(self, wire, request, ordered=False):
            sender = MTProtoSender(wire.auth_key, loggers=wire.client._log)
            sender._user_connected, sender._send_queue = True, []
            future = sender.send(request, ordered=ordered)
            state = sender._send_queue.pop()
            state.msg_id = 124
            sender._pending_state[124] = state
            async def repair_and_reply():
                await sender._handle_bad_server_salt(SimpleNamespace(obj=SimpleNamespace(
                    bad_msg_id=124, new_server_salt=99)))
                repeated = sender._send_queue.pop()
                observed['same_state'] = repeated is state
                observed['same_future'] = repeated.future is future
                assert repeated is state and repeated.future is future
                state.msg_id = 128
                sender._pending_state[128] = state
                await sender._handle_rpc_result(SimpleNamespace(obj=SimpleNamespace(
                    req_msg_id=128, error=None, body=bytes(self.value))))
            t.h.RPC_TASKS.append(asyncio.create_task(repair_and_reply()))
            return future
    tg, fixture, budget = t.setup(responses={'JoinChannelRequest': Repair(
        types.messages.ChatInviteJoinResultOk(types.Updates([], [], [], t.DATE, 1)))})
    answer = await tg.join_group('synthetic_room', account_id=222)
    assert answer.status == 'joined' and budget.status(222).used == len(t.requests(fixture)) == 1
    observed.update(status=answer.status, application_sends=1, charged=1)
    return observed


async def crash_worker(mode, root):
    with environment(root):
        tg, fixture, budget = t.setup()
        (Path(root)/'budget-path.txt').write_text(budget.path)
        original_claim, original_connect = budget._claim, sqlite3.connect
        active = [False]
        class Connection:
            def __init__(self, db):
                self.db = db
            def __getattr__(self, key):
                return getattr(self.db, key)
            def execute(self, sql, *args):
                result = self.db.execute(sql, *args)
                if active[0] and mode == 'uncommitted' and sql.startswith('INSERT INTO tgdata_join_attempts'):
                    os._exit(71)
                return result
            def commit(self):
                self.db.commit()
                if active[0] and mode == 'committed':
                    os._exit(72)
        def connect(*args, **kwargs):
            db = original_connect(*args, **kwargs)
            return Connection(db) if str(args[0]).startswith(Path(budget.path).as_uri()) else db
        def claim(owner):
            active[0] = True
            try:
                return original_claim(owner)
            finally:
                active[0] = False
        original_send = MTProtoSender.send
        def send(sender, request, ordered=False):
            result = original_send(sender, request, ordered=ordered)
            if isinstance(leaf(request), t.MUTATIONS):
                (Path(root)/'sdk-enqueued.txt').write_text('serialized RequestState enqueued\n')
                if mode == 'enqueued':
                    os._exit(73)
            return result
        with patch('tgdata.join_budget.sqlite3.connect', connect), \
             patch.object(budget, '_claim', claim), patch.object(MTProtoSender, 'send', send):
            await tg.join_group('synthetic_room', account_id=222)
        raise AssertionError('Worker did not reach its exit boundary')


def process_boundaries(root):
    output = []
    for mode, code, used, enqueued in [('uncommitted', 71, 0, False),
                                      ('committed', 72, 1, False), ('enqueued', 73, 1, True)]:
        folder = Path(root)/mode
        folder.mkdir()
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', mode, str(folder)],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == code, (mode, result.returncode, result.stdout, result.stderr)
        path = (folder/'budget-path.txt').read_text()
        status = JoinBudget(path, clock=lambda: 1000).status(222)
        assert status.used == used
        assert (folder/'sdk-enqueued.txt').exists() is enqueued
        output.append(dict(exit_at=mode, return_code=code, persisted_charge=status.used,
                           sdk_enqueue_observed=enqueued))
    return output


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata25-pr-probes-') as root:
        print(json.dumps(dict(probe='process_boundaries', result=process_boundaries(root))), flush=True)
        with environment(root):
            cases = [policy_changed_during_proof, different_facades_share_one_cap, database_failures,
                     serialized_local_faults_and_rpc_origins, cancel_after_identity_change_in_held_proof,
                     wrapped_result_cache_and_reply_failure, protocol_repair_retains_one_admission]
            for case in cases:
                try:
                    result = await asyncio.wait_for(case(), 40)
                    print(json.dumps(dict(probe=case.__name__, result=result)), flush=True)
                finally:
                    await t.cleanup()


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        asyncio.run(crash_worker(sys.argv[2], sys.argv[3]))
    else:
        asyncio.run(main())
