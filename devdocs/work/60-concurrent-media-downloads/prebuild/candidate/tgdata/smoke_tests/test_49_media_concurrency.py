"""Opt-in media windows through real Telethon 1.45 and native files; no sockets."""
import asyncio
from datetime import timedelta
import hashlib
import inspect
import json
from pathlib import Path
import socket
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from telethon import errors, functions, types
from telethon.client.telegrambaseclient import _ExportState
from telethon.crypto import AuthKey
from telethon.network.mtprotosender import MTProtoSender
from tgdata import TgData, AccountPool, SQLiteSyncStore, BackfillPrepareContext, PoolReadCapture, health
from tgdata.sync_engine import SyncEngine
from tgdata.media_downloads import MediaRead, media_boundary, _Resources
import tgdata.media_downloads as media
import tgdata.batch_files as files
from tgdata.smoke_tests import test_19_message_batches as b
from tgdata.smoke_tests import test_25_backfill_delivery as d
from tgdata.smoke_tests import test_31_account_pool as p
from tgdata.smoke_tests import test_44_batch_heartbeat as hb
f = b.f
CHAT = d.CHAT


async def until(check):
    for _ in range(2000):
        if check():
            return
        await asyncio.sleep(.001)
    raise AssertionError('controlled condition did not occur')


class Transfer:
    """Transport-only timing: all iteration, download, publication and joins are real."""
    def __init__(self, sender, messages, *, manual=False, delays=None, failures=None):
        self.sender, self.manual = sender, manual
        self.messages = messages
        self.data = {m.document.id: bytes([m.id % 251]) * m.document.size for m in messages}
        self.delays, self.failures = delays or {}, failures or {}
        self.active, self.peak = 0, 0
        self.requests, self.finished, self.futures = [], [], []
        self.original = sender.send
        sender.send = self.send

    def send(self, request, ordered=False):
        raw = f.unwrap(request)
        if not isinstance(raw, functions.upload.GetFileRequest):
            return self.original(request, ordered=ordered)
        bytes(request)
        future = asyncio.get_running_loop().create_future()
        asset = getattr(raw.location, 'id', getattr(raw.location, 'photo_id', None))
        self.requests.append((asset, raw.offset, time.monotonic()))
        self.active += 1
        self.peak = max(self.peak, self.active)
        self.futures.append((raw, future))
        def done(value):
            self.active -= 1
            if not value.cancelled() and value.exception() is None:
                self.finished.append(asset)
        future.add_done_callback(done)
        if not self.manual:
            asyncio.get_running_loop().call_later(self.delays.get(asset, .01), self.complete, len(self.futures)-1)
        return future

    def complete(self, index, error=None):
        request, future = self.futures[index]
        if future.done():
            return
        asset = getattr(request.location, 'id', getattr(request.location, 'photo_id', None))
        pending = self.failures.get(asset, [])
        error = error or (pending.pop(0) if pending else None)
        if error is not None:
            future.set_exception(error)
        else:
            data = self.data[asset][request.offset:request.offset+request.limit]
            future.set_result(types.upload.File(types.storage.FileUnknown(), 0, data))


def messages(count=3, start=101, size=257):
    return [b.document(i, asset_id=b.ASSET_ID+i, data=b'x'*size) for i in range(start, start+count)]


class ConcurrentMediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='tgdata-media-concurrency-')
        self.root = Path(self.tmp.name)
        f.TMP = d.TMP = self.root
        f.CLIENTS.clear(); p.POOLS.clear()
        for name in ('connect', 'connect_ex'):
            guard = patch.object(socket.socket, name, side_effect=AssertionError('network forbidden'))
            guard.start(); self.addCleanup(guard.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_async(self, work):
        async def run():
            try:
                return await work()
            finally:
                for pool in p.POOLS:
                    await pool.close()
                for client in f.CLIENTS:
                    client.session.close()
        return asyncio.run(run())

    def setup_read(self, count=3, *, budget=None, events=None, **transport):
        tg, client, sender = b.instance(budget, events)
        rows = messages(count)
        b.script_messages(sender, rows)
        transfer = Transfer(sender, rows, **transport)
        return tg, client, sender, transfer, rows

    async def batch(self, tg, root='media', **kwargs):
        return await tg.get_message_batch(CHAT, after_id=100, limit=kwargs.pop('limit', 3),
            download_media_to=self.root/root, **kwargs)

    def test_public_defaults_and_invalid_values_before_io(self):
        async def run():
            for cls, names in ((TgData, ('get_messages', 'get_message_batch', 'sync_group', 'prepare_backfill')),
                               (AccountPool, ('read', 'get_message_batch', 'sync_group', 'prepare_backfill'))):
                for name in names:
                    self.assertEqual(inspect.signature(getattr(cls, name)).parameters['download_concurrency'].default, 1)
            tg, _, sender, _, _ = self.setup_read()
            for value in (False, True, 0, -1, 17, 2.0, '3', None):
                for call in (lambda: self.batch(tg, download_concurrency=value),
                             lambda: tg.get_messages(CHAT, limit=1, download_concurrency=value),
                             lambda: tg.sync_group(CHAT, download_concurrency=value),
                             lambda: tg.prepare_backfill(None, download_concurrency=value)):
                    with self.assertRaises(ValueError): await call()
            self.assertFalse(sender.calls)
            self.assertFalse((self.root/'media').exists())
        self.run_async(run)

    def test_batch_overlap_order_bytes_and_default_parity(self):
        async def run():
            outputs=[]
            for n in (1, 3):
                rows=messages(6)
                tg, _, sender=b.instance(); b.script_messages(sender,rows)
                transfer=Transfer(sender,rows,delays={rows[0].document.id:.04})
                value=await self.batch(tg,str(n),limit=6,download_concurrency=n)
                self.assertEqual([int(r['id']) for r in value.messages],list(range(101,107)))
                self.assertEqual(transfer.peak,n)
                self.assertEqual(transfer.active,0)
                for record in value.messages:
                    data=transfer.data[int(record['media']['id'])]
                    self.assertEqual((self.root/str(n)/record['media']['blob']['path']).read_bytes(),data)
                outputs.append(value.to_json())
                if n==3:self.assertNotEqual(transfer.finished[:3],[r.document.id for r in rows[:3]])
            self.assertEqual(*outputs)
        self.run_async(run)

    def test_legacy_overlap_disk_and_bytes(self):
        async def run():
            tg, _, _, transfer, rows=self.setup_read(6)
            frame=await tg.get_messages(CHAT,after_id=100,limit=6,download_media_to=self.root/'legacy',
                                        include_media=True,download_concurrency=3)
            self.assertEqual(frame.MessageId.tolist(),list(range(101,107)))
            self.assertEqual(transfer.peak,3)
            for row in frame.itertuples():
                expected=transfer.data[b.ASSET_ID+row.MessageId]
                self.assertEqual(Path(row.MediaPath).read_bytes(),expected)
                self.assertEqual(row.MediaData,expected)
            self.assertFalse(list((self.root/'legacy').glob('.tgdata-media-*')))
        self.run_async(run)

    def test_default_best_effort_and_opted_strict_error(self):
        async def run():
            for n in (1,3):
                error=ValueError('controlled source failure')
                tg,_,_,transfer,rows=self.setup_read(1,failures={b.ASSET_ID+101:[error]})
                if n==1:
                    frame=await tg.get_messages(CHAT,after_id=100,limit=1,include_media=True)
                    self.assertEqual(len(frame),1);self.assertIsNone(frame.MediaData.iloc[0])
                else:
                    with self.assertRaises(ValueError) as got:
                        await tg.get_messages(CHAT,after_id=100,limit=1,include_media=True,download_concurrency=n)
                    self.assertIs(got.exception,error);self.assertTrue(error.partial_result.empty)
        self.run_async(run)

    def test_failure_keeps_only_ordered_prefix_and_later_file(self):
        async def run():
            tg,_,_,transfer,rows=self.setup_read(manual=True)
            error=errors.ChannelPrivateError(request=None)
            task=asyncio.create_task(self.batch(tg,download_concurrency=3))
            await until(lambda:len(transfer.futures)==3)
            transfer.complete(0);transfer.complete(2)
            await until(lambda:len(list((self.root/'media').iterdir()))>=2 and transfer.active==1)
            transfer.complete(1,error)
            with self.assertRaises(errors.ChannelPrivateError) as got:await task
            self.assertIs(got.exception,error)
            self.assertEqual([x['id'] for x in error.partial_result.messages],['101'])
            self.assertEqual(error.partial_result.next_after_id,101)
            self.assertTrue((self.root/'media'/hashlib.sha256(transfer.data[rows[2].document.id]).hexdigest()).exists())
            self.assertFalse(list((self.root/'media').glob('.tgdata-media-*')))
        self.run_async(run)

    def test_legacy_failure_retains_prepared_prefix(self):
        async def run():
            tg,_,_,transfer,_=self.setup_read(manual=True)
            task=asyncio.create_task(tg.get_messages(CHAT,after_id=100,limit=3,include_media=True,download_concurrency=3))
            await until(lambda:len(transfer.futures)==3)
            transfer.complete(0);transfer.complete(2);await until(lambda:transfer.active==1)
            error=ValueError('source failed');transfer.complete(1,error)
            with self.assertRaises(ValueError) as got:await task
            self.assertIs(got.exception,error);self.assertEqual(error.partial_result.MessageId.tolist(),[101])
        self.run_async(run)

    def test_stalled_window_never_refills_from_long_history(self):
        async def run():
            tg,_,_,transfer,_=self.setup_read(200,manual=True)
            task=asyncio.create_task(self.batch(tg,limit=200,download_concurrency=3))
            await until(lambda:len(transfer.futures)==3)
            transfer.complete(1);transfer.complete(2);await asyncio.sleep(.03)
            self.assertEqual(len(transfer.futures),3)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(transfer.active,0)
            self.assertFalse(list((self.root/'media').glob('.tgdata-media-*')))
        self.run_async(run)

    def test_same_engine_opted_overlap_refuses_before_source(self):
        async def run():
            tg,_,sender,transfer,_=self.setup_read(manual=True)
            task=asyncio.create_task(self.batch(tg,download_concurrency=3))
            await until(lambda:len(transfer.futures)==3);calls=list(sender.calls)
            with self.assertRaises(RuntimeError):await self.batch(tg,'second',download_concurrency=2)
            self.assertEqual(sender.calls,calls);self.assertFalse((self.root/'second').exists())
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
        self.run_async(run)

    def test_callbacks_have_no_inflight_or_next_batch_downloads(self):
        async def run():
            tg,_,_,transfer,_=self.setup_read(8);seen=[]
            failure=RuntimeError('caller stopped')
            async def callback(frame,info):
                seen.append(frame.MessageId.tolist())
                self.assertEqual(transfer.active,0);self.assertEqual(len(transfer.requests),2)
                raise failure
            with self.assertRaises(RuntimeError) as got:
                await tg.get_messages(CHAT,after_id=100,limit=8,include_media=True,
                    download_concurrency=3,batch_size=2,batch_callback=callback)
            self.assertIs(got.exception,failure);self.assertEqual(seen,[[101,102]])
            self.assertEqual(got.exception.partial_result.MessageId.tolist(),[101,102])
        self.run_async(run)

    def test_nested_default_and_other_client_are_not_enrolled(self):
        async def run():
            tg,client,sender,transfer,_=self.setup_read(3);other,other_client,other_sender=b.instance();seen=[]
            original=other_sender.send
            def send(request,ordered=False):
                seen.append(media._current(other_client))
                return original(request,ordered=ordered)
            other_sender.send=send
            async def callback(frame,info):
                await other.get_message_batch(CHAT,after_id=100,limit=1)
                with self.assertRaises(RuntimeError):
                    await self.batch(tg,'nested',limit=1,download_concurrency=3)
                await tg.get_message_batch(CHAT,after_id=200,limit=1)
            result=await tg.get_messages(CHAT,after_id=100,limit=3,include_media=True,
                batch_size=3,batch_callback=callback,download_concurrency=3)
            self.assertEqual(len(result),3);self.assertTrue(seen);self.assertTrue(all(s is None for s in seen))
        self.run_async(run)

    def test_reference_only_option_has_no_owner(self):
        async def run():
            tg,_,sender=b.instance();seen=[];original=sender.send
            def send(request,ordered=False):
                seen.append(media._SCOPE.get());return original(request,ordered=ordered)
            sender.send=send
            await tg.get_message_batch(CHAT,after_id=100,limit=1,download_concurrency=3)
            self.assertTrue(seen);self.assertTrue(all(s is None for s in seen))
            self.assertFalse(hasattr(tg.connection_engine,'_tgdata_media_control'))
        self.run_async(run)

    def test_sdk_wait_pauses_sibling_admission_and_keeps_policy(self):
        async def run():
            events=[];tg,client,_,transfer,_=self.setup_read(events=events,
                failures={b.ASSET_ID+101:[errors.FloodWaitError(request=None,capture=1)]})
            started=time.monotonic();task=asyncio.create_task(self.batch(tg,download_concurrency=3))
            await until(lambda:bool(getattr(getattr(tg.connection_engine,'_tgdata_media_control',None),'error',None)))
            first=len(transfer.requests);await asyncio.sleep(.05)
            self.assertEqual(len(transfer.requests),first)
            result=await task
            self.assertGreaterEqual(time.monotonic()-started,.95)
            self.assertEqual(len(transfer.requests),4);self.assertEqual(client.flood_sleep_threshold,60)
            self.assertEqual(result.next_after_id,103)
            waits=[e for e in events if e['verdict']=='waiting']
            self.assertTrue(waits);self.assertTrue(all(e['call']=='get_message_batch' for e in waits))
        self.run_async(run)

    def test_cached_wait_happens_before_new_media_send(self):
        async def run():
            tg,client,_,transfer,_=self.setup_read(1)
            client._flood_waited_requests[functions.upload.GetFileRequest.CONSTRUCTOR_ID]=time.time()+4
            started=time.monotonic();task=asyncio.create_task(self.batch(tg,limit=1,download_concurrency=3))
            await asyncio.sleep(.03);self.assertFalse(transfer.requests)
            await task;self.assertGreaterEqual(transfer.requests[0][2]-started,3.8)
        self.run_async(run)

    def test_no_wait_policy_preserves_original_error(self):
        async def run():
            error=errors.FloodWaitError(request=None,capture=30)
            tg,client,_,transfer,_=self.setup_read(1,failures={b.ASSET_ID+101:[error]})
            client.flood_sleep_threshold=0;client._request_retries=0;client._raise_last_call_error=True
            started=time.monotonic()
            with self.assertRaises(errors.FloodWaitError) as got:
                await self.batch(tg,limit=1,download_concurrency=3)
            self.assertIs(got.exception,error);self.assertLess(time.monotonic()-started,.5)
            self.assertEqual(len(transfer.requests),1);self.assertEqual(client.flood_sleep_threshold,0)
        self.run_async(run)

    def test_actual_export_return_survives_repeated_cancellation(self):
        async def run():
            tg,client,_,transfer,rows=self.setup_read(1,
                failures={b.ASSET_ID+101:[errors.FileMigrateError(request=None,capture=2)]})
            exported=b.Sender();exported.dc_id=2;other=Transfer(exported,rows,manual=True)
            state=_ExportState();state.add_borrow();state.add_return()
            client._borrowed_senders[2]=(state,exported)
            entered=asyncio.Event();release=asyncio.Event();native=client._return_exported_sender
            async def delayed(sender):
                entered.set();await release.wait();await native(sender)
            with patch.object(client,'_return_exported_sender',delayed):
                task=asyncio.create_task(self.batch(tg,limit=1,download_concurrency=3))
                await until(lambda:bool(other.futures));self.assertEqual(state._n,1)
                task.cancel();await entered.wait();task.cancel();task.cancel();await asyncio.sleep(.02)
                self.assertFalse(task.done());self.assertEqual(state._n,1)
                release.set()
                with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(state._n,0);self.assertEqual(other.active,0)
            self.assertEqual(list((self.root/'media').iterdir()),[])
        self.run_async(run)

    def test_export_success_closes_native_iterator(self):
        async def run():
            tg,client,_,transfer,rows=self.setup_read(1,
                failures={b.ASSET_ID+101:[errors.FileMigrateError(request=None,capture=2)]})
            exported=b.Sender();exported.dc_id=2;other=Transfer(exported,rows)
            state=_ExportState();state.add_borrow();state.add_return();client._borrowed_senders[2]=(state,exported)
            result=await self.batch(tg,limit=1,download_concurrency=3)
            self.assertEqual(result.next_after_id,101);self.assertEqual(state._n,0)
        self.run_async(run)

    def test_cdn_factory_owns_connect_and_copies_request_policy(self):
        async def run():
            tg,client,_=b.instance();client._sender.auth_key=AuthKey(b'x'*256)
            client.flood_sleep_threshold=0;client._request_retries=0;client._raise_last_call_error=True
            children=[]
            async def connect(sender,connection):return True
            async def dc(*args,**kwargs):return SimpleNamespace(id=2,ip_address='127.0.0.1',port=443)
            with media_boundary(),MediaRead(tg.connection_engine,3) as owner,owner.bind(client):
                async def work(_):
                    scope=media._current(client)
                    async with _Resources(scope):
                        helper=await client._get_cdn_client(SimpleNamespace(dc_id=2));children.append(helper)
                        self.assertEqual(helper.flood_sleep_threshold,0);self.assertEqual(helper._request_retries,0)
                        self.assertIsNotNone(media._current(helper))
                        source=b.Sender();source.file_script=[errors.FloodWaitError(request=None,capture=10)]
                        error=await f.expect(errors.FloodWaitError,helper._call(source,
                            functions.upload.GetFileRequest(types.InputDocumentFileLocation(9,9,b'x',''),0,4096)))
                        self.assertEqual(error.seconds,10)
                    return True
                with patch.object(client,'_get_dc',dc),patch.object(MTProtoSender,'connect',connect):
                    accepted=[]
                    await owner.window([1],work,accepted.append)
                    self.assertEqual(accepted,[True])
            self.assertEqual(len(children),1);self.assertFalse(children[0].is_connected())
        self.run_async(run)

    def test_message_reference_refresh_is_budgeted(self):
        async def run():
            budget,_=f.ledger(10)
            error=errors.FileReferenceExpiredError(request=None)
            tg,client,sender,transfer,rows=self.setup_read(1,budget=budget,failures={b.ASSET_ID+101:[error]})
            sender.script.append(f.response(rows))
            result=await self.batch(tg,limit=1,download_concurrency=3)
            self.assertEqual(result.next_after_id,101)
            self.assertEqual(budget.status(111).used,2);self.assertEqual(len(sender.reads),2)
            self.assertEqual(len(transfer.requests),2)
        self.run_async(run)

    def test_local_failure_is_not_telegram_health(self):
        async def run():
            events=[];tg,_,_,_,_=self.setup_read(1,events=events)
            def fail(*args,**kwargs):
                try:raise errors.ChannelPrivateError(request=None)
                except errors.ChannelPrivateError:raise OSError('local filesystem private')
            with patch.object(files.os,'fsync',fail):
                with self.assertRaises(OSError) as got:await self.batch(tg,limit=1,download_concurrency=3)
            self.assertIsNone(health.classify(got.exception,include_reported=True))
            self.assertFalse([e for e in events if e['verdict']=='no_access'])
            self.assertEqual(list((self.root/'media').iterdir()),[])
        self.run_async(run)

    def test_identical_blob_publication_reuses_complete_file(self):
        async def run():
            tg,_,_,transfer,rows=self.setup_read()
            for row in rows:transfer.data[row.document.id]=b's'*row.document.size
            result=await self.batch(tg,download_concurrency=3)
            self.assertEqual(len(result.messages),3);self.assertEqual(len(list((self.root/'media').iterdir())),1)
        self.run_async(run)

    def test_slow_download_beats_and_stall_stays_cancellable(self):
        async def run():
            tg,_,sender=b.instance();rows=messages(3,size=256*1024);b.script_messages(sender,rows)
            transfer=Transfer(sender,rows,delays={r.document.id:.035 for r in rows})
            value,beats,elapsed=await hb.watched(lambda beat:self.batch(tg,download_concurrency=3,heartbeat=beat),stall=.08)
            self.assertGreaterEqual(transfer.peak,2);self.assertIn('media',beats);self.assertEqual(value.next_after_id,103)
            tg,_,_,held,_=self.setup_read(manual=True)
            with self.assertRaises(TimeoutError):
                await hb.watched(lambda beat:self.batch(tg,'stalled',download_concurrency=3,heartbeat=beat),stall=.05)
            self.assertEqual(held.active,0);self.assertFalse(list((self.root/'stalled').iterdir()))
        self.run_async(run)

    def test_daily_real_download_replay_and_ack(self):
        async def run():
            tg,_,sender,transfer,_=self.setup_read();store=SQLiteSyncStore(self.root/'daily')
            tg.sync_engine=SyncEngine(tg.get_message_batch,store)
            await tg.initialize_sync(CHAT,after_id=100,media_mode='download')
            first=await tg.sync_group(CHAT,limit=3,download_media_to=self.root/'media',download_concurrency=3)
            self.assertEqual(transfer.peak,3);count=len(sender.calls);files_count=len(transfer.requests)
            replay=await tg.sync_group(CHAT,limit=3,download_media_to=self.root/'media',download_concurrency=2)
            self.assertEqual(first.to_json(),replay.to_json());self.assertEqual(len(sender.calls),count)
            self.assertEqual(len(transfer.requests),files_count);self.assertEqual((await tg.get_sync_status(CHAT)).after_id,100)
            await tg.acknowledge_sync(CHAT,first.batch_id);self.assertEqual((await tg.get_sync_status(CHAT)).after_id,103)
        self.run_async(run)

    def test_backfill_real_download_and_replay(self):
        async def run():
            tg,_,sender,transfer,_=self.setup_read();tg._backfill_store=SQLiteSyncStore(self.root/'history')
            req=d.request(batch_size=3,media_mode='download')
            started=await tg.start_backfill(req,submission='new');context=BackfillPrepareContext.from_status(started.status)
            first=await tg.prepare_backfill(context,download_media_to=self.root/'media',download_concurrency=3)
            self.assertEqual(transfer.peak,3);count=len(transfer.requests)
            replay=await tg.prepare_backfill(context,download_media_to=self.root/'media',download_concurrency=1)
            self.assertEqual(replay.batch,first.batch);self.assertEqual(replay.delivery,first.delivery)
            self.assertEqual(len(transfer.requests),count)
        self.run_async(run)

    def test_pool_raw_batch_daily_backfill_propagate(self):
        async def run():
            for mode in ('raw','batch','daily','backfill'):
                e=await p.setup(daily=SQLiteSyncStore(self.root/('daily-'+mode)),history=SQLiteSyncStore(self.root/('history-'+mode)))
                for aid,client in e.clients.items():
                    sender=b.Sender();sender.account=aid;client._sender=sender;e.senders[aid]=sender
                rows=messages();sender=e.senders[111];b.script_messages(sender,rows);transfer=Transfer(sender,rows)
                cap=PoolReadCapture();opts=dict(download_concurrency=3,download_media_to=self.root/('pool-'+mode),capture=cap)
                if mode=='raw':result=(await e.pool.read(CHAT,after_id=100,limit=3,**opts)).batch
                elif mode=='batch':result=await e.pool.get_message_batch(CHAT,after_id=100,limit=3,**opts)
                elif mode=='daily':
                    await e.pool.initialize_sync(CHAT,after_id=100,media_mode='download')
                    result=await e.pool.sync_group(CHAT,limit=3,**opts)
                else:
                    started=await e.pool.start_backfill(d.request(batch_size=3,media_mode='download'),submission='new')
                    result=(await e.pool.prepare_backfill(BackfillPrepareContext.from_status(started.status),**opts)).batch
                self.assertEqual(result.next_after_id,103);self.assertEqual(transfer.peak,3)
                self.assertEqual(cap.snapshot().state,'succeeded');self.assertEqual(cap.snapshot().account_id,111)
        self.run_async(run)

    def test_default_omission_for_injected_reader(self):
        async def run():
            calls=[]
            async def reader(chat_id,*,after_id,limit,download_media_to):
                calls.append(1);return d.sample(after=after_id)
            engine=SyncEngine(reader,SQLiteSyncStore(self.root/'injected'))
            await engine.initialize(CHAT,after_id=100)
            self.assertIsNotNone(await engine.prepare(CHAT,download_concurrency=1))
            self.assertEqual(calls,[1])
        self.run_async(run)


    def test_zero_and_premium_wait_errors_keep_sdk_policy(self):
        async def run():
            for kind, seconds in ((errors.FloodWaitError,0),(errors.FloodPremiumWaitError,1)):
                error=kind(request=None,capture=seconds)
                tg,client,_,transfer,_=self.setup_read(1,failures={b.ASSET_ID+101:[error]})
                client.flood_sleep_threshold=0;client._request_retries=0;client._raise_last_call_error=True
                with self.assertRaises(kind) as got:await self.batch(tg,str(seconds),limit=1,download_concurrency=3)
                self.assertIs(got.exception,error);self.assertEqual(error.seconds,1)
                self.assertEqual(len(transfer.requests),1)
        self.run_async(run)

    def test_cleanup_failure_does_not_replace_source_error_or_allow_reuse(self):
        async def run():
            tg,client,sender,_,rows=self.setup_read(1,
                failures={b.ASSET_ID+101:[errors.FileMigrateError(request=None,capture=2)]})
            exported=b.Sender();exported.dc_id=2
            source_error=ValueError('source-primary')
            Transfer(exported,rows,failures={rows[0].document.id:[source_error]})
            state=_ExportState();state.add_borrow();state.add_return();client._borrowed_senders[2]=(state,exported)
            async def fail(sender):raise RuntimeError('PRIVATE cleanup')
            with patch.object(client,'_return_exported_sender',fail),self.assertLogs('tgdata.media_downloads',level='WARNING') as log:
                with self.assertRaises(ValueError) as got:await self.batch(tg,limit=1,download_concurrency=3)
            self.assertIs(got.exception,source_error);self.assertNotIn('PRIVATE',' '.join(log.output))
            calls=list(sender.calls)
            with self.assertRaises(RuntimeError):await self.batch(tg,'reuse',limit=1,download_concurrency=3)
            self.assertEqual(sender.calls,calls);self.assertFalse((self.root/'reuse').exists())
            self.assertEqual(list((self.root/'media').iterdir()),[])
        self.run_async(run)

    def test_cleanup_only_failure_is_local_not_success(self):
        async def run():
            events=[];tg,client,_,_,rows=self.setup_read(1,events=events,
                failures={b.ASSET_ID+101:[errors.FileMigrateError(request=None,capture=2)]})
            exported=b.Sender();exported.dc_id=2;Transfer(exported,rows)
            state=_ExportState();state.add_borrow();state.add_return();client._borrowed_senders[2]=(state,exported)
            async def fail(sender):raise errors.ChannelPrivateError(request=None)
            with patch.object(client,'_return_exported_sender',fail),self.assertLogs('tgdata.media_downloads',level='WARNING'):
                with self.assertRaises(RuntimeError) as got:await self.batch(tg,limit=1,download_concurrency=3)
            self.assertIsNone(health.classify(got.exception,include_reported=True))
            self.assertFalse([e for e in events if e['verdict']=='no_access'])
            self.assertEqual(list((self.root/'media').iterdir()),[])
        self.run_async(run)

    def test_cdn_connect_cancellation_retires_created_helper(self):
        async def run():
            tg,client,_=b.instance();client._sender.auth_key=AuthKey(b'x'*256)
            entered=asyncio.Event();helpers=[];disconnected=[]
            native_disconnect=client.__class__.disconnect
            async def connect(sender,connection):entered.set();await asyncio.Future()
            def disconnect(helper):
                if helper is not client:disconnected.append(helper)
                return native_disconnect(helper)
            async def dc(*args,**kwargs):return SimpleNamespace(id=2,ip_address='127.0.0.1',port=443)
            async def operation():
                with media_boundary(),MediaRead(tg.connection_engine,3) as owner,owner.bind(client):
                    async def work(_):
                        async with _Resources(media._current(client)) as held:
                            try:await client._get_cdn_client(SimpleNamespace(dc_id=2))
                            finally:helpers.extend(held.clients)
                    await owner.window([1],work,lambda x:None)
            with patch.object(client,'_get_dc',dc),patch.object(MTProtoSender,'connect',connect),patch.object(client.__class__,'disconnect',disconnect):
                task=asyncio.create_task(operation());await entered.wait();task.cancel()
                with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(len(helpers),1);self.assertEqual(disconnected,helpers)
            self.assertFalse(helpers[0].is_connected())
        self.run_async(run)

    def test_reference_refresh_refusal_preserves_budget(self):
        async def run():
            budget,_=f.ledger(1)
            tg,_,sender,transfer,rows=self.setup_read(1,budget=budget,
                failures={b.ASSET_ID+101:[errors.FileReferenceExpiredError(request=None)]})
            sender.script.append(f.response(rows))
            with self.assertRaises(f.ReadBudgetExceeded):await self.batch(tg,limit=1,download_concurrency=3)
            self.assertEqual(budget.status(111).used,1);self.assertEqual(len(sender.reads),1)
            self.assertEqual(len(transfer.requests),1)
        self.run_async(run)

    def test_profile_photos_remain_serial_before_attachment_window(self):
        async def run():
            tg,_,sender,transfer,rows=self.setup_read()
            sender.script[0].users[0].photo=types.UserProfilePhoto(photo_id=900,dc_id=0,has_video=False)
            transfer.data[900]=b'profile-photo'
            frame=await tg.get_messages(CHAT,after_id=100,limit=3,include_media=True,
                include_profile_photos=True,download_concurrency=3)
            self.assertEqual([x[0] for x in transfer.requests[:3]],[900,900,900])
            self.assertEqual(transfer.peak,3);self.assertEqual(frame.PhotoData.tolist(),[b'profile-photo']*3)
        self.run_async(run)

    def test_legacy_new_file_collision_never_overwrites(self):
        async def run():
            tg,_,_,_,_=self.setup_read(1);native=files._publish;winner=[]
            def collision(temp,destination,digest,size):
                destination.write_bytes(b'other-writer');winner.append(destination)
                return native(temp,destination,digest,size)
            with patch.object(files,'_publish',collision):
                with self.assertRaises(files.BatchStorageError):
                    await tg.get_messages(CHAT,after_id=100,limit=1,download_media_to=self.root/'legacy',download_concurrency=3)
            self.assertEqual(winner[0].read_bytes(),b'other-writer')
            self.assertFalse(list((self.root/'legacy').glob('.tgdata-media-*')))
        self.run_async(run)

    def test_legacy_reuse_and_date_exclusion(self):
        async def run():
            tg,_,sender,transfer,rows=self.setup_read(4)
            # The existing legacy cache only reuses media with a known extension.
            for row in rows:row.document.mime_type='image/jpeg'
            rows[0].date=b.NOW-timedelta(days=2);rows[-1].date=b.NOW+timedelta(days=2)
            b.script_messages(sender,rows)
            kwargs=dict(start_date=b.NOW-timedelta(days=1),end_date=b.NOW+timedelta(days=1),
                limit=4,download_media_to=self.root/'legacy',download_concurrency=3)
            first=await tg.get_messages(CHAT,**kwargs)
            self.assertEqual(first.MessageId.tolist(),[102,103]);self.assertEqual(len(transfer.requests),2)
            b.script_messages(sender,rows);second=await tg.get_messages(CHAT,**kwargs)
            self.assertEqual(second.MediaPath.tolist(),first.MediaPath.tolist());self.assertEqual(len(transfer.requests),2)
        self.run_async(run)

    def test_background_inheritance_never_receives_media_membership(self):
        async def run():
            tg,client,_,_,_=self.setup_read(1);observed=[]
            with media_boundary(),MediaRead(tg.connection_engine,3) as owner,owner.bind(client):
                async def work(_):
                    self.assertIsNotNone(media._current(client))
                    async def background():
                        observed.append(media._current(client))
                        await client(functions.updates.GetStateRequest())
                    await asyncio.create_task(background())
                    return True
                await owner.window([1],work,lambda x:None)
            self.assertEqual(observed,[None])
        self.run_async(run)

    def test_pool_wait_keeps_fast_failover_and_no_worker_retry(self):
        async def run():
            e=await p.setup();transfers={}
            for aid,client in e.clients.items():
                sender=b.Sender();sender.account=aid;client._sender=sender;e.senders[aid]=sender
                rows=messages();b.script_messages(sender,rows)
                transfers[aid]=Transfer(sender,rows,failures=({rows[0].document.id:[errors.FloodWaitError(request=None,capture=60)]} if aid==111 else None))
            cap=PoolReadCapture();started=time.monotonic()
            result=await e.pool.read(CHAT,capture=cap,after_id=100,limit=3,
                download_media_to=self.root/'pool',download_concurrency=3)
            self.assertEqual(result.account_id,222);self.assertLess(time.monotonic()-started,1)
            self.assertEqual(len(transfers[111].requests),3)
            self.assertEqual(transfers[222].peak,3);self.assertEqual(cap.snapshot().account_id,222)
        self.run_async(run)


    def test_queued_heartbeat_stop_precedes_next_page_admission(self):
        async def run():
            tg,_,sender,transfer,_=self.setup_read(100)
            sender.script.append(f.PENDING)
            accepted=[0]
            def beat(phase):
                if phase=='messages':
                    accepted[0]+=1
                    if accepted[0]==99:asyncio.current_task().cancel()
            task=asyncio.create_task(self.batch(tg,limit=103,download_concurrency=3,heartbeat=beat))
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(len(sender.reads),1)
            self.assertEqual(len(transfer.requests),99)
            self.assertEqual(transfer.active,0)
        self.run_async(run)


    def test_daily_failure_publishes_only_prepared_prefix(self):
        async def run():
            tg,_,_,transfer,_=self.setup_read(manual=True)
            store=SQLiteSyncStore(self.root/'daily-failure');tg.sync_engine=SyncEngine(tg.get_message_batch,store)
            await tg.initialize_sync(CHAT,after_id=100,media_mode='download')
            task=asyncio.create_task(tg.sync_group(CHAT,limit=3,download_media_to=self.root/'media',download_concurrency=3))
            await until(lambda:len(transfer.futures)==3)
            transfer.complete(0);transfer.complete(2);await until(lambda:transfer.active==1)
            error=ValueError('download failed');transfer.complete(1,error)
            with self.assertRaises(ValueError) as got:await task
            self.assertIs(got.exception,error)
            replay=await tg.sync_group(CHAT,limit=3,download_media_to=self.root/'media',download_concurrency=2)
            self.assertEqual([x['id'] for x in replay.messages],['101'])
            self.assertEqual((await tg.get_sync_status(CHAT)).after_id,100)
            await tg.acknowledge_sync(CHAT,replay.batch_id)
            self.assertEqual((await tg.get_sync_status(CHAT)).after_id,101)
        self.run_async(run)

    def test_pool_cancel_retains_prefix_after_media_quiesces(self):
        async def run():
            e=await p.setup();sender=b.Sender();sender.account=111;e.clients[111]._sender=sender
            rows=messages(6);b.script_messages(sender,rows);transfer=Transfer(sender,rows,manual=True)
            cap=PoolReadCapture();beats=[]
            task=asyncio.create_task(e.pool.read(CHAT,capture=cap,after_id=100,limit=6,
                download_media_to=self.root/'pool-cancel',download_concurrency=3,heartbeat=beats.append))
            await until(lambda:len(transfer.futures)==3)
            for i in range(3):transfer.complete(i)
            await until(lambda:len(transfer.futures)==6)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            snapshot=cap.snapshot();self.assertEqual(snapshot.state,'cancelled')
            self.assertEqual(snapshot.batch.next_after_id,103);self.assertEqual(transfer.active,0)
            count=len(beats);await asyncio.sleep(.02);self.assertEqual(len(beats),count)
            self.assertFalse(list((self.root/'pool-cancel').glob('.tgdata-media-*')))
        self.run_async(run)


if __name__=='__main__':
    unittest.main()
