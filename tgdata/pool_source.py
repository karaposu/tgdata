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
from .pool_lifecycle import _await_cleanup, _start_owned, _wait_owned
from .pool_observation import PoolMonitor
from .message_batch import _interrupted_prefix
from .message_engine import GroupAccessError
from .pool_state import (
    PoolConfigurationError, PoolIdentityError, PoolStateError, PoolTimeoutError,
    _UnresolvedGroup, _WarmupPending, _SourceInterrupted,
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
    def __init__(self, account, ledger, policy, groups, observations):
        super().__init__(config_path=account.config_path, pool_size=1,
                         interactive_login=False, session_store=account.session_store)
        self.account = account
        self.policy = policy
        self.groups = groups
        self.verified_id = None
        self.task = None
        self._retirement_blocked = False
        self.read_budget = _BoundBudget(self, ledger, policy.min_warmup_days)
        self.monitor = PoolMonitor(observations, account.label, self._identity)
        self.batch_reader = BatchEngine(self, _resolve_entity=self._resolve,
                                        _retain_cancelled_prefix=True)

    def _new_client(self, session_file=None, **client_options):
        # Use the common factory's existing policy seam. This owned source never
        # permits an internal caller to relax its wait/retry policy.
        client_options.update(request_retries=0, raise_last_call_error=True,
                              flood_sleep_threshold=0, connection_retries=0,
                              retry_delay=0, auto_reconnect=False, receive_updates=False)
        return super()._new_client(session_file, **client_options)

    def _require_usable(self):
        if self._retirement_blocked:
            raise PoolStateError('Account client retirement has not completed; retry recheck or close')

    def _identity(self):
        name = self._config.session_file if self._config is not None else None
        if name is not None:
            name = os.path.basename(str(name))
            if name.endswith('.session'):
                name = name[:-8]
        return name, self.verified_id

    def preflight(self):
        """Load configuration/session locally. Never connects or asks for a code."""
        self._require_usable()
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
        except (Exception, asyncio.CancelledError) as error:
            raise PoolConfigurationError('Account configuration/session unavailable ({})'.format(
                type(error).__name__)) from None

    def claim_identity(self, actual):
        if type(actual) is not int or actual != self.account.account_id:
            self.verified_id = None
            raise PoolIdentityError('Authenticated account differs from this inventory slot') from None
        self.verified_id = actual

    async def _verify(self):
        self._require_usable()
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
                    outcome['error'] = error
                    outcome['done'] = not isinstance(error, asyncio.CancelledError)
                    raise
                else:
                    outcome['value'], outcome['done'] = value, True
                    return value

        await asyncio.sleep(0)
        child = self.task = _start_owned(observed)
        try:
            _, terminal, timed_out = await _wait_owned(child, self.policy.attempt_timeout)
        except asyncio.CancelledError as error:
            error.partial_result = _interrupted_prefix(outcome.get('value') or
                                      getattr(outcome.get('error'), 'partial_result', None))
            raise
        finally:
            self.task = None
        if outcome.get('done'):
            if 'error' in outcome:
                raise outcome['error']
            return outcome['value']
        if timed_out:
            error = PoolTimeoutError('The account source attempt timed out')
        elif isinstance(terminal, asyncio.CancelledError) or terminal is None:
            error = _SourceInterrupted('Account source was interrupted; recover its unresolved attempt')
        else:
            raise terminal
        error.partial_result = _interrupted_prefix(getattr(outcome.get('error'), 'partial_result', None))
        raise error from None

    async def retire(self):
        client = self._primary_client
        if client is None:
            return
        self._retirement_blocked = True

        async def finish():
            try:
                await client.disconnect()
            except (Exception, asyncio.CancelledError) as error:
                # Unlike a one-off lookup, this source could otherwise be reused
                # after failed cleanup. Retain the block until an explicit retry.
                raise PoolStateError('Account client could not be retired ({})'.format(
                    type(error).__name__)) from None
            self._primary_client = None
            self.verified_id = None
            self._config = None
            self._retirement_blocked = False

        await _await_cleanup(finish())
