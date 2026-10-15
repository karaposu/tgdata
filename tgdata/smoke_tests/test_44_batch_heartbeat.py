"""Batch heartbeat: actual Telethon 1.45 request/download loops, no sockets."""
import asyncio
from datetime import timedelta
import gc
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

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from telethon import errors, functions, types
from telethon.client import users as sdk_users
from tgdata import BatchFormatError, SQLiteSyncStore, PoolReadCapture, BackfillPrepareContext, health
from tgdata.sync_engine import SyncEngine
from tgdata.backfill_engine import BackfillEngine
from tgdata.batch_heartbeat import heartbeat_scope, heartbeat_sleep
import tgdata.batch_heartbeat as hb
from tgdata.smoke_tests import test_19_message_batches as b
from tgdata.smoke_tests import test_25_backfill_delivery as d
from tgdata.smoke_tests import test_31_account_pool as p
from tgdata.smoke_tests import pool_storage_cases as ps

f=b.f
CHAT=d.CHAT

async def watched(factory, stall=.15):
    last=[time.monotonic()];beats=[]
    def beat(phase):last[0]=time.monotonic();beats.append(phase)
    started=time.monotonic();task=asyncio.create_task(factory(beat))
    try:
        while not task.done():
            await asyncio.sleep(.01)
            if time.monotonic()-last[0]>stall:
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
                raise TimeoutError('source remained silent')
        return await task,beats,time.monotonic()-started
    finally:
        if not task.done():task.cancel()
        await asyncio.gather(task,return_exceptions=True)


def delayed_media(sender,delay=.035):
    original=sender.send
    def send(request,ordered=False):
        value=original(request,ordered=ordered)
        if not isinstance(f.unwrap(request),functions.upload.GetFileRequest):return value
        pending=asyncio.get_running_loop().create_future()
        def finish():
            if pending.done():return
            if value.exception():pending.set_exception(value.exception())
            else:pending.set_result(value.result())
        asyncio.get_running_loop().call_later(delay,finish)
        return pending
    sender.send=send


class HeartbeatTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='tgdata_heartbeat_')
        self.root=Path(self.tmp.name);f.TMP=d.TMP=self.root
        f.CLIENTS.clear();p.POOLS.clear()
        for name in ('connect','connect_ex'):
            guard=patch.object(socket.socket,name,side_effect=AssertionError('network forbidden'))
            guard.start();self.addCleanup(guard.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_async(self,work):
        async def run():
            try:return await work()
            finally:
                for pool in p.POOLS:await pool.close()
                for client in f.CLIENTS:
                    for pending in getattr(client._sender,'pending',[]):
                        if not pending.done():pending.cancel()
                    client.session.close()
        return asyncio.run(run())

    def test_slow_real_sdk_download_outlasts_watchdog(self):
        async def run():
            tg,client,sender=b.instance();data=b'x'*(1024*1024)
            b.script_messages(sender,[b.document(data=data)])
            sender.files[b.ASSET_ID]=data;delayed_media(sender)
            batch,beats,elapsed=await watched(lambda beat:tg.get_message_batch(CHAT,after_id=100,limit=1,
                                            download_media_to=self.root/'media',heartbeat=beat))
            self.assertGreater(elapsed,.15);self.assertGreaterEqual(beats.count('media'),4)
            self.assertEqual(batch.next_after_id,101)
            self.assertEqual((self.root/'media'/hashlib.sha256(data).hexdigest()).read_bytes(),data)
        self.run_async(run)

    def test_stalled_chunk_still_cancels_and_cleans(self):
        async def run():
            tg,_,sender=b.instance();b.script_messages(sender,[b.document()]);sender.file_script=[f.PENDING]
            root=self.root/'media'
            with self.assertRaises(TimeoutError):
                await watched(lambda beat:tg.get_message_batch(CHAT,after_id=100,limit=1,download_media_to=root,heartbeat=beat),stall=.05)
            self.assertEqual(list(root.iterdir()),[])
            self.assertTrue(sender.pending[0].cancelled())
        self.run_async(run)

    def test_phases_and_bytes_unchanged(self):
        async def run():
            tg,_,sender=b.instance();beats=[]
            first=await tg.get_message_batch(CHAT,after_id=100,limit=2)
            second=await tg.get_message_batch(CHAT,after_id=100,limit=2,heartbeat=beats.append)
            self.assertEqual(first.to_json(),second.to_json())
            self.assertEqual(beats.count('messages'),2)
            self.assertTrue({'connect','connected','resolve','resolved','request','message scanned'}<=set(beats))
            count=len(beats);await asyncio.sleep(0);self.assertEqual(len(beats),count)
        self.run_async(run)

    def test_excluded_window_messages_signal_scanning(self):
        async def run():
            tg,_,sender=b.instance();beats=[]
            sender.script=[f.response([f.message(102),f.message(101)]),d.finite_response([])]
            value=await tg.get_message_batch(CHAT,after_id=100,limit=2,start_date=b.NOW+timedelta(seconds=1),
                                            end_date=b.NOW+timedelta(seconds=2),heartbeat=beats.append)
            # An explicit short terminal response stops the lower-bound scan.
            self.assertFalse(value.messages);self.assertGreaterEqual(beats.count('message scanned'),2)
            self.assertNotIn('messages',beats)
        self.run_async(run)

    def test_dialog_sync_fallback_phases(self):
        async def run():
            tg,client,sender=b.instance();beats=[];calls=[0];real=client.get_entity
            async def entity(group):
                calls[0]+=1
                if calls[0]==1:raise ValueError('unknown entity')
                return await real(group)
            async def dialogs():return []
            with patch.object(client,'get_entity',side_effect=entity),patch.object(client,'get_dialogs',side_effect=dialogs):
                await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=beats.append)
            self.assertIn('dialog-sync',beats);self.assertIn('dialog-sync done',beats)
        self.run_async(run)

    def test_callback_errors_are_local_and_content_free(self):
        async def run():
            for error in (ValueError('PRIVATE'),errors.ChannelPrivateError(request=None),asyncio.CancelledError('PRIVATE')):
                events=[];tg,_,sender=b.instance(events=events)
                def bad(phase):raise error
                with self.assertLogs('tgdata.batch_heartbeat',level='WARNING') as log:
                    value=await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=bad)
                self.assertEqual(value.next_after_id,101)
                self.assertNotIn('PRIVATE','\n'.join(log.output))
                self.assertTrue(all(e.get('verdict') not in ('no_access','banned','logged_out') for e in events))
        self.run_async(run)

    def test_logging_failure_does_not_replace_result(self):
        async def run():
            tg,_,_=b.instance()
            def bad(phase):raise ValueError('private')
            with patch.object(hb.logger,'warning',side_effect=OSError('log unavailable')):
                value=await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=bad)
            self.assertEqual(value.next_after_id,101)
        self.run_async(run)

    def test_invalid_callbacks_refuse_before_io(self):
        async def run():
            tg,_,sender=b.instance()
            async def bad(phase):pass
            class AsyncObject:
                async def __call__(self,phase):pass
            for callback in (False,42,{},bad,AsyncObject()):
                with self.assertRaises(BatchFormatError):
                    await tg.get_message_batch(CHAT,heartbeat=callback,download_media_to=self.root/'never')
                with self.assertRaises(BatchFormatError):await tg.sync_group(CHAT,heartbeat=callback)
            self.assertFalse(sender.calls);self.assertFalse((self.root/'never').exists())
        self.run_async(run)

    def test_returned_coroutine_is_closed_not_awaited(self):
        async def run():
            tg,_,_=b.instance();returned=[];executed=[]
            async def work():executed.append(True)
            def callback(phase):
                value=work();returned.append(value);return value
            with self.assertLogs('tgdata.batch_heartbeat',level='WARNING'):
                await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=callback)
            self.assertTrue(returned);self.assertFalse(executed)
            self.assertTrue(all(inspect.getcoroutinestate(c)=='CORO_CLOSED' for c in returned))
        self.run_async(run)

    def test_real_task_cancellation_is_preserved(self):
        async def run():
            tg,_,sender=b.instance();sender.script=[f.PENDING];beats=[]
            task=asyncio.create_task(tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=beats.append))
            await d.until(lambda:bool(sender.pending));before=len(beats);task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            await asyncio.sleep(0);self.assertEqual(len(beats),before)
            self.assertTrue(sender.pending[0].cancelled())
        self.run_async(run)

    def test_callback_requested_task_cancellation_survives(self):
        async def run():
            tg,_,sender=b.instance();sender.script=[f.PENDING]
            def callback(phase):
                if phase=='resolved':asyncio.current_task().cancel()
            task=asyncio.create_task(tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=callback))
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertTrue(task.cancelled())
        self.run_async(run)

    def test_concurrent_same_client_callbacks_are_separate(self):
        async def run():
            tg,_,sender=b.instance();sender.script=[f.PENDING,f.PENDING];a=[];z=[]
            ta=asyncio.create_task(tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=a.append))
            tz=asyncio.create_task(tg.get_message_batch(CHAT,after_id=200,limit=1,heartbeat=z.append))
            await d.until(lambda:len(sender.pending)==2)
            na,nz=len(a),len(z)
            sender.pending[0].set_result(f.response([f.message(101)]));await ta
            self.assertGreater(len(a),na);self.assertEqual(len(z),nz)
            sender.pending[1].set_result(f.response([f.message(201)]));await tz
            self.assertEqual(a.count('messages'),1);self.assertEqual(z.count('messages'),1)
        self.run_async(run)

    def test_inherited_background_request_does_not_beat(self):
        async def run():
            _,client,_=b.instance();beats=[]
            with heartbeat_scope(beats.append):
                await asyncio.create_task(client(functions.updates.GetStateRequest()))
                await asyncio.sleep(0)
                self.assertEqual(beats,[])
                await client(functions.updates.GetStateRequest());await asyncio.sleep(0)
                self.assertIn('request',beats)
            count=len(beats);await client(functions.updates.GetStateRequest());await asyncio.sleep(0)
            self.assertEqual(len(beats),count)
        self.run_async(run)

    def test_none_nested_scope_masks_outer(self):
        async def run():
            tg,_,_=b.instance();beats=[]
            with heartbeat_scope(beats.append):
                await tg.get_message_batch(CHAT,after_id=100,limit=1)
                await asyncio.sleep(0)
            self.assertEqual(beats,[])
        self.run_async(run)

    def test_future_lists_and_direct_exported_sender_call(self):
        async def run():
            _,client,sender=b.instance();beats=[]
            with heartbeat_scope(beats.append):
                values=await client([functions.updates.GetStateRequest(),functions.updates.GetStateRequest()])
                await asyncio.sleep(0)
                self.assertEqual(len(values),2);self.assertEqual(beats.count('request done'),2)
                await client._call(sender,functions.updates.GetStateRequest());await asyncio.sleep(0)
                self.assertEqual(beats.count('request done'),3)
        self.run_async(run)

    def test_repeated_sdk_waits_keep_counts_and_notify_between(self):
        async def run():
            tg,client,sender=b.instance();waits=[];beats=[]
            sender.script=[errors.FloodWaitError(request=None,capture=60),errors.FloodWaitError(request=None,capture=60),f.response([f.message(101)])]
            async def sleep(seconds):
                await asyncio.sleep(0);waits.append((seconds,beats.count('flood-wait')))
            with patch.object(sdk_users,'asyncio',SimpleNamespace(sleep=sleep)):
                value=await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=beats.append)
            self.assertEqual(value.next_after_id,101);self.assertEqual(waits,[(60,1),(60,2)])
            self.assertEqual(len(sender.reads),3);self.assertEqual(client.flood_sleep_threshold,60)
        self.run_async(run)

    def test_cached_sdk_wait_keeps_policy_and_emits_request_start(self):
        async def run():
            tg,client,sender=b.instance();beats=[];waits=[]
            client._flood_waited_requests[functions.messages.GetHistoryRequest.CONSTRUCTOR_ID]=time.time()+30
            async def sleep(seconds):waits.append((seconds,beats[-1]));await asyncio.sleep(0)
            with patch.object(sdk_users,'asyncio',SimpleNamespace(sleep=sleep)):
                await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=beats.append)
            self.assertEqual(len(waits),1);self.assertEqual(waits[0][0],30)
            self.assertIn(waits[0][1],('request','request done'));self.assertEqual(len(sender.reads),1)
        self.run_async(run)

    def test_budget_charging_identical_with_callback(self):
        async def run():
            results=[]
            for callback in (None,lambda phase:None):
                budget,_=f.ledger(10);tg,client,sender=b.instance(budget)
                sender.script=[errors.FloodWaitError(request=None,capture=1),f.response([f.message(101)])]
                async def sleep(seconds):await asyncio.sleep(0)
                with patch.object(sdk_users,'asyncio',SimpleNamespace(sleep=sleep)):
                    value=await tg.get_message_batch(CHAT,after_id=100,limit=1,heartbeat=callback)
                status=budget.status(111)
                results.append((value.to_json(),status.used,status.reserved,len(sender.reads)))
            self.assertEqual(results[0],results[1]);self.assertEqual(results[0][-1],2)
        self.run_async(run)

    def test_owned_sleep_ticks_only_while_waiting(self):
        async def run():
            beats=[];started=time.monotonic()
            with patch.object(hb,'_WAIT_SLICE',.01),heartbeat_scope(beats.append):
                await heartbeat_sleep(.035)
            self.assertGreaterEqual(time.monotonic()-started,.035)
            self.assertGreaterEqual(beats.count('flood-wait'),3)
            count=len(beats);await asyncio.sleep(.02);self.assertEqual(len(beats),count)
            sleeps=[]
            async def sleep(seconds):sleeps.append(seconds)
            with patch.object(hb,'_sleep',side_effect=sleep):await heartbeat_sleep(37)
            self.assertEqual(sleeps,[37])
        self.run_async(run)

    def test_owned_sleep_cancellation_stops_notifications(self):
        async def run():
            beats=[]
            async def work():
                with heartbeat_scope(beats.append):await heartbeat_sleep(30)
            task=asyncio.create_task(work());await asyncio.sleep(0);task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(beats,['flood-wait'])
        self.run_async(run)

    def test_daily_actual_download_then_local_replay(self):
        async def run():
            tg,client,sender=b.instance();data=b'hello';b.script_messages(sender,[b.document(data=data)])
            sender.files[b.ASSET_ID]=data;store=SQLiteSyncStore(self.root/'daily');tg.sync_engine=SyncEngine(tg.get_message_batch,store)
            await tg.initialize_sync(CHAT,after_id=100,media_mode='download');beats=[]
            first=await tg.sync_group(CHAT,limit=1,download_media_to=self.root/'media',heartbeat=beats.append)
            self.assertIn('media',beats);calls=list(sender.calls);beats.clear()
            with patch.object(tg.connection_engine,'session',side_effect=AssertionError('replay opened client')):
                replay=await tg.sync_group(CHAT,limit=1,download_media_to=self.root/'media',heartbeat=beats.append)
            self.assertEqual(replay.to_json(),first.to_json());self.assertEqual(beats,[]);self.assertEqual(sender.calls,calls)
            self.assertEqual((await tg.get_sync_status(CHAT)).after_id,100)
            await tg.acknowledge_sync(CHAT,first.batch_id)
            self.assertEqual((await tg.get_sync_status(CHAT)).after_id,101)
        self.run_async(run)

    def test_daily_callback_failure_preserves_pending(self):
        async def run():
            tg,_,_=b.instance();store=SQLiteSyncStore(self.root/'daily');tg.sync_engine=SyncEngine(tg.get_message_batch,store)
            await tg.initialize_sync(CHAT,after_id=100)
            def bad(phase):raise errors.ChannelPrivateError(request=None)
            with self.assertLogs('tgdata.batch_heartbeat',level='WARNING'):
                first=await tg.sync_group(CHAT,limit=1,heartbeat=bad)
            saved=await store.load(CHAT);replay=await tg.sync_group(CHAT,limit=1,heartbeat=bad)
            self.assertEqual(first.to_json(),replay.to_json());self.assertEqual(await store.load(CHAT),saved)
        self.run_async(run)

    def test_read_error_prefix_keeps_original_error_and_pending(self):
        async def run():
            tg,_,sender=b.instance();store=SQLiteSyncStore(self.root/'daily');tg.sync_engine=SyncEngine(tg.get_message_batch,store)
            await tg.initialize_sync(CHAT,after_id=100)
            error=errors.ChannelPrivateError(request=None)
            sender.script=[f.response([f.message(n) for n in reversed(range(101,201))]),error]
            def bad(phase):raise ValueError('PRIVATE')
            with self.assertLogs('tgdata.batch_heartbeat',level='WARNING'):
                with self.assertRaises(errors.ChannelPrivateError) as got:await tg.sync_group(CHAT,limit=200,heartbeat=bad)
            self.assertIs(got.exception,error);self.assertEqual(len(error.partial_result.messages),100)
            replay=await tg.sync_group(CHAT,limit=200)
            self.assertEqual(replay.to_json(),error.partial_result.to_json())
        self.run_async(run)

    def test_public_backfill_forwarding_and_replay(self):
        async def run():
            tg,_,sender=b.instance();tg._backfill_store=SQLiteSyncStore(self.root/'backfill');beats=[]
            req=d.request(batch_size=1);status=(await tg.start_backfill(req,submission='new')).status
            context=BackfillPrepareContext.from_status(status)
            first=await tg.prepare_backfill(context,heartbeat=beats.append)
            self.assertIn('messages',beats);calls=list(sender.calls);beats.clear()
            replay=await tg.prepare_backfill(context,heartbeat=beats.append)
            self.assertEqual(replay.delivery,first.delivery);self.assertEqual(replay.batch,first.batch)
            self.assertEqual(beats,[]);self.assertEqual(sender.calls,calls)
        self.run_async(run)

    def test_legacy_injected_readers_receive_no_none_keyword(self):
        async def run():
            calls=[]
            async def read(chat_id,*,after_id,limit,download_media_to):
                calls.append(1);return d.sample(after=after_id)
            engine=SyncEngine(read,SQLiteSyncStore(self.root/'daily'));await engine.initialize(CHAT,after_id=100)
            self.assertIsNotNone(await engine.prepare(CHAT,heartbeat=None))
            async def history(chat_id,*,after_id,limit,download_media_to,start_date,end_date):
                calls.append(1);return d.sample(after=after_id)
            source=d.engine(SQLiteSyncStore(self.root/'history'),history)
            ctx=BackfillPrepareContext.from_status((await source.start(d.request(),submission='new')).status)
            self.assertIsNotNone((await source.prepare(ctx,heartbeat=None)).batch);self.assertEqual(calls,[1,1])
        self.run_async(run)

    def test_all_pool_apis_forward_to_owned_source(self):
        async def run():
            for mode in ('raw','batch','daily','backfill'):
                e,state,provider,context=await ps.setup('raw' if mode=='batch' else mode)
                ps.source(e,False);beats=[];cap=PoolReadCapture()
                if mode=='raw':result=await e.pool.read(CHAT,capture=cap,after_id=100,limit=1,heartbeat=beats.append)
                elif mode=='batch':result=await e.pool.get_message_batch(CHAT,capture=cap,after_id=100,limit=1,heartbeat=beats.append)
                elif mode=='daily':result=await e.pool.sync_group(CHAT,capture=cap,limit=1,heartbeat=beats.append)
                else:result=await e.pool.prepare_backfill(context,capture=cap,heartbeat=beats.append)
                self.assertIn('messages',beats);self.assertEqual(cap.snapshot().state,'succeeded')
                self.assertEqual(cap.snapshot().account_id,111)
                if mode in ('daily','backfill'):
                    beats.clear();calls=sum(len(s.calls) for s in e.senders.values());cap=PoolReadCapture()
                    if mode=='daily':await e.pool.sync_group(CHAT,capture=cap,limit=1,heartbeat=beats.append)
                    else:await e.pool.prepare_backfill(context,capture=cap,heartbeat=beats.append)
                    self.assertEqual(beats,[]);self.assertEqual(sum(len(s.calls) for s in e.senders.values()),calls)
        self.run_async(run)

    def test_pool_flood_response_does_not_enable_sleep(self):
        async def run():
            e=await p.setup();beats=[];e.senders[111].script=[errors.FloodWaitError(request=None,capture=60)]
            async def no_sleep(seconds):raise AssertionError('pool enabled SDK wait')
            with patch.object(sdk_users,'asyncio',SimpleNamespace(sleep=no_sleep)):
                result=await e.pool.read(CHAT,capture=PoolReadCapture(),after_id=100,limit=1,heartbeat=beats.append)
            self.assertEqual(result.account_id,222);self.assertIn('flood-wait',beats)
            self.assertEqual(e.budget.status(111).reserved,1)
        self.run_async(run)

    def test_pool_cancel_keeps_capture_and_no_late_callback(self):
        async def run():
            e=await p.setup();e.senders[111].script=[f.response([f.message(n) for n in reversed(range(101,201))]),f.PENDING]
            beats=[];cap=PoolReadCapture()
            task=asyncio.create_task(e.pool.read(CHAT,capture=cap,after_id=100,limit=200,heartbeat=beats.append))
            await d.until(lambda:bool(e.senders[111].pending));task.cancel()
            with self.assertRaises(asyncio.CancelledError):await task
            self.assertEqual(len(cap.snapshot().batch.messages),100);self.assertEqual(cap.snapshot().state,'cancelled')
            count=len(beats);await asyncio.sleep(0);self.assertEqual(len(beats),count)
        self.run_async(run)

    def test_async_generator_callback_refuses_before_read(self):
        async def run():
            tg,_,sender=b.instance()
            async def callback(phase):yield phase
            with self.assertRaises(BatchFormatError):
                await tg.get_message_batch(CHAT,heartbeat=callback)
            self.assertEqual(sender.calls,[])
        self.run_async(run)

    def test_zero_owned_wait_preserves_cancellation_checkpoint(self):
        async def run():
            async def work():
                with heartbeat_scope(lambda phase:None):
                    asyncio.current_task().cancel()
                    await heartbeat_sleep(0)
                    raise AssertionError('zero sleep lost cancellation checkpoint')
            with self.assertRaises(asyncio.CancelledError):await asyncio.create_task(work())
        self.run_async(run)

    def test_no_callback_keeps_download_keyword_compatibility(self):
        async def run():
            tg,client,sender=b.instance();b.script_messages(sender,[b.document()])
            sender.files[b.ASSET_ID]=b.PAYLOAD;real=client.download_media
            async def old_signature(message,*,file):return await real(message,file=file)
            with patch.object(client,'download_media',side_effect=old_signature):
                result=await tg.get_message_batch(CHAT,after_id=100,limit=1,download_media_to=self.root/'media')
            self.assertEqual(result.next_after_id,101)
        self.run_async(run)

if __name__=='__main__':unittest.main()
