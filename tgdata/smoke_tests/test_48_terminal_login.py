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


def main():
    assert telethon.__version__=='1.45.0'
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
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
