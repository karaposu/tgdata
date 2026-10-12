"""Planning-only experiments; compile candidates in memory, never edit product files.

Qualifies the two narrow mechanisms, not the complete revised phase contract.
The reviewed implementation still needs the broader prebuild specified in plan r3.
"""
import asyncio
import inspect
import json
import logging
from pathlib import Path
import signal
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_lifetime as lifetime
import pr_diagnostics as diagnostics
from tgdata import worker, worker_protocol as protocol, health
from tgdata.connection_engine import _BANNED
from telethon.errors import UnauthorizedError, AuthKeyError


def stop_candidate():
    source = inspect.getsource(worker.serve)
    old = '            active.cancel()\n'
    lines = source.splitlines(keepends=True)
    assert lines.count(old) == 1
    source = ''.join(line + '            loop.call_soon_threadsafe(lambda: None)\n'
                     if line == old else line for line in lines)
    namespace = dict(worker.__dict__)
    exec(compile(source, '<planning-cancel-and-wake>', 'exec'), namespace)
    return namespace['serve']


def diagnostic_candidate():
    known = frozenset(name for cls, name in health._TELEGRAM_NAMES.items()
                      if issubclass(cls, (UnauthorizedError, AuthKeyError))) | frozenset(_BANNED)
    source = inspect.getsource(protocol.describe_error)
    old = 'if type(reason) is str and _NAME.fullmatch(reason):'
    assert source.count(old) == 1
    source = source.replace(old, 'if type(reason) is str and reason in _CANONICAL_AUTH_REASONS:')
    namespace = dict(protocol.__dict__, _CANONICAL_AUTH_REASONS=known)
    exec(compile(source, '<planning-known-auth-reasons>', 'exec'), namespace)
    return namespace['describe_error'], known


async def cancellation_order():
    for mode in ('queued_cancel', 'mark_then_wake'):
        stepped = []
        async def operation():
            stepped.append(True)
            await asyncio.get_running_loop().create_future()
        loop = asyncio.get_running_loop()
        task = loop.create_task(operation())
        if mode == 'queued_cancel':
            loop.call_soon_threadsafe(task.cancel)
        else:
            task.cancel()
            loop.call_soon_threadsafe(lambda: None)
        await asyncio.gather(task, return_exceptions=True)
        assert bool(stepped) is (mode == 'queued_cancel')
        print(json.dumps(dict(case='native_task_order', mode=mode,
                              task_stepped_before_cancel=bool(stepped))), flush=True)


async def diagnostic_cases():
    candidate, known = diagnostic_candidate()
    import socket
    with patch.object(protocol, 'describe_error', candidate), \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        for code, name in ((401, diagnostics.SENTINEL), (406, diagnostics.SENTINEL),
                           (403, diagnostics.SENTINEL), (401, 'AUTH_KEY_UNREGISTERED'),
                           (401, 'SESSION_REVOKED'), (401, 'USER_DEACTIVATED_BAN')):
            value = await diagnostics.auth_case(code, name)
            assert not value['raw_text_forwarded']
            assert value['error'].get('reason') == (name if name in known else None)
    print('PASS six actual SDK/worker diagnostic candidates; library errors unchanged', flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        with patch.object(worker, 'serve', stop_candidate()):
            raise SystemExit(lifetime.child(sys.argv[2], sys.argv[3]))
    logging.disable(logging.CRITICAL)
    lifetime.__file__ = __file__  # Its real process runner starts this candidate bootstrap.
    for sig in (signal.SIGINT, signal.SIGTERM):
        value = lifetime.signal_case(sig, 'quiet')
        assert not value['stalled_before_explicit_wake']
        assert value['cleanup_started_before_wake']
    asyncio.run(cancellation_order())
    asyncio.run(diagnostic_cases())
    print('PASS planning feasibility: 2 quiet processes, 2 native ordering controls, 6 SDK errors', flush=True)
