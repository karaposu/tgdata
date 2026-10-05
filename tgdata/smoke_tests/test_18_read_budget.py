"""Offline budget behavior: real SQLite and Telethon with scripted replies.

Run: python -m tgdata.smoke_tests.test_18_read_budget
No account config/session is read. Telegram sockets are forbidden. Process
workers use only temporary SQLite files and synthetic account IDs.
"""
import asyncio
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import inspect
import itertools
import json
import logging
import os
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import telethon
from telethon import TelegramClient, errors
from telethon.tl import functions, types

from tgdata import (TgData, ReadBudget, ReadBudgetError, ReadBudgetExceeded,
                    ReadBudgetConfigError, ReadBudgetStorageError, UnsupportedBudgetRequest)
import tgdata.connection_engine as ce
from tgdata import health
from tgdata.read_budget import WINDOW_SECONDS

NOW = 1700000000.0
ACCOUNT = 111
TMP = None
CLIENTS = []
NUMBERS = itertools.count(1)
PENDING = object()


class Clock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


class Store(dict):
    def load(self, name):
        return self.get(name)

    def save(self, name, data):
        self[name] = data


def ledger(limit=100, *, account=ACCOUNT, curve=None, clock=None):
    clock = clock or Clock()
    budget = ReadBudget(TMP / f'budget_{next(NUMBERS)}.sqlite3', clock=clock)
    budget.configure(account, limit, warmup=curve)
    return budget, clock


def room():
    return types.Channel(id=7, title='Synthetic Room', photo=types.ChatPhotoEmpty(),
                         date=datetime.fromtimestamp(NOW, timezone.utc), access_hash=7,
                         username='synthetic_room', megagroup=True)


def message(mid, text=None, media=False, empty=False):
    if empty:
        return types.MessageEmpty(id=mid, peer_id=types.PeerChannel(7))
    return types.Message(id=mid, peer_id=types.PeerChannel(7), from_id=types.PeerUser(88),
                         date=datetime.fromtimestamp(NOW, timezone.utc),
                         message=text if text is not None else f'message {mid}',
                         media=types.MessageMediaPhoto(photo=types.PhotoEmpty(mid)) if media else None)


def response(messages):
    kwargs = dict(count=5000, messages=messages, chats=[room()],
                  users=[types.User(id=88, access_hash=88, first_name='Author')])
    if 'topics' in inspect.signature(types.messages.MessagesSlice).parameters:
        kwargs['topics'] = []
    return types.messages.MessagesSlice(**kwargs)


def unwrap(request):
    while hasattr(request, 'query') and hasattr(request.query, 'CONSTRUCTOR_ID'):
        request = request.query
    return request


def history(limit=5):
    return functions.messages.GetHistoryRequest(types.InputPeerChannel(7, 7),
                                               0, None, 0, limit, 0, 0, 0)


class Sender:
    def __init__(self, account=ACCOUNT):
        self.account = account
        self.up = True
        self.calls = []
        self.reads = []
        self.script = []
        self.identities = []
        self.pending = []
        self.text = None
        self.media = False
        self.auth_error = False
        self.on_resolve = None

    def is_connected(self):
        return self.up

    async def disconnect(self):
        self.up = False

    def send(self, request, ordered=False):
        if isinstance(request, (list, tuple)):
            return [self.send(item, ordered=ordered) for item in request]
        r = unwrap(request)
        self.calls.append(type(r).__name__)
        future = asyncio.get_running_loop().create_future()
        if isinstance(r, functions.users.GetUsersRequest):
            if self.auth_error:
                result = errors.AuthKeyUnregisteredError(request=r)
            else:
                ident = self.identities.pop(0) if self.identities else self.account
                result = [types.User(id=ident, is_self=True, access_hash=ident, first_name='Account')]
        elif isinstance(r, functions.updates.GetStateRequest):
            result = (errors.AuthKeyUnregisteredError(request=r) if self.auth_error else
                      types.updates.State(1, 1, datetime.fromtimestamp(NOW, timezone.utc), 1, 0))
        elif isinstance(r, functions.channels.GetChannelsRequest):
            result = types.messages.Chats(chats=[room()])
        elif isinstance(r, functions.contacts.ResolveUsernameRequest):
            if self.on_resolve:
                self.on_resolve()
            result = types.contacts.ResolvedPeer(types.PeerChannel(7), [room()], [])
        elif isinstance(r, (functions.messages.GetHistoryRequest, functions.messages.SearchRequest,
                            functions.messages.SearchGlobalRequest, functions.messages.GetRepliesRequest,
                            functions.messages.GetMessagesRequest, functions.channels.GetMessagesRequest)) \
                or type(r).__name__ == 'GetScheduledMessagesRequest':
            bound = getattr(r, 'limit', len(getattr(r, 'id', [])))
            self.reads.append((type(r).__name__, bound, getattr(r, 'offset_id', None),
                               getattr(r, 'add_offset', None)))
            if self.script:
                result = self.script.pop(0)
                if callable(result):
                    result = result(r)
            elif hasattr(r, 'id'):
                ids = [x.id if hasattr(x, 'id') else x for x in r.id]
                result = response([message(mid, media=self.media) for mid in ids])
            else:
                if getattr(r, 'add_offset', 0) < 0:
                    start = r.offset_id or 1
                    ids = reversed(range(start, start + r.limit))
                else:
                    top = (getattr(r, 'offset_id', 0) or 1001) - 1
                    ids = reversed(range(max(1, top - r.limit + 1), top + 1))
                result = response([message(mid, self.text(mid) if self.text else None, self.media) for mid in ids])
        else:
            raise AssertionError(f'unexpected request: {type(r).__name__}')
        if result is PENDING:
            self.pending.append(future)
        elif isinstance(result, BaseException):
            future.set_exception(result)
        else:
            future.set_result(result)
        return future


def config():
    ident = next(NUMBERS)
    path = TMP / f'config_{ident}.ini'
    path.write_text('[Telegram]\napi_id = 12345\n'
                    'api_hash = 0123456789abcdef0123456789abcdef\n'
                    f'session_file = {TMP / ("account_" + str(ident))}\n')
    return str(path)


def instance(budget=None, *, account=ACCOUNT, cached=None, events=None):
    tg = TgData(config(), session_store=Store(), read_budget=budget,
                health_callback=events.append if events is not None else None)
    client = tg.connection_engine._new_client()
    client.session.process_entities([room()])
    client._mb_entity_cache.set_self_user(account if cached is None else cached, False, 1)
    client._sender = sender = Sender(account)
    tg.connection_engine._primary_client = client
    CLIENTS.append(client)
    return tg, client, sender


async def expect(error_type, awaitable):
    try:
        await awaitable
    except error_type as error:
        return error
    raise AssertionError(f'{error_type.__name__} was not raised')


def rejected(error_type, call):
    try:
        call()
    except error_type as error:
        return error
    raise AssertionError(f'{error_type.__name__} was not raised')


async def test_policy_and_defaults():
    tg = TgData(config())
    assert await tg.get_read_budget() is None
    assert tg.connection_engine._primary_client is None
    rejected(ReadBudgetConfigError, lambda: ReadBudget(':memory:'))
    budget, clock = ledger()
    for value in (-1, True, 2.5, '100'):
        rejected(ReadBudgetConfigError, lambda value=value: budget.configure(ACCOUNT, value))
    for curve in ([(1, 10)], [(0, 10), (0, 20)], [(0, 20), (1, 10)], [(0, 101)]):
        rejected(ReadBudgetConfigError, lambda curve=curve: budget.configure(ACCOUNT, 100, curve))
    rejected(ReadBudgetConfigError, lambda: budget.configure(ACCOUNT, 100, started_at=clock() + 1))
    rejected(ReadBudgetConfigError, lambda: budget.configure(ACCOUNT, 100, started_at=datetime.now()))
    rejected(ReadBudgetConfigError, lambda: budget.status(222))
    assert budget.status(ACCOUNT).remaining == 100
    json.dumps(budget.status(ACCOUNT).to_dict())


async def test_persistence_and_isolation():
    budget, clock = ledger(10)
    budget.configure(222, 3)
    token = budget._reserve(ACCOUNT, 7)
    budget._settle(token, 5)
    restarted = ReadBudget(budget.path, clock=clock)
    assert restarted.status(ACCOUNT).used == 5
    assert restarted.status(222).remaining == 3
    rejected(ReadBudgetExceeded, lambda: restarted._reserve(ACCOUNT, 6))
    assert restarted.status(ACCOUNT).used == 5


async def test_warmup_and_policy_changes():
    budget, clock = ledger(300, curve=[(0, 0), (1, 100), (2, 300)])
    stop = rejected(ReadBudgetExceeded, lambda: budget._reserve(ACCOUNT, 1))
    assert stop.retry_after == WINDOW_SECONDS
    clock.value += WINDOW_SECONDS
    assert budget.status(ACCOUNT).limit == 100
    clock.value += WINDOW_SECONDS
    assert budget.status(ACCOUNT).limit == 300
    token = budget._reserve(ACCOUNT, 50)
    budget._settle(token, 50)
    before = budget.status(ACCOUNT)
    after = budget.configure(ACCOUNT, 20)
    assert after.started_at == before.started_at and after.used == 50 and after.remaining == 0
    raised = rejected(ReadBudgetExceeded, lambda: budget._reserve(ACCOUNT, 21))
    assert raised.retry_after is None
    budget.configure(ACCOUNT, 200)
    assert budget.status(ACCOUNT).remaining == 150


async def test_rolling_window_and_clock():
    budget, clock = ledger(10)
    budget._reserve(ACCOUNT, 6)
    clock.value += 100
    budget._reserve(ACCOUNT, 4)
    one = rejected(ReadBudgetExceeded, lambda: budget._reserve(ACCOUNT, 1))
    seven = rejected(ReadBudgetExceeded, lambda: budget._reserve(ACCOUNT, 7))
    assert one.retry_after == WINDOW_SECONDS - 100
    assert seven.retry_after == WINDOW_SECONDS
    clock.value = NOW - 500
    assert budget.status(ACCOUNT).observed_at == NOW + 100
    assert budget.status(ACCOUNT).used == 10
    clock.value = NOW + WINDOW_SECONDS - 0.001
    assert budget.status(ACCOUNT).used == 10
    clock.value = NOW + WINDOW_SECONDS
    assert budget.status(ACCOUNT).used == 4 and budget.status(ACCOUNT).remaining == 6
    clock.value += 100
    assert budget.status(ACCOUNT).remaining == 10


async def test_settlement_and_late_responses():
    budget, clock = ledger(10)
    old = budget._reserve(ACCOUNT, 10)
    assert budget.status(ACCOUNT).reserved == 10
    budget._settle(old, 3)
    budget._settle(old, 0)
    assert budget.status(ACCOUNT).used == 3 and budget.status(ACCOUNT).reserved == 0
    zero = budget._reserve(ACCOUNT, 7)
    budget._settle(zero, 0)
    assert budget.status(ACCOUNT).remaining == 7
    clock.value += WINDOW_SECONDS
    new = budget._reserve(ACCOUNT, 8)
    budget._settle(old, 0)
    assert budget.status(ACCOUNT).used == 8
    budget._settle(new, 8)


def process_claim(args):
    path, amount = args
    budget = ReadBudget(path, clock=lambda: NOW)
    try:
        budget._reserve(ACCOUNT, amount)
        return amount
    except ReadBudgetExceeded:
        return 0


async def test_process_claims():
    budget, _ = ledger(100)
    with ProcessPoolExecutor(max_workers=4) as pool:
        total = sum(pool.map(process_claim, [(budget.path, 7)] * 40))
    assert total == 98 and budget.status(ACCOUNT).used == 98


async def test_identity_authority():
    budget, _ = ledger(50)
    budget.configure(222, 5)
    tg, client, sender = instance(budget, account=222, cached=111)
    await client(history(3))
    assert budget.status(222).used == 3 and budget.status(111).used == 0
    assert (await tg.get_read_budget()).account_id == 222
    assert client._self_id == 111  # no unrelated SDK cache mutation
    sender.account = 111
    await client(history(4))
    assert budget.status(111).used == 4 and budget.status(222).used == 3


async def test_identity_changes_before_send():
    budget, _ = ledger(100)
    budget.configure(222, 0)
    _, client, sender = instance(budget)
    sender.identities = [111, 222]  # page sizing, then the actual attempt
    error = await expect(ReadBudgetExceeded, client.get_messages(types.InputPeerChannel(7, 7), limit=10))
    assert error.account_id == 222 and not sender.reads
    assert budget.status(111).used == budget.status(222).used == 0


async def test_missing_policy_and_logout():
    budget, _ = ledger()
    _, client, sender = instance(budget, account=222)
    await expect(ReadBudgetConfigError, client(history(1)))
    assert not sender.reads
    events = []
    tg, client, sender = instance(budget, events=events)
    sender.auth_error = True
    await expect(errors.AuthKeyUnregisteredError, tg.get_message_count(7))
    assert not sender.reads and budget.status(ACCOUNT).used == 0
    assert [event['verdict'] for event in events] == ['logged out']
    assert 'GetStateRequest' in sender.calls


async def test_refunds_and_wire_bounds():
    budget, _ = ledger(10)
    _, client, sender = instance(budget)
    sender.script = [response([message(1), message(2, empty=True), message(3)])]
    await client(history(8))
    assert budget.status(ACCOUNT).used == 3 and budget.status(ACCOUNT).reserved == 0
    sender.script = [types.messages.MessagesNotModified(count=9000)]
    await client(history(5))
    assert budget.status(ACCOUNT).used == 3
    sender.script = [response([message(i) for i in range(1, 7)])]
    await expect(ReadBudgetError, client(history(5)))
    assert budget.status(ACCOUNT).used == 9
    await expect(ReadBudgetExceeded, client(history(2)))
    assert len(sender.reads) == 3


async def test_retry_admission():
    budget, _ = ledger(7)
    _, client, sender = instance(budget)
    sender.script = [errors.RpcCallFailError(request=None)]
    await expect(ReadBudgetExceeded, client(history(5)))
    assert len(sender.reads) == 1 and budget.status(ACCOUNT).used == 5
    assert budget.status(ACCOUNT).reserved == 5
    before = len(sender.reads)
    client._flood_waited_requests[history().CONSTRUCTOR_ID] = __import__('time').time() + 30
    client.flood_sleep_threshold = 0
    await expect(errors.FloodWaitError, client(history(1)))
    assert len(sender.reads) == before and budget.status(ACCOUNT).used == 5


async def test_concurrent_clients_and_cancellation():
    budget, clock = ledger(100)
    other = ReadBudget(budget.path, clock=clock)
    _, first, sender = instance(budget)
    _, second, second_sender = instance(other)
    sender.script = [PENDING]
    task = asyncio.create_task(first(history(70)))
    await asyncio.sleep(0)
    assert sender.pending and budget.status(ACCOUNT).reserved == 70
    await expect(ReadBudgetExceeded, second(history(70)))
    assert not second_sender.reads
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert budget.status(ACCOUNT).used == 70
    clock.value += WINDOW_SECONDS
    assert other.status(ACCOUNT).used == 0


async def test_forward_and_reverse_pages():
    for reverse in (False, True):
        budget, clock = ledger(37)
        _, client, sender = instance(budget)
        iterator = client.iter_messages(types.InputPeerChannel(7, 7), limit=2000,
                                        min_id=100 if reverse else 0, reverse=reverse)
        rows = []
        try:
            async for msg in iterator:
                rows.append(msg.id)
        except ReadBudgetExceeded:
            pass
        else:
            raise AssertionError('large fetch did not stop at its allowance')
        assert len(rows) == 37 and [r[1] for r in sender.reads] == [37]
        if reverse:
            assert rows == list(range(101, 138)) and sender.reads[0][3] == -37
            clock.value += WINDOW_SECONDS
            budget.configure(ACCOUNT, 100)
            resumed = [(await iterator.__anext__()).id for _ in range(100)]
            assert resumed == list(range(138, 238))
            assert sender.reads[-1][1:] == (100, 138, -100)
        else:
            assert rows == list(range(1000, 963, -1))


async def test_ids_keep_position():
    budget, clock = ledger(2)
    _, client, sender = instance(budget)
    iterator = client.iter_messages(types.InputPeerChannel(7, 7), ids=[10, 20, 30])
    await expect(ReadBudgetExceeded, iterator.__anext__())
    assert not sender.reads
    budget.configure(ACCOUNT, 3)
    actual = [(await iterator.__anext__()).id for _ in range(3)]
    assert actual == [10, 20, 30]
    assert budget.status(ACCOUNT).used == 3


async def test_request_families_and_wrappers():
    budget, _ = ledger(30)
    _, client, sender = instance(budget)
    peer = types.InputPeerChannel(7, 7)
    calls = [
        functions.messages.SearchRequest(peer, 'x', types.InputMessagesFilterEmpty(),
                                         None, None, 0, 0, 2, 0, 0, 0),
        functions.messages.SearchGlobalRequest('x', types.InputMessagesFilterEmpty(),
                                               None, None, 0, types.InputPeerEmpty(), 0, 2),
        functions.messages.GetRepliesRequest(peer, 1, 0, None, 0, 2, 0, 0, 0),
        functions.messages.GetMessagesRequest([types.InputMessageID(1), types.InputMessageID(2)]),
        functions.channels.GetMessagesRequest(types.InputChannel(7, 7),
                                              [types.InputMessageID(3), types.InputMessageID(4)]),
        functions.InvokeWithoutUpdatesRequest(history(2)),
        functions.InvokeWithTakeoutRequest(123, functions.InvokeWithoutUpdatesRequest(history(2))),
    ]
    if hasattr(functions.messages, 'GetScheduledMessagesRequest'):
        calls.append(functions.messages.GetScheduledMessagesRequest(peer, [1, 2]))
    for request in calls:
        await client(request)
    assert budget.status(ACCOUNT).used == 2 * len(calls)
    before = len(sender.reads)
    await expect(UnsupportedBudgetRequest, client([history(1), history(1)]))
    await expect(UnsupportedBudgetRequest, client(functions.messages.GetScheduledHistoryRequest(peer, 0)))
    await expect(UnsupportedBudgetRequest, client(functions.messages.GetDiscussionMessageRequest(peer, 1)))
    await expect(UnsupportedBudgetRequest, client(history(0)))
    assert len(sender.reads) == before and budget.status(ACCOUNT).used == 2 * len(calls)


async def test_no_updates_wrapper_and_metadata():
    budget, _ = ledger(2)
    _, client, sender = instance(budget)
    client._no_updates = True
    await client(history(2))
    await client.get_me()
    metadata = await client([functions.updates.GetStateRequest(), functions.updates.GetStateRequest()])
    assert len(metadata) == 2
    assert budget.status(ACCOUNT).used == 2
    await expect(ReadBudgetExceeded, client(history(1)))
    assert len(sender.reads) == 1


async def test_admission_after_resolution():
    budget, clock = ledger(10)
    budget._reserve(ACCOUNT, 5)
    _, client, sender = instance(budget)
    sender.on_resolve = lambda: setattr(clock, 'value', NOW + WINDOW_SECONDS)
    request = history(5)
    request.peer = 'budget_peer'
    await client(request)
    assert 'ResolveUsernameRequest' in sender.calls
    assert budget.status(ACCOUNT).used == 5
    assert budget.status(ACCOUNT).reserved == 0


async def test_no_budget_message_path():
    tg, _, sender = instance()
    rows = await tg.get_messages(7, limit=3)
    assert len(rows) == 3 and [r[1] for r in sender.reads] == [3]
    assert 'GetUsersRequest' not in sender.calls


async def test_storage_failures():
    budget, _ = ledger(5)
    _, client, sender = instance(budget)
    with sqlite3.connect(budget.path) as db:
        db.execute('UPDATE tgdata_budget_meta SET version = 99')
    await expect(ReadBudgetStorageError, client(history(1)))
    assert not sender.reads
    rejected(ReadBudgetStorageError, lambda: ReadBudget(budget.path))
    with sqlite3.connect(budget.path) as db:
        db.execute('UPDATE tgdata_budget_meta SET version = 1')
        db.execute("UPDATE tgdata_budget_accounts SET warmup = 'not JSON'")
    await expect(ReadBudgetStorageError, client(history(1)))
    assert not sender.reads
    budget.configure(ACCOUNT, 5)
    Path(budget.path).unlink()
    await expect(ReadBudgetStorageError, client(history(1)))
    assert not sender.reads


async def test_settlement_failure_keeps_charge():
    budget, _ = ledger(5)
    _, client, sender = instance(budget)

    def invalid_schema(request):
        with sqlite3.connect(budget.path) as db:
            db.execute('UPDATE tgdata_budget_meta SET version = 99')
        return response([message(1)])

    sender.script = [invalid_schema]
    await expect(ReadBudgetStorageError, client(history(5)))
    with sqlite3.connect(budget.path) as db:
        db.execute('UPDATE tgdata_budget_meta SET version = 1')
    assert budget.status(ACCOUNT).used == 5 and budget.status(ACCOUNT).reserved == 5


async def test_fetch_partial_and_filtered_rows():
    budget, _ = ledger(300)
    events = []
    tg, _, sender = instance(budget, events=events)
    error = await expect(ReadBudgetExceeded, tg.get_messages(7, limit=2000, after_id=100))
    assert isinstance(error.partial_result, pd.DataFrame) and len(error.partial_result) == 300
    assert error.partial_result['MessageId'].tolist() == list(range(101, 401))
    assert set(error.partial_result['SenderId']) == {88} and error.account_id == ACCOUNT
    assert sum(row[1] for row in sender.reads) == 300 and not events

    budget, _ = ledger(3)
    tg, _, sender = instance(budget)
    # Keep IDs above the page bound: older Telethon treats low IDs as the
    # end of history even in reverse. This case tests filtering, not that
    # SDK heuristic; all three returned slots must still consume allowance.
    sender.script = [response([message(mid) for mid in range(1003, 1000, -1)])]
    future = datetime.fromtimestamp(NOW + 1000, timezone.utc)
    error = await expect(ReadBudgetExceeded, tg.get_messages(7, limit=100, start_date=future))
    assert error.partial_result.empty and budget.status(ACCOUNT).used == 3


async def test_search_and_count():
    budget, _ = ledger(3)
    tg, _, sender = instance(budget)
    error = await expect(ReadBudgetExceeded, tg.search_messages('message', 7, limit=100))
    assert len(error.partial_result) == 3 and budget.status(ACCOUNT).used == 3
    count = len(sender.reads)
    await expect(ReadBudgetExceeded, tg.get_message_count(7))
    assert len(sender.reads) == count


async def test_polling_partial_stop():
    budget, _ = ledger(3)
    tg, _, sender = instance(budget)
    delivered = []

    async def receive(df):
        delivered.extend(df['MessageId'].tolist())

    error = await expect(ReadBudgetExceeded, tg.poll_for_messages(
        7, interval=0, after_id=100, callback=receive, max_iterations=5))
    assert delivered == [101, 102, 103]
    assert len(sender.reads) == 1 and len(error.partial_result) == 3


async def test_media_partial_and_default():
    budget, _ = ledger(100)
    tg, client, sender = instance(budget)
    sender.media = True

    async def download(msg, file=None, **kwargs):
        return f'media-{msg.id}'.encode()

    client.download_media = download
    error = await expect(ReadBudgetExceeded, tg.download_media_by_id(7, list(range(1, 151))))
    assert len(error.partial_result) == 100
    assert error.partial_result[1] == b'media-1' and error.partial_result[100] == b'media-100'
    assert len(sender.reads) == 1

    plain, plain_client, plain_sender = instance()
    plain_sender.media = True
    plain_client.download_media = download
    assert await plain.download_media_by_id(7, [1, 2]) == {1: b'media-1', 2: b'media-2'}
    assert 'GetUsersRequest' not in plain_sender.calls


async def test_discovery_partial():
    budget, _ = ledger(3)
    tg, _, sender = instance(budget)
    sender.text = lambda mid: f'https://t.me/room_{mid}'
    found = []
    error = await expect(ReadBudgetExceeded, tg.linked_groups(
        7, posts=100, pace=0, found_callback=found.append))
    assert len(error.partial_result) == len(found) == 3
    assert set(error.partial_result['FoundVia']) == {'link'}
    assert len(sender.reads) == 1 and budget.status(ACCOUNT).used == 3


async def test_conversion_and_callback_errors():
    budget, _ = ledger(3)
    tg, client, sender = instance(budget)
    sender.media = True

    async def blocked_media(*args, **kwargs):
        status = budget.status(ACCOUNT)
        raise ReadBudgetExceeded(status, 1, status.next_available_at)

    client.download_media = blocked_media
    error = await expect(ReadBudgetExceeded, tg.get_messages(7, limit=3, include_media=True))
    assert error.partial_result.empty and budget.status(ACCOUNT).used == 3

    budget, _ = ledger(20)
    tg, _, _ = instance(budget)
    deliberate = ValueError('caller callback error')

    async def broken(*args):
        raise deliberate

    caught = await expect(ValueError, tg.get_messages(7, limit=5, batch_size=2, batch_callback=broken))
    assert caught is deliberate


async def test_budget_errors_are_local():
    budget, _ = ledger(0)
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        error = rejected(ReadBudgetExceeded, lambda: budget._reserve(ACCOUNT, 1))
    assert health.classify(error) is None
    assert error.retry_after is None


async def test_factory_paths():
    budget, _ = ledger(10)
    built = []

    class StandIn(TelegramClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._sender = Sender()
            self.session.process_entities([room()])
            built.append(self)
            CLIENTS.append(self)

        async def connect(self):
            self._sender.up = True

        async def start(self, *args, **kwargs):
            raise AssertionError('login forbidden')

    with patch.object(ce, 'TelegramClient', StandIn):
        tg = TgData(config(), connection_pool_size=3, session_store=Store(), read_budget=budget)
        await tg.connection_engine.get_client()
        async with tg.connection_engine.ephemeral_client() as ephemeral:
            await ephemeral(history(1))
        for client in tg.connection_engine._pool.connections:
            await client(history(1))
        assert len(built) == 4 and all(c._tgdata_read_budget is budget for c in built)
        assert budget.status(ACCOUNT).used == 4
        await tg.close()


async def main():
    global TMP
    tests = [test_policy_and_defaults, test_persistence_and_isolation, test_warmup_and_policy_changes,
             test_rolling_window_and_clock, test_settlement_and_late_responses, test_process_claims,
             test_identity_authority, test_identity_changes_before_send, test_missing_policy_and_logout,
             test_refunds_and_wire_bounds, test_retry_admission, test_concurrent_clients_and_cancellation,
             test_forward_and_reverse_pages, test_ids_keep_position, test_request_families_and_wrappers,
             test_no_updates_wrapper_and_metadata, test_admission_after_resolution, test_no_budget_message_path,
             test_storage_failures, test_settlement_failure_keeps_charge,
             test_fetch_partial_and_filtered_rows, test_search_and_count, test_polling_partial_stop,
             test_media_partial_and_default, test_discovery_partial, test_conversion_and_callback_errors,
             test_budget_errors_are_local, test_factory_paths]
    print(f'Read Budget Tests — Telethon {telethon.__version__}; synthetic credentials; no Telegram sockets')
    logging.getLogger('tgdata').addHandler(logging.NullHandler())
    results = []
    with tempfile.TemporaryDirectory(prefix='tgdata_budget_test_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        TMP = Path(tmp)
        try:
            for number, test in enumerate(tests, 1):
                print(f'\nTEST {number}: {test.__name__[5:]}')
                try:
                    await asyncio.wait_for(test(), timeout=40)
                    results.append(True)
                    print('✓ Passed')
                except Exception:
                    results.append(False)
                    traceback.print_exc()
                    print('✗ Failed')
        finally:
            for client in CLIENTS:
                await client.disconnect()
            CLIENTS.clear()
    print(f'\nPassed: {sum(results)}/{len(results)}')
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
