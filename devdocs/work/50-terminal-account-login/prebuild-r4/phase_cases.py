# Additional revision4 cases; inserted into the permanent suite after prebuild.
import threading
import termios


def test_stop_admission_and_finalization():
    for phase in ('preflight','before_task','registered','completed','authenticated','finalizing','asyncgens','report'):
        with fixture() as (config,s,root,target,previous):
            stack=__import__('contextlib').ExitStack();fired=[False]
            def stop_once():
                if not fired[0]:fired[0]=True;os.kill(os.getpid(),signal.SIGINT)
            if phase in ('preflight','authenticated'):
                say=cli._say
                def say_hook(message):
                    result=say(message)
                    if message.startswith('Session destination:' if phase=='preflight' else 'Authenticated account'):stop_once()
                    return result
                stack.enter_context(patch.object(cli,'_say',say_hook))
            elif phase in ('before_task','completed'):
                drive=cli._TerminalRun.drive
                def drive_hook(run,factory,**kw):
                    if not kw.get('retire') and phase=='before_task':stop_once()
                    result=drive(run,factory,**kw)
                    if not kw.get('retire') and phase=='completed':stop_once()
                    return result
                stack.enter_context(patch.object(cli._TerminalRun,'drive',drive_hook))
            elif phase=='registered':
                ensure=asyncio.ensure_future
                def ensure_hook(*args,**kw):
                    task=ensure(*args,**kw);stop_once();return task
                stack.enter_context(patch.object(asyncio,'ensure_future',ensure_hook))
            elif phase=='finalizing':
                retire=cli._retire
                def retire_hook(*args):stop_once();return retire(*args)
                stack.enter_context(patch.object(cli,'_retire',retire_hook))
            elif phase=='asyncgens':
                create=asyncio.new_event_loop
                def create_hook():
                    loop=create();shutdown=loop.shutdown_asyncgens
                    async def ending():stop_once();await shutdown()
                    loop.shutdown_asyncgens=ending
                    return loop
                stack.enter_context(patch.object(asyncio,'new_event_loop',create_hook))
            elif phase=='report':
                report=cli._report
                def report_hook(result):
                    report(result)
                    if result.status=='published':stop_once()
                stack.enter_context(patch.object(cli,'_report',report_hook))
            values=[] if phase=='preflight' else [fx.PHONE] if phase in ('before_task','registered','completed') else [fx.PHONE,fx.CODE]
            before=signal.getsignal(signal.SIGINT)
            with stack:status,text=invoke(config,values)
            saved=phase in ('finalizing','asyncgens','report')
            assert fired[0] and status==130 and target.exists()==saved,(phase,status,text)
            assert signal.getsignal(signal.SIGINT)==before
            expected=0 if phase in ('preflight','before_task','registered') else 1
            assert s.calls.count('SendCodeRequest')==expected
            assert all(not w.up for w in s.wires)
            if saved:reopen(config,s);assert 'Saved session' in text
            no_secrets(text)
            print('STOP_PHASE',phase,'saved',saved,flush=True)


def test_terminal_results_and_stale_cancel_registration():
    for kind in ('value','error','cancelled','interrupt','task_interrupt'):
        loop=asyncio.new_event_loop();asyncio.set_event_loop(loop);before=signal.getsignal(signal.SIGINT)
        run=cli._TerminalRun(loop)
        try:
            calls=[];native=loop.run_until_complete
            def observe(future):calls.append(future.done());return native(future)
            loop.run_until_complete=observe
            if kind=='task_interrupt':
                async def interrupted():raise KeyboardInterrupt()
                factory=interrupted
            else:
                future=loop.create_future()
                if kind=='value':future.set_result(42)
                elif kind=='error':future.set_exception(LoginErrorForTest('fixture_error'))
                elif kind=='cancelled':future.cancel()
                else:future.set_exception(KeyboardInterrupt())
                factory=lambda:future
            try:
                value=run.drive(factory)
                assert kind=='value' and value==42
            except cli._Stopped:assert kind in ('cancelled','interrupt','task_interrupt')
            except LoginErrorForTest:assert kind=='error'
            assert not any(calls),'completed future was driven through loop'
            if kind!='task_interrupt':assert not calls
        finally:run.close()
        assert signal.getsignal(signal.SIGINT)==before
    # A queued callback for a retired action must not cancel explicit retirement.
    loop=asyncio.new_event_loop();asyncio.set_event_loop(loop);run=cli._TerminalRun(loop)
    try:
        old=loop.create_future();registration=dict(task=old,retire=False,queued=False,sent=False)
        run._active=registration;run._signal(signal.SIGINT,None)
        old.set_result('done');run._active=None
        async def cleanup():await asyncio.sleep(0);return 'settled'
        assert run.drive(cleanup,retire=True)=='settled'
        assert not registration['sent'] and run.stopped
    finally:run.close()


LoginErrorForTest=cli.LoginError


def test_stop_across_publication_effects():
    phases=('before_save','prepared','mutated','parent_sync','uncertain','cleanup','output')
    for existing in (False,True):
        for phase in phases:
            with fixture(existing=existing) as (config,s,root,target,previous):
                stack=__import__('contextlib').ExitStack();fired=[False];mutated=[False]
                def stop_once():
                    if not fired[0]:fired[0]=True;os.kill(os.getpid(),signal.SIGINT)
                if phase=='before_save':
                    publish=cli._publish
                    def before_save(*args):stop_once();return publish(*args)
                    stack.enter_context(patch.object(cli,'_publish',before_save))
                if phase=='prepared':
                    prepare=publication._prepare_candidate
                    def prepared(*args):prepare(*args);stop_once()
                    stack.enter_context(patch.object(publication,'_prepare_candidate',prepared))
                method='replace' if existing else 'link';mutate=getattr(os,method)
                def mutation(source,dest,*args,**kw):
                    result=mutate(source,dest,*args,**kw)
                    if Path(dest)==target:
                        mutated[0]=True
                        if phase=='mutated':stop_once()
                    return result
                stack.enter_context(patch.object(publication.os,method,mutation))
                if phase in ('parent_sync','uncertain'):
                    sync=publication._sync_directory
                    def synchronized(path):
                        if mutated[0] and Path(path)==root:
                            stop_once()
                            if phase=='uncertain':raise OSError(fx.PASSWORD)
                        return sync(path)
                    stack.enter_context(patch.object(publication,'_sync_directory',synchronized))
                if phase=='cleanup':
                    unlink=Path.unlink
                    def cleaned(path,*args,**kw):
                        if mutated[0]:stop_once()
                        return unlink(path,*args,**kw)
                    stack.enter_context(patch.object(Path,'unlink',cleaned))
                if phase=='output':
                    report=cli._report
                    def reporting(result):
                        report(result)
                        if result.status=='published':stop_once();raise BrokenPipeError('synthetic output failure')
                    stack.enter_context(patch.object(cli,'_report',reporting))
                with stack:status,text=invoke(config,[fx.PHONE,fx.CODE],[True] if existing else [],replace=existing)
                saved=phase not in ('before_save','prepared')
                assert fired[0] and status==130,(existing,phase,status,text)
                if saved:
                    value=SQLiteSession(str(target));assert value.auth_key.key==fx.KEY;value.close()
                    if phase=='uncertain':
                        assert 'publication is uncertain' in text
                        directories=list(root.glob('.tgdata-login-*'));assert len(directories)==1
                        if existing:assert (directories[0]/'previous.session').read_bytes()==previous
                    else:assert 'Saved session' in text
                elif existing:assert target.read_bytes()==previous
                else:assert not target.exists()
                assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
                no_secrets(text)
                print('PUBLICATION_STOP',existing,phase,flush=True)


def phase_child(scenario,release):
    two_factor=scenario.startswith('password_') or scenario=='native_srp'
    existing=scenario.startswith('replace_') or scenario.startswith('retry_')
    with fixture(two_factor=two_factor,existing=existing) as (config,s,root,target,previous):
        terminal_before=termios.tcgetattr(0);handler_before=signal.getsignal(signal.SIGINT)
        stack=__import__('contextlib').ExitStack();timers=[];active=[False];repeated=[False];retirement=[0]
        # Use actual inputs, restoring the fixture's deliberate no-console guard.
        stack.enter_context(patch('builtins.input',ORIGINAL_INPUT))
        stack.enter_context(patch.object(cli.getpass,'getpass',ORIGINAL_GETPASS))
        if scenario.endswith('_repeat') and not scenario.startswith(('replace_','retry_')):
            tcsetattr=termios.tcsetattr
            def restoring(fd,when,attrs):
                if attrs[3]&termios.ECHO and not repeated[0]:
                    repeated[0]=True;print('SIGNAL_DURING_INPUT_RESTORE',flush=True)
                    os.kill(os.getpid(),signal.SIGINT)
                return tcsetattr(fd,when,attrs)
            # Only arm repeated signal at the selected prompt, below.
            hidden=cli._hidden
            def selected_input(prompt):
                selected=(scenario.startswith('phone_') and prompt.startswith('Phone')) or (scenario.startswith('code_') and prompt.startswith('Telegram code')) or (scenario.startswith('password_') and prompt.startswith('Two-factor'))
                if selected:
                    with patch.object(termios,'tcsetattr',restoring):return hidden(prompt)
                return hidden(prompt)
            stack.enter_context(patch.object(cli,'_hidden',selected_input))
        if scenario.startswith(('replace_','retry_')) and scenario.endswith('_repeat'):
            confirm=cli._confirm
            def confirmation(prompt,expected='yes'):
                selected=('Retry saving' in prompt) if scenario.startswith('retry_') else ('Type REPLACE' in prompt)
                try:return confirm(prompt,expected)
                except KeyboardInterrupt:
                    if selected:repeated[0]=True;os.kill(os.getpid(),signal.SIGINT)
                    raise
            stack.enter_context(patch.object(cli,'_confirm',confirmation))
        if scenario.startswith('retry_'):
            stack.enter_context(patch.object(publication,'_prepare_candidate',side_effect=OSError('synthetic local failure')))
        if scenario=='validation':
            import tgdata.login as login_module
            phone=login_module._phone
            def validation(value):print('SIGNAL_IN_VALIDATION',flush=True);os.kill(os.getpid(),signal.SIGINT);return phone(value)
            stack.enter_context(patch.object(login_module,'_phone',validation))
        if scenario=='native_srp':
            import tgdata.login as login_module
            compute=login_module.srp.compute_check
            def computing(*args):
                in_compute=[True]
                def interrupt():
                    active[0]=in_compute[0];print('SIGNAL_NATIVE_SRP_ACTIVE='+str(active[0]),flush=True)
                    os.kill(os.getpid(),signal.SIGINT)
                timer=threading.Timer(0.002,interrupt);timers.append(timer);timer.start()
                try:return compute(*args)
                finally:in_compute[0]=False
            stack.enter_context(patch.object(login_module.srp,'compute_check',computing))
        async def hold():
            print('HOLD_CLEANUP',flush=True)
            while not release.exists():await asyncio.sleep(0.005)
        if scenario in ('connect_stop','cleanup_hold','auth_cleanup_hold','final_retire_hold','explicit_retire_hold'):
            if scenario=='connect_stop':
                async def connecting(w):
                    print('HOLD_CONNECT',flush=True);await asyncio.Future()
                s.connect_hook=connecting
            async def close(w):
                if scenario=='connect_stop':await hold()
                elif scenario=='cleanup_hold' and 'SendCodeRequest' in s.calls:await hold()
                elif scenario=='auth_cleanup_hold' and 'SignInRequest' in s.calls:await hold()
                elif scenario in ('final_retire_hold','explicit_retire_hold') and 'SignInRequest' in s.calls:
                    retirement[0]+=1
                    if retirement[0]==1:
                        if scenario=='final_retire_hold':os.kill(os.getpid(),signal.SIGINT)
                        raise OSError('synthetic cleanup failure')
                    await hold()
            s.close_hook=close
        try:
            with stack:status=cli.main(['--config',config]+(['--replace'] if existing else []))
        finally:
            for timer in timers:timer.join()
        assert status==130,(scenario,status)
        if existing:assert target.read_bytes()==previous
        else:assert not target.exists()
        assert all(not w.up for w in s.wires)
        assert signal.getsignal(signal.SIGINT)==handler_before
        after=termios.tcgetattr(0)
        assert after==terminal_before,(scenario,'terminal attributes changed')
        if scenario=='native_srp':assert active[0]
        if scenario.endswith('_repeat'):assert repeated[0]
        count=0 if scenario in ('phone_eof','phone_repeat','validation','connect_stop') else 1
        assert s.calls.count('SendCodeRequest')==count
        print('PHASE_RESULT '+json.dumps(dict(scenario=scenario,status=status,codes=count,terminal_restored=True)),flush=True)
        return status


def phase_terminal_case(scenario):
    import pty,fcntl
    with tempfile.TemporaryDirectory(prefix='login-phase-') as tmp:
        release=Path(tmp)/'release'
        master,slave=pty.openpty()
        def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
        process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--phase-child',scenario,str(release)],
            cwd=ROOT,stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,
            env=dict(os.environ,TMPDIR=tmp,PYTHONDONTWRITEBYTECODE='1'))
        os.close(slave);data=bytearray();deadline=time.monotonic()+15
        def wait(marker):
            while marker.encode() not in data:
                if time.monotonic()>deadline:raise AssertionError('phase timeout '+scenario+' '+data.decode(errors='replace'))
                ready,_,_=select.select([master],[],[],0.05)
                if ready:
                    try:block=os.read(master,65536)
                    except OSError:block=b''
                    if not block:raise AssertionError('phase ended '+scenario+' '+data.decode(errors='replace'))
                    data.extend(block)
        def stop_input():
            if scenario.endswith('_eof'):os.write(master,b'\x04')
            else:os.kill(process.pid,signal.SIGINT)
        try:
            wait('Phone number with country code (hidden):')
            if scenario.startswith('phone_'):stop_input()
            else:
                os.write(master,(fx.PHONE+'\n').encode())
                if scenario=='connect_stop':wait('HOLD_CONNECT');os.kill(process.pid,signal.SIGINT)
                if scenario in ('connect_stop','cleanup_hold'):
                    wait('HOLD_CLEANUP');os.kill(process.pid,signal.SIGINT)
                    time.sleep(0.03);assert process.poll() is None
                    os.kill(process.pid,signal.SIGINT);release.write_text('release')
                elif scenario!='validation':
                    wait('Telegram code (hidden):')
                    if scenario.startswith('code_'):stop_input()
                    else:
                        os.write(master,(fx.CODE+'\n').encode())
                        if scenario.startswith('password_') or scenario=='native_srp':
                            wait('Two-factor password (hidden):')
                            if scenario.startswith('password_'):stop_input()
                            else:os.write(master,(fx.PASSWORD+'\n').encode())
                        elif scenario.startswith(('replace_','retry_')):
                            wait('Type REPLACE:')
                            if scenario.startswith('replace_'):stop_input()
                            else:
                                os.write(master,b'REPLACE\n');wait('Retry saving this completed login');stop_input()
                        elif scenario in ('auth_cleanup_hold','final_retire_hold','explicit_retire_hold'):
                            wait('HOLD_CLEANUP');os.kill(process.pid,signal.SIGINT)
                            time.sleep(0.03);assert process.poll() is None
                            os.kill(process.pid,signal.SIGINT);release.write_text('release')
            wait('PHASE_RESULT');code=process.wait(timeout=4)
            text=data.decode(errors='replace');no_secrets(text)
            assert code==130,(scenario,code,text)
            print('PTY_PHASE',scenario,'terminal restored; exit130',flush=True)
        finally:
            if process.poll() is None:process.kill();process.wait(timeout=4)
            os.close(master)


def test_real_phase_terminal_matrix():
    for scenario in ('phone_eof','phone_repeat','code_eof','code_repeat','password_eof','password_repeat',
                     'replace_eof','replace_repeat','retry_eof','retry_repeat','validation','native_srp',
                     'connect_stop','cleanup_hold','auth_cleanup_hold','explicit_retire_hold','final_retire_hold'):
        phase_terminal_case(scenario)
