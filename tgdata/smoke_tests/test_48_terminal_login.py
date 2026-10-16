"""Offline terminal login: real SDK/SRP/native files and controlled terminal children."""
import asyncio
import base64
import builtins
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
import telethon
from telethon import errors,functions,types
from telethon.crypto import AuthKey
from telethon.sessions import SQLiteSession
import tgdata
from tgdata.connection_engine import ConnectionEngine
from tgdata.smoke_tests import test_41_stepwise_login as fx


from tgdata import login_file as publication
from tgdata import login_cli as cli
ORIGINAL_INPUT=builtins.input
ORIGINAL_GETPASS=cli.getpass.getpass


class Terminal(io.StringIO):
    def isatty(self):return True


def old_session(path):
    value=SQLiteSession(str(path));value.set_dc(2,'149.154.167.51',443)
    value.auth_key=AuthKey(fx.OTHER);value.save();value.close()
    return path.read_bytes()


@contextmanager
def fixture(*,two_factor=False,existing=False,no_hash=False):
    with fx.fixture(two_factor) as (config,service), tempfile.TemporaryDirectory(prefix='login-output-') as out:
        root=Path(out).resolve(); target=root/'account.session'
        path=Path(config)
        path.write_text(path.read_text().replace(str(path.parent/'do-not-open'),str(root/'account')))
        if no_hash:service.user.access_hash=None
        previous=old_session(target) if existing else None
        yield config,service,root,target,previous


def invoke(config,values=(),confirmations=(),replace=False,tty=True):
    entered=iter(values);accepted=iter(confirmations)
    output=io.StringIO()
    def hidden(prompt):
        try:return next(entered)
        except StopIteration:raise AssertionError('unexpected input '+prompt)
    def confirm(prompt,expected='yes'):
        try:return next(accepted)
        except StopIteration:raise AssertionError('unexpected confirmation '+prompt)
    stream=Terminal() if tty else io.StringIO()
    with patch.object(sys,'stdin',stream),patch.object(cli,'_hidden',hidden), \
         patch.object(cli,'_confirm',confirm),redirect_stdout(output),redirect_stderr(output):
        status=cli.main(['--config',config]+(['--replace'] if replace else []))
    return status,output.getvalue()


def reopen(config,service,expected=4242):
    async def verify():
        engine=ConnectionEngine(config,interactive_login=False)
        original=engine._new_client
        def make(*args,**kw):
            client=original(*args,**kw);client._sender=fx.Wire(client,service)
            service.clients.append(client);service.wires.append(client._sender)
            return client
        engine._new_client=make
        async with engine._account_operation(expected) as op:
            assert op.account_id==expected
            assert op.client.session.auth_key.key==fx.KEY
            assert op.client.session.get_entity_rows_by_id(0)==(0,expected)
    asyncio.run(verify())


def no_secrets(text):
    for value in (fx.PHONE,fx.CODE,fx.PASSWORD,fx.HASH,base64.b64encode(fx.KEY).decode()):
        assert value not in text, 'secret appeared in output'


def test_native_reopen_and_optional_cache():
    for two_factor,no_hash in ((False,False),(True,False),(False,True)):
        with fixture(two_factor=two_factor,no_hash=no_hash) as (config,s,root,target,previous):
            values=[fx.PHONE,fx.CODE]+([fx.PASSWORD] if two_factor else [])
            status,text=invoke(config,values)
            assert status==0,(status,text)
            assert stat.S_IMODE(target.stat().st_mode)==0o600
            assert not list(root.glob('.tgdata-login-*'))
            before=s.calls.count('SendCodeRequest');reopen(config,s)
            assert s.calls.count('SendCodeRequest')==before==1
            assert s.calls.count('SignInRequest')==1
            if two_factor:assert s.srp_accepted==1
            no_secrets(text)
    print('native file + normal reader: plain, SRP and missing access_hash PASS')


def test_new_existing_and_replacement():
    with fixture(existing=True) as (config,s,root,target,previous):
        status,text=invoke(config)
        assert status==2 and not s.calls and target.read_bytes()==previous
        status,text=invoke(config,[fx.PHONE,fx.CODE],[False],replace=True)
        assert status==130 and target.read_bytes()==previous
        # A new controlled service is required for a new synthetic challenge.
    with fixture(existing=True) as (config,s,root,target,previous):
        status,text=invoke(config,[fx.PHONE,fx.CODE],[True],replace=True)
        assert status==0 and target.read_bytes()!=previous
        assert not list(root.glob('.tgdata-login-*'));reopen(config,s);no_secrets(text)


def test_invalid_inputs_wait_and_unsupported():
    with fixture() as (config,s,root,target,previous):
        status,text=invoke(config,['bad phone',fx.PHONE,'99999',fx.CODE])
        assert status==0 and s.calls.count('SendCodeRequest')==1 and s.calls.count('SignInRequest')==2
    for response in ('wait','unsupported','setup'):
        with fixture() as (config,s,root,target,previous):
            def hook(w,r):
                if not isinstance(r,functions.auth.SendCodeRequest):return NotImplemented
                if response=='wait':return errors.FloodWaitError(r,capture=20)
                if response=='unsupported':return types.auth.SentCodePaymentRequired('p',fx.HASH,'x','y',1,'USD',1)
                s.authorized.add(w.auth_key.key)
                return types.auth.SentCodeSuccess(types.auth.Authorization(s.user,setup_password_required=True,otherwise_relogin_days=7))
            s.hook=hook
            status,text=invoke(config,[fx.PHONE])
            assert status==3 and not target.exists() and s.calls.count('SendCodeRequest')==1
            no_secrets(text)


def test_uncertain_check_without_replaying_code():
    with fixture() as (config,s,root,target,previous):
        def hook(w,r):
            if isinstance(r,functions.auth.SignInRequest):
                s.answer(w,r)
                return OSError(fx.PASSWORD)
            return NotImplemented
        s.hook=hook
        status,text=invoke(config,[fx.PHONE,fx.CODE],[True])
        assert status==0,(status,text)
        assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
        reopen(config,s);no_secrets(text)


def test_local_retry_never_authenticates_again():
    with fixture(existing=True) as (config,s,root,target,previous):
        original=publication._prepare_candidate;calls=[]
        def fail_once(*args):
            calls.append(1)
            assert target.read_bytes()==previous
            if len(calls)==1:raise OSError(fx.PASSWORD)
            return original(*args)
        with patch.object(publication,'_prepare_candidate',fail_once):
            status,text=invoke(config,[fx.PHONE,fx.CODE],[True,True],replace=True)
        assert status==0 and len(calls)==2,(status,text)
        assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
        reopen(config,s);no_secrets(text)


def test_preflight_sidecar_symlink_and_missing_tty():
    for kind in ('sidecar','symlink','directory','no_tty'):
        with fixture() as (config,s,root,target,previous):
            if kind=='sidecar':Path(str(target)+'-wal').write_bytes(b'preserve')
            if kind=='symlink':target.symlink_to(root/'missing')
            if kind=='directory':target.mkdir()
            status,text=invoke(config,replace=True,tty=kind!='no_tty')
            assert status==2 and not s.calls,(kind,status,text)
            assert not list(root.glob('.tgdata-login-*'))


def test_changed_and_appeared_destination():
    for existing in (False,True):
        with fixture(existing=existing) as (config,s,root,target,previous):
            def hook(w,r):
                if isinstance(r,functions.auth.SignInRequest):target.write_bytes(b'changed during input')
                return NotImplemented
            s.hook=hook
            status,text=invoke(config,[fx.PHONE,fx.CODE],[True] if existing else [],replace=existing)
            assert status==4 and target.read_bytes()==b'changed during input'
            assert 'destination_changed' in text and s.calls.count('SendCodeRequest')==1


def test_prepublication_barriers_preserve_old_bytes():
    for fault in ('stage_parent','backup_file','backup_directory'):
        with fixture(existing=True) as (config,s,root,target,previous):
            syncdir=publication._sync_directory;syncfile=publication._sync_file
            def directory(path):
                if fault=='stage_parent' and Path(path)==root:raise OSError('parent sync')
                if fault=='backup_directory' and (Path(path)/'previous.session').exists():raise OSError('backup sync')
                return syncdir(path)
            def file(path):
                if fault=='backup_file' and Path(path).name=='previous.session':raise OSError('old bytes sync')
                return syncfile(path)
            with patch.object(publication,'_sync_directory',directory),patch.object(publication,'_sync_file',file):
                status,text=invoke(config,[fx.PHONE,fx.CODE] if fault!='stage_parent' else [],
                                   [True,False] if fault!='stage_parent' else [],replace=True)
            assert status==(2 if fault=='stage_parent' else 4),(fault,status,text)
            assert target.read_bytes()==previous
            assert s.calls.count('SendCodeRequest')==(0 if fault=='stage_parent' else 1)


def test_post_replace_uncertainty_retains_old_backup():
    with fixture(existing=True) as (config,s,root,target,previous):
        syncdir=publication._sync_directory;rename=os.replace;switched=[False];events=[]
        def directory(path):
            events.append(('sync',str(path)))
            if switched[0] and Path(path)==root:raise OSError('post-publication '+fx.PASSWORD)
            return syncdir(path)
        def replace(source,destination):
            if Path(destination)==target:
                recovery=Path(source).parent
                assert ('sync',str(root)) in events
                assert ('sync',str(recovery)) in events
                assert (recovery/'previous.session').read_bytes()==previous
                events.append(('replace',str(target)))
                rename(source,destination);switched[0]=True
            else:rename(source,destination)
        with patch.object(publication,'_sync_directory',directory),patch.object(publication.os,'replace',replace):
            status,text=invoke(config,[fx.PHONE,fx.CODE],[True],replace=True)
        assert status==5 and switched[0],(status,text)
        directories=list(root.glob('.tgdata-login-*'));assert len(directories)==1
        assert (directories[0]/'previous.session').read_bytes()==previous
        assert stat.S_IMODE(directories[0].stat().st_mode)==0o700
        assert target.read_bytes()!=previous
        no_secrets(text)


def test_native_commit_and_close_failures_retire_connections():
    for fault in ('save','close'):
        with fixture(existing=True) as (config,s,root,target,previous):
            originals={name:getattr(SQLiteSession,name) for name in ('save','close')};connections=[]
            def broken(session):
                if 'candidate-' in session.filename:
                    if session._conn is not None:connections.append(session._conn)
                    raise OSError('native '+fx.PASSWORD)
                return originals[fault](session)
            with patch.object(SQLiteSession,fault,broken):
                status,text=invoke(config,[fx.PHONE,fx.CODE],[True,False],replace=True)
            assert status==4 and target.read_bytes()==previous,(fault,status,text)
            assert connections
            for connection in connections:
                try:connection.execute('select 1')
                except Exception as error:assert type(error).__name__=='ProgrammingError'
                else:raise AssertionError('native connection left open')
            no_secrets(text)


def test_output_failure_does_not_reverse_saved_state():
    with fixture() as (config,s,root,target,previous):
        say=cli._say
        def broken(text):
            if text.startswith('Saved session'):raise BrokenPipeError('output')
            return say(text)
        with patch.object(cli,'_say',broken):status,text=invoke(config,[fx.PHONE,fx.CODE])
        assert status==0 and target.exists(),(status,text)
        reopen(config,s)


def test_no_echo_fallback_and_redacted_arguments():
    with warnings_context(),patch.object(cli.getpass,'_raw_input',side_effect=AssertionError('echo input')):
        try:cli.getpass.fallback_getpass('secret')
        except cli.getpass.GetPassWarning:pass
        else:raise AssertionError('echo fallback allowed')
    output=io.StringIO()
    with redirect_stdout(output),redirect_stderr(output):
        try:cli.main(['--password',fx.PASSWORD])
        except SystemExit as error:assert error.code==2
        else:raise AssertionError('secret argument accepted')
    no_secrets(output.getvalue())


def test_config_name_precedence_and_working_directory():
    for kind in ('explicit','legacy','tilde'):
        with fixture() as (config,s,root,target,previous):
            path=Path(config);text=path.read_text()
            for line in text.splitlines():
                if line.startswith('session_file='):text=text.replace(line,'')
            if kind=='explicit':
                text+='\nsession_file="relative-account"\nusername=unused\n'
                target=root/'relative-account.session'
            elif kind=='legacy':
                text+='\nusername=legacy-account\n';target=root/'legacy-account.session'
            else:
                (root/'~').mkdir();text+='\nsession_file=~/literal-account\n'
                target=root/'~'/'literal-account.session'
            path.write_text(text);before=Path.cwd()
            try:
                os.chdir(root)
                status,text=invoke(config,[fx.PHONE,fx.CODE])
                assert status==0 and target.exists(),(kind,status,text)
                assert not (path.parent/target.name).exists()
                reopen(config,s)
            finally:os.chdir(before)


def test_last_moment_no_clobber_collision():
    with fixture() as (config,s,root,target,previous):
        link=os.link;created=[False]
        def race(source,destination,*args,**kwargs):
            if Path(destination)==target:
                target.write_bytes(b'other publisher');created[0]=True
            return link(source,destination,*args,**kwargs)
        with patch.object(publication.os,'link',race):
            status,text=invoke(config,[fx.PHONE,fx.CODE])
        assert status==4 and created[0] and target.read_bytes()==b'other publisher'
        assert 'destination_changed' in text and 'uncertain' not in text


def test_cleanup_failure_preserves_confirmed_publication():
    with fixture(existing=True) as (config,s,root,target,previous):
        unlink=Path.unlink
        def fail_backup(path,*args,**kwargs):
            if path.name=='previous.session':raise OSError('private cleanup detail')
            return unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail_backup):
            status,text=invoke(config,[fx.PHONE,fx.CODE],[True],replace=True)
        assert status==0 and 'Saved session' in text and 'cleanup failed' in text
        roots=list(root.glob('.tgdata-login-*'));assert len(roots)==1
        assert (roots[0]/'previous.session').read_bytes()==previous
        assert target.read_bytes()!=previous
        reopen(config,s)


def test_module_entry_help_and_headless_refusal():
    with tempfile.TemporaryDirectory() as directory:
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
        help_result=subprocess.run([sys.executable,'-m','tgdata.login_cli','--help'],
            cwd=directory,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10)
        assert help_result.returncode==0 and '--replace' in help_result.stdout
        refuse=subprocess.run([sys.executable,'-m','tgdata.login_cli','--config','missing.ini'],
            cwd=directory,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10)
        assert refuse.returncode==2 and 'interactive terminal' in refuse.stderr
        assert not list(Path(directory).iterdir())


@contextmanager
def warnings_context():
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('error',cli.getpass.GetPassWarning)
        yield


def test_real_flow_cleanup_retry_and_secret_logs():
    output=io.StringIO();handler=logging.StreamHandler(output);rootlog=logging.getLogger()
    old_level=rootlog.level;rootlog.setLevel(logging.DEBUG);rootlog.addHandler(handler)
    try:
        with fixture() as (config,s,root,target,previous):
            failures=[0]
            async def once(wire):
                if 'SignInRequest' in s.calls and failures[0]==0:
                    failures[0]+=1
                    raise OSError(fx.PASSWORD+fx.HASH)
            s.close_hook=once
            status,text=invoke(config,[fx.PHONE,fx.CODE])
            assert status==0 and failures[0]==1,(status,text)
            assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
            assert all(not w.up for w in s.wires)
            no_secrets(text+output.getvalue())
    finally:
        rootlog.removeHandler(handler);rootlog.setLevel(old_level)


def child(scenario):
    with fixture(two_factor=scenario=='password',existing=scenario=='replace') as (config,s,root,target,previous):
        if scenario=='source_stop':
            async def held(wire,request):
                if isinstance(request,functions.auth.SendCodeRequest):
                    print('WAIT_SOURCE',flush=True)
                    await asyncio.Future()
                return NotImplemented
            async def close(wire):
                print('WAIT_CLEANUP',flush=True)
                await asyncio.sleep(0.25)
            s.hook=held;s.close_hook=close
        link=os.link;prepare=publication._prepare_candidate
        def interrupted_link(source,destination,*args,**kwargs):
            result=link(source,destination,*args,**kwargs)
            if scenario=='during_publish' and Path(destination)==target:
                os.kill(os.getpid(),signal.SIGINT)
            return result
        def interrupted_prepare(*args):
            result=prepare(*args)
            if scenario=='before_publish':os.kill(os.getpid(),signal.SIGINT)
            return result
        with patch('builtins.input',ORIGINAL_INPUT),patch.object(cli.getpass,'getpass',ORIGINAL_GETPASS), \
             patch.object(publication.os,'link',interrupted_link), \
             patch.object(publication,'_prepare_candidate',interrupted_prepare):
            status=cli.main(['--config',config]+(['--replace'] if scenario=='replace' else []))
        expected=0 if scenario in ('plain','password','replace') else 130
        assert status==expected,(scenario,status)
        saved=scenario in ('plain','password','replace','during_publish')
        assert target.exists()==saved
        if saved:reopen(config,s)
        assert all(not w.up for w in s.wires)
        count=0 if scenario=='input_stop' else 1
        assert s.calls.count('SendCodeRequest')==count
        print('CHILD_RESULT '+json.dumps(dict(scenario=scenario,status=status,saved=saved,codes=count)),flush=True)
        return status


def terminal_case(scenario):
    import pty,fcntl,termios
    master,slave=pty.openpty()
    def own_terminal():
        os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',scenario],
        cwd=ROOT,stdin=slave,stdout=slave,stderr=slave,preexec_fn=own_terminal,env=env)
    os.close(slave);data=bytearray();deadline=time.monotonic()+15
    def wait_for(marker):
        encoded=marker.encode()
        while encoded not in data:
            if time.monotonic()>deadline:raise AssertionError('TTY timeout '+scenario+' '+data.decode(errors='replace'))
            ready,_,_=select.select([master],[],[],0.1)
            if ready:
                try:block=os.read(master,65536)
                except OSError:block=b''
                if not block:raise AssertionError('TTY ended '+scenario+' '+data.decode(errors='replace'))
                data.extend(block)
        return data.decode(errors='replace')
    try:
        wait_for('Phone number with country code (hidden):')
        if scenario=='input_stop':
            os.kill(process.pid,signal.SIGINT)
        else:
            os.write(master,(fx.PHONE+'\n').encode())
            if scenario=='source_stop':
                wait_for('WAIT_SOURCE');os.kill(process.pid,signal.SIGINT)
                wait_for('WAIT_CLEANUP');os.kill(process.pid,signal.SIGINT)
                time.sleep(0.03);os.kill(process.pid,signal.SIGINT)
            else:
                wait_for('Telegram code (hidden):')
                if scenario=='code_eof':os.write(master,b'\x04')
                else:
                    os.write(master,(fx.CODE+'\n').encode())
                    if scenario=='password':
                        wait_for('Two-factor password (hidden):');os.write(master,(fx.PASSWORD+'\n').encode())
                    if scenario=='replace':
                        wait_for('Type REPLACE:');os.write(master,b'REPLACE\n')
        wait_for('CHILD_RESULT')
        code=process.wait(timeout=4)
        text=data.decode(errors='replace')
        no_secrets(text)
        assert code==(0 if scenario in ('plain','password','replace') else 130),(scenario,code,text)
        print('PTY',scenario,'exit',code,'secret echo absent',flush=True)
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=4)
        os.close(master)


def test_real_terminal_composition():
    for scenario in ('plain','password','replace','input_stop','code_eof','source_stop','before_publish','during_publish'):
        terminal_case(scenario)


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

def test_review_source_and_storage_histories():
 from datetime import datetime, timezone
 from types import SimpleNamespace
 t=sys.modules[__name__]
 f=publication
 def record(name,details):print('REVIEW_HISTORY',name,json.dumps(details),flush=True)
 def unchanged(target,previous):
  assert target.read_bytes()==previous if previous is not None else not target.exists()
 # Source results and actual SRP, independent of the implementation's test list.
 for mode in ('expired','phone_reply_lost','code_retry','code_loss_twice','wrong_password','migration'):
  with t.fixture(two_factor=mode=='wrong_password') as (config,s,root,target,previous):
   seen=[0]
   def hook(w,r):
    if mode=='expired' and isinstance(r,functions.auth.SignInRequest):return errors.PhoneCodeExpiredError(r)
    if mode=='phone_reply_lost' and isinstance(r,functions.auth.SendCodeRequest):
     s.answer(w,r);return OSError(t.fx.PASSWORD)
    if mode in ('code_retry','code_loss_twice') and isinstance(r,functions.auth.SignInRequest):
     seen[0]+=1
     if seen[0]==1 or mode=='code_loss_twice':return OSError(t.fx.PASSWORD)
    if mode=='migration' and isinstance(r,functions.auth.SendCodeRequest) and w.client.session.dc_id!=3:
     return errors.PhoneMigrateError(r,capture=3)
    return NotImplemented
   s.hook=hook
   values=[t.fx.PHONE,t.fx.CODE]
   if mode=='phone_reply_lost':values=[t.fx.PHONE]
   if mode in ('code_retry','code_loss_twice'):values.append(t.fx.CODE)
   if mode=='wrong_password':values.extend(['incorrect-private-password',t.fx.PASSWORD])
   confirms=[True] if mode in ('phone_reply_lost','code_retry','code_loss_twice') else []
   status,text=t.invoke(config,values,confirms)
   expected=3 if mode in ('expired','phone_reply_lost','code_loss_twice') else 0
   assert status==expected,(mode,status,text)
   assert target.exists()==(expected==0)
   assert s.calls.count('SendCodeRequest')==(2 if mode=='migration' else 1)
   if mode=='wrong_password':assert s.calls.count('CheckPasswordRequest')==2 and s.srp_accepted==1
   if mode=='code_loss_twice':assert s.calls.count('SignInRequest')==2
   if mode=='migration':
    native=SQLiteSession(str(target));assert native.dc_id==3 and native.auth_key.key==t.fx.OTHER;native.close()
    async def reader():
     engine=ConnectionEngine(config,interactive_login=False);original=engine._new_client
     def make(*args,**kwargs):
      client=original(*args,**kwargs);client._sender=t.fx.Wire(client,s);s.clients.append(client);s.wires.append(client._sender);return client
     engine._new_client=make
     async with engine._account_operation(4242) as op:assert op.client.session.auth_key.key==t.fx.OTHER
    asyncio.run(reader())
   elif expected==0:t.reopen(config,s)
   t.no_secrets(text)
   record(mode,dict(exit=status,saved=target.exists(),codes=s.calls.count('SendCodeRequest'),signins=s.calls.count('SignInRequest')))

 # Sidecars appearing after actual native candidate preparation, including dangling links.
 for suffix in ('-wal','-shm','-journal'):
  with t.fixture(existing=True) as (config,s,root,target,previous):
   prepare=f._prepare_candidate
   def late(*args):
    prepare(*args);Path(str(target)+suffix).symlink_to(root/'absent-sidecar')
   with patch.object(f,'_prepare_candidate',late):status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],[True],replace=True)
   assert status==4 and 'sqlite_sidecar_present' in text
   unchanged(target,previous);assert Path(str(target)+suffix).is_symlink();t.no_secrets(text)
   record('late_'+suffix,dict(exit=status,old_bytes_preserved=True))

 # Real syscall effects followed by failures; no implicit retry/rollback.
 for existing in (False,True):
  for effect in (False,True):
   with t.fixture(existing=existing) as (config,s,root,target,previous):
    operation='replace' if existing else 'link';original=getattr(os,operation)
    def fault(source,dest,*args,**kwargs):
     if Path(dest)==target:
      if effect:original(source,dest,*args,**kwargs)
      raise OSError(t.fx.PASSWORD)
     return original(source,dest,*args,**kwargs)
    with patch.object(f.os,operation,fault):status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],[True] if existing else [],replace=existing)
    assert status==5 and 'publication is uncertain' in text
    recovery=list(root.glob('.tgdata-login-*'));assert len(recovery)==1
    if existing:assert (recovery[0]/'previous.session').read_bytes()==previous
    if not effect:unchanged(target,previous)
    else:
     native=SQLiteSession(str(target));assert native.auth_key.key==t.fx.KEY;native.close()
    assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
    t.no_secrets(text)
    record(operation+('_after_effect' if effect else '_before_effect'),dict(exit=status,recovery_retained=True,effect=effect))

 # A second local attempt does not authorize a replacement of a changed target.
 with t.fixture(existing=True) as (config,s,root,target,previous):
  prepare=f._prepare_candidate;count=[0]
  def first(*args):
   count[0]+=1
   if count[0]==1:raise OSError(t.fx.PASSWORD)
   return prepare(*args)
  confirmations=[0]
  def confirm(prompt,expected='yes'):
   confirmations[0]+=1
   if confirmations[0]==2:target.write_bytes(b'new independent destination')
   return True
  with patch.object(f,'_prepare_candidate',first),patch.object(t.cli,'_confirm',confirm):
   # invoke patches confirm itself; use a local iterator with side effect instead.
   class Answers:
    def __iter__(self):return self
    def __next__(self):return confirm('')
   status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],Answers(),replace=True)
  assert status==4 and target.read_bytes()==b'new independent destination' and count[0]==1
  assert s.calls.count('SendCodeRequest')==s.calls.count('SignInRequest')==1
  record('retry_refuses_changed_target',dict(exit=status,candidate_attempts=count[0],codes=1))

 # Real native constructor opens a connection and fails; it must be retired.
 with t.fixture(existing=True) as (config,s,root,target,previous):
  original=SQLiteSession.__init__;connections=[]
  def broken(value,*args,**kwargs):
   original(value,*args,**kwargs)
   if 'candidate-' in value.filename:
    connections.append(value._conn);raise OSError(t.fx.PASSWORD)
  with patch.object(SQLiteSession,'__init__',broken):status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],[True,False],replace=True)
  assert status==4;unchanged(target,previous);assert connections
  for conn in connections:
   try:conn.execute('select 1')
   except Exception as e:assert type(e).__name__=='ProgrammingError'
   else:raise AssertionError('constructor connection remains open')
  t.no_secrets(text);record('constructor_failure_retired',dict(exit=status,connections=len(connections)))

 # LoginFlow naturally completes without own hash; add available native state at the source boundary.
 with t.fixture(no_hash=True) as (config,s,root,target,previous):
  def state(w,r):
   if isinstance(r,functions.auth.SignInRequest):
    w.client._message_box.load(SimpleNamespace(pts=123,qts=456,date=datetime(2026,10,16,1,2,3,123456,tzinfo=timezone.utc).timestamp(),seq=789),[])
    w.client.session.takeout_id=2**62+19
   return NotImplemented
  s.hook=state
  status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE]);assert status==0
  native=SQLiteSession(str(target));v=native.get_update_state(0)
  # Native disconnect exports the real message-box state into the completed credential.
  assert native.takeout_id==2**62+19 and native.get_entity_rows_by_id(4242) is None
  assert v is not None and v.pts==123 and v.date.microsecond==123456
  native.close();t.reopen(config,s);t.no_secrets(text)
  record('available_state_and_optional_hash',dict(exit=status,fractional_date=True,takeout_exact=True))

 # Failed retirement after known authorization blocks publication even on repeated failures.
 with t.fixture(existing=True) as (config,s,root,target,previous):
  async def bad_close(w):
   if 'SignInRequest' in s.calls:raise OSError(t.fx.PASSWORD)
  s.close_hook=bad_close
  try:
   status,text=t.invoke(config,[t.fx.PHONE,t.fx.CODE],replace=True)
   assert status==3;unchanged(target,previous);assert s.calls.count('SignInRequest')==1
   t.no_secrets(text);record('unsettled_auth_not_published',dict(exit=status,old_bytes_preserved=True,signins=1))
  finally:
   s.close_hook=None
   async def cleanup():
    for wire in s.wires:
     if wire.up:await wire.disconnect()
   asyncio.run(cleanup())


def main():
    assert telethon.__version__=='1.45.0'
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1 and sys.argv[1]=='--phase-child':return phase_child(sys.argv[2],Path(sys.argv[3]))
        if len(sys.argv)>1 and sys.argv[1]=='--child':return child(sys.argv[2])
        tests=sorted((n,f) for n,f in globals().items() if n.startswith('test_'))
        failed=0
        for name,test in tests:
            try:
                test();print('PASS',name,flush=True)
            except BaseException:
                failed+=1;print('FAIL',name,flush=True);traceback.print_exc()
    print('{} passed; {} failed'.format(len(tests)-failed,failed),flush=True)
    return bool(failed)


if __name__=='__main__':
    raise SystemExit(main())
