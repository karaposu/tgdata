"""Apply only the critiqued complete candidate to our isolated export."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'evidence/outcome'


def replace(file, old, new):
    value=file.read_text()
    assert value.count(old)==1,(file.name,old[:100],value.count(old))
    file.write_text(value.replace(old,new))


def migrate(file):
    """Only add required capture inputs; never change a prior assertion/oracle."""
    source=file.read_text(); tree=ast.parse(source); lines=source.splitlines(keepends=True)
    offsets=[0]
    for line in lines: offsets.append(offsets[-1]+len(line))
    inserts=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):continue
        fn=node.func; owner=fn.value
        is_pool=(isinstance(owner,ast.Name) and owner.id=='pool' or
                 isinstance(owner,ast.Attribute) and owner.attr=='pool')
        if not is_pool or fn.attr not in ('read','get_message_batch','sync_group','prepare_backfill'):continue
        assert not any(kw.arg=='capture' for kw in node.keywords)
        # The shared t.read helper allows a new test to pass an explicit capture.
        expr="kwargs.pop('capture', PoolReadCapture())" if any(
            kw.arg is None and isinstance(kw.value,ast.Name) and kw.value.id=='kwargs' for kw in node.keywords
        ) else 'PoolReadCapture()'
        assert node.args, (file, node.lineno)
        arg=node.args[-1]
        end=offsets[arg.end_lineno-1]+arg.end_col_offset
        inserts.append((end, ', capture='+expr))
    for at,text in sorted(inserts,reverse=True): source=source[:at]+text+source[at:]
    if inserts:
        # Place after module docstring (and any future imports, if present).
        tree2=ast.parse(source); position=0
        for node in tree2.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,(ast.Str,ast.Constant)) and isinstance(getattr(node.value,'value',getattr(node.value,'s',None)),str):
                position=node.end_lineno
            elif isinstance(node,ast.ImportFrom) and node.module=='__future__':position=node.end_lineno
            else:break
        split=source.splitlines(keepends=True);split.insert(position,'from tgdata import PoolReadCapture\n');source=''.join(split)
    before_asserts=[ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Assert)]
    after=ast.parse(source)
    # Removing only added capture keywords restores each original assert.
    for n in ast.walk(after):
        if isinstance(n,ast.Call):n.keywords=[kw for kw in n.keywords if kw.arg!='capture']
    after_asserts=[ast.dump(n,include_attributes=False) for n in ast.walk(after) if isinstance(n,ast.Assert)]
    assert before_asserts==after_asserts,(file,'oracle changed')
    file.write_text(source)
    return dict(file=str(file),calls=len(inserts),assertions=len(before_asserts))


def build(source):
    assert source.parent.name.startswith('tgdata17-outcome-prebuild-') and source.name=='source'
    lib=source/'tgdata'
    assert not (lib/'pool_result.py').exists()
    shutil.copyfile(HERE/'pool_result.py',lib/'pool_result.py')
    file=lib/'pool_lifecycle.py'
    with file.open('a') as f:f.write('''\n\nclass _Invocation:
    """Completion of one library-owned span, not its containing caller Task."""
    def __init__(self):
        self.caller = asyncio.current_task()
        self.done = asyncio.get_running_loop().create_future()

    def stop(self, active):
        if active is self and not self.done.done() and self.caller is not None:
            self.caller.cancel()

    def finish(self):
        self.caller = None
        self.done.set_result(None)
''')
    file=lib/'batch_engine.py'
    replace(file,'                          start_date=None, end_date=None):',
                 '                          start_date=None, end_date=None, _capture=None):')
    replace(file,'                chat_id = resolved_id','''                chat_id = resolved_id
                if _capture is not None:
                    _capture.attach(chat_id, after_id, mode, records)''')
    file=lib/'pool_source.py'
    replace(file,'    async def run(self, chat_id=None, **options):','    async def run(self, chat_id=None, *, _capture=None, **options):')
    replace(file,'await self.batch_reader.fetch_batch(chat_id, **options)',
                 'await self.batch_reader.fetch_batch(chat_id, _capture=_capture, **options)')
    replace(file,"                    outcome['error'] = error", "                    outcome['error'] = error\n                    if _capture is not None:\n                        _capture.source_error(error)")
    replace(file,"                    outcome['value'], outcome['done'] = value, True", "                    outcome['value'], outcome['done'] = value, True\n                    if _capture is not None:\n                        _capture.offer(value)")
    file=lib/'account_pool.py'
    replace(file,'from .pool_lifecycle import _scope, _inside, _call_store, _StoreBoundary',
        'from .pool_lifecycle import _scope, _inside, _call_store, _StoreBoundary, _Invocation\nfrom .pool_result import _capture_call\nfrom .backfill_engine import BackfillEngine\nfrom .backfill import BackfillPrepareContext')
    replace(file,'        self._active_task = None','        self._active_invocation = None') if file.read_text().count('        self._active_task = None')==1 else None
    # Initial slot and operation are replaced independently; no second mutable task slot.
    text=file.read_text();text=text.replace('        self._active_task = None\n        self._closed', '        self._active_invocation = None\n        self._closed')
    start=text.index('    @contextmanager\n    def _operation(');end=text.index('    def _now(',start)
    text=text[:start]+'''    @property
    def _active_task(self):
        record = self._active_invocation
        return record.caller if record is not None else None

    @contextmanager
    def _operation(self):
        if _inside(self):
            raise PoolBusyError('Cannot control this pool from its live operation/provider scope')
        if self._closed:
            raise PoolClosedError('Account pool is closed')
        if self._active_invocation is not None:
            raise PoolBusyError('Another account-pool operation is active')
        record = self._active_invocation = _Invocation()
        try:
            with _scope(self):
                yield
        finally:
            self._active_invocation = None
            record.finish()

'''+text[end:]
    text=text.replace('self.sync_engine = SyncEngine(self.get_message_batch,','self.sync_engine = SyncEngine(self._read_batch,')
    text=text.replace('    async def read(self, chat_id, *, after_id=0, limit=200, download_media_to=None,\n                   start_date=None, end_date=None):',
                      '    async def _read(self, chat_id, *, after_id=0, limit=200, download_media_to=None,\n                    start_date=None, end_date=None, _capture=None):')
    text=text.replace('                batch = source_error = None','                batch = source_error = None\n                if _capture is not None:\n                    _capture.attempt(aid)')
    text=text.replace('await self._sources[aid].run(chat_id, **options)','await self._sources[aid].run(chat_id, _capture=_capture, **options)')
    start=text.index('    async def get_message_batch(');end=text.index('    async def recover_account(',start)
    text=text[:start]+'''    async def read(self, chat_id, *, capture, after_id=0, limit=200,
                   download_media_to=None, start_date=None, end_date=None):
        """Read with a caller-retained, single-use data destination."""
        with _capture_call(capture) as writer:
            result = await self._read(chat_id, after_id=after_id, limit=limit,
                download_media_to=download_media_to, start_date=start_date,
                end_date=end_date, _capture=writer)
            writer.offer(result.batch)
            return result

    async def _read_batch(self, group_id, *, after_id=0, limit=200,
                          download_media_to=None, start_date=None, end_date=None, _capture=None):
        result = await self._read(group_id, after_id=after_id, limit=limit,
            download_media_to=download_media_to, start_date=start_date,
            end_date=end_date, _capture=_capture)
        return result.batch

    async def get_message_batch(self, group_id, *, capture, after_id=0, limit=200,
                                download_media_to=None, start_date=None, end_date=None):
        with _capture_call(capture) as writer:
            batch = await self._read_batch(group_id, after_id=after_id, limit=limit,
                download_media_to=download_media_to, start_date=start_date,
                end_date=end_date, _capture=writer)
            writer.offer(batch)
            return batch

    async def sync_group(self, chat_id, *, capture, limit=200, download_media_to=None):
        with _capture_call(capture) as writer:
            batch = await self.sync_engine.prepare(chat_id, limit=limit,
                download_media_to=download_media_to, _capture=writer)
            writer.offer(batch)
            return batch

    def _new_backfill_engine(self, collection):
        return BackfillEngine(self._backfill_store, collection, read_batch=self._read_batch)

    async def prepare_backfill(self, context, *, capture, download_media_to=None):
        with _capture_call(capture) as writer:
            engine, context = self._backfill_for(context, BackfillPrepareContext)
            turn = await engine.prepare(context, download_media_to=download_media_to, _capture=writer)
            writer.offer(turn.batch)
            return turn

'''+text[end:]
    old='''            active = self._active_task
            if active is not None and not active.done():
                active.cancel()
                try:
                    await active
                except asyncio.CancelledError:
                    pass  # Expected reader cancellation; this worker is retained.
                except Exception:
                    pass  # the source caller retains its own exception
'''
    new='''            active = self._active_invocation
            if active is not None:
                active.stop(self._active_invocation)
                await active.done
'''
    assert text.count(old)==1;text=text.replace(old,new);file.write_text(text)
    file=lib/'sync_engine.py'
    replace(file,'    async def prepare(self, chat_id, *, limit=200, download_media_to=None):',
        '    async def prepare(self, chat_id, *, limit=200, download_media_to=None, _capture=None):')
    replace(file,'                return state.pending', '                if _capture is not None:\n                    _capture.offer(state.pending)\n                return state.pending')
    replace(file,'                batch = await self._read_batch(chat_id, **options)',
        "                if _capture is not None:\n                    options['_capture'] = _capture\n                batch = await self._read_batch(chat_id, **options)")
    file=lib/'backfill_engine.py'
    replace(file,'    async def prepare(self, context, *, download_media_to=None):',
        '    async def prepare(self, context, *, download_media_to=None, _capture=None):')
    replace(file,'                return self._turn(state, previous=key == \'previous\', replayed=True)',
        "                if _capture is not None:\n                    _capture.offer(batch)\n                return self._turn(state, previous=key == 'previous', replayed=True)")
    replace(file,'            try:\n                result = await self._read_batch(chat_id, **options)',
        "            if _capture is not None:\n                options['_capture'] = _capture\n            try:\n                result = await self._read_batch(chat_id, **options)")
    file=lib/'__init__.py'
    replace(file,'# Errors\nfrom .message_engine', 'from .pool_result import PoolReadCapture, PoolReadSnapshot\n\n# Errors\nfrom .message_engine')
    replace(file,'    "PoolReadResult",','    "PoolReadResult",\n    "PoolReadCapture",\n    "PoolReadSnapshot",')
    migrations=[migrate(lib/'smoke_tests'/name) for name in
                ('test_31_account_pool.py','test_39_pool_lifecycle.py','pool_storage_cases.py')]
    migrations.append(migrate(source/'examples/account_pool.py'))
    for file in source.rglob('*.py'): ast.parse(file.read_text(),feature_version=(3,7))
    return migrations

if __name__=='__main__':
    baseline=json.loads((OUT/'export-manifest.json').read_text());source=Path(baseline['source'])
    migrations=build(source)
    hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*.py'))}
    manifest=dict(source=str(source),sha256=hashes,
        changed=[p for p,h in hashes.items() if baseline['sha256'].get(p)!=h],migrations=migrations,
        candidate_code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')})
    (OUT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(source=str(source),changed=manifest['changed'],migrations=migrations)))
