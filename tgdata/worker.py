"""Resident explicit-account worker: python -m tgdata.worker --config worker.json."""

import argparse
import asyncio
import logging
import os
from pathlib import Path
import signal
import sys
import threading

from .join_budget import JoinBudget
from .read_budget import ReadBudget
from .worker_engine import Worker, WorkerAccount
from . import worker_protocol as wire


class _Stop(BaseException):
    pass


class _Arguments(argparse.ArgumentParser):
    def error(self, message):
        # argparse's usual diagnostic echoes arbitrary argument contents.
        raise wire.WorkerError('invalid_config')


def _path(value, parent, field, must_exist=True):
    if type(value) is not str or not value or value == ':memory:' or value.lower().startswith('file:'):
        raise wire.WorkerError('invalid_config', field=field)
    try:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = parent / path
        path = path.resolve()
        if must_exist and not path.is_file():
            raise ValueError
        return path
    except (ValueError, OSError, RuntimeError):
        raise wire.WorkerError('invalid_config', field=field) from None


def load_inventory(path):
    """Trusted local JSON configuration; no credentials or policies in jobs."""
    path = Path(path).expanduser().resolve()
    with path.open('rb') as stream:
        raw = stream.read(wire.MAX_MANIFEST_BYTES + 1)
    if len(raw) > wire.MAX_MANIFEST_BYTES:
        raise wire.WorkerError('invalid_config')
    value = wire.decode_json(raw)
    required = {'version', 'worker_id', 'read_budget', 'accounts'}
    if (type(value) is not dict or not required <= set(value)
            or not set(value) <= required | {'join_budget', 'media_directory'}
            or type(value['version']) is not int or value['version'] != wire.VERSION):
        raise wire.WorkerError('invalid_config')
    rows = value['accounts']
    if type(rows) is not list or len(rows) > wire.MAX_ACCOUNTS:
        raise wire.WorkerError('invalid_config', field='accounts')
    accounts = []
    for row in rows:
        if (type(row) is not dict or not {'account_id', 'config_path'} <= set(row)
                or not set(row) <= {'account_id', 'config_path', 'label'}):
            raise wire.WorkerError('invalid_config', field='accounts')
        ident = wire.canonical_id(row['account_id'])
        config = _path(row['config_path'], path.parent, 'config_path')
        accounts.append(WorkerAccount(ident, config, label=row.get('label')))
    budget_path = _path(value['read_budget'], path.parent, 'read_budget')
    budget = ReadBudget(budget_path)
    join = None
    if value.get('join_budget') is not None:
        join = JoinBudget(_path(value['join_budget'], path.parent, 'join_budget'), create=False)
    options = dict(accounts=accounts, worker_id=value['worker_id'], read_budget=budget, join_budget=join)
    if value.get('media_directory') is not None:
        options['media_directory'] = _path(value['media_directory'], path.parent,
                                            'media_directory', must_exist=False)
    return options


def _raw_output(stream):
    stream = getattr(sys.stdout, 'buffer', sys.stdout) if stream is None else stream
    # Worker bytes never enter the buffer which Python would flush again at exit.
    raw = getattr(stream, 'raw', None)
    stream = raw if raw is not None else stream
    if not callable(getattr(stream, 'write', None)):
        raise wire.WorkerError('invalid_config', field='output')
    return stream


def _write_all(stream, data):
    view = memoryview(data)
    while view:
        count = stream.write(view)
        if type(count) is not int or not 0 < count <= len(view):
            raise wire.WorkerError('output_failure', fatal=True)
        view = view[count:]


def _fatal(error, output, category='configuration_error'):
    detail = wire.describe_error(error)
    detail['category'] = category
    frame = dict(version=wire.VERSION, kind='fatal', error=detail, worker_stopping=True)
    try:
        _write_all(output, wire.encode_frame(frame))
    except BaseException:
        pass  # A failed output channel cannot carry another diagnostic.


def serve(accounts, *, worker_id, read_budget, join_budget=None,
          media_directory=None, input_stream=None, output_stream=None):
    """Run in a dedicated process's main thread and return its exit code.

    A Python bootstrap can supply trusted session stores via WorkerAccount.
    Exit that process with the returned code. Supplied output must be unbuffered
    (a standard buffered binary stream is unwrapped to its raw stream).
    """
    output = _raw_output(output_stream)
    source = getattr(sys.stdin, 'buffer', sys.stdin) if input_stream is None else input_stream
    if threading.current_thread() is not threading.main_thread():
        _fatal(wire.WorkerError('invalid_config'), output)
        return 2
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        _fatal(wire.WorkerError('invalid_config'), output)
        return 2
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    loop = None
    worker = active = None
    handlers = {}
    stopping_signal = None
    code = 0
    creating = finalizing = False

    def stop(signum, frame):
        nonlocal stopping_signal
        if stopping_signal is not None:
            return
        stopping_signal = signum
        if worker is not None:
            worker.stopping = True
        if creating or finalizing:
            # Retain ownership while publishing a task or settling cleanup.
            if loop is not None and not loop.is_closed():
                loop.call_soon_threadsafe(lambda: None)
            return
        if active is not None and not active.done():
            active.cancel()
            # Cancellation alone does not wake a selector inside a signal handler.
            loop.call_soon_threadsafe(lambda: None)
        else:
            raise _Stop()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, stop)
        worker = Worker(accounts, worker_id=worker_id, read_budget=read_budget,
                        join_budget=join_budget, media_directory=media_directory)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        decoder = wire.RequestDecoder()
        _write_all(output, wire.encode_frame(worker.ready()))
        while not worker.stopping and stopping_signal is None:
            try:
                frame = source.readline(wire.MAX_REQUEST_BYTES + 1)
            except (OSError, ValueError, TypeError):
                raise wire.WorkerError('input_failure', fatal=True) from None
            if frame == b'':
                break
            try:
                job = decoder.decode(frame)
            except wire.WorkerError as error:
                _write_all(output, wire.encode_frame(worker.refusal(error)))
                if error.fatal:
                    code = 2
                    break
                continue
            creating = True
            try:
                active = loop.create_task(worker.execute(job))
            finally:
                creating = False
            if stopping_signal is not None:
                # A stop during creation must win before the task's first turn.
                active.cancel()
            try:
                frames = loop.run_until_complete(active)
            except asyncio.CancelledError:
                if stopping_signal is None:
                    code = 3
                break
            finally:
                active = None
            for encoded in frames:
                _write_all(output, encoded)
            if worker.stopping:
                code = 3
                break
    except _Stop:
        pass
    except (BrokenPipeError, ConnectionError, OSError):
        code = 3
    except wire.WorkerError as error:
        code = 2 if worker is None or error.code in ('input_failure', 'incomplete_frame', 'frame_too_large') else 3
        _fatal(error, output, 'configuration_error' if worker is None else 'worker_error')
    except Exception as error:
        code = 2 if worker is None else 3
        _fatal(error, output, 'configuration_error' if worker is None else 'worker_error')
    finally:
        finalizing = True
        if worker is not None:
            worker.stopping = True
        if loop is not None:
            try:
                if active is not None and not active.done():
                    active.cancel()
                    loop.run_until_complete(asyncio.gather(active, return_exceptions=True))
                if worker is not None:
                    loop.run_until_complete(worker.close())
            except BaseException:
                if stopping_signal is None:
                    code = 3
            finally:
                try:
                    # A failed SDK disconnect can leave update/keepalive tasks.
                    # This process owns the loop: settle its remaining tasks
                    # before closing it, without retrying a source or output.
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except BaseException:
                    if stopping_signal is None:
                        code = 3
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
        for sig, previous in handlers.items():
            signal.signal(sig, previous)
        logging.disable(previous_logging)
    return 128 + stopping_signal if stopping_signal is not None else code


def main(argv=None):
    parser = _Arguments(prog='tgdata-worker', description='Run a serial JSON-line Telegram reading worker.')
    parser.add_argument('--config', required=True, help='trusted worker inventory JSON file')
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        args = parser.parse_args(argv)
        options = load_inventory(args.config)
        return serve(**options)
    except Exception as error:
        try:
            _fatal(error, _raw_output(None))
        except BaseException:
            pass
        return 2
    finally:
        logging.disable(previous_logging)


if __name__ == '__main__':
    raise SystemExit(main())
