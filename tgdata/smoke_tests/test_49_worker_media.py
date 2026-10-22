"""Worker media options over real SDK readers, files, SQLite and process pipes.

Only Telegram replies/transport and named failure timing are controlled. No login
or remote sockets. Run: python -m tgdata.smoke_tests.test_49_worker_media
"""
import asyncio
from contextlib import ExitStack
import hashlib
import inspect
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import tgdata
assert Path(tgdata.__file__).resolve().parents[1] == ROOT
from telethon import errors, functions, types
from tgdata import MessageBatch, ReadBudget
from tgdata import batch_files, worker, worker_protocol as wire
from tgdata.worker_engine import Worker, WorkerAccount
from tgdata.smoke_tests import test_37_worker as f

PHOTO = b'photo-bytes\x00' * 701
VIDEO = bytes(range(256)) * 601
ASSET_PHOTO, ASSET_VIDEO = 9001, 9002


def media_messages():
    photo = f.b.photo(101, sizes=[types.PhotoSize('w', 100, 100, len(PHOTO))])
    photo.media.photo.id = ASSET_PHOTO
    video = f.b.document(102, asset_id=ASSET_VIDEO, data=VIDEO, mime='video/mp4')
    video.media.document.attributes.append(types.DocumentAttributeVideo(2, 100, 100))
    return [photo, video]


def configure_media(item):
    item.scripts['GetHistoryRequest'] = [f.b.f.response(list(reversed(media_messages())))]
    item.file_requests = []
    def hook(client, sender):
        original = sender.send
        def send(request, ordered=False):
            r = f.b.f.unwrap(request)
            if not isinstance(r, functions.upload.GetFileRequest):
                return original(request, ordered=ordered)
            bytes(request)  # Native TL encoding, with real-width fields.
            sender.calls.append(type(r).__name__)
            sender.requests.append(r)
            item.file_requests.append((r.location.id, r.offset, r.limit))
            if item.trace is not None:
                item.trace('request', type(r).__name__)
            if getattr(item, 'file_pending', None) is not None:
                return item.file_pending
            future = asyncio.get_running_loop().create_future()
            if r.location.id == getattr(item, 'fail_asset', None):
                error = getattr(item, 'file_error', errors.FloodWaitError(request=r, capture=30))
                future.set_exception(error)
            else:
                data = {ASSET_PHOTO: PHOTO, ASSET_VIDEO: VIDEO}[r.location.id]
                future.set_result(types.upload.File(types.storage.FileUnknown(), 0,
                                                    data[r.offset:r.offset + r.limit]))
            return future
        sender.send = send
        if getattr(item, 'close_release', None) is not None:
            sender.close_release = item.close_release
        if getattr(item, 'close_error', None) is not None:
            sender.close_error = item.close_error
    item.hook = hook


def enable(s, directory=None):
    directory = s.root / 'media' if directory is None else directory
    s.worker = Worker(s.worker.accounts, worker_id='test-worker', read_budget=s.budget,
                      join_budget=s.join, media_directory=directory)
    return Path(directory).resolve()


def params(media=True):
    result = dict(group_id='@synthetic_room', after_id='100', limit=2)
    if media is not None:
        result['download_media'] = media
    return result


def check_files(root, document):
    batch = MessageBatch.from_json(json.dumps(document))
    assert batch.to_dict() == document
    assert batch.media_mode == 'download'
    for row in batch.messages:
        if row['media'] is None or not row['media']['downloadable']:
            continue
        blob = row['media']['blob']
        assert blob['path'] == blob['sha256'] and not Path(blob['path']).is_absolute()
        data = (root / blob['path']).read_bytes()
        assert len(data) == blob['size']
        assert hashlib.sha256(data).hexdigest() == blob['sha256']
    assert not list(root.glob('.tgdata-media-*'))
    return batch


async def test_default_false_matches_omission_without_directory_io():
    async with f.Setup() as s:
        item = s.items[111];configure_media(item)
        first, _ = await s.call(**params(None))
        root = enable(s)
        omitted, _ = await s.call(**params(None))
        explicit, _ = await s.call(**params(False))
        assert first['data'] == omitted['data'] == explicit['data']
        assert first['data']['media_mode'] == 'references'
        assert not root.exists() and not item.file_requests
        assert s.job(**params(False)).options() == s.job(**params(None)).options()
        assert all(c._sender.closed for c in item.clients)


async def test_strict_switch_and_job_path_refusal():
    async with f.Setup() as s:
        enable(s)
        cases = [params(v) for v in (0, 1, 'true', '', None, [], {})]
        cases[4]['download_media'] = None
        cases += [dict(params(), **{name: f.SECRET}) for name in
                  ('media_directory', 'download_media_to', 'path', 'output_path')]
        for options in cases:
            try:s.job(**options)
            except wire.WorkerError as error:
                assert error.code == 'invalid_parameters'
                assert f.SECRET not in json.dumps(s.worker.refusal(error))
            else:raise AssertionError('Invalid job accepted')
        for verb in ('lookup_group', 'check_group_access', 'join_group'):
            try:s.job(verb, target='@synthetic_room', download_media=True)
            except wire.WorkerError as error:assert error.code == 'invalid_parameters'
            else:raise AssertionError('Other verb accepted media')
        assert not s.items[111].clients and s.budget.status(111).used == 0


async def test_media_disabled_before_source_then_default_still_works():
    async with f.Setup() as s:
        value, events = await s.call(**params())
        assert value['error']['code'] == 'media_disabled' and not events
        assert not s.items[111].clients and s.budget.status(111).used == 0
        assert not s.worker.stopping
        assert (await s.call())[0]['ok']


async def test_native_photo_video_files_hashes_and_distinct_batch_identity():
    async with f.Setup() as s:
        root = enable(s);item=s.items[111];configure_media(item)
        reference, _ = await s.call(**params(False))
        result, events = await s.call(**params())
        assert result['ok'] and not events
        batch = check_files(root,result['data'])
        assert batch.next_after_id == 102 and len(batch.messages)==2
        assert [m['media']['kind'] for m in batch.messages] == ['photo','video']
        assert batch.batch_id != reference['data']['batch_id']
        assert s.budget.status(111).used == 4  # File bytes do not consume message allowance.
        assert str(root) not in json.dumps(result)
        assert item.clients[-1]._sender.closed
        assert item.clients[-1]._sender.policy_at_connect['flood'] == 0
        assert [x[0] for x in item.file_requests] == sorted(x[0] for x in item.file_requests)
        assert len(item.file_requests)>2  # Real native multi-chunk video path.
        again, _ = await s.call(**params())
        assert again['data']==result['data'] and len(list(root.iterdir()))==2


async def test_download_failure_keeps_only_completed_prefix():
    async with f.Setup() as s:
        root=enable(s);item=s.items[111];configure_media(item);item.fail_asset=ASSET_VIDEO
        value, events=await s.call(**params())
        assert not value['ok'] and value['error']['wait_seconds']==30
        batch=check_files(root,value['partial_result'])
        assert batch.next_after_id==101 and len(batch.messages)==1 and batch.stop_reason=='interrupted'
        assert len(list(root.iterdir()))==1 and s.budget.status(111).used==2
        assert item.clients[-1]._sender.closed and not s.worker.stopping
        assert all(e['account_id']=='111' for e in events)


async def test_local_publication_failure_preserves_prefix_and_health():
    async with f.Setup() as s:
        root=enable(s);configure_media(s.items[111]);original=batch_files.os.link
        calls=[]
        def link(source,destination):
            calls.append(destination)
            if len(calls)==2:raise OSError(f.SECRET)
            return original(source,destination)
        with patch.object(batch_files.os,'link',link):value,events=await s.call(**params())
        assert not value['ok'] and value['error']['type']=='OSError' and not events
        assert check_files(root,value['partial_result']).next_after_id==101
        assert len(list(root.iterdir()))==1


async def test_corrupt_existing_blob_refuses_without_overwrite():
    async with f.Setup() as s:
        root=enable(s);configure_media(s.items[111]);root.mkdir()
        name=hashlib.sha256(PHOTO).hexdigest();(root/name).write_bytes(b'corrupt')
        value,events=await s.call(**params())
        assert value['error']['type']=='BatchStorageError' and not events
        assert value['partial_result']['next_after_id']=='100'
        assert (root/name).read_bytes()==b'corrupt' and not list(root.glob('.tgdata-media-*'))


async def test_reference_refresh_retains_message_budget():
    async with f.Setup() as s:
        root=enable(s);item=s.items[111];configure_media(item)
        item.scripts['GetHistoryRequest']=[f.b.f.response([media_messages()[1]])]
        item.fail_asset=ASSET_VIDEO;item.file_error=errors.FileReferenceExpiredError(request=None)
        s.budget.configure(111,1)
        value,events=await s.call(**dict(params(),limit=1))
        assert value['error']['type']=='ReadBudgetExceeded' and not events
        assert value['partial_result']['next_after_id']=='100' and s.budget.status(111).used==1
        assert not list(root.iterdir())


async def test_result_delivery_failure_retains_complete_files():
    async with f.Setup() as s:
        root=enable(s);configure_media(s.items[111]);original=wire.encode_frame
        def fail(frame,**kw):
            if frame.get('kind')=='result' and frame.get('ok'):raise ValueError(f.SECRET)
            return original(frame,**kw)
        with patch.object(wire,'encode_frame',fail):value,events=await s.call(**params())
        assert value['error']['code']=='delivery_failed' and value['worker_stopping'] and not events
        assert value['source_outcome']=='returned' and value['partial_omitted']
        assert {p.name for p in root.iterdir()}=={hashlib.sha256(x).hexdigest() for x in (PHOTO,VIDEO)}
        assert s.items[111].clients[-1]._sender.closed


async def test_cancelled_download_settles_existing_cleanup():
    async with f.Setup() as s:
        root=enable(s);item=s.items[111];configure_media(item)
        item.file_pending=asyncio.get_running_loop().create_future();item.close_release=asyncio.Event()
        task=asyncio.create_task(s.worker.execute(s.job(**params())))
        await f.until(lambda:bool(item.file_requests))
        sender=item.clients[-1]._sender
        assert list(root.glob('.tgdata-media-*'))
        task.cancel();await sender.close_entered.wait();task.cancel();await asyncio.sleep(0)
        assert not task.done() and not sender.closed and not list(root.iterdir())
        item.close_release.set();await f.expect(asyncio.CancelledError,task)
        assert sender.closed and item.file_pending.cancelled() and s.worker.stopping
        # Observe before Setup's safety teardown; this is a primary sender path.


async def test_cleanup_failure_keeps_completed_media_and_stops_worker():
    async with f.Setup() as s:
        root=enable(s);item=s.items[111];configure_media(item);item.close_error=OSError(f.SECRET)
        value,_=await s.call(**params())
        assert value['ok'] and value['worker_stopping'];check_files(root,value['data'])
        assert not item.clients[-1]._sender.closed
        assert (await f.expect(wire.WorkerError,s.worker.execute(s.job(account=222)))).code=='worker_stopping'
        assert not s.items[222].clients


async def test_directory_normalization_validation_and_lazy_creation():
    async with f.Setup() as s:
        file=s.root/'file';file.write_text('untouched')
        for bad in ('',False,1,b'bytes',':memory:','file:///tmp/media','bad\x00path',file):
            try:enable(s,bad)
            except wire.WorkerError as e:
                assert e.code=='invalid_config' and e.field=='media_directory'
            else:raise AssertionError('Bad trusted root accepted')
        root=enable(s,s.root/'new'/'nested');assert not root.exists()
        configure_media(s.items[111]);value,_=await s.call(**params());check_files(root,value['data'])
        assert file.read_text()=='untouched'


async def test_python_root_is_pinned_before_working_directory_changes():
    async with f.Setup() as s:
        previous=Path.cwd()
        try:
            os.chdir(s.root)
            root=enable(s,Path('python-media'))
            os.chdir(previous)
            configure_media(s.items[111])
            value,_=await s.call(**params())
            assert root==(s.root/'python-media').resolve()
            check_files(root,value['data'])
        finally:
            os.chdir(previous)


def child(root,mode):
    root=Path(root);item=f.fixture(root,111);configure_media(item)
    if mode=='partial':item.fail_asset=ASSET_VIDEO
    def trace(kind,detail):
        with (root/'trace.jsonl').open('a') as out:out.write(json.dumps([kind,detail])+'\n')
    item.trace=trace
    with patch.object(socket.socket,'connect',side_effect=AssertionError('no network')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')), \
         f.install_factory({111:item}):
        code=worker.main(['--config',str(root/'worker.json')])
    # Assert before any fixture-driven cleanup, after actual driver shutdown.
    assert all(c._sender.closed for c in item.clients)
    return code


def test_cli_config_jobs_files_and_partial_results():
    for mode in ('normal','partial','disabled','path','default','null','invalid-root'):
        with tempfile.TemporaryDirectory(prefix='worker_media_process_') as tmp:
            root=Path(tmp);f.fixture(root,111)
            budget=ReadBudget(root/'read.sqlite3');budget.configure(111,20)
            manifest=dict(version=1,worker_id='media-test',read_budget='read.sqlite3',
                          accounts=[dict(account_id='111',config_path='account-111.ini')])
            if mode not in ('disabled','null'):manifest['media_directory']='out/nested'
            if mode=='null':manifest['media_directory']=None
            if mode=='invalid-root':
                (root/'not-dir').write_text('keep');manifest['media_directory']='not-dir'
            (root/'worker.json').write_text(json.dumps(manifest))
            options=params(False if mode=='default' else True)
            if mode=='path':options['download_media_to']=f.SECRET
            raw=(json.dumps(dict(version=1,request_id=1,account_id='111',operation='read_batch',params=options))+'\n').encode()
            command=[sys.executable,'-m','tgdata.smoke_tests.test_49_worker_media','--child',str(root),mode]
            run=subprocess.run(command,cwd='/',env=dict(os.environ,PYTHONPATH=str(ROOT)),input=raw,capture_output=True,timeout=20)
            assert not run.stderr,run.stderr.decode(errors='replace')
            assert f.SECRET.encode() not in run.stdout
            frames=[json.loads(line) for line in run.stdout.splitlines()];value=frames[-1]
            out=root/'out'/'nested'
            if mode=='invalid-root':
                assert run.returncode==2 and value['kind']=='fatal' and value['error']['field']=='media_directory'
            else:
                assert run.returncode==0 and frames[0]['kind']=='ready'
                if mode in ('disabled','null','path'):
                    assert value['error']['code']==('invalid_parameters' if mode=='path' else 'media_disabled')
                    assert not (root/'trace.jsonl').exists() and budget.status(111).used==0
                elif mode=='default':assert value['data']['media_mode']=='references'
                else:
                    batch=check_files(out,value['partial_result'] if mode=='partial' else value['data'])
                    assert batch.next_after_id==(101 if mode=='partial' else 102)
            if mode not in ('normal','partial'):assert not out.exists()


def test_manifest_invalid_root_types_are_sanitized():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);ReadBudget(root/'r.db')
        for bad in ('',True,3,[],{},'file:/private','bad\x00path'):
            config=root/'worker.json';config.write_text(json.dumps(dict(version=1,worker_id='w',
                read_budget='r.db',accounts=[],media_directory=bad)))
            try:Worker(**worker.load_inventory(config))
            except wire.WorkerError as e:assert e.code=='invalid_config' and e.field=='media_directory'
            else:raise AssertionError('Invalid manifest root accepted')


def test_example_rejects_media_on_other_verbs_before_process():
    run=subprocess.run([sys.executable,str(ROOT/'examples/reading_worker.py'),'--config','missing.json',
        '--account','111','--target','@room','--operation','lookup_group','--download-media'],capture_output=True)
    assert run.returncode==2 and b'only valid with read_batch' in run.stderr and not run.stdout


def main():
    tests=[f for n,f in globals().items() if n.startswith('test_')];passed=0
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        for test in tests:
            try:
                if inspect.iscoroutinefunction(test):asyncio.run(asyncio.wait_for(test(),30))
                else:test()
                print('PASS',test.__name__,flush=True);passed+=1
            except Exception:traceback.print_exc();print('FAIL',test.__name__,flush=True)
    print('Passed: {}/{}'.format(passed,len(tests)),flush=True)
    return int(passed!=len(tests))

if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    if len(sys.argv)>1 and sys.argv[1]=='--child':raise SystemExit(child(sys.argv[2],sys.argv[3]))
    raise SystemExit(main())
