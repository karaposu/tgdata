"""Offline public group operations: real Telethon1.45 dispatch and SQLite.

Run: python -m tgdata.smoke_tests.test_20_group_operations
No live accounts, network, login, membership changes or production files.
"""
import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import io
import itertools
import json
import logging
import multiprocessing
from pathlib import Path
import socket
import sqlite3
import tempfile
import traceback
from unittest.mock import patch

import telethon
from telethon import TelegramClient, errors
from telethon.crypto import AuthKey
from telethon.extensions import BinaryReader
from telethon.sessions import SQLiteSession
from telethon.tl import functions, types
from telethon.tl.tlobject import TLRequest

from tgdata import (TgData, GroupInfo, GroupReferenceError, GroupResponseError,
                    GroupOperationError, GroupJoin, JoinBudget, JoinBudgetError,
                    JoinBudgetConfigError, JoinBudgetStorageError, JoinBudgetExceeded,
                    UnsupportedJoinRequest, ReadBudget, ReadBudgetExceeded)
from tgdata import health
import tgdata.connection_engine as ce
from tgdata.group_operations import _parse_target
from tgdata.smoke_tests import test_18_read_budget as f

TMP = None
SEQ = itertools.count()
ACTIVE = None
TOKEN = 'Synthetic_PRIVATE-Invite_7'
LINK = 'https://t.me/+' + TOKEN
NOW = f.NOW


def room(**changes):
    result = f.room()
    result.left = True
    for name, value in changes.items():
        setattr(result, name, value)
    return result


def preview(**changes):
    args = dict(title='Synthetic Private Room', photo=types.PhotoEmpty(0),
                participants_count=12, color=0, megagroup=True, channel=True)
    args.update(changes)
    return types.ChatInvite(**args)


def joined(chats=None):
    return types.messages.ChatInviteJoinResultOk(types.Updates(
        [], [], [room(left=False)] if chats is None else chats,
        datetime.fromtimestamp(NOW, timezone.utc), 1))


def decoded(reply):
    with BinaryReader(bytes(reply)) as reader:
        return reader.tgread_object()


class Sender(f.Sender):
    def __init__(self, account=f.ACCOUNT):
        super().__init__(account)
        self.entity = room()
        self.invite = preview()
        self.resolve_reply = None
        self.channels_reply = None
        self.join_script = []
        self.requests = []
        self.join_requests = []
        self.state_error = None
        self.on_join = None

    def send(self, request, ordered=False):
        if isinstance(request, (list, tuple)):
            return [self.send(x, ordered) for x in request]
        r = f.unwrap(request)
        self.requests.append(r)
        if isinstance(r, functions.contacts.ResolveUsernameRequest):
            reply = self.resolve_reply
            if reply is None:
                peer = types.PeerChat(self.entity.id) if isinstance(self.entity, types.Chat) else types.PeerChannel(self.entity.id)
                reply = types.contacts.ResolvedPeer(peer, [self.entity], [])
        elif isinstance(r, functions.channels.GetChannelsRequest):
            reply = self.channels_reply if self.channels_reply is not None else types.messages.Chats([self.entity])
        elif isinstance(r, functions.messages.GetChatsRequest):
            reply = types.messages.Chats([self.entity])
        elif isinstance(r, functions.messages.CheckChatInviteRequest):
            assert r.hash == TOKEN
            reply = self.invite
        elif isinstance(r, (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest)):
            self.join_requests.append(r)
            if self.on_join:
                self.on_join(r)
            reply = self.join_script.pop(0) if self.join_script else decoded(joined())
        elif isinstance(r, functions.updates.GetStateRequest) and self.state_error is not None:
            reply = self.state_error
        else:
            return super().send(request, ordered)
        self.calls.append(type(r).__name__)
        future = asyncio.get_running_loop().create_future()
        if callable(reply):
            reply = reply(r)
        if reply is f.PENDING:
            self.pending.append(future)
        elif isinstance(reply, BaseException):
            future.set_exception(reply)
        else:
            future.set_result(reply)
        return future


class StandIn(TelegramClient):
    """Only transport lifecycle stands in; SDK dispatch and sessions are real."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test_rig = ACTIVE
        self._sender = ACTIVE.queue.pop(0) if ACTIVE.queue else Sender()
        self._mb_entity_cache.set_self_user(ACTIVE.cached, False, 1)
        self.session.set_dc(2, '149.154.167.51', 443)
        self.session.auth_key = AuthKey(bytes(range(256)))
        for entity in ACTIVE.seed:
            self.session.process_entities([entity])
        self.starts = self.connects = self.disconnects = 0
        ACTIVE.clients.append(self)

    async def connect(self):
        self.connects += 1
        self._sender.up = True
        return True

    async def disconnect(self):
        self.disconnects += 1
        self._sender.up = False
        self.session.close()

    async def start(self, *args, **kwargs):
        self.starts += 1
        raise AssertionError('interactive login forbidden')


@contextmanager
def rig(budget=None, read=None, senders=None, seed=(), cached=999, callback=None, config_extra=''):
    global ACTIVE
    class State:
        pass
    r = State()
    r.queue, r.clients, r.seed, r.cached = list(senders or []), [], seed, cached
    r.events = []
    r.store = f.Store()
    config = TMP / ('group_config_{}.ini'.format(next(SEQ)))
    config.write_text('[Telegram]\napi_id=12345\napi_hash=synthetic_api_hash\n'
                      'session_file=synthetic_group_account\n' + config_extra)
    r.tg = TgData(str(config), session_store=r.store, join_budget=budget, read_budget=read,
                  health_callback=callback or r.events.append)
    previous = ACTIVE
    ACTIVE = r
    try:
        with patch.object(ce, 'TelegramClient', StandIn):
            yield r
    finally:
        ACTIVE = previous
        for client in r.clients:
            client.session.close()


def ledger(limit=5, account=f.ACCOUNT, clock=None):
    clock = clock or f.Clock()
    result = JoinBudget(TMP / ('join_{}.sqlite3'.format(next(SEQ))), clock=clock)
    result.configure(account, limit)
    return result, clock


async def expect(cls, operation):
    return await f.expect(cls, operation)


def reject(cls, fn):
    return f.rejected(cls, fn)


def count(sender, cls):
    return sum(isinstance(r, cls) for r in sender.requests)


async def test_defaults_and_values():
    before = GroupInfo(id=7, title='Room').to_dict()
    with rig() as r:
        assert await r.tg.get_join_budget() is None and not r.clients
        r.tg.set_group(900)
        value = await r.tg.lookup_group('@synthetic_room')
        assert value.group.peer_id == -1000000000007 and value.member is False
        assert r.tg.current_group.id == 900 and r.tg.connection_engine._primary_client is None
        assert len(r.clients) == 1 and r.clients[0].connects == r.clients[0].disconnects == 1
        assert r.clients[0].starts == 0
        assert r.clients[0]._tgdata_join_budget is None
        json.dumps(value.to_dict())
        reject(FrozenInstanceError, lambda: setattr(value, 'member', True))
    assert before == GroupInfo(id=7, title='Room').to_dict()


async def test_reference_grammar():
    for value in ('@Synthetic_room', 'synthetic_room', 'https://t.me/synthetic_room',
                  'telegram.me/synthetic_room', 'http://www.t.me/synthetic_room'):
        assert _parse_target(value).value == 'synthetic_room'
    for value in (LINK, 't.me/joinchat/' + TOKEN, 'https://telegram.me/+' + TOKEN):
        target = _parse_target(value)
        assert target.value == TOKEN and TOKEN not in repr(target)
    for value in (7, -7, -1000000000007, '7'):
        assert _parse_target(value).kind == 'id'
    invalid = (None, False, 0, '', [], object(), '+905551111111', 'me', 'https://evil.test/synthetic_room',
               'https://t.me@evil.test/synthetic_room', 'https://t.me:80/synthetic_room',
               LINK + '?x=1', LINK + '#fragment', LINK + '/more', 'https://t.me/[bad',
               'https://[invalid/', 'https://t.me/joinchat/', '@bad/name', 't.me/s/room')
    with rig() as r:
        for value in invalid:
            exc = await expect(GroupReferenceError, r.tg.lookup_group(value))
            assert TOKEN not in str(exc)
        for value in (7, '-7'):
            await expect(GroupReferenceError, r.tg.join_group(value))
        assert not r.clients and not r.events


async def test_entity_projection_and_numeric_cache():
    chat = types.Chat(8, 'Basic', types.ChatPhotoEmpty(), 4, None, 1)
    sender = Sender(); sender.entity = chat
    with rig(senders=[sender], seed=[chat]) as r:
        value = await r.tg.lookup_group(-8)
        assert value.group.kind == 'group' and value.member is True
    with rig() as r:
        await expect(GroupReferenceError, r.tg.lookup_group(99999))
        assert not count(r.clients[0]._sender, functions.channels.GetChannelsRequest)
    with rig(seed=[room(), types.User(id=7, access_hash=7, is_self=True)]) as r:
        await expect(GroupReferenceError, r.tg.lookup_group(7))
    sender = Sender(); sender.entity = types.ChannelForbidden(7, 7, 'Forbidden', megagroup=True)
    with rig(senders=[sender]) as r:
        value = await r.tg.lookup_group('synthetic_room')
        assert value.member is None and value.group.kind == 'megagroup'
    sender = Sender(); sender.resolve_reply = types.contacts.ResolvedPeer(types.PeerUser(88), [], [types.User(88)])
    with rig(senders=[sender]) as r:
        await expect(GroupReferenceError, r.tg.lookup_group('synthetic_user'))
    sender = Sender(); sender.resolve_reply = types.contacts.ResolvedPeer(types.PeerChannel(7), [], [])
    with rig(senders=[sender]) as r:
        await expect(GroupResponseError, r.tg.lookup_group('synthetic_room'))


async def test_invite_shapes():
    expiry = datetime.fromtimestamp(NOW + 600, timezone.utc)
    for reply, member, ident in ((preview(request_needed=True), False, None),
                                  (types.ChatInviteAlready(room(left=False)), True, 7),
                                  (types.ChatInvitePeek(room(), expiry), False, 7)):
        sender = Sender(); sender.invite = decoded(reply)
        with rig(senders=[sender]) as r:
            value = await r.tg.lookup_group(LINK)
            assert value.member is member and value.group.id == ident
            assert not sender.join_requests and not sender.reads
            assert TOKEN not in json.dumps(value.to_dict())
            if isinstance(reply, types.ChatInvitePeek):
                assert value.preview_expires_at == expiry
                assert value.to_dict()['preview_expires_at'] == expiry.isoformat()


async def test_readable_nonmember_and_budget():
    budget = ReadBudget(TMP / 'access_read.sqlite', clock=f.Clock())
    budget.configure(f.ACCOUNT, 2)
    sender = Sender(); sender.script = [f.response([])]
    with rig(read=budget, senders=[sender]) as r:
        result = await r.tg.check_group_access('synthetic_room')
        assert result.readable is True and result.member is False
        assert sender.reads[0][1] == 1 and len(sender.reads) == 1
        assert budget.status(f.ACCOUNT).used == 0
    sender = Sender()
    with rig(read=budget, senders=[sender]) as r:
        assert (await r.tg.check_group_access('synthetic_room')).readable
        assert budget.status(f.ACCOUNT).used == 1


async def test_denials_and_other_errors():
    for resolve in (True, False):
        sender = Sender(); error = errors.ChannelPrivateError(None)
        if resolve: sender.resolve_reply = error
        else: sender.script = [error]
        with rig(senders=[sender]) as r:
            value = await r.tg.check_group_access('synthetic_room')
            assert value.status == 'denied' and value.readable is False
            assert (value.group is None) is resolve
            assert len([x for x in r.events if x['verdict'] == health.NO_ACCESS]) == 1
            assert r.events[-1]['account']['user_id'] == f.ACCOUNT
    for error in (OSError('synthetic transport'), errors.AuthKeyUnregisteredError(None),
                  errors.FloodWaitError(None, capture=9)):
        sender = Sender(); sender.script = [error]
        with rig(senders=[sender]) as r:
            exc = await expect(type(error), r.tg.check_group_access('synthetic_room'))
            assert exc is error and len(sender.reads) == 1
    budget = ReadBudget(TMP / 'denied_read.sqlite', clock=f.Clock()); budget.configure(f.ACCOUNT, 0)
    with rig(read=budget) as r:
        await expect(ReadBudgetExceeded, r.tg.check_group_access('synthetic_room'))
        assert not r.clients[0]._sender.reads and not r.events


async def test_unprobed_and_min_entities():
    sender = Sender()
    with rig(senders=[sender]) as r:
        result = await r.tg.check_group_access(LINK)
        assert result.readable is None and result.reason == 'NO_PEER' and not sender.reads
    for entity in (room(min=True), room(access_hash=None)):
        sender = Sender(); sender.entity = entity
        with rig(senders=[sender]) as r:
            result = await r.tg.check_group_access('synthetic_room')
            assert result.status == 'unprobed' and not sender.reads


async def test_join_ack_and_existing_membership():
    budget, _ = ledger()
    for target in ('synthetic_room', LINK):
        sender = Sender()
        with rig(budget, senders=[sender]) as r:
            result = await r.tg.join_group(target)
            assert result.status == 'joined' and result.member is True
            assert result.group.id == 7 and len(sender.join_requests) == 1
            assert isinstance(sender.requests[-1], (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest))
            assert r.clients[0].session.get_input_entity('synthetic_room').channel_id == 7
    assert budget.status(f.ACCOUNT).used == 2
    for invite in (False, True):
        sender = Sender(); sender.entity = room(left=False)
        sender.invite = types.ChatInviteAlready(sender.entity)
        with rig(budget, senders=[sender]) as r:
            assert (await r.tg.join_group(LINK if invite else 'synthetic_room')).status == 'already_joined'
            assert not sender.join_requests
    assert budget.status(f.ACCOUNT).used == 2
    sender = Sender(); sender.join_script = [errors.UserAlreadyParticipantError(None)]
    with rig(budget, senders=[sender]) as r:
        assert (await r.tg.join_group(LINK)).status == 'already_joined'
    assert budget.status(f.ACCOUNT).used == 3


async def test_incomplete_join_outcomes():
    replies = [(errors.InviteRequestSentError(None), 'requested'),
               (decoded(types.messages.ChatInviteJoinResultWebView(9, 17, [])), 'interaction_required'),
               (errors.RPCError(None, 'STARS_PAYMENT_REQUIRED', 400), 'payment_required')]
    for reply, expected in replies:
        budget, _ = ledger()
        sender = Sender(); sender.join_script = [reply]
        with rig(budget, senders=[sender]) as r:
            result = await r.tg.join_group(LINK)
            assert result.status == expected and result.member is None
            assert budget.status(f.ACCOUNT).used == 1
            if expected == 'interaction_required':
                assert result.bot_id == 9 and result.query_id == 17
            assert TOKEN not in json.dumps(result.to_dict()) and not r.events
    budget, _ = ledger()
    sender = Sender(); sender.invite = preview(subscription_pricing=types.StarsSubscriptionPricing(86400, 10))
    with rig(budget, senders=[sender]) as r:
        assert (await r.tg.join_group(LINK)).status == 'payment_required'
        assert not sender.join_requests and budget.status(f.ACCOUNT).used == 0


async def test_ack_without_details_and_unknown_reply():
    for updates in (types.UpdatesTooLong(), types.Updates([], [], [], datetime.now(timezone.utc), 1)):
        budget, _ = ledger(); sender = Sender()
        sender.join_script = [types.messages.ChatInviteJoinResultOk(updates)]
        with rig(budget, senders=[sender]) as r:
            value = await r.tg.join_group(LINK)
            assert value.status == 'joined' and value.group.id is None
    budget, _ = ledger(); sender = Sender(); sender.join_script = [types.UpdatesTooLong()]
    with rig(budget, senders=[sender]) as r:
        await expect(GroupResponseError, r.tg.join_group(LINK))
        assert budget.status(f.ACCOUNT).used == 1 and not r.events


async def test_policy_window_and_persistence():
    clock = f.Clock(); budget, _ = ledger(3, clock=clock)
    for delta in (0, 10, 20):
        clock.value = NOW + delta; budget._claim(f.ACCOUNT)
    assert budget.status(f.ACCOUNT).used == 3
    status = budget.configure(f.ACCOUNT, 1)
    assert status.next_available_at == NOW + 20 + 86400
    clock.value = NOW - 100
    assert budget.status(f.ACCOUNT).observed_at == NOW + 20
    restarted = JoinBudget(budget.path, clock=clock)
    assert restarted.status(f.ACCOUNT).used == 3
    clock.value = NOW + 20 + 86400
    assert restarted.status(f.ACCOUNT).remaining == 1
    restarted.configure(222, 0)
    assert restarted.status(222).retry_after is None
    reject(JoinBudgetExceeded, lambda: restarted._claim(222))
    assert restarted.status(f.ACCOUNT).used == 0
    for invalid in (True, -1, 1.2, '3'):
        reject(JoinBudgetConfigError, lambda: budget.configure(f.ACCOUNT, invalid))
    reject(JoinBudgetConfigError, lambda: JoinBudget(':memory:'))
    json.dumps(status.to_dict())


async def test_missing_policy_and_zero_cap():
    with rig() as r:
        await expect(JoinBudgetConfigError, r.tg.join_group(LINK))
        assert not r.clients
    budget, _ = ledger(account=222)
    with rig(budget) as r:
        await expect(JoinBudgetConfigError, r.tg.join_group(LINK))
        assert not r.clients[0]._sender.join_requests and not r.events
    budget, _ = ledger(0)
    with rig(budget) as r:
        await expect(JoinBudgetExceeded, r.tg.join_group(LINK))
        assert not r.clients[0]._sender.join_requests
    sender = Sender(); sender.invite = types.ChatInviteAlready(room(left=False))
    with rig(budget, senders=[sender]) as r:
        assert (await r.tg.join_group(LINK)).status == 'already_joined'


def process_claims(path):
    budget = JoinBudget(path, clock=lambda: NOW)
    accepted = 0
    for _ in range(6):
        try: budget._claim(f.ACCOUNT); accepted += 1
        except JoinBudgetExceeded: pass
    return accepted


async def test_process_atomicity():
    budget, _ = ledger(7)
    with ProcessPoolExecutor(max_workers=4, mp_context=multiprocessing.get_context('spawn')) as pool:
        accepted = list(pool.map(process_claims, [budget.path] * 4))
    assert sum(accepted) == budget.status(f.ACCOUNT).used == 7


async def test_storage_and_read_budget_coexistence():
    budget, _ = ledger(4)
    read = ReadBudget(budget.path, clock=f.Clock()); read.configure(f.ACCOUNT, 8)
    budget._claim(f.ACCOUNT)
    read._reserve(f.ACCOUNT, 3)
    assert budget.status(f.ACCOUNT).used == 1 and read.status(f.ACCOUNT).used == 3
    reject(JoinBudgetStorageError, lambda: JoinBudget(TMP / 'missing' / 'ledger.sqlite'))
    with sqlite3.connect(budget.path) as db:
        db.execute('UPDATE tgdata_join_meta SET version=99')
    with rig(budget) as r:
        error = await expect(JoinBudgetStorageError, r.tg.join_group(LINK))
        assert TOKEN not in str(error) and not r.clients[0]._sender.join_requests and not r.events
    budget, _ = ledger()
    with sqlite3.connect(budget.path) as db:
        db.execute('DROP TABLE tgdata_join_attempts')
    reject(JoinBudgetStorageError, lambda: budget._claim(f.ACCOUNT))


async def test_actual_retry_and_failure_charge():
    async def no_wait(_): pass
    for limit in (1, 2):
        budget, _ = ledger(limit); sender = Sender()
        sender.join_script = [errors.ServerError(None, 'synthetic retry'), joined()]
        with rig(budget, senders=[sender]) as r, patch('telethon.client.users.asyncio.sleep', no_wait):
            if limit == 1: await expect(JoinBudgetExceeded, r.tg.join_group(LINK))
            else: assert (await r.tg.join_group(LINK)).status == 'joined'
            assert len(sender.join_requests) == limit and budget.status(f.ACCOUNT).used == limit
    budget, _ = ledger(); sender = Sender(); failure = OSError('synthetic network loss')
    sender.join_script = [failure]
    with rig(budget, senders=[sender]) as r:
        assert await expect(OSError, r.tg.join_group(LINK)) is failure
        assert budget.status(f.ACCOUNT).used == 1 and not r.events


async def test_cancelled_send_and_no_open_transaction():
    budget, _ = ledger(); sender = Sender(); sender.join_script = [f.PENDING]
    with rig(budget, senders=[sender]) as r:
        task = asyncio.create_task(r.tg.join_group(LINK))
        for _ in range(100):
            if sender.pending: break
            await asyncio.sleep(0)
        assert sender.pending
        with sqlite3.connect(budget.path, timeout=0) as db:
            db.execute('BEGIN IMMEDIATE'); db.rollback()
        task.cancel()
        await expect(asyncio.CancelledError, task)
        assert budget.status(f.ACCOUNT).used == 1
        assert r.clients[0].disconnects == 1


async def test_fresh_identity_and_factory_controls():
    budget, _ = ledger(account=222)
    sender = Sender(account=222)
    with rig(budget, senders=[sender], cached=111, config_extra='device_model=Pinned Device\n') as r:
        result = await r.tg.join_group(LINK)
        client = r.clients[0]
        assert result.member and budget.status(222).used == 1 and client._self_id == 111
        assert client._init_request.device_model == 'Pinned Device'
        for name in ('synthetic_group_account_1', 'synthetic_group_account_2'):
            extra = r.tg.connection_engine._new_client(name)
            assert extra._tgdata_join_budget is budget
        r.queue.append(Sender(222))
        status = await r.tg.get_join_budget()
        assert status.account_id == 222


async def test_identity_changes_and_resolution_refusal():
    budget, _ = ledger(account=222); budget.configure(333, 5)
    sender = Sender(222); sender.identities = [222, 222, 333]
    with rig(budget, senders=[sender]) as r:
        assert (await r.tg.join_group(LINK)).member
        assert budget.status(222).used == 0 and budget.status(333).used == 1
    sender = Sender(); sender.resolve_reply = errors.UsernameNotOccupiedError(None)
    budget, _ = ledger()
    with rig(budget, senders=[sender]) as r:
        await expect(errors.UsernameNotOccupiedError, r.tg.join_group('synthetic_missing'))
        assert budget.status(f.ACCOUNT).used == 0
    sender = Sender(); sender.auth_error = True
    with rig(budget, senders=[sender]) as r:
        await expect(ce.AuthRequiredError, r.tg.join_group(LINK))
        assert budget.status(f.ACCOUNT).used == 0 and not sender.join_requests


async def test_wrappers_batches_and_read_independence():
    budget, _ = ledger()
    read = ReadBudget(TMP / 'wrapper_read.sqlite', clock=f.Clock()); read.configure(f.ACCOUNT, 2)
    with rig(budget, read=read) as r:
        client = r.tg.connection_engine._new_client()
        request = functions.channels.JoinChannelRequest(types.InputChannel(7,7))
        await client(functions.InvokeWithoutUpdatesRequest(request))
        client._no_updates = True
        await client(request)
        assert budget.status(f.ACCOUNT).used == 2 and read.status(f.ACCOUNT).used == 0
        before = len(client._sender.requests)
        await expect(UnsupportedJoinRequest, client([request, functions.updates.GetStateRequest()]))
        assert len(client._sender.requests) == before
        class Unknown(TLRequest):
            CONSTRUCTOR_ID = 123
            SUBCLASS_OF_ID = 456
            def __init__(self, query): self.query = query
        await expect(UnsupportedJoinRequest, client(Unknown(request)))
        class FutureJoin(TLRequest):
            CONSTRUCTOR_ID = 124
            SUBCLASS_OF_ID = types.messages.ChatInviteJoinResultOk.SUBCLASS_OF_ID
        await expect(UnsupportedJoinRequest, client(FutureJoin()))
        await client(f.history(1))
        assert read.status(f.ACCOUNT).used == 1 and budget.status(f.ACCOUNT).used == 2


async def test_health_recovery_and_identity():
    budget, _ = ledger()
    denial = Sender(); denial.script = [errors.ChannelPrivateError(None)]
    metadata, joining, reading = Sender(), Sender(), Sender()
    with rig(budget, senders=[denial, metadata, joining, reading], cached=999) as r:
        assert (await r.tg.check_group_access('synthetic_room')).status == 'denied'
        await r.tg.lookup_group('synthetic_room')
        await r.tg.join_group('synthetic_room')
        assert 'synthetic_room' in r.tg._health._no_access
        assert not [e for e in r.events if e['verdict'] == health.OK]
        await r.tg.check_group_access('synthetic_room')
        assert 'synthetic_room' not in r.tg._health._no_access
        assert all(e['account']['user_id'] == f.ACCOUNT for e in r.events)
        assert all(e['account']['session'] == 'synthetic_group_account' for e in r.events)
    sender = Sender(); sender.state_error = errors.AuthKeyUnregisteredError(None)
    with rig(senders=[sender]) as r:
        await expect(ce.AuthRequiredError, r.tg.lookup_group('synthetic_room'))
        assert r.events[0]['account']['user_id'] is None and r.clients[0].disconnects == 1


async def test_native_errors_inside_rpc_handler():
    with rig() as r:
        try: raise errors.ChannelPrivateError(None)
        except errors.ChannelPrivateError:
            error = await expect(GroupReferenceError, r.tg.lookup_group(55555))
            assert health.classify(error) is None
            error = await expect(GroupReferenceError, r.tg.lookup_group('https://[invalid/'))
            assert health.classify(error) is None
        assert not r.events
    sender = Sender(); sender.channels_reply = types.messages.Chats([])
    with rig(senders=[sender], seed=[room()]) as r:
        await expect(GroupReferenceError, r.tg.lookup_group(-1000000000007))
        assert not r.events
    sender = Sender(); transport = OSError('synthetic connection loss')
    sender.resolve_reply = transport
    with rig(senders=[sender]) as r:
        try: raise errors.ChannelPrivateError(None)
        except errors.ChannelPrivateError:
            assert await expect(OSError, r.tg.lookup_group('synthetic_room')) is transport
        assert not r.events and health.classify(transport) is None


async def test_ack_survives_real_cache_failure():
    budget, _ = ledger(); sender = Sender()
    with rig(budget, senders=[sender]) as r:
        folder = TMP / ('broken_session_{}'.format(next(SEQ))); folder.mkdir()
        session = SQLiteSession(str(folder / 'synthetic'))
        session.close(); (folder/'synthetic.session').unlink(); folder.rmdir()
        def switch_session(_):
            r.clients[0].session = session
        sender.on_join = switch_session
        output = io.StringIO(); handler = logging.StreamHandler(output)
        log = logging.getLogger('tgdata.group_operations'); log.addHandler(handler)
        try:
            result = await r.tg.join_group(LINK)
        finally:
            log.removeHandler(handler)
        assert result.status == 'joined' and result.group.id is None
        assert 'OperationalError' in output.getvalue() and TOKEN not in output.getvalue()
        assert budget.status(f.ACCOUNT).used == 1 and not r.events


async def test_ack_survives_warning_failure():
    class BrokenHandler(logging.Handler):
        def emit(self, record):
            raise RuntimeError('synthetic logging failure')
    budget, _ = ledger(); sender = Sender()
    with rig(budget, senders=[sender]) as r:
        def broken_cache(value):
            if isinstance(value, types.Updates):
                raise sqlite3.OperationalError('synthetic cache fault')
        def inject(_):
            r.clients[0].session.process_entities = broken_cache
        sender.on_join = inject
        handler = BrokenHandler(); logger = logging.getLogger('tgdata.group_operations')
        logger.addHandler(handler)
        try:
            assert (await r.tg.join_group(LINK)).status == 'joined'
        finally:
            logger.removeHandler(handler)
        assert budget.status(f.ACCOUNT).used == 1 and not r.events


async def test_concurrent_identity_and_callback_reentry():
    a, b = Sender(222), Sender(333)
    a.script = [errors.ChannelPrivateError(None)]; b.script = [errors.ChannelPrivateError(None)]
    with rig(senders=[a,b]) as r:
        values = await asyncio.gather(r.tg.check_group_access('synthetic_aaa'),
                                      r.tg.check_group_access('synthetic_bbb'))
        assert all(v.status == 'denied' for v in values)
        assert {(e['group'],e['account']['user_id']) for e in r.events} == {('synthetic_aaa',222),('synthetic_bbb',333)}
    delivered=[]
    async def callback(event):
        delivered.append(event)
        await r.tg.lookup_group(LINK)
    a=Sender(222); a.script=[errors.ChannelPrivateError(None)]
    with rig(senders=[a,Sender(333)],callback=callback) as r:
        await r.tg.check_group_access('synthetic_room')
        assert len(delivered)==1 and delivered[0]['account']['user_id']==222
        assert len(r.clients)==2 and all(c.disconnects==1 for c in r.clients)


async def test_private_diagnostics_and_stored_entities():
    budget, _ = ledger(); sender = Sender()
    sender.join_script = [errors.ChannelPrivateError(None)]
    output = io.StringIO(); handler = logging.StreamHandler(output)
    log = logging.getLogger('tgdata'); log.addHandler(handler)
    try:
        with rig(budget, senders=[sender]) as r:
            error = await expect(errors.ChannelPrivateError, r.tg.join_group(LINK))
            assert TOKEN not in str(error) + json.dumps(r.events) + output.getvalue()
            assert r.events[0]['group'].startswith('invite:')
    finally: log.removeHandler(handler)
    budget, _ = ledger(); sender = Sender()
    reply = joined(); reply.updates.users = [types.User(id=88, access_hash=88, first_name='Other')]
    sender.join_script=[reply]
    with rig(budget,senders=[sender]) as r:
        result=await r.tg.join_group(LINK)
        assert TOKEN not in repr(result)
        reject(ValueError,lambda:r.clients[0].session.get_input_entity(types.PeerUser(88)))
        assert r.clients[0].session.get_input_entity(types.PeerChannel(7)).channel_id==7


async def main():
    assert telethon.__version__ == '1.45.0'
    tests=[(name, fn) for name,fn in globals().items() if name.startswith('test_') and callable(fn)]
    passed=0
    print('Group Operation Tests — Telethon1.45.0; synthetic credentials; sockets forbidden', flush=True)
    for name,fn in tests:
        print('\n'+name, flush=True)
        try:
            await fn()
            passed+=1;print('PASS',flush=True)
        except Exception:
            traceback.print_exc()
    print('\nPassed: {}/{}'.format(passed,len(tests)),flush=True)
    if passed != len(tests): raise SystemExit(1)


if __name__=='__main__':
    with tempfile.TemporaryDirectory() as tmp, patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
        TMP=Path(tmp)
        f.TMP=TMP
        asyncio.run(main())
