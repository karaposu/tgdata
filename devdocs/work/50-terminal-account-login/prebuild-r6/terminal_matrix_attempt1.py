"""Whole candidate CLI under actual terminals; source transport only is controlled."""
import contextlib, fcntl, json, os, pty, select, signal, socket, subprocess, sys, tempfile, termios, time
from pathlib import Path
from unittest.mock import patch
import combined_suite as base
cli=base.cli; ti=base.terminal_input; fx=base.fx
HERE=Path(__file__).resolve().parent
PROMPTS={'phone':'Phone number with country code (hidden):','code':'Telegram code (hidden):',
 'password':'Two-factor password (hidden):','replace':'Type REPLACE:','retry':'Retry saving this completed login'}
FIRST=['first_'+p+'_'+end for p in PROMPTS for end in ('normal','eof')]
MODES=FIRST+['after_restore_normal','after_restore_eof']+['stop_'+p for p in ('acquire','snapshot','hidden','wait','read','flush','close')]+[
 'fault_acquire','fault_snapshot','fault_apply_before','fault_apply_after','fault_wait','fault_read',
 'fault_flush','fault_restore','fault_restore_stop','fault_restore_after','fault_readback','fault_close','fault_output',
 'unicode','editing','limit128','limit129','kernel_overflow','invalid_utf8','partial_eof','typeahead',
 'two_terminals','no_controlling','background','noncanonical','istrip','istrip_afterphone','bad_cr','small_canon','no_termios','echo_off']


def child(mode):
    if mode=='background':
        pid=os.fork()
        if pid:
            unused,status=os.waitpid(pid,0)
            return os.waitstatus_to_exitcode(status)
        os.setpgid(0,0)
    original_stdin=termios.tcgetattr(0)
    control=None
    try:
        if mode!='no_controlling':control=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        original_control=None if control is None else termios.tcgetattr(control)
        attrs=termios.tcgetattr(control) if control is not None else None
        if mode=='noncanonical':attrs[3]&=~termios.ICANON
        if mode=='istrip':attrs[0]|=termios.ISTRIP
        if mode=='bad_cr':attrs[0]|=termios.IGNCR
        if mode=='echo_off':attrs[3]&=~(termios.ECHO|termios.ECHONL)
        if attrs is not None:termios.tcsetattr(control,termios.TCSANOW,attrs)
        before_control=termios.tcgetattr(control) if control is not None else None
        before_stdin=termios.tcgetattr(0)
        phase=mode.split('_')[1] if mode.startswith('first_') else 'phone'
        two_factor=phase=='password'
        existing=phase in ('replace','retry')
        state=dict(selected=False, fd=None, fired=False, restored=False, reads=0, value=False, two_observed=False)
        original_handler=signal.getsignal(signal.SIGINT)
        native={n:getattr(os,n) for n in ('open','close','read','fpathconf')}
        get=termios.tcgetattr;put=termios.tcsetattr;flush=termios.tcflush;wait=select.select
        def fire():
            state['fired']=True;os.kill(os.getpid(),signal.SIGINT)
        def opening(path,*args,**kw):
            if state['selected'] and path=='/dev/tty' and mode=='fault_acquire':
                state['fired']=True;raise OSError('synthetic input error')
            fd=native['open'](path,*args,**kw)
            if state['selected'] and path=='/dev/tty':
                state['fd']=fd
                if mode=='stop_acquire':fire()
            return fd
        def getting(fd):
            target=state['selected'] and fd==state['fd']
            if target and mode=='fault_snapshot' and not state['fired']:
                state['fired']=True;raise OSError('snapshot')
            result=get(fd)
            if target and mode=='stop_snapshot' and not state['fired']:fire()
            if target and mode=='fault_readback' and state['restored']:
                state['fired']=True;result[3]^=termios.ECHO
            return result
        def setting(fd,when,settings):
            target=state['selected'] and fd==state['fd']
            restoring=target and settings==before_control
            hiding=target and not restoring
            if hiding and mode=='fault_apply_before':
                state['fired']=True;raise OSError('apply-before')
            if restoring and not state['fired']:
                if mode.startswith('first_'):fire()
                if mode in ('fault_restore','fault_restore_stop'):
                    state['fired']=True
                    if mode.endswith('_stop'):fire()
                    raise OSError('restore')
            result=put(fd,when,settings)
            if hiding:
                if mode=='fault_apply_after':state['fired']=True;raise OSError('apply-after')
                if mode=='stop_hidden':fire()
                if mode=='two_terminals':
                    assert not get(control)[3]&termios.ECHO and get(0)[3]&termios.ECHO
                    state['two_observed']=True
            if restoring:
                state['restored']=True
                if mode.startswith('after_restore_'):fire()
                if mode=='fault_restore_after':state['fired']=True;raise OSError('restore-after')
            return result
        def flushing(fd,queue):
            if state['selected'] and fd==state['fd']:
                if mode=='stop_flush':fire()
                if mode=='fault_flush':state['fired']=True;raise OSError('flush')
            return flush(fd,queue)
        def closing(fd):
            target=state['selected'] and fd==state['fd']
            result=native['close'](fd)
            if target:
                if mode=='stop_close':fire()
                if mode=='fault_close':state['fired']=True;raise OSError('close-after-effect')
            return result
        def waiting(r,w,x,timeout=None):
            if state['selected'] and state['fd'] in r:
                if mode=='stop_wait':fire()
                if mode=='fault_wait':state['fired']=True;raise OSError('wait')
            return wait(r,w,x,timeout)
        def reading(fd,count):
            target=state['selected'] and fd==state['fd']
            if target and mode=='fault_read':state['fired']=True;raise OSError('read')
            result=native['read'](fd,count)
            if target and mode=='stop_read':fire()
            return result
        with base.fixture(two_factor=two_factor,existing=existing) as (config,service,root,target,previous):
            hidden=cli._hidden;confirm=cli._confirm
            def selected(prompt):return PROMPTS[phase] in prompt
            def wrapper(function,prompt,*args,**kwargs):
                state['selected']=selected(prompt)
                try:
                    value=function(prompt,*args,**kwargs)
                    if state['selected'] and mode in ('unicode','editing','limit128'):
                        expected={'unicode':'éπ💬','editing':'ac','limit128':'x'*128}[mode]
                        assert value==expected
                        assert get(control)==before_control
                        state['value']=True;fire()
                    if prompt.startswith('Phone') and mode=='typeahead':
                        assert not wait([control],[],[],0)[0], 'queued next input survived flush'
                    return value
                finally:state['selected']=False
            def hidden_wrapper(prompt,**kwargs):return wrapper(hidden,prompt,**kwargs)
            def confirm_wrapper(prompt,expected='yes',**kwargs):return wrapper(confirm,prompt,expected,**kwargs)
            if mode=='istrip_afterphone':
                def hook(w,r):
                    if isinstance(r,base.functions.auth.SendCodeRequest):
                        changed=get(control);changed[0]|=termios.ISTRIP;put(control,termios.TCSANOW,changed)
                    return NotImplemented
                service.hook=hook
            with contextlib.ExitStack() as stack:
                for name,fn in [('open',opening),('close',closing),('read',reading)]:stack.enter_context(patch.object(os,name,fn))
                stack.enter_context(patch.object(termios,'tcgetattr',getting));stack.enter_context(patch.object(termios,'tcsetattr',setting))
                stack.enter_context(patch.object(termios,'tcflush',flushing));stack.enter_context(patch.object(select,'select',waiting))
                stack.enter_context(patch.object(cli,'_hidden',hidden_wrapper));stack.enter_context(patch.object(cli,'_confirm',confirm_wrapper))
                if phase=='retry':stack.enter_context(patch.object(base.publication,'_prepare_candidate',side_effect=OSError('local failure')))
                if mode=='small_canon':stack.enter_context(patch.object(os,'fpathconf',return_value=128))
                if mode=='no_termios':stack.enter_context(patch.object(ti,'termios',None))
                if mode=='fault_output':
                    real_print=__import__('builtins').print
                    def printing(*args,**kwargs):
                        if state['selected'] and args and PROMPTS['phone'] in str(args[0]):
                            state['fired']=True;raise OSError('prompt output')
                        return real_print(*args,**kwargs)
                    stack.enter_context(patch('builtins.print',printing))
                code=cli.main(['--config',config]+(['--replace'] if existing else []))
            after=get(control) if control is not None else None
            restoration_observed=after==before_control
            if mode=='istrip_afterphone':
                expected_modes=before_control[:];expected_modes[0]|=termios.ISTRIP
                assert after==expected_modes
            elif mode in ('fault_restore','fault_restore_stop'):
                assert not restoration_observed and not after[3]&termios.ECHO
            else:assert restoration_observed,(mode,'terminal not restored')
            if mode=='two_terminals':assert state['two_observed'] and get(0)==before_stdin
            assert signal.getsignal(signal.SIGINT)==original_handler
            assert all(not w.up for w in service.wires)
            saved=mode in ('typeahead','two_terminals','echo_off')
            expected_code=0 if saved else 2 if mode in ('no_controlling','background','noncanonical','istrip','bad_cr','small_canon','no_termios') else 3 if (mode.startswith('fault_') and mode!='fault_restore_stop') or mode in ('limit129','kernel_overflow','invalid_utf8','istrip_afterphone') else 130
            assert code==expected_code,(mode,code,expected_code)
            assert target.exists()==(existing or saved)
            if existing:assert target.read_bytes()==previous
            if saved:base.reopen(config,service)
            expected_codes=1 if phase!='phone' or saved or mode=='istrip_afterphone' else 0
            assert service.calls.count('SendCodeRequest')==expected_codes,(mode,service.calls)
            if phase=='code' or mode=='istrip_afterphone':assert 'SignInRequest' not in service.calls
            if phase=='password':assert 'CheckPasswordRequest' not in service.calls
            if mode in ('unicode','editing','limit128'):assert state['value']
            if mode.startswith(('first_','after_restore_','stop_','fault_')):assert state['fired'],mode
            result=dict(mode=mode,exit=code,terminal_restored=restoration_observed,codes=expected_codes,saved=saved,
                        signal_or_fault_fired=state['fired'],value_checked=state['value'],two_terminals_observed=state['two_observed'])
            print('MATRIX_RESULT '+json.dumps(result),flush=True)
            return 0
    finally:
        if control is not None:
            termios.tcsetattr(control,termios.TCSANOW,original_control);os.close(control)
        termios.tcsetattr(0,termios.TCSANOW,original_stdin)


def parent(mode):
    master,slave=pty.openpty(); extra=[]
    stdin_slave=slave
    if mode=='two_terminals':
        other_master,stdin_slave=pty.openpty();extra=[other_master,stdin_slave]
    def control():
        os.setsid()
        if mode!='no_controlling':fcntl.ioctl(slave,termios.TIOCSCTTY,0)
    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],
        stdin=stdin_slave,stdout=slave,stderr=slave,preexec_fn=control,pass_fds=(slave,),
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    os.close(slave)
    if mode=='two_terminals':os.close(stdin_slave);extra.remove(stdin_slave)
    data=bytearray();seen={};deadline=time.monotonic()+12
    target_phase=mode.split('_')[1] if mode.startswith('first_') else 'phone'
    try:
        while time.monotonic()<deadline:
            ready,_,_=select.select([master],[],[],0.03)
            if ready:
                try:block=os.read(master,65536)
                except OSError:block=b''
                if not block:break
                data.extend(block)
            text=data.decode(errors='replace')
            for phase,marker in PROMPTS.items():
                count=text.count(marker)
                if count<=seen.get(phase,0):continue
                seen[phase]=count
                if (mode.startswith('first_') and phase==target_phase and mode.endswith('_eof')) or (mode=='after_restore_eof' and phase=='phone'):
                    payload=b'\x04'
                elif phase=='phone' and mode=='partial_eof':payload=b'partial\x04'
                elif phase=='phone' and mode=='unicode':payload='éπ💬\n'.encode()
                elif phase=='phone' and mode=='editing':payload=b'ab\x7fc\n'
                elif phase=='phone' and mode=='limit128':payload=b'x'*128+b'\n'
                elif phase=='phone' and mode=='limit129':payload=b'x'*129+b'\n'
                elif phase=='phone' and mode=='kernel_overflow':payload=b'x'*5000+b'\n'
                elif phase=='phone' and mode=='invalid_utf8':payload=b'\xff\n'
                elif phase=='phone' and mode=='typeahead':payload=(fx.PHONE+'\nqueued-private-text\n').encode()
                else:payload=({'phone':fx.PHONE,'code':fx.CODE,'password':fx.PASSWORD,'replace':'REPLACE','retry':'yes'}[phase]+'\n').encode()
                os.write(master,payload)
            if process.poll() is not None and not ready:break
        process.wait(timeout=max(0.1,deadline-time.monotonic()))
        text=data.decode(errors='replace')
        assert process.returncode==0,(mode,text)
        result=json.loads(next(line[len('MATRIX_RESULT '):] for line in text.splitlines() if line.startswith('MATRIX_RESULT ')))
        base.no_secrets(text)
        if mode in ('fault_restore','fault_restore_stop','fault_restore_after','fault_readback'):assert 'terminal_restore_failed' in text
        if mode=='fault_flush':assert 'terminal_flush_failed' in text
        if mode=='fault_close':assert 'terminal_close_failed' in text
        for secret in ('éπ💬','queued-private-text','x'*40):assert secret not in text,(mode,'secret output')
        return result
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=3)
        os.close(master)
        for fd in extra:os.close(fd)


def run():
    results=[]
    for mode in MODES:
        row=parent(mode);results.append(row)
        print('OWNED_TERMINAL '+json.dumps(row),flush=True)
    return results

if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1:raise SystemExit(child(sys.argv[2]))
        run()
