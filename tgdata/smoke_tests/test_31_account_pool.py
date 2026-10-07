"""Account routing with actual Telethon/SQLite and synthetic wire; no sockets."""

import asyncio
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import inspect
import itertools
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from telethon import errors, functions, types
from telethon.crypto import AuthKey
import telethon
from tgdata import (
    AccountPool, PoolAccount, PoolGroup, PoolPolicy, PoolReadResult, PoolUnavailable,
    PoolConfigurationError, PoolStorageError, PoolStateError, PoolConflictError,
    PoolClockError, PoolBusyError, PoolClosedError, PoolIdentityError, PoolTimeoutError,
    SQLiteAccountPoolStore, SQLiteSyncStore, ReadBudget, ReadBudgetExceeded,
    MessageBatch, BatchFormatError, BackfillPrepareContext, TgData, health,
)
from tgdata.session_store import StoredSession
from tgdata import pool_state
from tgdata.smoke_tests import test_19_message_batches as b
from tgdata.smoke_tests import test_25_backfill_delivery as d

f = b.f
CHAT, OTHER = d.CHAT, -1000000000008
COUNT = itertools.count(1)
POOLS = []
SECRET = 'POOL_PRIVATE_ERROR_TEXT_MUST_NOT_ESCAPE'


def path(stem):
    return f.TMP / ('{}_{}'.format(stem, next(COUNT)))


def room8():
    value = f.room()
    value.id, value.access_hash, value.username = 8, 8, 'synthetic_other'
    return value


def wire(source, account=None, cached=None):
    source.preflight()
    client = source._primary_client
    aid = account if account is not None else source.account.account_id
    sender = b.Sender()
    sender.account = aid
    client._sender = sender
    client.session.process_entities([f.room(), room8()])
    client._mb_entity_cache.set_self_user(cached if cached is not None else aid, False, 1)
    if client.session.auth_key is None:
        client.session.auth_key = AuthKey(bytes([source.account.account_id % 251 + 1]) * 256)
        client.session.save()
    return client, sender


async def setup(*, limits=(1000, 1000), policy=None, callback=None, store=None,
                daily=None, history=None, groups=None, attach=True):
    clock = f.Clock()
    budget = ReadBudget(path('budget.sqlite3'), clock=clock)
    accounts = []
    for aid, limit in zip((111, 222), limits):
        budget.configure(aid, limit)
        accounts.append(PoolAccount(aid, f.config(), session_store=f.Store(), label='synthetic-' + str(aid)))
    actual = store or SQLiteAccountPoolStore(path('pool.sqlite3'))
    pool = AccountPool(accounts, groups or [PoolGroup(CHAT), PoolGroup(OTHER)],
                       read_budget=budget, state_store=actual, policy=policy,
                       health_callback=callback, sync_store=daily, backfill_store=history)
    pool._wall_clock = clock
    ticks = f.Clock(100)
    pool._monotonic = ticks
    POOLS.append(pool)
    await pool.initialize()
    clients, senders = {}, {}
    if attach:
        for aid, source in pool._sources.items():
            clients[aid], senders[aid] = wire(source)
    return SimpleNamespace(pool=pool, budget=budget, store=actual, clock=clock, ticks=ticks,
                           clients=clients, senders=senders)


async def restart(e):
    await e.pool.close()
    pool = AccountPool(e.pool.accounts, tuple(e.pool.groups.values()), read_budget=e.budget,
                       state_store=e.store, policy=e.pool.policy)
    pool._wall_clock, pool._monotonic = e.clock, e.ticks
    POOLS.append(pool)
    e.pool = pool
    for aid, source in pool._sources.items():
        e.clients[aid], e.senders[aid] = wire(source)
    return e


async def read(e, **kwargs):
    return await e.pool.read(CHAT, after_id=100, limit=kwargs.pop('limit', 1), **kwargs)


class FaultStore:
    def __init__(self, actual):
        self.actual, self.calls = actual, 0
        self.before, self.after = {}, {}
        self.load_error = None
        self.hook = None

    async def load(self):
        if self.load_error is not None:
            raise self.load_error
        return await self.actual.load()

    async def compare_and_swap(self, *args):
        self.calls += 1
        if self.calls in self.before:
            raise self.before[self.calls]
        if self.hook is not None:
            await self.hook(self.calls, *args)
        value = await self.actual.compare_and_swap(*args)
        if self.calls in self.after:
            raise self.after[self.calls]
        return value


async def test_values_and_constructor_are_local():
    for create in (
        lambda: PoolAccount(True, 'x'), lambda: PoolAccount(0, 'x'),
        lambda: PoolGroup(7), lambda: PoolGroup(CHAT, 'https://t.me/+invite'),
        lambda: PoolGroup(CHAT, OTHER), lambda: PoolPolicy(strategy='random'),
        lambda: PoolPolicy(attempt_timeout=float('nan')), lambda: PoolPolicy(max_attempts=0),
        lambda: PoolPolicy(min_warmup_days=True),
    ):
        f.rejected(PoolConfigurationError, create)
    account = PoolAccount(111, '/nonexistent-secret-config.ini')
    assert 'nonexistent' not in repr(account)
    f.rejected(FrozenInstanceError, lambda: setattr(account, 'account_id', 222))
    e = await setup(attach=False)
    assert all(s._config is None and s._primary_client is None for s in e.pool._sources.values())
    assert len((await e.pool.get_pool_status(CHAT)).accounts) == 2
    f.rejected(PoolConfigurationError, lambda: AccountPool([account, account], [],
               read_budget=e.budget, state_store=e.store))
    names = list(inspect.signature(TgData.__init__).parameters)
    assert names == ['self', 'config_path', 'connection_pool_size', 'log_file', 'interactive_login',
                     'health_callback', 'account_label', 'session_store', 'read_budget', 'sync_store', 'backfill_store']


async def test_actual_factory_policy_and_proxy_identity():
    e = await setup(attach=False)
    account = e.pool.accounts[0]
    with open(account.config_path, 'a') as stream:
        stream.write('device_model = Pool Test Device\nproxy = socks5://user:password@127.0.0.1:9\n')
    source = e.pool._sources[111]
    source.preflight()
    client = source._primary_client
    assert client._request_retries == 0 and client._raise_last_call_error
    assert client.flood_sleep_threshold == 0 and client._no_updates
    assert client._sender._retries == 0 and not client._sender._auto_reconnect
    assert client._proxy['addr'] == '127.0.0.1'
    assert client._init_request.device_model == 'Pool Test Device'
    e.clients[111], e.senders[111] = wire(source)
    e.clients[222], e.senders[222] = wire(e.pool._sources[222])
    assert (await read(e)).account_id == 111
    assert not any('Code' in name or 'SignIn' in name for name in e.senders[111].calls)


async def test_real_pagination_and_drain_budget():
    e = await setup()
    result = await read(e, limit=150)
    assert isinstance(result, PoolReadResult) and result.account_id == 111
    assert [int(m['id']) for m in result.batch.messages] == list(range(101, 251))
    assert len(e.senders[111].reads) == 2 and not e.senders[222].reads
    assert e.budget.status(111).used == 150 and e.budget.status(222).used == 0
    assert result.to_dict()['account_id'] == '111'


async def test_spread_uses_remaining_and_stable_ties():
    e = await setup(limits=(2, 5), policy=PoolPolicy(strategy='spread'))
    assert (await read(e, limit=3)).account_id == 222
    assert (await read(e, limit=1)).account_id == 111
    assert e.budget.status(111).used == 1 and e.budget.status(222).used == 3


async def test_flood_failover_and_restart_wait():
    e = await setup()
    e.senders[111].script = [errors.FloodWaitError(request=None, capture=7200)]
    result = await read(e)
    assert result.account_id == 222 and [a.outcome for a in result.attempts] == ['waiting', 'ok']
    assert e.budget.status(111).reserved == 1
    await restart(e)
    result = await read(e)
    assert result.account_id == 222 and not e.senders[111].calls
    status = (await e.pool.get_pool_status(CHAT)).accounts[0]
    assert status.retry_at == f.NOW + 7200 and 'waiting' in status.reasons
    await f.expect(PoolConflictError, e.pool.recheck_account(111))


async def test_group_denial_does_not_disable_other_groups():
    e = await setup()
    e.senders[111].script = [errors.ChannelPrivateError(request=None)]
    assert (await read(e)).account_id == 222
    e.senders[111].entity = room8()
    message = f.message(101)
    message.peer_id = types.PeerChannel(8)
    response = d.finite_response([message])
    response.chats = [room8()]
    e.senders[111].script = [response]
    result = await e.pool.read(OTHER, after_id=100, limit=1)
    assert result.account_id == 111 and result.batch.chat_id == OTHER
    assert 'no_access' in (await e.pool.get_pool_status(CHAT)).accounts[0].reasons


async def test_actual_identity_overrides_stale_cache_for_events():
    events = []
    e = await setup(callback=events.append)
    e.clients[111]._mb_entity_cache.set_self_user(999, False, 1)
    e.senders[111].script = [errors.ChannelPrivateError(request=None)]
    assert (await read(e)).account_id == 222
    assert events[0]['account']['user_id'] == 111
    assert e.budget.status(111).reserved == 1
    assert e.clients[111]._self_id == 999  # The actual SDK cache remains stale.


async def test_changed_identity_at_admission_never_sends_history():
    for identities in ([222], [111, 222], [111, 111, 222]):
        e = await setup()
        e.senders[111].identities = list(identities)
        await f.expect(PoolIdentityError, read(e))
        assert not e.senders[111].reads and not e.senders[222].reads
        assert e.budget.status(111).used == e.budget.status(222).used == 0
        assert 'identity_mismatch' in (await e.pool.get_pool_status(CHAT)).accounts[0].reasons


async def test_duplicate_auth_keys_refuse_before_admission():
    e = await setup()
    e.clients[222].session.auth_key = AuthKey(e.clients[111].session.auth_key.key)
    await f.expect(PoolConfigurationError, read(e))
    assert not any(s.calls for s in e.senders.values())
    assert all(a.attempt_id is None for a in (await e.pool.get_pool_status()).accounts)


async def test_alias_redirect_and_missing_entity_do_not_scan_dialogs():
    e = await setup(groups=[PoolGroup(OTHER, '@synthetic_room')])
    await f.expect(PoolConfigurationError, e.pool.read(OTHER, limit=1))
    assert not any(s.reads for s in e.senders.values())
    e = await setup()
    for client in e.clients.values():
        async def unresolved(*args, **kwargs):
            raise ValueError('uncached peer')
        client.get_entity = unresolved
    error = await f.expect(PoolUnavailable, read(e))
    assert all('unresolved' in a.reasons for a in error.accounts)
    assert not any('GetDialogsRequest' in s.calls for s in e.senders.values())


async def test_source_partial_stops_failover_and_keeps_charge():
    e = await setup()
    failure = errors.FloodWaitError(request=None, capture=7200)
    e.senders[111].script = [f.response([f.message(n) for n in reversed(range(101, 201))]), failure]
    caught = await f.expect(errors.FloodWaitError, read(e, limit=200))
    assert caught is failure and len(caught.partial_result.messages) == 100
    assert caught.pool_account_id == 111 and len(caught.pool_attempts) == 1
    assert not e.senders[222].reads and e.budget.status(111).used == 200


async def test_timeout_retains_completed_page_and_awaits_cancel():
    e = await setup(policy=PoolPolicy(attempt_timeout=0.04))
    e.senders[111].script = [f.response([f.message(n) for n in reversed(range(101, 201))]), f.PENDING]
    error = await f.expect(PoolTimeoutError, read(e, limit=200))
    assert len(error.partial_result.messages) == 100 and error.partial_result.stop_reason == 'interrupted'
    assert e.senders[111].pending[0].cancelled() and not e.senders[222].reads
    assert e.budget.status(111).used == 200 and e.pool._sources[111].task is None


async def test_empty_timeout_fails_over_after_quiescence():
    e = await setup(policy=PoolPolicy(attempt_timeout=0.03))
    e.senders[111].script = [f.PENDING]
    result = await read(e)
    assert result.account_id == 222 and e.senders[111].pending[0].cancelled()
    assert e.budget.status(111).used == e.budget.status(222).used == 1


async def test_observer_timeout_preserves_original_flood_and_prefix():
    async def callback(event):
        await asyncio.Event().wait()
    e = await setup(policy=PoolPolicy(attempt_timeout=0.04), callback=callback)
    failure = errors.FloodWaitError(request=None, capture=7200)
    e.senders[111].script = [f.response([f.message(n) for n in reversed(range(101, 201))]), failure]
    caught = await f.expect(errors.FloodWaitError, read(e, limit=200))
    assert caught is failure and len(caught.partial_result.messages) == 100
    assert (await e.pool.get_pool_status(CHAT)).accounts[0].retry_at == f.NOW + 7200
    assert not e.senders[222].reads


async def test_success_observer_timeout_keeps_successful_batch():
    async def callback(event):
        await asyncio.Event().wait()
    e = await setup(policy=PoolPolicy(attempt_timeout=0.03), callback=callback)
    monitor = e.pool._sources[111].monitor
    # Actual prior health fact; source success proves recovery, whose callback blocks.
    monitor.callback = None
    async with monitor.call('prior', group=CHAT):
        await health.report(errors.ChannelPrivateError(request=None), 'handled')
    monitor.callback = callback
    result = await read(e)
    assert result.account_id == 111 and len(result.batch.messages) == 1
    assert not e.senders[222].reads


async def test_budget_and_minimum_age_are_local_eligibility():
    e = await setup(limits=(0, 0))
    error = await f.expect(PoolUnavailable, read(e))
    assert error.retry_after is None and all('budget' in a.reasons for a in error.accounts)
    assert not any(s.calls for s in e.senders.values())
    e = await setup(policy=PoolPolicy(min_warmup_days=2))
    error = await f.expect(PoolUnavailable, read(e))
    assert error.retry_after == 2 * 86400 and all('warmup' in a.reasons for a in error.accounts)
    assert not any(s.calls for s in e.senders.values())
    e.clock.value += 2 * 86400
    assert (await read(e)).account_id == 111


async def test_budget_race_at_real_send_uses_other_account():
    e = await setup(limits=(1, 2))
    original = e.senders[111].send
    count = 0
    def send(request, ordered=False):
        nonlocal count
        if isinstance(f.unwrap(request), functions.users.GetUsersRequest):
            count += 1
            if count == 3:
                e.budget._reserve(111, 1)  # another ledger caller wins after advisory selection
        return original(request, ordered=ordered)
    e.senders[111].send = send
    result = await read(e)
    assert result.account_id == 222 and not e.senders[111].reads
    assert e.budget.status(111).used == 1 and e.budget.status(222).used == 1


async def test_real_sdk_server_exhaustion_is_preserved_for_failover():
    e = await setup()
    e.senders[111].script = [errors.ServerError(request=None, message='SYNTHETIC', code=500)]
    result = await read(e)
    assert result.account_id == 222 and result.attempts[0].error_type == 'ServerError'
    assert len(e.senders[111].reads) == 1


async def test_external_cancel_remains_unresolved_and_no_failover():
    e = await setup()
    e.senders[111].script = [f.PENDING]
    task = asyncio.create_task(read(e))
    await d.until(lambda: bool(e.senders[111].pending))
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    before = (await e.pool.get_pool_status(CHAT)).accounts[0]
    assert before.attempt_id and 'unresolved_attempt' in before.reasons
    assert not e.senders[222].reads and e.senders[111].pending[0].cancelled()
    bound = datetime.fromtimestamp(f.NOW + 60, timezone.utc)
    await f.expect(PoolConfigurationError, e.pool.recover_account(111, attempt_id=before.attempt_id,
                     previous_reader_stopped=False, retry_not_before=bound))
    await e.pool.recover_account(111, attempt_id=before.attempt_id,
                                previous_reader_stopped=True, retry_not_before=bound)
    raw = await e.store.load()
    await e.pool.recover_account(111, attempt_id=before.attempt_id,
                                previous_reader_stopped=True, retry_not_before=bound)
    assert await e.store.load() == raw and e.budget.status(111).used == 1
    assert (await read(e)).account_id == 222


async def test_overlapping_calls_are_real_and_close_quiesces():
    e = await setup()
    e.senders[111].script = [f.PENDING]
    task = asyncio.create_task(read(e))
    await d.until(lambda: bool(e.senders[111].pending))
    await f.expect(PoolBusyError, read(e))
    await f.expect(PoolBusyError, e.pool.initialize())
    await f.expect(PoolBusyError, e.pool.recheck_account(222))
    await e.pool.close()
    assert task.done() and task.cancelled() and e.senders[111].pending[0].cancelled()
    await f.expect(PoolClosedError, read(e))
    assert not e.senders[222].reads


async def test_callback_close_cannot_create_parent_child_deadlock():
    holder, outcomes = {}, []
    async def callback(event):
        await f.expect(PoolBusyError, holder['pool'].close())
        outcomes.append('refused')
    e = await setup(callback=callback)
    holder['pool'] = e.pool
    e.senders[111].script = [errors.ChannelPrivateError(request=None)]
    assert (await read(e)).account_id == 222 and outcomes == ['refused']
    assert not e.pool._closed


async def test_uncertain_admission_opens_no_source_and_survives_restart():
    actual = SQLiteAccountPoolStore(path('uncertain.sqlite3'))
    backend = FaultStore(actual)
    e = await setup(store=backend)
    backend.after[backend.calls + 1] = RuntimeError(SECRET)
    error = await f.expect(PoolStorageError, read(e))
    assert SECRET not in str(error) and not any(s.calls for s in e.senders.values())
    assert (await e.pool.get_pool_status(CHAT)).accounts[0].attempt_id is not None
    await restart(e)
    assert (await read(e)).account_id == 222 and not e.senders[111].calls


async def test_settlement_failure_preserves_data_and_daily_replay():
    for after_commit in (False, True):
        backend = FaultStore(SQLiteAccountPoolStore(path('settle.sqlite3')))
        daily = SQLiteSyncStore(path('daily.sqlite3'))
        e = await setup(store=backend, daily=daily)
        await e.pool.initialize_sync(CHAT, after_id=100)
        faults = backend.after if after_commit else backend.before
        faults[backend.calls + 2] = RuntimeError(SECRET)
        error = await f.expect(PoolStorageError, e.pool.sync_group(CHAT, limit=1))
        assert len(error.partial_result.messages) == 1 and error.partial_result.stop_reason == 'interrupted'
        assert SECRET not in str(error) and health.classify(error) is None
        count = len(e.senders[111].reads)
        backend.load_error = RuntimeError('pool backend offline during local replay')
        batch = await e.pool.sync_group(CHAT, limit=1)
        assert batch.batch_id == error.partial_result.batch_id and len(e.senders[111].reads) == count
        await e.pool.acknowledge_sync(CHAT, batch.batch_id)
        assert (await e.pool.get_sync_status(CHAT)).after_id == 101
        assert not e.senders[222].reads


async def test_stale_settlement_cannot_erase_newer_stored_facts():
    actual = SQLiteAccountPoolStore(path('stale.sqlite3'))
    backend = FaultStore(actual)
    e = await setup(store=backend)
    target = backend.calls + 2
    async def change(number, expected, data):
        if number == target:
            raw = await actual.load()
            value = json.loads(raw)
            value['accounts']['111']['repair'] = 'banned'
            assert await actual.compare_and_swap(raw, json.dumps(value))
    backend.hook = change
    error = await f.expect(PoolConflictError, read(e))
    assert len(error.partial_result.messages) == 1
    status = (await e.pool.get_pool_status(CHAT)).accounts[0]
    assert 'banned' in status.reasons and status.attempt_id is not None


async def test_state_corruption_missing_and_schema_collision_refuse():
    for bad in (None, '{}', '{"format":"x","format":"y"}', '[]', '{"version":true}'):
        e = await setup()
        raw = await e.store.load()
        if bad is None:
            class Absent:
                async def load(self): return None
                async def compare_and_swap(self, *args): raise AssertionError('unexpected initialization')
            e.pool._store = Absent()
        else:
            assert await e.store.compare_and_swap(raw, bad)
        await f.expect(PoolStateError, read(e))
        assert not any(s.calls for s in e.senders.values())
    file = path('shared.sqlite3')
    daily = SQLiteSyncStore(file)
    assert await daily.compare_and_swap(-1, None, b.GOLDEN)
    e = await setup(attach=False)
    e.pool._store = SQLiteAccountPoolStore(file, create=False)
    await f.expect(PoolStateError, e.pool.initialize())


async def test_initialization_and_inventory_changes_never_reset_waits():
    e = await setup()
    e.senders[111].script = [errors.FloodWaitError(request=None, capture=7200)]
    await read(e)
    raw = await e.store.load()
    await e.pool.initialize()
    assert await e.store.load() == raw
    reduced = AccountPool([e.pool.accounts[1]], [PoolGroup(CHAT)], read_budget=e.budget,
                          state_store=e.store)
    reduced._wall_clock = e.clock
    POOLS.append(reduced)
    await reduced.initialize()
    assert '111' in json.loads(await e.store.load())['accounts']
    assert (await e.pool.get_pool_status(CHAT)).accounts[0].retry_at == f.NOW + 7200


async def test_clock_regression_and_monotonic_wait_floor():
    e = await setup()
    e.senders[111].script = [errors.FloodWaitError(request=None, capture=30)]
    await read(e)
    e.clock.value -= 1
    await f.expect(PoolClockError, read(e))
    e.clock.value += 100
    assert 'waiting' in (await e.pool.get_pool_status(CHAT)).accounts[0].reasons
    e.ticks.value += 31
    assert 'waiting' not in (await e.pool.get_pool_status(CHAT)).accounts[0].reasons


async def test_recheck_reloads_repaired_stored_credential():
    e = await setup(policy=PoolPolicy(max_attempts=1))
    e.senders[111].script = [errors.ChannelPrivateError(request=None)]
    await f.expect(PoolUnavailable, read(e))
    e.senders[111].auth_error = True
    await f.expect(PoolUnavailable, e.pool.read(OTHER, after_id=100, limit=1))
    source = e.pool._sources[111]
    name = source._config.session_file
    replacement = StoredSession(source.session_store, name)
    new_key = b'\x9a' * 256
    replacement.auth_key = AuthKey(new_key)
    replacement.save()
    factory = source._new_client
    def rebuilt(*args, **kwargs):
        client = factory(*args, **kwargs)
        client._sender = b.Sender()
        client._sender.account = 111
        return client
    with patch.object(source, '_new_client', side_effect=rebuilt):
        await e.pool.recheck_account(111)
    assert source._primary_client.session.auth_key.key == new_key
    assert StoredSession(source.session_store, name).auth_key.key == new_key
    assert 'logged_out' not in (await e.pool.get_pool_status(OTHER)).accounts[0].reasons
    assert 'no_access' in (await e.pool.get_pool_status(CHAT)).accounts[0].reasons


async def test_backfill_failover_replay_ack_are_public_and_source_free():
    backend = FaultStore(SQLiteAccountPoolStore(path('backfillpool.sqlite3')))
    history = SQLiteSyncStore(path('history.sqlite3'))
    e = await setup(store=backend, history=history)
    request = d.request()
    started = await e.pool.start_backfill(request, submission='new')
    e.senders[111].script = [errors.ChannelPrivateError(request=None)]
    e.senders[222].script = [d.finite_response([f.message(102), f.message(101)])]
    turn = await e.pool.prepare_backfill(BackfillPrepareContext.from_status(started.status))
    assert len(turn.batch.messages) == 2
    counts = [len(s.reads) for s in e.senders.values()]
    backend.load_error = RuntimeError(SECRET)
    await e.pool.close()
    replay = await e.pool.prepare_backfill(BackfillPrepareContext.from_status(turn.status))
    assert replay.delivery == turn.delivery and replay.replayed
    status = await e.pool.acknowledge_backfill(replay.delivery)
    assert status.after_id == 102 and [len(s.reads) for s in e.senders.values()] == counts


async def test_local_media_failure_is_not_failover_or_health():
    events = []
    e = await setup(callback=events.append)
    message = b.document()
    e.senders[111].files[b.ASSET_ID] = b.PAYLOAD
    e.senders[111].script = [d.finite_response([message])]
    failure = PermissionError(SECRET)
    with patch('tgdata.batch_files._publish', side_effect=failure):
        caught = await f.expect(PermissionError, read(e, download_media_to=path('media')))
    assert caught is failure and not e.senders[222].calls and not events
    assert (await e.pool.get_pool_status(CHAT)).accounts[0].eligible


async def test_local_state_error_does_not_inherit_handled_rpc():
    backend = FaultStore(SQLiteAccountPoolStore(path('context.sqlite3')))
    e = await setup(store=backend)
    backend.load_error = RuntimeError(SECRET)
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        error = await f.expect(PoolStorageError, read(e))
    assert health.classify(error) is None and SECRET not in str(error)
    assert not any(s.calls for s in e.senders.values())


async def test_input_refusal_and_unsupported_sdk_are_source_free():
    e = await setup()
    for kwargs in (dict(limit=True), dict(after_id=-1), dict(limit=10001)):
        await f.expect(BatchFormatError, e.pool.read(CHAT, **kwargs))
    await f.expect(PoolConfigurationError, e.pool.read(-1000000000099))
    with patch.object(telethon, '__version__', 'unqualified'):
        await f.expect(PoolConfigurationError, read(e))
        assert (await e.pool.get_pool_status(CHAT)).accounts[0].eligible
    assert not any(s.calls for s in e.senders.values())


async def test_recovery_retry_preserves_a_newer_unknown_attempt():
    e = await setup()
    async def cancel_one():
        before = len(e.senders[111].pending)
        e.senders[111].script = [f.PENDING]
        task = asyncio.create_task(read(e))
        await d.until(lambda: len(e.senders[111].pending) > before)
        task.cancel()
        await f.expect(asyncio.CancelledError, task)
        return (await e.pool.get_pool_status(CHAT)).accounts[0].attempt_id
    first = await cancel_one()
    arguments = dict(attempt_id=first, previous_reader_stopped=True,
                     retry_not_before=datetime.fromtimestamp(f.NOW, timezone.utc))
    await e.pool.recover_account(111, **arguments)
    second = await cancel_one()
    assert second != first
    raw = await e.store.load()
    result = await e.pool.recover_account(111, **arguments)
    assert result.accounts[0].attempt_id == second and await e.store.load() == raw
    arguments['retry_not_before'] = datetime.fromtimestamp(f.NOW + 1, timezone.utc)
    await f.expect(PoolConflictError, e.pool.recover_account(111, **arguments))
    assert e.budget.status(111).used == 2


async def test_recovery_preserves_stronger_restored_restrictions():
    e = await setup()
    e.senders[111].script = [f.PENDING]
    task = asyncio.create_task(read(e))
    await d.until(lambda: bool(e.senders[111].pending))
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    raw = await e.store.load()
    restored = json.loads(raw)
    row = restored['accounts']['111']
    attempt = row['active']['id']
    # Valid restored facts from an operator/backend recovery, not synthetic RPC proof.
    row['not_before'], row['repair'] = f.NOW + 7200, 'banned'
    assert await e.store.compare_and_swap(raw, json.dumps(restored))
    result = await e.pool.recover_account(111, attempt_id=attempt, previous_reader_stopped=True,
                      retry_not_before=datetime.fromtimestamp(f.NOW + 1, timezone.utc))
    assert 'banned' in result.accounts[0].reasons and 'waiting' in result.accounts[0].reasons
    assert json.loads(await e.store.load())['accounts']['111']['not_before'] == f.NOW + 7200


async def test_context_cleanup_keeps_primary_exception():
    e = await setup()
    source = e.pool._sources[111]
    original = source.retire
    async def failed(): raise PoolStateError('synthetic retirement failure')
    source.retire = failed
    primary = LookupError('receiver failure')
    try:
        try:
            async with e.pool:
                raise primary
        except LookupError as error:
            assert error is primary
        else:
            raise AssertionError('primary error was swallowed')
        assert e.pool._closed and e.pool._sources[222]._primary_client is None
    finally:
        source.retire = original


def save_json(file, value):
    with Path(file).open('w') as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())


async def crash_child(manifest, phase, mode, trace):
    values = json.loads(Path(manifest).read_text())
    f.TMP = Path(manifest).parent
    budget = ReadBudget(values['budget'], clock=f.Clock())
    actual = SQLiteAccountPoolStore(values['state'], create=False)
    sources = {}
    class Crash:
        async def load(self): return await actual.load()
        async def compare_and_swap(self, expected, data):
            active = json.loads(data)['accounts']['111']['active'] is not None
            hit = active if phase == 'admission' else not active
            if hit and mode == 'before':
                save_json(trace, dict(source_reads=sum(len(s.reads) for s in sources.values())))
                os._exit(41)
            result = await actual.compare_and_swap(expected, data)
            if hit and mode == 'after':
                save_json(trace, dict(source_reads=sum(len(s.reads) for s in sources.values())))
                os._exit(42)
            return result
    accounts = [PoolAccount(a['id'], a['config'], session_store=f.Store()) for a in values['accounts']]
    pool = AccountPool(accounts, [PoolGroup(CHAT)], read_budget=budget, state_store=Crash())
    pool._wall_clock = f.Clock()
    for aid, source in pool._sources.items():
        _, sources[aid] = wire(source)
    await pool.read(CHAT, after_id=100, limit=1)
    raise AssertionError('crash boundary was not reached')


async def test_process_exit_at_actual_admission_and_settlement():
    for phase in ('admission', 'settlement'):
        for mode in ('before', 'after'):
            e = await setup(attach=False)
            manifest, trace = path('manifest.json'), path('trace.json')
            save_json(manifest, dict(budget=e.budget.path, state=e.store.path,
                accounts=[dict(id=a.account_id, config=a.config_path) for a in e.pool.accounts]))
            process = await asyncio.create_subprocess_exec(sys.executable, __file__, '--crash',
                str(manifest), phase, mode, str(trace), stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(process.communicate(), 15)
            assert process.returncode == (41 if mode == 'before' else 42), stderr.decode()
            assert json.loads(trace.read_text())['source_reads'] == (0 if phase == 'admission' else 1)
            status = (await e.pool.get_pool_status(CHAT)).accounts[0]
            unresolved = (phase == 'admission' and mode == 'after') or (phase == 'settlement' and mode == 'before')
            assert (status.attempt_id is not None) == unresolved
            assert e.budget.status(111).used == (0 if phase == 'admission' else 1)


async def main():
    tests = [value for name, value in globals().items() if name.startswith('test_') and inspect.iscoroutinefunction(value)]
    print('Account Pool Tests — Telethon {}; actual SDK/SQLite, synthetic wire'.format(telethon.__version__))
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata_pool_test_') as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP = d.TMP = Path(directory)
        try:
            for test in tests:
                try:
                    await asyncio.wait_for(test(), 25)
                    print('PASS', test.__name__)
                    results.append(True)
                except Exception:
                    traceback.print_exc()
                    print('FAIL', test.__name__)
                    results.append(False)
        finally:
            for pool in POOLS:
                await pool.close()
            POOLS.clear()
    print('Passed: {}/{}'.format(sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    if len(sys.argv) > 1 and sys.argv[1] == '--crash':
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
             patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
            asyncio.run(crash_child(*sys.argv[2:]))
    else:
        sys.exit(asyncio.run(main()))
