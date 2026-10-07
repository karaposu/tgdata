"""Private, exclusively owned Telethon 1.45 sources for AccountPool."""

import asyncio
import hashlib
import os
from contextlib import asynccontextmanager
from pathlib import Path

from telethon import functions, utils
from telethon.tl import types

from .batch_engine import BatchEngine
from .connection_engine import ConnectionEngine
from .health import HealthMonitor
from .message_engine import GroupAccessError
from .pool_state import (
    PoolConfigurationError, PoolIdentityError, PoolStateError, PoolTimeoutError,
    _UnresolvedGroup, _WarmupPending,
)


class _BoundBudget:
    def __init__(self, source, ledger, minimum_age):
        self.source, self.ledger, self.minimum_age = source, ledger, minimum_age

    def status(self, account_id):
        self.source.claim_identity(account_id)
        status = self.ledger.status(account_id)
        if status.warmup_day < self.minimum_age:
            error = _WarmupPending('Account has not reached the configured minimum warm-up age')
            error.retry_at = status.started_at + self.minimum_age * 86400
            raise error
        return status

    def _reserve(self, account_id, amount):
        self.status(account_id)
        return self.ledger._reserve(account_id, amount)

    def _settle(self, reservation, actual):
        return self.ledger._settle(reservation, actual)


class _OwnedSource(ConnectionEngine):
    def __init__(self, account, ledger, policy, groups, callback):
        super().__init__(config_path=account.config_path, pool_size=1,
                         interactive_login=False, session_store=account.session_store)
        self.account = account
        self.policy = policy
        self.groups = groups
        self.verified_id = None
        self.task = None
        self.read_budget = _BoundBudget(self, ledger, policy.min_warmup_days)
        self.monitor = HealthMonitor(callback, account.label, self._identity)
        self.batch_reader = BatchEngine(self, _resolve_entity=self._resolve,
                                        _retain_cancelled_prefix=True)

    def _client_options(self):
        return dict(request_retries=0, raise_last_call_error=True, flood_sleep_threshold=0,
                    connection_retries=0, auto_reconnect=False, receive_updates=False)

    def _identity(self):
        name = self._config.session_file if self._config is not None else None
        if name is not None:
            name = os.path.basename(str(name))
            if name.endswith('.session'):
                name = name[:-8]
        return name, self.verified_id

    def preflight(self):
        """Load configuration/session locally. Never connects or asks for a code."""
        try:
            config = self._load_config()
            if self._primary_client is None:
                self._primary_client = self._new_client()
            key = self._primary_client.session.auth_key
            fingerprint = hashlib.sha256(key.key).digest() if key is not None and key.key else None
            if self.session_store is not None:
                session = ('store', id(self.session_store), str(config.session_file))
            else:
                name = str(config.session_file)
                if not name.endswith('.session'):
                    name += '.session'
                session = ('file', str(Path(name).expanduser().resolve()))
            return session, fingerprint
        except (PoolConfigurationError, PoolIdentityError):
            raise
        except Exception as error:
            raise PoolConfigurationError('Account configuration/session unavailable ({})'.format(
                type(error).__name__)) from None

    def claim_identity(self, actual):
        if type(actual) is not int or actual != self.account.account_id:
            self.verified_id = None
            raise PoolIdentityError('Authenticated account differs from this inventory slot') from None
        self.verified_id = actual

    async def _verify(self):
        client = self._primary_client
        if client is None:
            raise PoolStateError('Account source was not preflighted')
        self.verified_id = None
        if not client.is_connected():
            await client.connect()
        # No ordinary _authenticate/_ensure_connected path: those can sleep
        # through a flood wait or prompt for an interactive login.
        await client(functions.updates.GetStateRequest())
        me = await client.get_me(input_peer=False)
        if me is None:
            await client(functions.updates.GetStateRequest())
            raise PoolIdentityError('Telegram did not provide an authenticated identity') from None
        self.claim_identity(me.id)
        return client

    @asynccontextmanager
    async def session(self):
        yield await self._verify()

    async def _resolve(self, client, chat_id):
        group = self.groups[chat_id]
        try:
            entity = await client.get_entity(group.reference if group.reference is not None else chat_id)
        except ValueError:
            raise _UnresolvedGroup('This account cannot resolve the registered group') from None
        if isinstance(entity, (types.ChatForbidden, types.ChannelForbidden)):
            raise GroupAccessError('Account cannot access the registered group')
        if not isinstance(entity, (types.Chat, types.Channel)) or utils.get_peer_id(entity) != chat_id:
            raise PoolConfigurationError('Group reference does not resolve to its canonical chat ID') from None
        return entity

    async def run(self, chat_id=None, **options):
        outcome = {}

        async def observed():
            async with self.monitor.call('account_pool_read' if chat_id is not None else 'account_pool_recheck',
                                         group=chat_id):
                try:
                    value = (await self.batch_reader.fetch_batch(chat_id, **options)
                             if chat_id is not None else await self._verify())
                except BaseException as error:
                    # Capture before HealthMonitor awaits observers. A timer
                    # expiring during callback delivery must not replace a
                    # completed FloodWait or its already-collected records.
                    outcome['error'] = error
                    outcome['done'] = not isinstance(error, asyncio.CancelledError)
                    raise
                else:
                    outcome['value'], outcome['done'] = value, True
                    return value

        cancelled = None
        self.task = asyncio.ensure_future(observed())
        try:
            try:
                return await asyncio.wait_for(self.task, self.policy.attempt_timeout)
            except asyncio.TimeoutError as error:
                cancelled = error.__cause__
        finally:
            self.task = None
        # Outside the except block: preserve the actual source exception's
        # original cause, without making the observer timeout its new context.
        if outcome.get('done'):
            if 'error' in outcome:
                raise outcome['error']
            return outcome['value']
        error = PoolTimeoutError('The account source attempt timed out')
        prefix = getattr(outcome.get('error', cancelled), 'partial_result', None)
        error.partial_result = prefix
        raise error from None

    async def retire(self):
        client = self._primary_client
        if client is None:
            return
        try:
            await client.disconnect()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise PoolStateError('Account client could not be retired ({})'.format(type(error).__name__)) from None
        self._primary_client = None
        self.verified_id = None
        self._config = None
