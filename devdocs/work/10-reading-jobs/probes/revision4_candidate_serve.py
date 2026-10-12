# Experiment-only function snapshot; helper globals come from the unchanged worker module.
def serve(accounts, *, worker_id, read_budget, join_budget=None,
          input_stream=None, output_stream=None):
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
            if loop is not None and not loop.is_closed():
                loop.call_soon_threadsafe(lambda: None)
            return
        if active is not None and not active.done():
            active.cancel()
            loop.call_soon_threadsafe(lambda: None)
        else:
            raise _Stop()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, stop)
        worker = Worker(accounts, worker_id=worker_id, read_budget=read_budget, join_budget=join_budget)
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
