"""Apply the reviewed prototype only to a newly owned isolated export."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parents[1] / 'evidence/restart'


def replace(file, old, new):
    text = file.read_text()
    assert text.count(old) == 1, (file.name, old[:100], text.count(old))
    file.write_text(text.replace(old, new))


def build(source):
    assert source.is_relative_to(Path('/private/tmp')) and source.name == 'source'
    lib = source / 'tgdata'
    for name in ('pool_lifecycle.py', 'pool_observation.py'):
        assert not (lib / name).exists()
        (lib / name).write_text((HERE / name).read_text())
    file = lib / 'message_batch.py'
    with file.open('a') as stream:
        stream.write('''\n\ndef _interrupted_prefix(value):
    """Available complete records, never a durable receipt or history-end proof."""
    if not isinstance(value, MessageBatch) or not value.messages:
        return None
    if value.stop_reason == 'interrupted':
        return value
    wire = value.to_dict()
    return MessageBatch._from_records(int(wire['chat_id']), int(wire['after_id']),
                wire['messages'], wire['media_mode'], 'interrupted')
''')
    file = lib / 'pool_state.py'
    replace(file, 'class _UnresolvedGroup(PoolError):', '''class _SourceInterrupted(PoolStateError):
    """Source ended without a completed outcome; account admission stays unresolved."""


class _UnresolvedGroup(PoolError):''')
    file = lib / 'pool_source.py'
    text = file.read_text()
    start = text.index('async def _await_cleanup('); end = text.index('class _BoundBudget:')
    text = text[:start]+text[end:]
    text = text.replace('from .health import HealthMonitor',
        'from .pool_lifecycle import _await_cleanup, _start_owned, _wait_owned\nfrom .pool_observation import PoolMonitor\nfrom .message_batch import _interrupted_prefix')
    text = text.replace('_UnresolvedGroup, _WarmupPending,','_UnresolvedGroup, _WarmupPending, _SourceInterrupted,')
    text = text.replace('groups, callback):','groups, observations):').replace(
        'HealthMonitor(callback, account.label, self._identity)', 'PoolMonitor(observations, account.label, self._identity)')
    text = text.replace('except Exception as error:\n            raise PoolConfigurationError',
        'except (Exception, asyncio.CancelledError) as error:\n            raise PoolConfigurationError')
    start=text.index('    async def run('); end=text.index('    async def retire(',start)
    text=text[:start]+'''    async def run(self, chat_id=None, **options):
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

'''+text[end:]
    file.write_text(text)
    file=lib/'account_pool.py'
    replace(file,'from .sync_engine import SyncEngine','''from .sync_engine import SyncEngine
from .sync_store import SyncStorageError
from .backfill import BackfillStorageError
from .message_batch import _interrupted_prefix
from .pool_lifecycle import _scope, _inside, _call_store, _StoreBoundary
from .pool_observation import ObservationBuffer''')
    replace(file,'_integer, _seconds, _chat, _UnresolvedGroup, _WarmupPending,',
        '_integer, _seconds, _chat, _UnresolvedGroup, _WarmupPending, _SourceInterrupted,')
    replace(file,"if health_callback is not None and not callable(health_callback):\n            raise PoolConfigurationError('health_callback must be callable or None')", "if health_callback is not None:\n            raise PoolConfigurationError('AccountPool does not run health callbacks; use drain_health_events()')")
    replace(file,'self._sources = {a.account_id: _OwnedSource(a, read_budget, self.policy, self.groups, health_callback)',
        'self._observations = ObservationBuffer()\n        self._sources = {a.account_id: _OwnedSource(a, read_budget, self.policy, self.groups, self._observations)')
    replace(file,'self.sync_engine = SyncEngine(self.get_message_batch, sync_store)\n        self._backfill_store = backfill_store', '''self.sync_engine = SyncEngine(self.get_message_batch,
            _StoreBoundary(self, sync_store, SyncStorageError, 'Sync') if sync_store is not None else None)
        self._backfill_store = (_StoreBoundary(self, backfill_store, BackfillStorageError, 'Backfill')
                                if backfill_store is not None else None)''')
    replace(file,'    def _operation(self):\n        if self._closed:', '''    def _operation(self):
        if _inside(self):
            raise PoolBusyError('Cannot control this pool from its live operation/provider scope')
        if self._closed:''')
    replace(file,'        try:\n            yield\n        finally:\n            self._active_task = None',
        '        try:\n            with _scope(self):\n                yield\n        finally:\n            self._active_task = None')
    replace(file,"return await getattr(self._store, method)(*args)",
        "return await _call_store(self, self._store, method, args, PoolStorageError, 'Pool')")
    text=file.read_text(); start=text.index('    @staticmethod\n    def _prefix('); end=text.index('    async def _settle(',start)
    text=text[:start]+'    _prefix = staticmethod(_interrupted_prefix)\n\n'+text[end:];file.write_text(text)
    replace(file,'        row = self._require_row(document, account_id)\n        if row[\'active\'] is None or row[\'active\'][\'id\'] != attempt_id:',
        "        if isinstance(source_error, _SourceInterrupted):\n            raise source_error\n        row = self._require_row(document, account_id)\n        if row['active'] is None or row['active']['id'] != attempt_id:")
    replace(file,'        except asyncio.CancelledError:\n            raise\n        except Exception as error:\n            local = error if isinstance(error, PoolError)', '''        except asyncio.CancelledError as error:
            error.partial_result = self._prefix(batch if batch is not None else
                                               getattr(source_error, 'partial_result', None))
            if source_error is not None:
                error.read_error = source_error
            raise
        except Exception as error:
            local = error if isinstance(error, PoolError)''')
    replace(file,'        current = asyncio.current_task()\n        if current is self._active_task',
        "        if _inside(self):\n            raise PoolBusyError('Cannot close this pool from its live operation/provider scope')\n        current = asyncio.current_task()\n        if current is self._active_task")
    replace(file,'    async def __aenter__(self):', '''    def drain_health_events(self):
        """Return/reset bounded captured-so-far observations; no I/O in any state."""
        return self._observations.drain()

    async def __aenter__(self):''')
    file=lib/'sync_engine.py'
    replace(file,'from .message_batch import MessageBatch, BatchFormatError, MAX_BATCH_MESSAGES, MAX_MESSAGE_ID',
        'from .message_batch import MessageBatch, BatchFormatError, MAX_BATCH_MESSAGES, MAX_MESSAGE_ID, _interrupted_prefix')
    replace(file,'        await self._replace(state.chat_id, raw, replace(state, pending=batch))', '''        try:
            await self._replace(state.chat_id, raw, replace(state, pending=batch))
        except (SyncError, asyncio.CancelledError) as error:
            error.partial_result = _interrupted_prefix(batch)
            raise''')
    file=lib/'backfill_engine.py'
    replace(file,'from .message_batch import MessageBatch, MAX_LONG',
        'from .message_batch import MessageBatch, MAX_LONG, _interrupted_prefix')
    replace(file,'    async def _settle(self, admitted, batch, timing, failure=None):', '''    async def _settle(self, admitted, batch, timing, failure=None):
        try:
            return await self._settle_state(admitted, batch, timing, failure)
        except (BackfillError, asyncio.CancelledError) as error:
            error.partial_result = _interrupted_prefix(batch)
            raise

    async def _settle_state(self, admitted, batch, timing, failure=None):''')
    hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(lib.rglob('*.py'))}
    for p in lib.glob('*.py'):
        ast.parse(p.read_text(), feature_version=(3,7))
    return hashes

if __name__ == '__main__':
    manifest=json.loads((EVIDENCE/'export-manifest.json').read_text())
    hashes=build(Path(manifest['export']))
    (EVIDENCE/'candidate-manifest.json').write_text(json.dumps(dict(
        source=manifest['export'], runtime_sha256=hashes,
        changed=[p for p,h in hashes.items() if manifest['runtime_sha256'].get(p)!=h]),indent=2)+'\n')
    print(json.dumps(dict(export=manifest['export'], runtime_files=len(hashes))))
