"""Explicit existing-account login; secret state belongs to the application.

This API never prompts and never writes the configured account's session. Use
one owner per flow, retain only its latest settled checkpoint in private storage,
and explicitly save session_data to the intended session-store slot on completion.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import math
import re
import time
from dataclasses import dataclass

from telethon import TelegramClient, errors, functions, password as srp, types

from tgdata import health
from tgdata.account_operation import _disconnect_owned
from tgdata.connection_engine import ConnectionEngine, IDENTITY_KEYS
from tgdata.session_store import StoredSession


_PREFIX = 'tgdata-login:1:'
_LIMIT = 65536
_STEPS = {'phone', 'code', 'password', 'complete', 'uncertain',
          'restart_required', 'unsupported'}
_DELIVERIES = {'app', 'sms', 'call'}
_ACTIONS = {'signup', 'payment', 'delivery', 'response', 'password_algorithm',
            'password_setup', 'identity'}
_KEYS = {'version', 'binding', 'identity', 'step', 'phone', 'code_hash',
         'delivery', 'code_length', 'account_id', 'action_required',
         'uncertain_action', 'not_before', 'session'}
class _PrivateSDKLogger(logging.Logger):
    def getChild(self, suffix):
        # Telethon asks for child loggers. Standard getChild() would register
        # new global loggers which do not inherit this private instance.
        return self


_SDK_LOG = _PrivateSDKLogger('tgdata.login.sdk', level=logging.CRITICAL + 1)
_SDK_LOG.disabled = True


class LoginError(RuntimeError):
    """A credential-free error; inspect kind, retry_after and flow.status."""

    def __init__(self, kind, retry_after=None):
        self.kind = kind
        self.retry_after = retry_after
        super().__init__('Telegram login: ' + kind)


@dataclass(frozen=True)
class LoginStatus:
    """Safe observation, never a credential or a storage-commit receipt."""

    step: str
    account_id: int = None
    delivery: str = None
    code_length: int = None
    retry_after: int = None
    action_required: str = None
    cleanup_pending: bool = False


class _MemoryStore:
    def __init__(self, value=None):
        self.value = value

    def load(self, name):
        return self.value

    def save(self, name, data):
        self.value = data


class _LoginClient(TelegramClient):
    """Auth-only policy. Ordinary reader clients keep native update setup."""

    _login_close = None
    _login_transport_close = None
    _login_observe = None

    async def _on_login(self, user):
        # Native connect uses this too. No update RPC may obscure this fact.
        self._login_observe(user)
        self._authorized = True
        self._mb_entity_cache.set_self_user(user.id, user.bot, user.access_hash)
        return user

    async def connect(self):
        # A new physical connection needs its own future retirement. Until
        # then, every waiter shares the prior attempt, even after it completes.
        if self._login_close is not None:
            await asyncio.shield(self._login_close)
            self._login_close = None
        if self._login_transport_close is not None:
            await asyncio.shield(self._login_transport_close)
            self._login_transport_close = None
        return await super().connect()

    async def _disconnect(self):
        # Native _switch_dc goes through this private transport boundary,
        # whereas final disconnect also flushes session state. Both must
        # observe the same transport retirement if migration is cancelled.
        if self._login_transport_close is None:
            self._login_transport_close = asyncio.ensure_future(super()._disconnect())
        await asyncio.shield(self._login_transport_close)

    def disconnect(self):
        # Retain the entire native flush/close as well as its transport close.
        if self._login_close is None:
            self._login_close = asyncio.ensure_future(super().disconnect())
        return asyncio.shield(self._login_close)


def _phone(value):
    if not isinstance(value, str):
        raise LoginError('invalid_phone')
    value = value.replace(' ', '').strip()
    if not re.fullmatch(r'\+?[1-9][0-9]{4,14}', value):
        raise LoginError('invalid_phone')
    return value.lstrip('+')


def _integer(value, minimum=1):
    return type(value) is int and value >= minimum


class LoginFlow:
    """One deliberate phone/code/password conversation.

    state is an opaque secret previously returned by export_state(), from
    trusted server storage only. Restoration does not coordinate old copies or
    promise recovery of a process killed during a request. Each async call owns
    and retires its client; failed cleanup blocks further work until close().
    """

    def __init__(self, config_path='config.ini', *, state=None):
        self._engine = ConnectionEngine(config_path, interactive_login=False)
        self._engine._route_logged = True  # No auth/config payload diagnostics.
        self._busy = False
        self._loop = None
        self._pending_client = None
        self._step = 'phone'
        self._phone = self._hash = self._delivery = self._length = None
        self._account = self._action = self._uncertain = None
        self._not_before = 0.0
        failure = None
        try:
            config = self._engine._load_config()
            settings = dict(api_id=int(config.api_id), api_hash=config.api_hash,
                            proxy=config.proxy, require_proxy=config.require_proxy,
                            identity=self._engine._identity_kwargs(config))
            self._binding = hashlib.sha256(json.dumps(
                settings, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self._session = StoredSession(_MemoryStore(), 'login')
            if state is not None:
                self._restore(state)
                for key, value in self._identity.items():
                    setattr(config, key, value)
            else:
                # Constructor only: no socket, task, session file or login.
                client = self._make_client()
                self._identity = {key: getattr(client._init_request, key)
                                  for key in IDENTITY_KEYS}
                for key, value in self._identity.items():
                    setattr(config, key, value)
        except LoginError as exc:
            failure = exc
        except Exception:
            failure = LoginError('invalid_configuration')
        if failure is not None:
            raise failure from None

    @property
    def status(self):
        remaining = max(0, math.ceil(self._not_before - time.time()))
        return LoginStatus(self._step, self._account, self._delivery,
                           self._length, remaining or None, self._action,
                           self._pending_client is not None)

    def _quiescent(self):
        if self._busy:
            raise LoginError('busy')
        if self._pending_client is not None:
            raise LoginError('cleanup_required')

    def export_state(self):
        """Export a secret checkpoint, only after all owned work has settled."""
        self._quiescent()
        data = dict(version=1, binding=self._binding, identity=self._identity,
                    step=self._step, phone=self._phone, code_hash=self._hash,
                    delivery=self._delivery, code_length=self._length,
                    account_id=self._account, action_required=self._action,
                    uncertain_action=self._uncertain, not_before=self._not_before,
                    session=self._session.dump())
        value = _PREFIX + base64.urlsafe_b64encode(json.dumps(
            data, sort_keys=True, separators=(',', ':')).encode()).decode()
        if len(value) > _LIMIT:
            raise LoginError('invalid_state')
        return value

    @property
    def session_data(self):
        """Secret final #5 session text. The caller must save it explicitly."""
        self._quiescent()
        if self._step != 'complete':
            raise LoginError('not_complete')
        return self._session.dump()

    def _restore(self, value):
        failed = False
        try:
            if not isinstance(value, str) or len(value) > _LIMIT or not value.startswith(_PREFIX):
                raise ValueError()
            data = json.loads(base64.b64decode(value[len(_PREFIX):].encode('ascii'),
                                              altchars=b'-_', validate=True))
            if not isinstance(data, dict) or set(data) != _KEYS or type(data['version']) is not int or data['version'] != 1:
                raise ValueError()
            if not isinstance(data['binding'], str) or not hmac.compare_digest(data['binding'], self._binding):
                raise ValueError()
            identity = data['identity']
            if not isinstance(identity, dict) or set(identity) != set(IDENTITY_KEYS):
                raise ValueError()
            if any(not isinstance(v, str) or not 1 <= len(v) <= 1024 for v in identity.values()):
                raise ValueError()
            if data['step'] not in _STEPS:
                raise ValueError()
            if data['phone'] is not None and _phone(data['phone']) != data['phone']:
                raise ValueError()
            if data['code_hash'] is not None and (not isinstance(data['code_hash'], str) or not 1 <= len(data['code_hash']) <= 4096):
                raise ValueError()
            if data['delivery'] is not None and data['delivery'] not in _DELIVERIES:
                raise ValueError()
            if data['code_length'] is not None and not _integer(data['code_length']):
                raise ValueError()
            if data['account_id'] is not None and not _integer(data['account_id']):
                raise ValueError()
            if data['action_required'] is not None and data['action_required'] not in _ACTIONS:
                raise ValueError()
            if data['uncertain_action'] not in (None, 'phone', 'code', 'password'):
                raise ValueError()
            if type(data['not_before']) not in (int, float) or not math.isfinite(data['not_before']) or data['not_before'] < 0:
                raise ValueError()
            if data['step'] != 'phone' and data['phone'] is None:
                raise ValueError()
            if data['step'] in ('code', 'password') and not data['code_hash']:
                raise ValueError()
            if (data['step'] == 'complete') != (data['account_id'] is not None):
                raise ValueError()
            if (data['step'] == 'uncertain') != (data['uncertain_action'] is not None):
                raise ValueError()
            session = StoredSession(_MemoryStore(data['session']), 'login')
            if data['step'] in ('code', 'password', 'complete') and not session._key_bytes():
                raise ValueError()
        except Exception:
            failed = True
        if failed:
            raise LoginError('invalid_state') from None
        self._identity = identity
        self._session = session
        self._step, self._phone, self._hash = data['step'], data['phone'], data['code_hash']
        self._delivery, self._length = data['delivery'], data['code_length']
        self._account, self._action = data['account_id'], data['action_required']
        self._uncertain, self._not_before = data['uncertain_action'], data['not_before']

    def _make_client(self):
        client = self._engine._new_client(
            session_file=self._session, _client_base=_LoginClient,
            request_retries=0, connection_retries=0, retry_delay=0,
            auto_reconnect=False, receive_updates=False,
            flood_sleep_threshold=0, raise_last_call_error=True,
            base_logger=_SDK_LOG)
        client._login_observe = self._observe_user
        return client

    def _observe_user(self, user):
        if not isinstance(user, types.User) or not _integer(user.id) or user.bot:
            raise LoginError('invalid_response')
        mismatch = (self._account is not None and user.id != self._account)
        if user.phone and self._phone and user.phone.lstrip('+') != self._phone:
            mismatch = True
        if mismatch:
            self._step, self._action, self._account = 'unsupported', 'identity', None
            self._uncertain = None
            raise LoginError('identity_mismatch')
        self._session.process_entities(user)
        self._session.process_entities(types.InputPeerUser(0, user.id))
        self._account = user.id
        self._step, self._uncertain, self._not_before = 'complete', None, 0.0

    def _authorization(self, client, result):
        if isinstance(result, types.auth.Authorization):
            self._observe_user(result.user)
            client._authorized = True
            client._mb_entity_cache.set_self_user(result.user.id, result.user.bot,
                                                   result.user.access_hash)
            if result.setup_password_required:
                self._action = 'password_setup'
        elif isinstance(result, types.auth.AuthorizationSignUpRequired):
            self._unsupported('signup')
        else:
            self._unsupported('response')

    def _unsupported(self, action):
        self._step, self._action, self._uncertain = 'unsupported', action, None
        self._account = None

    async def start(self, phone):
        value = _phone(phone)
        return await self._invoke('phone', value)

    async def submit_code(self, code):
        if not isinstance(code, str) or not re.fullmatch(r'[0-9]{1,32}', code.strip()):
            raise LoginError('invalid_code')
        return await self._invoke('code', code.strip())

    async def submit_password(self, password):
        if not isinstance(password, str) or not 1 <= len(password) <= 1024:
            raise LoginError('invalid_password')
        return await self._invoke('password', password)

    async def check_authorization(self):
        """Observe current authorization without sending/resending a code."""
        if not self._session._key_bytes():
            raise LoginError('no_credential')
        return await self._invoke('check', None)

    def _admit(self):
        self._quiescent()
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            raise LoginError('wrong_event_loop')
        self._loop = loop
        self._busy = True

    async def _invoke(self, action, value):
        with health.isolate_call():
            return await self._invoke_owned(action, value)

    async def _invoke_owned(self, action, value):
        self._quiescent()
        if action != 'check' and self._step != action:
            raise LoginError('wrong_step')
        if self.status.retry_after:
            raise LoginError('wait', self.status.retry_after)
        self._admit()
        try:
            # Deliver an already-queued stop before creating any source work.
            await asyncio.sleep(0)
            if action == 'phone':
                self._phone = value
            completion = asyncio.ensure_future(self._execute(action, value))
            cancelled = None
            while not completion.done():
                try:
                    await asyncio.shield(completion)
                except asyncio.CancelledError as exc:
                    if cancelled is None:
                        cancelled = exc
                        completion.cancel()
            failure = completion.result()
            if cancelled is not None:
                raise cancelled
            if failure is not None:
                raise failure from None
            return self.status
        finally:
            self._busy = False

    async def _execute(self, action, value):
        client = None
        failure = None
        with health.isolate_call():
            try:
                client = self._make_client()
                await client.connect()
                await self._perform(client, action, value)
            except (Exception, asyncio.CancelledError) as exc:
                failure = self._failure(exc, action)
            finally:
                if client is not None:
                    failures = []
                    try:
                        await _disconnect_owned(client, failures)
                    except asyncio.CancelledError:
                        if failure is None:
                            failure = LoginError('interrupted')
                    if failures:
                        self._pending_client = client
        return failure

    async def _self(self, client):
        try:
            users = await client(functions.users.GetUsersRequest([types.InputUserSelf()]))
        except (errors.UnauthorizedError, errors.AuthKeyError):
            return False
        if not isinstance(users, (list, tuple)) or len(users) != 1:
            raise LoginError('invalid_response')
        if isinstance(users[0], types.UserEmpty):
            return False
        self._observe_user(users[0])
        return True

    async def _perform(self, client, action, value):
        if await self._self(client):
            return
        if self._step == 'complete':
            self._step, self._account = 'restart_required', None
            return
        if action == 'check':
            if self._step == 'uncertain':
                self._step = self._uncertain if self._uncertain in ('code', 'password') else 'restart_required'
                self._uncertain = None
            return
        if action == 'phone':
            request = functions.auth.SendCodeRequest(
                self._phone, client.api_id, client.api_hash, types.CodeSettings())
            for attempt in range(2):
                self._step, self._uncertain = 'uncertain', 'phone'
                before_dc = client.session.dc_id
                try:
                    result = await client(request)
                    break
                except (errors.PhoneMigrateError, errors.NetworkMigrateError) as exc:
                    if self._step == 'complete':
                        return
                    if attempt or client.session.dc_id == before_dc or client.session.dc_id != exc.new_dc:
                        raise
            if isinstance(result, types.auth.SentCodeSuccess):
                self._authorization(client, result.authorization)
            elif isinstance(result, types.auth.SentCode):
                self._hash = result.phone_code_hash
                mapping = {types.auth.SentCodeTypeApp: 'app',
                           types.auth.SentCodeTypeSms: 'sms',
                           types.auth.SentCodeTypeCall: 'call'}
                self._delivery = mapping.get(type(result.type))
                if self._delivery is None:
                    self._unsupported('delivery')
                elif not isinstance(self._hash, str) or not self._hash:
                    raise LoginError('invalid_response')
                else:
                    self._length = result.type.length
                    self._step, self._uncertain = 'code', None
            elif isinstance(result, types.auth.SentCodePaymentRequired):
                self._unsupported('payment')
            else:
                self._unsupported('response')
        elif action == 'code':
            self._step, self._uncertain = 'uncertain', 'code'
            result = await client(functions.auth.SignInRequest(
                self._phone, self._hash, phone_code=value))
            self._authorization(client, result)
        elif action == 'password':
            parameters = await client(functions.account.GetPasswordRequest())
            try:
                check = srp.compute_check(parameters, value)
            except (ValueError, TypeError, AttributeError):
                self._unsupported('password_algorithm')
                return
            self._step, self._uncertain = 'uncertain', 'password'
            result = await client(functions.auth.CheckPasswordRequest(check))
            self._authorization(client, result)

    def _failure(self, exc, action):
        # Return a safe value, raised outside the native exception handler.
        if isinstance(exc, LoginError):
            return exc
        if isinstance(exc, errors.SessionPasswordNeededError) and action == 'code':
            self._step, self._uncertain = 'password', None
            return None
        known = ((errors.PhoneCodeInvalidError, 'code', 'invalid_code'),
                 (errors.PasswordHashInvalidError, 'password', 'invalid_password'),
                 (errors.PhoneNumberInvalidError, 'phone', 'invalid_phone'))
        for error_type, step, kind in known:
            if isinstance(exc, error_type):
                self._step, self._uncertain = step, None
                return LoginError(kind)
        if isinstance(exc, errors.FloodWaitError):
            if self._step == 'uncertain' and action != 'check':
                self._step, self._uncertain = action, None
            self._not_before = time.time() + max(1, exc.seconds)
            return LoginError('wait', max(1, exc.seconds))
        if isinstance(exc, (errors.PhoneCodeExpiredError, errors.PhoneCodeEmptyError,
                            errors.AuthRestartError, errors.PhoneMigrateError,
                            errors.NetworkMigrateError, errors.UserMigrateError,
                            errors.UnauthorizedError, errors.AuthKeyError)):
            self._step, self._uncertain, self._account = 'restart_required', None, None
            return LoginError('restart_required')
        if isinstance(exc, asyncio.CancelledError):
            return LoginError('interrupted')
        if isinstance(exc, (OSError, asyncio.TimeoutError)):
            return LoginError('transport_error')
        if isinstance(exc, errors.RPCError):
            return LoginError('telegram_error')
        return LoginError('operation_failed')

    async def close(self):
        """Retry a failed retirement. Does not log out or erase known progress."""
        if self._busy:
            raise LoginError('busy')
        if self._pending_client is None:
            return self.status
        # _admit would refuse pending cleanup; retain its loop/overlap guard here.
        if self._loop is not asyncio.get_running_loop():
            raise LoginError('wrong_event_loop')
        self._busy = True
        failures = []
        try:
            self._pending_client._login_close = None
            self._pending_client._login_transport_close = None
            await _disconnect_owned(self._pending_client, failures)
        finally:
            if not failures:
                self._pending_client = None
            self._busy = False
        if failures:
            raise LoginError('cleanup_required')
        return self.status
