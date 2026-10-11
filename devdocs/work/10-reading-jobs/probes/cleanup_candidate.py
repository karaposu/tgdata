"""Execute a small cleanup-feedback candidate without editing product files.

The actual current helper/context are compiled with only an optional failure
receipt and sticky engine fact. SDK cleanup, source policy and auth remain real.
"""
import asyncio
import inspect
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
import textwrap
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata import account_operation as owned
from tgdata import connection_engine as connection
from tgdata.smoke_tests import test_32_account_operation as f


def candidate():
    helper = inspect.getsource(owned._disconnect_owned)
    assert helper.count('async def _disconnect_owned(client):') == 1
    helper = helper.replace('async def _disconnect_owned(client):',
                            'async def _disconnect_owned(client, failures=None):')
    helper = helper.replace('    if failure is not None:\n',
        '    if failure is not None:\n        if failures is not None:\n            failures.append(failure)\n', 1)
    namespace = dict(vars(owned))
    exec(compile(helper, '<cleanup-feedback-candidate>', 'exec'), namespace)
    context = textwrap.dedent(inspect.getsource(connection.ConnectionEngine._account_operation))
    assert context.count('        await _disconnect_owned(client)') == 1
    context = context.replace('        await _disconnect_owned(client)', '''        failures = []
        try:
            await _disconnect_owned(client, failures=failures)
        finally:
            if failures:
                self._account_cleanup_failure = failures[0]''')
    outer = dict(vars(connection))
    outer['_disconnect_owned'] = namespace['_disconnect_owned']
    exec(compile(context, '<operation-feedback-candidate>', 'exec'), outer)
    return outer['_account_operation']


async def capture(work):
    try:
        return await work
    except BaseException as error:
        return error


async def main():
    with tempfile.TemporaryDirectory(prefix='tgdata10-cleanup-candidate-') as directory, \
         patch.object(connection.ConnectionEngine, '_account_operation', candidate()):
        f.TMP = Path(directory)
        fixtures = []
        try:
            for mode in ('success', 'body_failure', 'setup_failure', 'sdk_cancel', 'caller_cancel', 'logger_failure'):
                fx = f.Fixture(accounts=(222,), cached=111)
                fixtures.append(fx)
                body_error = LookupError('synthetic source body')
                setup_error = OSError('synthetic setup')
                failure = asyncio.CancelledError('internal') if mode == 'sdk_cancel' else OSError('cleanup')
                gate = asyncio.Event()
                if mode == 'setup_failure':
                    fx.connect_error = setup_error
                    factory = fx.engine._new_client
                    def build(*args, **kwargs):
                        client = factory(*args, **kwargs)
                        client._sender.close_error = failure
                        return client
                    fx.engine._new_client = build
                async def run():
                    async with fx.engine._account_operation(222):
                        if mode != 'success':
                            fx.wire.close_error = failure
                        if mode == 'caller_cancel':
                            fx.wire.close_release = gate
                        if mode == 'body_failure':
                            raise body_error
                        return 'source-completed'
                if mode == 'caller_cancel':
                    task = asyncio.create_task(run())
                    while not fx.clients:
                        await asyncio.sleep(0)
                    await fx.wire.close_entered.wait()
                    task.cancel()
                    await asyncio.sleep(0)
                    task.cancel()
                    await asyncio.sleep(0)
                    assert not task.done()
                    gate.set()
                    result = await capture(task)
                    assert isinstance(result, asyncio.CancelledError)
                elif mode == 'logger_failure':
                    with patch.object(owned.logger, 'error', side_effect=RuntimeError('diagnostic')):
                        result = await capture(run())
                    assert result == 'source-completed'
                else:
                    result = await capture(run())
                    if mode == 'body_failure':
                        assert result is body_error
                    elif mode == 'setup_failure':
                        assert result is setup_error
                    else:
                        assert result == 'source-completed'
                recorded = getattr(fx.engine, '_account_cleanup_failure', None)
                assert recorded == (None if mode == 'success' else type(failure).__name__)
                print(json.dumps(dict(case=mode, original_outcome_preserved=True,
                                      cleanup_failure=recorded, candidate_admission_predicate=recorded is None)))
                fx.wire.close_error = None
                fx.wire.close_release = None
                await fx.clients[-1].disconnect()
                # A legacy caller may still use the foundation after explicit
                # cleanup; the worker's conservative failure fact stays sticky.
                if mode != 'setup_failure':
                    async with fx.engine._account_operation(222):
                        pass
                    assert getattr(fx.engine, '_account_cleanup_failure', None) == recorded
        finally:
            for fx in fixtures:
                for client in fx.clients:
                    client._sender.close_error = None
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    await client.disconnect()
    print('PASS: six actual-composition cleanup-feedback cases; product files untouched.')


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(main())
