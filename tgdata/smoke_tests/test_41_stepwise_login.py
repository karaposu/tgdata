"""Full offline LoginFlow composition: actual SDK/SRP/codec, controlled wire.

No sockets, console input or real credentials. This does not qualify Telegram's
live delivery/acceptance. Run as a module; failures return a nonzero exit code.
"""
import asyncio
import base64
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import inspect
import io
import json
import logging
from pathlib import Path
import socket
import tempfile
import traceback
from unittest.mock import patch

from telethon import errors, functions, types
from telethon.crypto import AuthKey
from tgdata import health
from tgdata.connection_engine import ConnectionEngine
from tgdata.session_store import StoredSession
from tgdata.login import LoginFlow, LoginError

PHONE = '+15550001234'
CODE = '12345'
PASSWORD = 'synthetic-private-password'
HASH = 'synthetic-private-code-hash'
KEY = bytes(range(256))
OTHER = bytes(reversed(range(256)))
DATE = datetime(2026, 10, 14, tzinfo=timezone.utc)
PRIME = bytes.fromhex('''
C71CAEB9C6B1C9048E6C522F70F13F73980D40238E3E21C14934D037563D930F
48198A0AA7C14058229493D22530F4DBFA336F6E0AC925139543AE D44CCE7C37
20FD51F69458705AC68CD4FE6B6B13ABDC9746512969328454F18FAF8C595F64
2477FE96BB2A941D5BCD1D4AC8CC49880708FA9B378E3C4F3A9060BEE67CF9A4
A4A695811051907E162753B56B0F6B410DBA74D8A84B2A14B3144E0EF1284754
FD17ED950D5965B4B9DD46582DB1178D169C6BC465B0D6FF9CA3928FEF5B9AE4
E418FC15E83EBEA0F87FA9FF5EED70050DED2849F47BF959D956850CE929851F
0D8115F635B105EE2E4E15D04B2454BF6F4FADF034B10403119CD8E3B92FCC5B
''')


def sha(*parts):
    return hashlib.sha256(b''.join(parts)).digest()


def num(n):
    return n.to_bytes(256, 'big')


class PasswordServer:
    """Independent server-side SRP calculation checks native compute_check."""

    def __init__(self):
        self.p = int.from_bytes(PRIME, 'big')
        self.g, self.s1, self.s2 = 3, b'synthetic-salt1', b'synthetic-salt2'
        h1 = sha(self.s1, PASSWORD.encode(), self.s1)
        h2 = sha(self.s2, h1, self.s2)
        x = int.from_bytes(sha(self.s2, hashlib.pbkdf2_hmac(
            'sha512', h2, self.s1, 100000), self.s2), 'big')
        self.v = pow(self.g, x, self.p)
        self.b = int.from_bytes(b'synthetic-server-secret' * 12, 'big')
        k = int.from_bytes(sha(PRIME, num(self.g)), 'big')
        self.B = (k * self.v + pow(self.g, self.b, self.p)) % self.p

    def parameters(self):
        algo = types.PasswordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow(
            self.s1, self.s2, self.g, PRIME)
        return types.account.Password(types.PasswordKdfAlgoUnknown(),
            types.SecurePasswordKdfAlgoUnknown(), b'', has_password=True,
            current_algo=algo, srp_B=num(self.B), srp_id=711)

    def accepts(self, proof):
        assert isinstance(proof, types.InputCheckPasswordSRP)
        A = int.from_bytes(proof.A, 'big')
        u = int.from_bytes(sha(proof.A, num(self.B)), 'big')
        shared = pow((A * pow(self.v, u, self.p)) % self.p, self.b, self.p)
        combined = bytes(a ^ b for a, b in zip(sha(PRIME), sha(num(self.g))))
        expected = sha(combined, sha(self.s1), sha(self.s2), proof.A,
                       num(self.B), sha(num(shared)))
        return proof.srp_id == 711 and proof.M1 == expected


def config_response():
    values = {}
    for name, parameter in inspect.signature(types.Config).parameters.items():
        if parameter.default is inspect.Parameter.empty:
            values[name] = '' if parameter.annotation is str else 0
    values.update(date=DATE, expires=DATE + timedelta(days=1), this_dc=2,
                  test_mode=False, dc_options=[types.DcOption(2, '149.154.167.51', 443),
                                               types.DcOption(3, '149.154.175.100', 443)])
    return types.Config(**values)


class Service:
    def __init__(self, two_factor=False):
        self.two_factor = two_factor
        self.authorized = set()
        self.challenges = {}
        self.calls = []
        self.clients = []
        self.wires = []
        self.hook = None
        self.connect_hook = None
        self.close_hook = None
        self.password_server = PasswordServer() if two_factor else None
        self.srp_accepted = 0
        self.user = types.User(4242, is_self=True, access_hash=9988,
                               first_name='Synthetic', phone=PHONE[1:])

    def answer(self, wire, request):
        key = wire.auth_key.key
        if isinstance(request, functions.help.GetConfigRequest):
            return config_response()
        if isinstance(request, functions.users.GetUsersRequest):
            if key in self.authorized:
                return [self.user]
            return errors.AuthKeyUnregisteredError(request)
        if isinstance(request, functions.updates.GetStateRequest):
            if key in self.authorized:
                return types.updates.State(0, 0, DATE, 0, 0)
            return errors.AuthKeyUnregisteredError(request)
        if isinstance(request, functions.updates.GetDifferenceRequest):
            return types.updates.DifferenceEmpty(DATE, 0)
        if isinstance(request, functions.auth.SendCodeRequest):
            self.challenges[(key, request.phone_number)] = HASH
            return types.auth.SentCode(types.auth.SentCodeTypeApp(5), HASH, timeout=30)
        if isinstance(request, functions.auth.SignInRequest):
            if self.challenges.get((key, request.phone_number)) != request.phone_code_hash:
                return errors.PhoneCodeExpiredError(request)
            if request.phone_code != CODE:
                return errors.PhoneCodeInvalidError(request)
            if self.two_factor:
                return errors.SessionPasswordNeededError(request)
            self.authorized.add(key)
            return types.auth.Authorization(self.user)
        if isinstance(request, functions.account.GetPasswordRequest):
            return self.password_server.parameters()
        if isinstance(request, functions.auth.CheckPasswordRequest):
            if not self.password_server.accepts(request.password):
                return errors.PasswordHashInvalidError(request)
            self.srp_accepted += 1
            self.authorized.add(key)
            return types.auth.Authorization(self.user)
        raise AssertionError('Unexpected request: ' + type(request).__name__)


class Wire:
    def __init__(self, client, service):
        self.client, self.service = client, service
        self.auth_key = client.session.auth_key or AuthKey(None)
        self.up = False
        self.connections = []
        self.closes = 0
        self._disconnected = None

    def is_connected(self):
        return self.up

    @property
    def disconnected(self):
        return self._disconnected

    async def connect(self, connection):
        self.connections.append(connection)
        if self.service.connect_hook:
            await self.service.connect_hook(self)
        if not self.auth_key.key:
            self.auth_key = AuthKey(OTHER if self.client.session.dc_id == 3 else KEY)
        self.up = True
        self._disconnected = asyncio.get_running_loop().create_future()
        return True

    async def disconnect(self):
        self.closes += 1
        if self.service.close_hook:
            await self.service.close_hook(self)
        self.up = False
        if self._disconnected is not None and not self._disconnected.done():
            self._disconnected.set_result(None)

    def send(self, request, ordered=False):
        bytes(request)  # Real TL serialization, including SRP/code requests.
        while hasattr(request, 'query'):
            request = request.query
        self.service.calls.append(type(request).__name__)

        async def deliver():
            value = NotImplemented
            if self.service.hook:
                value = self.service.hook(self, request)
                if inspect.isawaitable(value):
                    value = await value
            if value is NotImplemented:
                value = self.service.answer(self, request)
            if isinstance(value, BaseException):
                raise value
            return value
        return asyncio.ensure_future(deliver())


@contextmanager
def fixture(two_factor=False):
    service = Service(two_factor)
    with tempfile.TemporaryDirectory(prefix='tgdata-login-test-') as directory:
        path = Path(directory)
        config = path / 'config.ini'
        config.write_text('[Telegram]\napi_id=12345\napi_hash=0123456789abcdef0123456789abcdef\n'
                          'session_file=' + str(path / 'do-not-open') + '\n'
                          'proxy=socks5://synthetic:private-proxy@127.0.0.1:9\n'
                          'require_proxy=true\ndevice_model=Login Test\n')
        original = LoginFlow._make_client

        def make(flow):
            client = original(flow)
            wire = Wire(client, service)
            client._sender = wire
            service.wires.append(wire)
            service.clients.append(client)
            return client
        with patch.object(LoginFlow, '_make_client', make), \
             patch('builtins.input', side_effect=AssertionError('console forbidden')), \
             patch('getpass.getpass', side_effect=AssertionError('console forbidden')):
            yield str(config), service
        assert not list(path.glob('*.session*'))
        assert all(not w.up for w in service.wires), 'live wire after test'


async def expect(kind, awaitable):
    try:
        await awaitable
    except LoginError as exc:
        assert exc.kind == kind, (exc.kind, kind)
        assert exc.__context__ is None, 'native exception leaked in context'
        return exc
    raise AssertionError('Expected LoginError ' + kind)


async def cancel_and_join(task):
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return
    raise AssertionError('Caller cancellation lost')


async def test_roundtrip_and_consumer():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        before = flow.export_state()
        assert (await flow.start(PHONE)).step == 'code'
        state = flow.export_state()
        assert before != state
        flow = LoginFlow(config, state=state)
        assert (await flow.submit_code(CODE)).account_id == 4242
        store = type('Store', (dict,), {'load': dict.get, 'save': dict.__setitem__})()
        store.save('finished', flow.session_data)
        engine = ConnectionEngine(config, session_store=store, interactive_login=False)
        client = engine._new_client('finished')
        assert client.session.auth_key.key == KEY
        assert client.session.get_input_entity(0).access_hash == 4242
        assert client.session.get_input_entity(4242).user_id == 4242
        assert s.calls.count('SendCodeRequest') == 1
        assert s.calls.count('SignInRequest') == 1
        assert 'ResendCodeRequest' not in s.calls
        assert 'GetDifferenceRequest' not in s.calls
        for c in s.clients:
            assert c._request_retries == 0 and c.flood_sleep_threshold == 0
            assert c._proxy['addr'] == '127.0.0.1'
        assert LoginFlow(config, state=flow.export_state()).session_data == flow.session_data


async def test_password_real_srp_and_restart():
    with fixture(True) as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        assert (await flow.submit_code(CODE)).step == 'password'
        flow = LoginFlow(config, state=flow.export_state())
        await expect('invalid_password', flow.submit_password('wrong-synthetic-password'))
        assert flow.status.step == 'password'
        assert (await flow.submit_password(PASSWORD)).step == 'complete'
        assert s.srp_accepted == 1 and s.calls.count('CheckPasswordRequest') == 2
        assert PASSWORD not in flow.export_state()
        data = json.loads(base64.urlsafe_b64decode(flow.export_state().split(':', 2)[2]))
        assert PASSWORD not in json.dumps(data) and CODE not in json.dumps(data)


async def test_local_refusals_and_invalid_code():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await expect('invalid_phone', flow.start('not a phone'))
        await expect('wrong_step', flow.submit_code(CODE))
        await expect('invalid_code', flow.submit_code(''))
        await expect('invalid_password', flow.submit_password(''))
        assert not s.calls
        await flow.start(PHONE)
        await expect('wrong_step', flow.start(PHONE))
        await expect('invalid_code', flow.submit_code('99999'))
        assert flow.status.step == 'code'
        await flow.submit_code(CODE)
        await expect('wrong_step', flow.submit_code(CODE))
        assert s.calls.count('SendCodeRequest') == 1


async def test_config_binding_and_device_defaults():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        state = flow.export_state()
        identity = dict(flow._identity)
        with patch('platform.uname', return_value=type('U', (), {'machine': 'OTHER', 'release': 'different'})()):
            restored = LoginFlow(config, state=state)
        assert restored._identity == identity
        await restored.submit_code(CODE)
        assert {k: getattr(s.clients[-1]._init_request, k) for k in identity} == identity
        Path(config).write_text(Path(config).read_text().replace('127.0.0.1', '127.0.0.2'))
        try:
            LoginFlow(config, state=state)
        except LoginError as exc:
            assert exc.kind == 'invalid_state'
        else:
            raise AssertionError('Changed proxy accepted')


async def test_malformed_state_and_configuration():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        valid = flow.export_state()
        for value in ('private-credential-text', 'x' * 70000, None):
            if value is None:
                data = json.loads(base64.urlsafe_b64decode(valid.split(':', 2)[2]))
                data['step'] = 'complete'
                value = 'tgdata-login:1:' + base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
            try:
                LoginFlow(config, state=value)
            except LoginError as exc:
                assert exc.kind == 'invalid_state' and value not in str(exc)
                assert exc.__context__ is None
            else:
                raise AssertionError('Invalid checkpoint accepted')
        Path(config).write_text('[Telegram]\napi_id=PRIVATE-CONFIG\napi_hash=PRIVATE-HASH\n')
        try:
            LoginFlow(config)
        except LoginError as exc:
            assert exc.kind == 'invalid_configuration' and 'PRIVATE' not in str(exc)
            assert exc.__context__ is None
        else:
            raise AssertionError('Invalid config accepted')
        assert not s.calls


async def test_wait_retained_and_no_implicit_retry():
    with fixture() as (config, s):
        s.hook = lambda w, r: errors.FloodWaitError(r, capture=30) if isinstance(r, functions.auth.SendCodeRequest) else NotImplemented
        flow = LoginFlow(config)
        await expect('wait', flow.start(PHONE))
        flow = LoginFlow(config, state=flow.export_state())
        assert flow.status.step == 'phone'
        before = list(s.calls)
        await expect('wait', flow.start(PHONE))
        assert s.calls == before and s.calls.count('SendCodeRequest') == 1


async def test_expired_challenge_requires_restart():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        s.challenges.clear()
        await expect('restart_required', flow.submit_code(CODE))
        assert flow.status.step == 'restart_required'
        await expect('wrong_step', flow.start(PHONE))
        assert s.calls.count('SendCodeRequest') == 1


async def test_unsupported_interactions():
    responses = [types.auth.SentCode(types.auth.SentCodeTypeEmailCode('s***@example.invalid', 5), HASH),
                 types.auth.SentCodePaymentRequired('product', HASH, 'x@example.invalid', 'subject', 1, 'USD', 1),
                 types.auth.SentCodeSuccess(types.auth.AuthorizationSignUpRequired())]
    for response in responses:
        with fixture() as (config, s):
            s.hook = lambda w, r: response if isinstance(r, functions.auth.SendCodeRequest) else NotImplemented
            flow = LoginFlow(config)
            assert (await flow.start(PHONE)).step == 'unsupported'
            assert flow.status.action_required in ('delivery', 'payment', 'signup')
            await expect('wrong_step', flow.submit_code(CODE))
            assert s.calls.count('SendCodeRequest') == 1


async def test_sent_code_success_and_setup_flag():
    with fixture() as (config, s):
        def reply(w, r):
            if isinstance(r, functions.auth.SendCodeRequest):
                s.authorized.add(w.auth_key.key)
                return types.auth.SentCodeSuccess(types.auth.Authorization(s.user, setup_password_required=True, otherwise_relogin_days=7))
            return NotImplemented
        s.hook = reply
        flow = LoginFlow(config)
        assert (await flow.start(PHONE)).step == 'complete'
        assert flow.status.action_required == 'password_setup' and flow.session_data


async def test_native_migration_and_proxy():
    with fixture() as (config, s):
        def migrate(w, r):
            if isinstance(r, functions.auth.SendCodeRequest) and w.client.session.dc_id != 3:
                return errors.PhoneMigrateError(r, capture=3)
            return NotImplemented
        s.hook = migrate
        flow = LoginFlow(config)
        with patch.object(type(s.clients[0]), '_config', None):
            assert (await flow.start(PHONE)).step == 'code'
        assert flow._session.dc_id == 3 and flow._session.auth_key.key == OTHER
        assert s.calls.count('SendCodeRequest') == 2
        assert any(len(w.connections) == 2 for w in s.wires)
        for w in s.wires:
            assert all(c._proxy == w.client._proxy for c in w.connections)
        flow = LoginFlow(config, state=flow.export_state())
        assert (await flow.submit_code(CODE)).step == 'complete'


async def test_native_migration_cancellation_joins_original_close():
    with fixture() as (config, s):
        entered, release = asyncio.Event(), asyncio.Event()
        s.hook = lambda w, r: errors.PhoneMigrateError(r, capture=3) if isinstance(r, functions.auth.SendCodeRequest) else NotImplemented
        async def hold_close(w):
            entered.set()
            await release.wait()
        s.close_hook = hold_close
        flow = LoginFlow(config)
        with patch.object(type(s.clients[0]), '_config', None):
            task = asyncio.create_task(flow.start(PHONE))
            await entered.wait()
            task.cancel()
            await asyncio.sleep(0)
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done()
            await expect('busy', flow.start(PHONE))
            release.set()
            await cancel_and_join(task)
        assert s.calls.count('SendCodeRequest') == 1
        assert s.wires[-1].closes == 1
        assert all(not w.up for w in s.wires)
        assert flow.status.step == 'uncertain'


async def test_cancel_before_work_and_during_connect():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        async def already_stopped():
            asyncio.current_task().cancel()
            await flow.start(PHONE)
        await cancel_and_join(asyncio.create_task(already_stopped()))
        assert not s.calls
        entered = asyncio.Event()
        async def hold(w):
            entered.set()
            await asyncio.Future()
        s.connect_hook = hold
        task = asyncio.create_task(flow.start(PHONE))
        await entered.wait()
        await cancel_and_join(task)
        assert flow.status.step == 'phone' and not s.calls


async def test_unknown_send_and_authorization_only_check():
    with fixture() as (config, s):
        entered = asyncio.Event()
        async def hold(w, r):
            if isinstance(r, functions.auth.SendCodeRequest):
                s.answer(w, r)  # Source effect occurred; caller never got hash.
                entered.set()
                await asyncio.Future()
            return NotImplemented
        s.hook = hold
        flow = LoginFlow(config)
        task = asyncio.create_task(flow.start(PHONE))
        await entered.wait()
        await cancel_and_join(task)
        assert flow.status.step == 'uncertain'
        flow = LoginFlow(config, state=flow.export_state())
        s.hook = None
        assert (await flow.check_authorization()).step == 'restart_required'
        assert s.calls.count('SendCodeRequest') == 1


async def test_unknown_signin_recovers_authorization():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        def lose_reply(w, r):
            if isinstance(r, functions.auth.SignInRequest):
                s.answer(w, r)
                return OSError('synthetic-private-response-loss')
            return NotImplemented
        s.hook = lose_reply
        await expect('transport_error', flow.submit_code(CODE))
        assert flow.status.step == 'uncertain'
        flow = LoginFlow(config, state=flow.export_state())
        assert (await flow.check_authorization()).step == 'complete'
        assert flow.session_data and s.calls.count('SignInRequest') == 1
        assert s.calls.count('SendCodeRequest') == 1


async def test_unknown_signin_not_authorized_allows_explicit_input():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        s.hook = lambda w, r: OSError('lost') if isinstance(r, functions.auth.SignInRequest) else NotImplemented
        await expect('transport_error', flow.submit_code(CODE))
        s.hook = None
        assert (await flow.check_authorization()).step == 'code'
        assert (await flow.submit_code(CODE)).step == 'complete'


async def test_known_challenge_retained_during_cancelled_cleanup():
    with fixture() as (config, s):
        entered, release = asyncio.Event(), asyncio.Event()
        async def hold(w):
            entered.set()
            await release.wait()
        s.close_hook = hold
        flow = LoginFlow(config)
        task = asyncio.create_task(flow.start(PHONE))
        await entered.wait()
        assert flow.status.step == 'code'
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        try:
            flow.export_state()
        except LoginError as exc:
            assert exc.kind == 'busy'
        else:
            raise AssertionError('In-flight export allowed')
        release.set()
        await cancel_and_join(task)
        flow = LoginFlow(config, state=flow.export_state())
        s.close_hook = None
        assert (await flow.submit_code(CODE)).step == 'complete'


async def test_known_auth_retained_after_cleanup_failure_and_retry():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        async def fail(w):
            raise OSError('SECRET cleanup detail')
        s.close_hook = fail
        result = await flow.submit_code(CODE)
        assert result.step == 'complete' and result.cleanup_pending
        await expect('cleanup_required', flow.check_authorization())
        try:
            flow.session_data
        except LoginError as exc:
            assert exc.kind == 'cleanup_required'
        else:
            raise AssertionError('Unsettled export allowed')
        await expect('cleanup_required', flow.close())
        s.close_hook = None
        assert not (await flow.close()).cleanup_pending
        assert flow.session_data and s.calls.count('SignInRequest') == 1


async def test_component_cancellation_is_not_caller_stop():
    with fixture() as (config, s):
        s.hook = lambda w, r: asyncio.CancelledError('SECRET') if isinstance(r, functions.auth.SendCodeRequest) else NotImplemented
        flow = LoginFlow(config)
        await expect('interrupted', flow.start(PHONE))
        assert flow.status.step == 'uncertain'


async def test_known_auth_survives_later_self_failure():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        await flow.submit_code(CODE)
        flow = LoginFlow(config, state=flow.export_state())
        count = 0
        def self_failure(w, r):
            nonlocal count
            if isinstance(r, functions.users.GetUsersRequest):
                count += 1
                if count > 1:
                    return OSError('post-auth failure')
            return NotImplemented
        # Force empty native message box so native connect invokes the real hook.
        flow._session._update_states.clear()
        s.hook = self_failure
        await expect('transport_error', flow.check_authorization())
        assert flow.status.step == 'complete' and flow.session_data


async def test_live_slot_untouched_and_save_failure_retry():
    with fixture() as (config, s):
        existing = Path(config).parent / 'do-not-open.session'
        existing.write_text('original credential sentinel')
        flow = LoginFlow(config)
        await flow.start(PHONE)
        await flow.submit_code(CODE)
        credential = flow.session_data
        assert existing.read_text() == 'original credential sentinel'
        existing.unlink()  # fixture's no-new-session check
        store = {}
        try:
            raise OSError('application store failed')
        except OSError:
            store['intended-account'] = flow.session_data
        assert store['intended-account'] == credential
        assert s.calls.count('SendCodeRequest') == 1


async def test_identity_mismatch_before_auth_mutation():
    with fixture() as (config, s):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        s.authorized.add(KEY)
        s.user.phone = '15550009999'
        await expect('identity_mismatch', flow.submit_code(CODE))
        assert flow.status.step == 'unsupported'
        assert 'SignInRequest' not in s.calls


async def test_safe_observations_logs_and_health():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    root = logging.getLogger()
    root.addHandler(handler)
    old = root.level
    root.setLevel(logging.DEBUG)
    try:
        with fixture() as (config, s):
            flow = LoginFlow(config)
            await flow.start(PHONE)
            s.hook = lambda w, r: OSError(PHONE + PASSWORD + HASH) if isinstance(r, functions.auth.SignInRequest) else NotImplemented
            parent = type('AmbientCall', (), {'parent': None, 'failed': False,
                          'owns_current_task': lambda self: True})()
            token = health._CURRENT.set(parent)
            try:
                error = await expect('transport_error', flow.submit_code(CODE))
                assert health._CURRENT.get() is parent and parent.failed
            finally:
                health._CURRENT.reset(token)
            public = stream.getvalue() + repr(flow) + repr(flow.status) + str(error)
            for secret in (PHONE, PASSWORD, HASH, base64.b64encode(KEY).decode()):
                assert secret not in public
            assert error.__cause__ is None and error.__context__ is None
    finally:
        root.setLevel(old)
        root.removeHandler(handler)


async def test_native_diagnostics_are_private():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    root = logging.getLogger()
    root.addHandler(handler)
    old = root.level
    root.setLevel(logging.DEBUG)
    try:
        with fixture() as (config, s):
            secret = PHONE + PASSWORD + HASH
            s.hook = lambda w, r: errors.ServerError(r, message=secret) if isinstance(r, functions.auth.SendCodeRequest) else NotImplemented
            flow = LoginFlow(config)
            await expect('telegram_error', flow.start(PHONE))
            assert flow.status.step == 'uncertain'
            assert secret not in stream.getvalue()
            assert s.calls.count('SendCodeRequest') == 1
    finally:
        root.setLevel(old)
        root.removeHandler(handler)


async def main():
    tests = [(name, fn) for name, fn in globals().items()
             if name.startswith('test_') and inspect.iscoroutinefunction(fn)]
    failed = 0
    for name, fn in tests:
        try:
            await asyncio.wait_for(fn(), 20)
            print('PASS ' + name, flush=True)
        except BaseException:
            failed += 1
            print('FAIL ' + name, flush=True)
            traceback.print_exc()
    print('Passed: {}/{}'.format(len(tests) - failed, len(tests)), flush=True)
    return failed


def run():
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        return asyncio.run(main())


if __name__ == '__main__':
    raise SystemExit(bool(run()))
