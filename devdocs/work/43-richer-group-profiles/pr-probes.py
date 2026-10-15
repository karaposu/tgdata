"""Independent PR47 histories against the product-only checkout; no live source."""
import asyncio
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

ROOT = Path(sys.argv[1]).resolve()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import telethon
from telethon import errors
from telethon.tl import functions, types
import tgdata
from tgdata import GroupProfile, GroupResponseError, ReadBudgetError, ReadBudgetStorageError
from tgdata.smoke_tests import test_34_group_access as wire

fx, h = wire.fx, wire.h
DATE = datetime(2025, 6, 1, tzinfo=timezone.utc)
CASES = 0


def checked():
    global CASES
    CASES += 1


def metadata(entity=None, count=None, online=None):
    entity = wire.channel() if entity is None else entity
    if isinstance(entity, types.Chat):
        full = types.ChatFull(entity.id, 'profile evidence',
                             types.ChatParticipantsForbidden(entity.id),
                             types.PeerNotifySettings())
    else:
        full = types.ChannelFull(entity.id, 'profile evidence', 0, 0, 0,
            types.PhotoEmpty(0), types.PeerNotifySettings(), [], 0,
            participants_count=count, online_count=online)
    return types.messages.ChatFull(full, [entity], [])


def post(number=51, peer=None):
    return types.Message(number, peer or types.PeerChannel(7), date=DATE,
                         message='synthetic pin', pinned=True)


def collection(rows=(), count=None, inexact=None, channel=False):
    if count is None:
        return types.messages.Messages(list(rows), [], [], [])
    if channel:
        return types.messages.ChannelMessages(1, count, list(rows), [], [], [], inexact=inexact)
    return types.messages.MessagesSlice(count, list(rows), [], [], [], inexact=inexact)


def fixture(full=None, pins=None, **kwargs):
    responses = dict(ResolveUsernameRequest=wire.resolved(),
        GetFullChannelRequest=wire.Reply(metadata() if full is None else full),
        SearchRequest=wire.Reply(collection() if pins is None else pins))
    responses.update(kwargs.pop('responses', {}))
    return wire.setup(responses=responses, **kwargs)


async def read(tg, limit=2, account=222, heartbeat=None):
    return await tg.get_group_profile('synthetic_room', account_id=account,
                                     pinned_limit=limit, heartbeat=heartbeat)


async def probe_source_and_public_abi():
    assert Path(tgdata.__file__).resolve() == ROOT/'tgdata/__init__.py'
    assert telethon.__version__ == '1.45.0' and tgdata.__version__ == '0.1.1'
    prior = subprocess.check_output(['git', 'show', 'origin/dev:tgdata/tgdata.py'], cwd=ROOT, text=True)
    current = (ROOT/'tgdata/tgdata.py').read_text()
    def methods(source):
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name=='TgData')
        return {n.name: ast.dump(n) for n in cls.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    old, new = methods(prior), methods(current)
    assert all(new[name] == body for name, body in old.items())
    assert set(new)-set(old) == {'get_group_profile'}
    manifest = json.loads((HERE/'evidence/verified-result.json').read_text())
    for name, sha in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == sha, name
    checked()


async def probe_count_provenance_extremes():
    for count, online in ((None, None), (0, 0), (2**31-1, 0), (0, 2**31-1)):
        reply = metadata(wire.channel(participants_count=999), count, online)
        reply.chats.insert(0, wire.chat(7))
        reply.users = [fx.user(222), fx.user(333)]
        tg, f = fixture(full=reply)
        value = await read(tg, 0)
        assert value.group.participants_count == count and value.online_count == online
        assert value.group.peer_id == -1000000000007
        assert not wire.requests(f, functions.messages.SearchRequest)
        checked()


async def probe_native_count_precision_and_coverage_matrix():
    scenarios = [
        (collection(), 'complete', 0, True),
        (collection([post(51), post(50)]), 'complete', 2, True),
        (collection([post(51), post(50)], 2, channel=True), 'complete', 2, True),
        (collection([post(51), post(50)], 3), 'limited', 3, True),
        (collection([post(51)], 3, channel=True), 'incomplete', 3, True),
        (collection([], 3), 'incomplete', 3, True),
        (collection([], 0, True, True), 'incomplete', 0, False),
        (collection([post(51)], 0, True), 'incomplete', 0, False),
        (collection([post(51)], 2**31-1, True, True), 'incomplete', 2**31-1, False),
        (collection([types.MessageEmpty(51, None), post(50)], 2), 'incomplete', 2, True),
    ]
    for reply, status, total, exact in scenarios:
        tg, f = fixture(pins=reply, budget=True)
        result = await read(tg)
        assert (result.pins_status, result.pins_total, result.pins_total_exact) == (status,total,exact)
        assert len(wire.requests(f, functions.messages.SearchRequest)) == 1
        assert f.budget.status(222).used == len(reply.messages)
        assert result.pins_observed_at is not None and f.wire.closed
        checked()


async def probe_budget_precedes_domain_rejection():
    cases = [(collection([post(51), post(50), post(49)]), ReadBudgetError, 3, 0),
             (types.messages.MessagesNotModified(0), GroupResponseError, 0, 0),
             (types.User(51), ReadBudgetError, 2, 2)]
    for reply, error_type, charged, reserved in cases:
        tg, f = fixture(pins=reply, budget=True)
        error = await fx.expect(error_type, read(tg))
        assert error.partial_result.pins_status == 'failed'
        assert (f.budget.status(222).used, f.budget.status(222).reserved) == (charged,reserved)
        assert tg.get_account_health(222)['events'] == 0
        checked()


async def probe_native_sqlite_settlement_failure_after_reply():
    def break_settlement(sender, _):
        # Destroy only the probe's temporary metadata table after durable admission.
        with sqlite3.connect(sender.fixture.budget.path) as db:
            assert db.execute('SELECT amount,settled FROM tgdata_budget_charges').fetchall() == [(2,0)]
            db.execute('DROP TABLE tgdata_budget_meta')
        return wire.Reply(collection([post()]))
    tg, f = fixture(budget=True, responses={'SearchRequest': break_settlement})
    error = await fx.expect(ReadBudgetStorageError, read(tg))
    assert error.partial_result.about == 'profile evidence'
    assert error.partial_result.pins_status == 'failed'
    with sqlite3.connect(f.budget.path) as db:
        assert db.execute('SELECT amount,settled FROM tgdata_budget_charges').fetchall() == [(2,0)]
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0
    checked()


async def probe_wait_recovery_needs_valid_same_request():
    wait = h.RPCReply(420, 'FLOOD_WAIT_90')
    tg, f = fixture(responses={'SearchRequest': wait})
    await fx.expect(errors.FloodWaitError, read(tg))
    f.responses['SearchRequest'] = wire.Reply(collection([post()]))
    await read(tg, 0)
    assert 'messages.SearchRequest' in tg.get_account_health(222)['waiting']
    f.responses['SearchRequest'] = wire.Reply(collection([post(peer=types.PeerChannel(8))]))
    await fx.expect(GroupResponseError, read(tg))
    assert 'messages.SearchRequest' in tg.get_account_health(222)['waiting']
    f.responses['SearchRequest'] = wire.Reply(collection([post()]))
    await read(tg)
    assert not tg.get_account_health(222)['waiting']
    checked()


async def probe_older_reply_cannot_clear_newer_wait():
    entered, release = asyncio.Event(), asyncio.Event()
    tg, f = fixture(responses={'SearchRequest': wire.Reply(collection([post()]),
                                                         entered=entered, release=release)})
    task = asyncio.create_task(read(tg))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        f.responses['SearchRequest'] = h.RPCReply(420, 'FLOOD_WAIT_90')
        await fx.expect(errors.FloodWaitError, read(tg))
        release.set()
        assert (await task).pins_status == 'complete'
        assert tg.get_account_health(222)['waiting']['messages.SearchRequest']['seconds'] == 90
        checked()
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


async def probe_overlapping_accounts_keep_evidence_separate():
    entered, release = asyncio.Event(), asyncio.Event()
    events = []
    tg, f = fixture(accounts=[222,333], cached=111, budget=True, callback=events.append,
        responses={'SearchRequest': wire.Reply(collection([post()]), entered=entered, release=release)})
    first = asyncio.create_task(read(tg))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        denial = h.RPCReply(400, 'CHANNEL_PRIVATE')
        f.responses['SearchRequest'] = denial
        error = await fx.expect(errors.ChannelPrivateError, read(tg, account=333))
        assert error is denial.error and error.partial_result.account_id == 333
        release.set()
        assert (await first).account_id == 222
        assert not tg.get_account_health(222)['no_access']
        assert tg.get_account_health(333)['no_access']['synthetic_room']
        assert f.budget.status(222).used == 1 and f.budget.status(333).reserved == 2
        await h.deliveries(tg)
        assert len(events) == 1 and events[0]['account']['user_id'] == 333
        checked()
    finally:
        release.set()
        await asyncio.gather(first, return_exceptions=True)


async def probe_heartbeat_boundary_cancellation_preserves_priority():
    for phase in ('profile done','pins done'):
        tg, f = fixture(budget=True)
        seen = []
        def beat(value):
            seen.append(value)
            if value == phase:
                asyncio.current_task().cancel()
        async def work():
            return await read(tg, heartbeat=beat)
        task = asyncio.create_task(work())
        await fx.expect(asyncio.CancelledError, task)
        assert f.wire.closed and tg.get_account_health(222)['events'] == 0
        before = list(seen)
        await fx.turns(12)
        assert seen == before
        checked()


async def probe_repeated_cancel_during_failure_cleanup():
    entered, release, closing, close_release = [asyncio.Event() for _ in range(4)]
    def prepare(client):
        client._sender.close_entered = closing
        client._sender.close_release = close_release
    tg, f = fixture(budget=True, prepare=prepare, responses={
        'SearchRequest':wire.Reply(collection([post()]), entered=entered, release=release)})
    task = asyncio.create_task(read(tg))
    try:
        await asyncio.wait_for(entered.wait(),3)
        task.cancel()
        await asyncio.wait_for(closing.wait(),3)
        task.cancel()
        await fx.turns()
        assert not task.done() and f.budget.status(222).reserved == 2
        close_release.set()
        await fx.expect(asyncio.CancelledError,task)
        assert f.wire.closed and tg.get_account_health(222)['events'] == 0
        checked()
    finally:
        release.set()
        close_release.set()
        await asyncio.gather(task,return_exceptions=True)


async def probe_annotation_failure_does_not_replace_source():
    for failure in (asyncio.CancelledError, errors.ChannelPrivateError):
        class AnnotationRefusal(OSError):
            def __setattr__(self,name,value):
                if name=='partial_result':
                    raise failure('synthetic annotation')
                super().__setattr__(name,value)
        original = AnnotationRefusal('synthetic transport')
        tg,f = fixture(responses={'SearchRequest':original})
        assert await fx.expect(AnnotationRefusal,read(tg)) is original
        assert f.wire.closed and tg.get_account_health(222)['events'] == 0
        checked()


async def probe_source_failure_before_full_projection_keeps_original():
    original = sqlite3.OperationalError('synthetic cache failure')
    def prepare(client):
        process = client.session.process_entities
        def fail_only_full(reply):
            if isinstance(reply,types.messages.ChatFull):
                raise original
            return process(reply)
        client.session.process_entities = fail_only_full
    tg,f = fixture(prepare=prepare)
    assert await fx.expect(sqlite3.OperationalError,read(tg)) is original
    assert getattr(original,'partial_result',None) is None
    assert not wire.requests(f,functions.messages.SearchRequest)
    assert f.wire.closed and tg.get_account_health(222)['events'] == 0
    checked()


async def probe_pin_rejection_and_failed_cleanup_notify_after_close():
    closing, release, events = asyncio.Event(), asyncio.Event(), []
    def prepare(client):
        client._sender.close_entered = closing
        client._sender.close_release = release
        client._sender.close_error = OSError('synthetic cleanup')
    denial = h.RPCReply(400,'CHANNEL_PRIVATE')
    tg,f = fixture(prepare=prepare,callback=events.append,responses={'SearchRequest':denial})
    task = asyncio.create_task(read(tg))
    try:
        await asyncio.wait_for(closing.wait(),3)
        assert not events and not task.done()
        release.set()
        actual = await fx.expect(errors.ChannelPrivateError,task)
        assert actual is denial.error and actual.partial_result.about=='profile evidence'
        await h.deliveries(tg)
        assert len(events)==1 and events[0]['request']=='messages.SearchRequest'
        assert f.wire.close_calls==1
        checked()
    finally:
        release.set()
        await asyncio.gather(task,return_exceptions=True)


async def main():
    tests=sorted((name,value) for name,value in globals().items()
                 if name.startswith('probe_') and callable(value))
    results=[]
    with tempfile.TemporaryDirectory(prefix='tgdata47-fresh-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')), \
         patch.object(telethon.TelegramClient,'start',side_effect=AssertionError('login forbidden')), \
         patch.object(fx.Wire,'send',wire.send):
        fx.TMP=Path(tmp)
        for name,test in tests:
            before=CASES
            try:
                await asyncio.wait_for(test(),20)
                result=dict(name=name,passed=True,cases=CASES-before)
            except (Exception,asyncio.CancelledError) as error:
                traceback.print_exc()
                result=dict(name=name,passed=False,error=type(error).__name__,cases=CASES-before)
            finally:
                for client in fx.CLIENTS:
                    client._sender.close_error=None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
                for tg in h.FACADES:
                    await tg.close()
                await asyncio.gather(*h.RPC_TASKS,return_exceptions=True)
                fx.CLIENTS.clear();h.FACADES.clear();h.RPC_TASKS.clear();wire.TRACE.clear()
            results.append(result)
            print(json.dumps(result),flush=True)
    report=dict(result='PASS' if all(r['passed'] for r in results) else 'FAIL',
                groups=len(results),cases=CASES,root=str(ROOT),
                head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                results=results)
    (HERE/'pr-probe-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',report['result'],'groups',len(results),'cases',CASES,flush=True)
    return 0 if report['result']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
