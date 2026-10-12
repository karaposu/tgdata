"""Worker protocol/source composition on actual Telethon and SQLite, offline."""
import asyncio
from datetime import timedelta
import inspect
import io
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from telethon import errors, functions, types
from telethon.crypto import AuthKey
from telethon.extensions import BinaryReader
from telethon._updates import SessionState
from tgdata import MessageBatch, ReadBudget, JoinBudget
from tgdata.connection_engine import AuthRequiredError, ConnectionEngine
from tgdata.worker_engine import Worker, WorkerAccount
from tgdata import worker_protocol as protocol
from tgdata.smoke_tests import test_32_account_operation as f
from tgdata.smoke_tests import test_19_message_batches as b

SECRET = 'WORKER_PRIVATE_TEXT_MUST_NOT_ESCAPE'
CHAT = -1000000000007
AUTH_CASES = {
    'auth_unknown401': (401, SECRET, None),
    'auth_unknown406': (406, SECRET, None),
    'auth_generic403': (403, SECRET, None),
    'auth_unregistered': (401, 'AUTH_KEY_UNREGISTERED', 'AUTH_KEY_UNREGISTERED'),
    'auth_revoked': (401, 'SESSION_REVOKED', 'SESSION_REVOKED'),
    'auth_banned': (401, 'USER_DEACTIVATED_BAN', 'USER_DEACTIVATED_BAN'),
}


def sdk_error(code, text):
    """Decode actual TL error bytes through the pinned SDK's error mapping."""
    with BinaryReader(bytes(types.RpcError(code, text))) as reader:
        decoded = reader.tgread_object()
    return errors.rpc_message_to_error(decoded,
        functions.users.GetUsersRequest([types.InputUserSelf()]))


def assert_auth_error(detail, mode):
    code, text, reason = AUTH_CASES[mode]
    assert detail.get('reason') == reason
    assert SECRET not in json.dumps(detail)
    if code == 403:
        assert detail['category'] == 'telegram_error' and detail['code'] == 403
        assert detail['type'] == 'ForbiddenError'
    else:
        assert detail['category'] == 'authentication_required'
        assert detail['type'] == 'AuthRequiredError'
        assert detail['first_login'] is False
        assert detail['banned'] is (mode == 'auth_banned')


def assert_auth_source_free(calls):
    assert not set(calls).intersection(('GetHistoryRequest', 'GetChannelsRequest',
        'CheckChatInviteRequest', 'JoinChannelRequest', 'ImportChatInviteRequest',
        'ResolveUsernameRequest', 'SendCodeRequest', 'SignInRequest'))


def fixture(root, aid):
    config = root / ('account-{}.ini'.format(aid))
    session = root / ('session-{}'.format(aid))
    config.write_text('[Telegram]\napi_id=12345\napi_hash={}\nsession_file={}\n'
        'device_model=Worker Test Device\nsystem_version=Worker Test OS\n'
        'app_version=1.0\nlang_code=en\nsystem_lang_code=en-GB\n'.format(SECRET, session))
    return SimpleNamespace(config=config, name=str(session), accounts=[], actual=aid, cached=999,
        logged_in=True, connect_error=None, responses={}, scripts={}, clients=[], store=f.Store(),
        room=b.f.room(), catalog=list(range(101, 401)), seed_group=False,
        join_result=None, hook=None, trace=None, key=bytes([aid % 251 + 1]) * 256)


class Wire(f.Wire):
    def __init__(self, client, item):
        super().__init__(client, item)
        self.account = item.actual
        self.auth_key = client.session.auth_key or AuthKey(item.key)
        self.requests = []
        self.script = {key: list(values) for key, values in item.scripts.items()}

    def send(self, request, ordered=False):
        bytes(request)
        while hasattr(request, 'query'):
            request = request.query
        self.requests.append(request)
        if self.fixture.trace is not None:
            self.fixture.trace('request', type(request).__name__)
        name = type(request).__name__
        if self.script.get(name) or name in self.fixture.responses:
            response = self.script[name][0] if self.script.get(name) else self.fixture.responses[name]
            if isinstance(response, errors.RPCError) and response.request is None:
                response.request = request  # The SDK wire decoder binds errors to their actual request.
            return super().send(request, ordered)
        if isinstance(request, functions.contacts.ResolveUsernameRequest):
            result = types.contacts.ResolvedPeer(types.PeerChannel(self.fixture.room.id),
                                                [self.fixture.room], [])
        elif isinstance(request, functions.channels.GetChannelsRequest):
            result = types.messages.Chats([self.fixture.room])
        elif isinstance(request, functions.messages.CheckChatInviteRequest):
            result = types.ChatInvite('Preview', types.PhotoEmpty(1), 0, 1, channel=True, megagroup=True)
        elif isinstance(request, functions.messages.GetHistoryRequest):
            ids = ([max(self.fixture.catalog)] if request.offset_id == 0 and self.fixture.catalog else
                   [n for n in self.fixture.catalog if n >= request.offset_id][:request.limit])
            result = b.f.response([b.f.message(n) for n in reversed(ids)])
        elif isinstance(request, (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest)):
            result = self.fixture.join_result or types.messages.ChatInviteJoinResultOk(
                types.Updates([], [], [], f.DATE, 0))
        else:
            return super().send(request, ordered)
        self.calls.append(name)
        future = asyncio.get_running_loop().create_future()
        future.set_result(result)
        return future

    async def disconnect(self):
        if self.fixture.trace is not None:
            self.fixture.trace('cleanup', 'entered')
        await super().disconnect()
        if self.fixture.trace is not None:
            self.fixture.trace('cleanup', 'finished')


def install_factory(fixtures):
    original = ConnectionEngine._new_client
    by_path = {str(item.config.resolve()): item for item in fixtures.values()}
    def factory(engine, session_file=None, **options):
        client = original(engine, session_file, **options)
        item = by_path[str(Path(engine.config_path).resolve())]
        if item.logged_in and client.session.auth_key is None:
            client.session.auth_key = AuthKey(item.key)
            client.session.save()
        client._sender = Wire(client, item)
        if item.cached is not None:
            client._mb_entity_cache.set_self_user(item.cached, False, 1)
            client._message_box.load(SessionState(0, 0, False, 1, 1, int(f.DATE.timestamp()), 1, None), [])
        if item.seed_group:
            client.session.process_entities([item.room])
        item.clients.append(client)
        if item.hook is not None:
            item.hook(client, client._sender)
        return client
    return patch.object(ConnectionEngine, '_new_client', factory)


class Setup:
    async def __aenter__(self):
        self.directory = tempfile.TemporaryDirectory(prefix='tgdata_worker_core_')
        self.root = Path(self.directory.name)
        self.budget = ReadBudget(self.root / 'read.sqlite3')
        self.join = JoinBudget(self.root / 'join.sqlite3', create=True)
        self.items = {aid: fixture(self.root, aid) for aid in (111, 222)}
        for aid in self.items:
            self.budget.configure(aid, 1000)
            self.join.configure(aid, 5)
        self.patch = install_factory(self.items)
        self.patch.start()
        self.worker = Worker([WorkerAccount(aid, item.config, session_store=item.store)
                              for aid, item in self.items.items()], worker_id='test-worker',
                             read_budget=self.budget, join_budget=self.join)
        self.decoder, self.next_id = protocol.RequestDecoder(), 1
        return self

    def job(self, operation='read_batch', account=111, **params):
        if not params:
            params = {'group_id': '@synthetic_room', 'after_id': '100', 'limit': 2} \
                if operation == 'read_batch' else {'target': '@synthetic_room'}
        value = dict(version=1, request_id=self.next_id, account_id=str(account),
                     operation=operation, params=params)
        self.next_id += 1
        return self.decoder.decode((json.dumps(value) + '\n').encode())

    async def call(self, operation='read_batch', account=111, **params):
        result = await self.worker.execute(self.job(operation, account, **params))
        frames = [json.loads(raw) for raw in result]
        assert SECRET not in b''.join(result).decode()
        assert all(frame['request_id'] == frames[-1]['request_id'] for frame in frames)
        return frames[-1], frames[:-1]

    async def __aexit__(self, *args):
        for item in self.items.values():
            for client in item.clients:
                client._sender.close_error = None
                if client._sender.close_release is not None:
                    client._sender.close_release.set()
                await client.disconnect()
        await self.worker.close()
        self.patch.stop()
        self.directory.cleanup()


async def expect(kind, work):
    try:
        await work
    except kind as error:
        return error
    raise AssertionError('Expected ' + kind.__name__)


async def until(predicate):
    for _ in range(10000):
        if predicate(): return
        await asyncio.sleep(.001)
    raise AssertionError('Fixture condition did not arrive')


async def test_ready_is_local_and_inventory_is_exclusive():
    async with Setup() as s:
        ready = s.worker.ready()
        assert ready['account_count'] == 2 and ready['account_ids'] == ['111', '222']
        assert ready['state'] == 'idle' and not any(item.clients for item in s.items.values())
        assert all(app.connection_engine.pool_size == 1 for app in s.worker._apps.values())
        accounts = s.worker.accounts
        for rows in ([accounts[0], accounts[0]], [WorkerAccount(333, s.items[111].config), accounts[0]]):
            try: Worker(rows, worker_id='x', read_budget=s.budget)
            except protocol.WorkerError: pass
            else: raise AssertionError('Duplicate inventory accepted')
        assert SECRET not in repr(accounts)


async def test_strict_decoder_and_consumed_request_ids():
    d = protocol.RequestDecoder()
    bad = [b'\xff\n', b'[]\n', b'{"version":1,"version":1}\n', b'{"version":NaN}\n',
           b'{"version":true,"request_id":1}\n', b'{}', b'x' * (protocol.MAX_REQUEST_BYTES + 1)]
    for raw in bad:
        try:d.decode(raw)
        except protocol.WorkerError:pass
        else:raise AssertionError('Invalid frame accepted')
    base = dict(version=1, request_id=1, account_id='111', operation='read_batch',
                params=dict(group_id='@room', limit=True))
    try:d.decode((json.dumps(base)+'\n').encode())
    except protocol.WorkerError as error:assert error.request_id == 1
    else:raise AssertionError('Boolean limit accepted')
    base['params']['limit'] = 1
    try:d.decode((json.dumps(base)+'\n').encode())
    except protocol.WorkerError as error:assert error.code == 'stale_request_id'
    else:raise AssertionError('Consumed identity reused')
    base['request_id'] = 2
    assert d.decode((json.dumps(base)+'\r\n').encode()).request_id == 2


async def test_two_accounts_real_pagination_and_exact_batch():
    async with Setup() as s:
        result, _ = await s.call(group_id='@synthetic_room', after_id='100', limit=150)
        batch = MessageBatch(result['data'])
        assert len(batch.messages) == 150 and result['account_id'] == '111'
        assert s.budget.status(111).used == 150 and s.budget.status(222).used == 0
        result2, _ = await s.call(account=222)
        assert result2['account_id'] == '222' and len(result2['data']['messages']) == 2
        assert s.budget.status(222).used == 2
        assert all(c._sender.closed for item in s.items.values() for c in item.clients)
        assert all(app.connection_engine._primary_client is None and app.connection_engine._pool is None
                   for app in s.worker._apps.values())


async def test_group_lookup_access_and_invite_qualification():
    async with Setup() as s:
        lookup, _ = await s.call('lookup_group')
        assert lookup['ok'] and lookup['data']['group']['peer_id'] == str(CHAT)
        access, _ = await s.call('check_group_access')
        assert access['ok'] and access['data']['status'] == 'readable'
        assert s.budget.status(111).used == 1
        preview, _ = await s.call('check_group_access', target='https://t.me/+PrivateToken')
        assert preview['data']['status'] == 'unprobed' and preview['data']['readable'] is None
        assert 'PrivateToken' not in json.dumps(preview)
        s.items[111].scripts['GetHistoryRequest'] = [errors.ChannelPrivateError(request=f.history())]
        denied, events = await s.call('check_group_access')
        assert denied['ok'] and denied['data']['status'] == 'denied' and not denied['data']['readable']
        assert events[-1]['event']['account']['user_id'] == '111'


async def test_join_outcomes_and_real_allowance_claims():
    async with Setup() as s:
        already, _ = await s.call('join_group')
        assert already['data']['status'] == 'already_joined' and s.join.status(111).used == 0
        s.items[111].room.left = True
        joined, _ = await s.call('join_group')
        assert joined['data']['status'] == 'joined' and s.join.status(111).used == 1
        s.items[111].scripts['JoinChannelRequest'] = [errors.InviteRequestSentError(request=None)]
        requested, _ = await s.call('join_group')
        assert requested['data']['status'] == 'requested' and requested['data']['member'] is None
        assert s.join.status(111).used == 2 and s.budget.status(111).used == 0


async def test_join_webview_ids_and_refusal_preserve_meaning():
    async with Setup() as s:
        s.items[111].room.left = True
        s.items[111].join_result = types.messages.ChatInviteJoinResultWebView(123, (1 << 63) - 1, [])
        value, _ = await s.call('join_group')
        assert value['data']['query_id'] == str((1 << 63) - 1)
        assert value['data']['status'] == 'interaction_required' and value['data']['member'] is None
        s.join.configure(111, 0)
        refused, events = await s.call('join_group')
        assert not refused['ok'] and refused['error']['type'] == 'JoinBudgetExceeded'
        assert not events and 'JoinChannelRequest' not in s.items[111].clients[-1]._sender.calls


async def test_missing_join_policy_is_local():
    async with Setup() as s:
        s.worker.join_budget = None
        result, events = await s.call('join_group')
        assert result['error']['code'] == 'join_disabled' and not events and not s.items[111].clients


async def test_original_wait_partial_batch_and_health_survive():
    async with Setup() as s:
        failure = errors.FloodWaitError(request=f.history(), capture=7200)
        s.items[111].scripts['GetHistoryRequest'] = [
            b.f.response([b.f.message(n) for n in reversed(range(101, 201))]), failure]
        result, events = await s.call(group_id='@synthetic_room', after_id='100', limit=200)
        assert not result['ok'] and result['error']['wait_seconds'] == 7200
        batch = MessageBatch(result['partial_result'])
        assert len(batch.messages) == 100 and batch.batch_id == failure.partial_result.batch_id
        assert events[-1]['event']['wait_seconds'] == 7200 and s.budget.status(111).used == 200
        assert not s.items[222].clients and not s.worker.stopping


async def test_unknown_rpc_text_and_metadata_fault_do_not_escape():
    async with Setup() as s:
        s.items[111].scripts['GetHistoryRequest'] = [errors.RPCError(f.history(), SECRET, 403)]
        result, events = await s.call()
        assert result['error']['type'] == 'RPCError' and result['error']['code'] == 403
        assert events[-1]['event']['error'] is None
        class BadMetadata(RuntimeError):
            @property
            def partial_result(self): raise asyncio.CancelledError(SECRET)
        s.items[111].responses['ResolveUsernameRequest'] = BadMetadata(SECRET)
        result, _ = await s.call('lookup_group')
        assert result['error']['type'] == 'BadMetadata' and result['partial_result'] is None
        assert not s.worker.stopping


async def authentication_cases(operation):
    for mode, (code, text, reason) in AUTH_CASES.items():
        async with Setup() as s:
            s.items[111].scripts['GetUsersRequest'] = [sdk_error(code, text)]
            result, events = await s.call(operation)
            assert not result['ok'] and not events and not s.worker.stopping
            assert_auth_error(result['error'], mode)
            sender = s.items[111].clients[-1]._sender
            assert sender.closed and sender.close_calls == 1
            assert_auth_source_free(sender.calls)
            assert s.budget.status(111).used == s.join.status(111).used == 0
            assert not s.items[222].clients


async def test_sdk_authentication_read_batch():
    await authentication_cases('read_batch')


async def test_sdk_authentication_lookup_group():
    await authentication_cases('lookup_group')


async def test_sdk_authentication_check_group_access():
    await authentication_cases('check_group_access')


async def test_sdk_authentication_join_group():
    await authentication_cases('join_group')


async def test_library_authentication_reason_is_unchanged():
    for mode, (code, text, reason) in AUTH_CASES.items():
        if code == 403:
            continue
        wrapped = ConnectionEngine._auth_required('private-session', sdk_error(code, text), False)
        assert wrapped.reason == text  # Ordinary library callers still receive the SDK reason.
        assert_auth_error(protocol.describe_error(wrapped), mode)


async def test_authentication_metadata_faults_are_omitted():
    class BadMetadata(AuthRequiredError):
        def __getattribute__(self, name):
            if name in ('reason', 'banned', 'first_login'):
                raise asyncio.CancelledError(SECRET)
            return super().__getattribute__(name)
    class BadString(str):
        def __hash__(self):
            raise AssertionError('Untrusted reason was hashed')
    for error in (BadMetadata(SECRET),
                  AuthRequiredError(SECRET, reason=BadString('SESSION_REVOKED'),
                                    banned=1, first_login=0)):
        assert protocol.describe_error(error) == {
            'category': 'authentication_required', 'type': type(error).__name__}
    assert asyncio.current_task().cancelling() == 0


async def test_authentication_delivery_failure_uses_same_projection():
    original = protocol.encode_frame
    def fail_terminal(value, **options):
        if value.get('kind') == 'result' and value.get('error', {}).get('category') in (
                'authentication_required', 'telegram_error'):
            raise protocol.WorkerError('delivery_failed')  # After the actual source error/cleanup.
        return original(value, **options)
    for mode, (code, text, reason) in AUTH_CASES.items():
        async with Setup() as s:
            s.items[111].scripts['GetUsersRequest'] = [sdk_error(code, text)]
            with patch.object(protocol, 'encode_frame', fail_terminal):
                result, events = await s.call()
            assert result['error']['code'] == 'delivery_failed' and not events
            assert result['partial_omitted'] and result['worker_stopping']
            assert result['source_outcome'] == 'raised'
            assert_auth_error(result['source_error'], mode)
            sender = s.items[111].clients[-1]._sender
            assert sender.closed and sender.close_calls == 1
            assert_auth_source_free(sender.calls)
            assert s.budget.status(111).used == s.join.status(111).used == 0
            assert (await expect(protocol.WorkerError,
                s.worker.execute(s.job(account=222)))).code == 'worker_stopping'
            assert not s.items[222].clients


async def test_fatal_authentication_uses_same_projection():
    from tgdata.worker import _fatal
    for mode, (code, text, reason) in AUTH_CASES.items():
        if code == 403:
            continue
        # Shared fatal encoder control, not a claim that startup authenticates.
        error = ConnectionEngine._auth_required('private-session', sdk_error(code, text), False)
        output = io.BytesIO()
        _fatal(error, output)
        raw = output.getvalue()
        assert SECRET.encode() not in raw
        frame = json.loads(raw)
        assert frame['kind'] == 'fatal' and frame['worker_stopping']
        assert frame['error']['category'] == 'configuration_error'
        detail = dict(frame['error'], category='authentication_required')
        assert_auth_error(detail, mode)


async def test_missing_authentication_never_requests_code():
    async with Setup() as s:
        s.items[111].logged_in = False
        s.items[111].responses['GetStateRequest'] = errors.AuthKeyUnregisteredError(request=None)
        result, events = await s.call('lookup_group')
        assert result['error']['category'] == 'authentication_required'
        assert result['error']['first_login'] and not events
        assert not any('Code' in name or 'SignIn' in name for name in s.items[111].clients[-1]._sender.calls)


async def test_wrong_owner_and_changed_admission_send_nothing():
    for operation in ('read_batch', 'join_group'):
        async with Setup() as s:
            s.items[111].actual = 222
            s.items[111].room.left = True
            result, _ = await s.call(operation)
            assert result['error']['category'] == 'identity_mismatch'
            assert not any('History' in n or 'Join' in n or 'ResolveUsername' in n
                           for n in s.items[111].clients[-1]._sender.calls)
            s.items[111].actual = 111
            s.items[111].scripts['GetUsersRequest'] = [[f.user(111)], [f.user(222)]]
            result, _ = await s.call(operation)
            assert result['error']['category'] == 'identity_mismatch'
            assert not any('History' in n or 'Join' in n for n in s.items[111].clients[-1]._sender.calls)
            assert s.budget.status(111).used == s.budget.status(222).used == s.join.status(111).used == 0


async def test_bounded_resolution_and_secret_invite():
    async with Setup() as s:
        for group in (str(CHAT), 'https://t.me/+PrivateToken', '+905551234567'):
            value, _ = await s.call(group_id=group, after_id='100', limit=1)
            assert value['error']['type'] == 'GroupReferenceError'
            assert 'PrivateToken' not in json.dumps(value)
            assert not any(name in s.items[111].clients[-1]._sender.calls for name in
                           ('GetDialogsRequest', 'GetContactsRequest', 'GetHistoryRequest', 'ImportChatInviteRequest'))
        s.items[111].seed_group = True
        value, _ = await s.call(group_id=str(CHAT), after_id='100', limit=1)
        assert value['ok'] and len(value['data']['messages']) == 1


async def test_dates_and_max_cursor_do_not_invent_access_recovery():
    async with Setup() as s:
        date = b.f.message(101).date
        value, _ = await s.call(group_id='@synthetic_room', after_id='100', limit=2,
            start_date=(date - timedelta(days=1)).isoformat(), end_date=(date + timedelta(days=1)).isoformat())
        assert value['ok'] and len(value['data']['messages']) == 2
        s.items[111].scripts['GetHistoryRequest'] = [errors.ChannelPrivateError(request=f.history())]
        await s.call()
        s.items[111].scripts.clear()
        value, events = await s.call(group_id='@synthetic_room', after_id=str(protocol.MAX_MESSAGE_ID), limit=1)
        assert value['ok'] and value['data']['messages'] == []
        assert 'GetHistoryRequest' not in s.items[111].clients[-1]._sender.calls
        assert s.worker._apps[111].get_account_health(111)['no_access']
        assert not any(row['event']['verdict'] == 'ok' and row['event']['scope'] == 'group' for row in events)


async def test_cleanup_failure_preserves_outcome_and_refuses_next_job():
    for mode in ('success', 'source', 'setup', 'internal_cancel'):
        async with Setup() as s:
            failure = asyncio.CancelledError(SECRET) if mode == 'internal_cancel' else OSError(SECRET)
            s.items[111].hook = lambda client, sender: setattr(sender, 'close_error', failure)
            if mode == 'source':
                s.items[111].scripts['GetHistoryRequest'] = [errors.ChannelPrivateError(request=f.history())]
            if mode == 'setup':
                s.items[111].connect_error = LookupError(SECRET)
            value, _ = await s.call()
            assert value['worker_stopping'] and s.worker.stopping
            assert value['ok'] is (mode in ('success', 'internal_cancel'))
            if mode == 'setup': assert value['error']['type'] == 'LookupError'
            count = len(s.items[111].clients)
            error = await expect(protocol.WorkerError, s.worker.execute(s.job(account=222)))
            assert error.code == 'worker_stopping' and len(s.items[111].clients) == count
            assert not s.items[222].clients


async def test_repeated_cancellation_waits_for_actual_cleanup():
    async with Setup() as s:
        pending, release = asyncio.get_running_loop().create_future(), asyncio.Event()
        s.items[111].scripts['GetHistoryRequest'] = [pending]
        s.items[111].hook = lambda client, sender: setattr(sender, 'close_release', release)
        task = asyncio.create_task(s.worker.execute(s.job()))
        await until(lambda: bool(s.items[111].clients) and 'GetHistoryRequest' in s.items[111].clients[-1]._sender.calls)
        sender = s.items[111].clients[-1]._sender
        task.cancel()
        await sender.close_entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done() and not sender.closed
        release.set()
        await expect(asyncio.CancelledError, task)
        assert sender.closed and s.worker.stopping and pending.cancelled()
        assert s.budget.status(111).used == 2


async def test_overlap_and_callback_child_close_refuse_without_cycle():
    async with Setup() as s:
        pending = asyncio.get_running_loop().create_future()
        s.items[111].scripts['GetHistoryRequest'] = [pending]
        task = asyncio.create_task(s.worker.execute(s.job()))
        await until(lambda: bool(s.items[111].clients) and 'GetHistoryRequest' in s.items[111].clients[-1]._sender.calls)
        assert (await expect(protocol.WorkerError, s.worker.execute(s.job(account=222)))).code == 'worker_busy'
        assert (await expect(protocol.WorkerError, s.worker.close())).code == 'worker_busy'
        pending.set_result(b.f.response([b.f.message(102), b.f.message(101)]))
        await task
        async def callback(event):
            error = await expect(protocol.WorkerError, asyncio.create_task(s.worker.close()))
            assert error.code == 'worker_busy'
        for monitor in s.worker._apps[111]._account_health.values(): monitor.callback = callback
        s.items[111].scripts['GetHistoryRequest'] = [errors.FloodWaitError(request=f.history(), capture=30)]
        value, _ = await asyncio.wait_for(s.call(), 3)
        assert value['error']['wait_seconds'] == 30 and not s.worker.stopping


async def test_observer_owned_cancellation_does_not_cancel_source():
    async with Setup() as s:
        async def callback(event):
            future = asyncio.get_running_loop().create_future();future.cancel();await future
        s.worker._apps[111]._health.callback = callback  # Explicit observer fault injection.
        failure = errors.FloodWaitError(request=f.history(), capture=7200)
        s.items[111].scripts['GetHistoryRequest'] = [
            b.f.response([b.f.message(n) for n in reversed(range(101, 201))]), failure]
        value, _ = await s.call(group_id='@synthetic_room', after_id='100', limit=200)
        assert value['error']['wait_seconds'] == 7200 and len(value['partial_result']['messages']) == 100
        assert not s.worker.stopping and asyncio.current_task().cancelling() == 0


async def test_delivery_limit_is_explicit_and_keeps_source_metadata():
    async with Setup() as s:
        failure = errors.FloodWaitError(request=f.history(), capture=7200)
        s.items[111].scripts['GetHistoryRequest'] = [
            b.f.response([b.f.message(n) for n in reversed(range(101, 201))]), failure]
        with patch.object(protocol, 'MAX_RESPONSE_BYTES', 8192):
            value, events = await s.call(group_id='@synthetic_room', after_id='100', limit=200)
        assert value['error']['code'] == 'delivery_failed' and value['partial_omitted']
        assert value['source_error']['wait_seconds'] == 7200 and value['worker_stopping']
        assert value['data'] is None and not events and s.budget.status(111).used == 200
        assert value['health_dropped'] == 1  # Pre-encoding rejected the entire unpublished reply set.


async def test_budget_refusal_and_factory_policy_are_preserved():
    async with Setup() as s:
        s.budget.configure(111, 0)
        value, events = await s.call()
        assert value['error']['type'] == 'ReadBudgetExceeded' and not events
        client = s.items[111].clients[-1]
        assert client._sender.policy_at_connect == dict(flood=0, requests=0, connections=0,
            delay=0, reconnect=False, last_error=True, updates=False)
        assert client._init_request.device_model == 'Worker Test Device'
        assert 'GetHistoryRequest' not in client._sender.calls


async def test_budget_exhaustion_keeps_the_completed_prefix():
    async with Setup() as s:
        s.budget.configure(111, 1)
        value, events = await s.call()
        assert value['error']['type'] == 'ReadBudgetExceeded' and not events
        assert len(value['partial_result']['messages']) == 1
        assert s.budget.status(111).used == 1 and not s.items[222].clients


async def test_mutation_named_error_from_identity_is_not_join_success():
    async with Setup() as s:
        s.items[111].room.left = True
        s.items[111].scripts['GetUsersRequest'] = [errors.InviteRequestSentError(request=None)]
        value, _ = await s.call('join_group')
        assert not value['ok'] and value['error']['type'] == 'InviteRequestSentError'
        assert s.join.status(111).used == 0
        assert 'JoinChannelRequest' not in s.items[111].clients[-1]._sender.calls


async def test_notification_capacity_is_counted_without_changing_source():
    from tgdata.owned_health import _OwnedHealthMonitor
    original = _OwnedHealthMonitor.dispatch
    def many(monitor, call):
        # Explicit capacity fault at notification dispatch, after one actual RPC.
        if call.events:
            call.events = call.events * (protocol.MAX_HEALTH_EVENTS + 4)
        original(monitor, call)
    async with Setup() as s:
        s.items[111].scripts['GetHistoryRequest'] = [errors.FloodWaitError(request=f.history(), capture=30)]
        with patch.object(_OwnedHealthMonitor, 'dispatch', many):
            value, events = await s.call()
        assert len(events) == protocol.MAX_HEALTH_EVENTS and value['health_dropped'] == 4
        assert value['error']['wait_seconds'] == 30 and not s.worker.stopping


async def test_store_clients_create_no_session_files_or_suffixes():
    async with Setup() as s:
        await s.call()
        await s.call(account=222)
        assert not list(s.root.glob('*.session'))
        assert all(item.store for item in s.items.values())


async def test_serialization_failure_keeps_known_source_outcome():
    original = protocol.encode_frame
    def broken(value, **options):
        if value.get('kind') == 'result' and value.get('ok'):
            # Explicit serializer failure after the actual SDK result/cleanup.
            raise ValueError(SECRET)
        return original(value, **options)
    async with Setup() as s:
        with patch.object(protocol, 'encode_frame', broken):
            value, events = await s.call()
        assert value['error']['code'] == 'delivery_failed' and value['partial_omitted']
        assert value['source_outcome'] == 'returned' and value['source_result_type'] == 'MessageBatch'
        assert value['worker_stopping'] and not events and s.budget.status(111).used == 2
        assert s.items[111].clients[-1]._sender.closed


async def test_one_large_health_event_is_counted_as_dropped():
    from tgdata.owned_health import _OwnedHealthMonitor
    original = _OwnedHealthMonitor.dispatch
    def oversized(monitor, call):
        if call.events:
            call.events[0]['session_name'] = 'x' * (protocol.MAX_HEALTH_EVENT_BYTES + 1)
        original(monitor, call)
    async with Setup() as s:
        s.items[111].scripts['GetHistoryRequest'] = [errors.FloodWaitError(request=f.history(), capture=30)]
        with patch.object(_OwnedHealthMonitor, 'dispatch', oversized):
            value, events = await s.call()
        assert not events and value['health_dropped'] == 1
        assert value['error']['wait_seconds'] == 30 and not s.worker.stopping


async def main():
    tests = [value for name, value in globals().items() if name.startswith('test_') and inspect.iscoroutinefunction(value)]
    results = []
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        for test in tests:
            try:
                await asyncio.wait_for(test(), 30)
                print('PASS', test.__name__)
                results.append(True)
            except Exception:
                traceback.print_exc()
                print('FAIL', test.__name__)
                results.append(False)
    print('Passed: {}/{}'.format(sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    raise SystemExit(asyncio.run(main()))
