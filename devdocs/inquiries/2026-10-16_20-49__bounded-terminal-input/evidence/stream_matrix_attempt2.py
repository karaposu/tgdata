"""Native adversarial input qualification; every writer honors partial writes."""
import fcntl,json,os,pty,select,signal,subprocess,sys,termios,time
from pathlib import Path
from unittest.mock import patch
from stream_input_probe import read_input,InputFailure,InputStopped
HERE=Path(__file__).resolve().parent
CASES={
 'plain':(b'private-probe-value\n','private-probe-value'),
 'unicode':('éπ💬\n'.encode(),'éπ💬'),
 'split_utf8':('éπ💬\n'.encode(),'éπ💬'),
 'erase':(b'ab\x7fc\n','ac'),
 'erase_unicode':('éπ💬'.encode()+b'\x7f\n','éπ'),
 'clear':(b'wrong\x15right\n','right'),
 'empty':(b'\n',''),
 'limit128':(b'x'*128+b'\n','x'*128),
 'unicode128':(('💬'*32+'\n').encode(),'💬'*32),
 'over129':(b'x'*129+b'\n',None),
 'over5000':(b'x'*5000+b'\n',None),
 'over500000':(b'x'*500000+b'\n',None),
 'paced_over5000':(b'x'*5000+b'\n',None),
 'overflow_erase':(b'x'*129+b'\x7f'*129+b'valid\n',None),
 'overflow_clear':(b'x'*129+b'\x15valid\n',None),
 'invalid_utf8':(b'\xff\n',None),
 'incomplete_utf8':(b'\xc3\n',None),
 'literal_next':(b'ab\x16c\n',None),
 'flow_stop':(b'ab\x13c\n',None),
 'quit_control':(b'ab\x1cc\n',None),
 'suspend_control':(b'ab\x1ac\n',None),
 'arrow_control':(b'ab\x1b[Ac\n',None),
 'two_lines':(b'first-value\nsecond-private-value\n','first-value'),
 'eof':(b'\x04',None),
 'partial_eof':(b'part\x04',None),
 'cancel_empty':(b'',None),
 'cancel_overflow':(b'x'*5000,None),
 'repeat_cancel':(b'',None),
 'first_restore':(b'abc\n',None),
 'first_restore_eof':(b'\x04',None),
 'restore_fault':(b'abc\n',None),
 'restore_fault_stop':(b'abc\n',None),
 'flush_fault':(b'abc\n',None),
 'two_terminals':(b'private-probe-value\n','private-probe-value'),
 'istrip':(b'',None),
 'no_controlling':(b'',None),
}
for stage in ('acquired','snapshot','hidden','read','framed','decoded','settled','restore_final','closed'):
    CASES['stop_'+stage]=(b'abc\n',None)


def child(mode):
    original_stdin=termios.tcgetattr(0);control=None;old_control=None
    before=signal.getsignal(signal.SIGINT);stopped=[False];signals=[0];events=[];stats={};bound=[False]
    def stop(*args):stopped[0]=True;signals[0]+=1
    signal.signal(signal.SIGINT,stop)
    try:
        if mode!='no_controlling':
            control=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
            old_control=termios.tcgetattr(control)
            if mode=='istrip':
                v=old_control[:];v[0]|=termios.ISTRIP;termios.tcsetattr(control,termios.TCSANOW,v)
        initial=termios.tcgetattr(control) if control is not None else None
        def point(stage,fd,current):
            events.append(stage);stats.update(current)
            if mode=='two_terminals' and stage=='hidden':
                assert not termios.tcgetattr(control)[3]&termios.ECHO
                assert termios.tcgetattr(0)==original_stdin
                bound[0]=True
            if mode=='stop_'+stage or (mode in ('first_restore','first_restore_eof') and stage=='restore'):
                os.kill(os.getpid(),signal.SIGINT)
            if mode=='repeat_cancel' and stage in ('restore','restored'):os.kill(os.getpid(),signal.SIGINT)
            if mode=='restore_fault_stop' and stage=='restore':os.kill(os.getpid(),signal.SIGINT)
        flush=termios.tcflush;put=termios.tcsetattr
        def failing_restore(fd,when,attrs):
            if 'hidden' in events and attrs[3]&termios.ICANON:raise OSError('synthetic restoration failure')
            return put(fd,when,attrs)
        def failing_flush(*args):raise OSError('synthetic flush failure')
        try:
            if mode.startswith('restore_fault'):
                with patch.object(termios,'tcsetattr',failing_restore):value,returned=read_input('INPUT_READY',lambda:stopped[0],point)
            elif mode=='flush_fault':
                with patch.object(termios,'tcflush',failing_flush):value,returned=read_input('INPUT_READY',lambda:stopped[0],point)
            else:value,returned=read_input('INPUT_READY',lambda:stopped[0],point)
            stats.update(returned);outcome='value';kind=None
            assert value==CASES[mode][1],mode
            assert CASES[mode][1] is not None
        except InputStopped:outcome='stop';kind=None
        except InputFailure as error:outcome='error';kind=str(error)
        except OSError as error:
            assert mode=='no_controlling';outcome='error';kind=type(error).__name__
        restored=control is None or termios.tcgetattr(control)==initial
        if mode.startswith('restore_fault') or mode=='flush_fault':assert not restored and kind=='restore_failed'
        else:assert restored,(mode,'modes changed')
        if mode=='two_terminals':assert bound[0] and termios.tcgetattr(0)==original_stdin
        assert stats.get('retained_peak',0)<=128 and stats.get('chunk_peak',0)<=256
        if mode.startswith(('over','paced_over')):assert outcome=='error' and kind=='input_too_long'
        elif mode in ('invalid_utf8','incomplete_utf8'):assert outcome=='error' and kind=='invalid_encoding'
        elif mode in ('literal_next','flow_stop','quit_control','suspend_control','arrow_control'):assert kind=='unsupported_control'
        elif mode in ('eof','partial_eof','cancel_empty','cancel_overflow','repeat_cancel','first_restore','first_restore_eof') or mode.startswith('stop_'):assert outcome=='stop'
        elif mode=='flush_fault':assert outcome=='error' and kind=='restore_failed'
        elif mode=='istrip':assert outcome=='error' and kind=='unsupported_terminal'
        elif mode=='no_controlling':assert outcome=='error'
        elif not mode.startswith('restore_fault'):assert outcome=='value'
        if mode=='repeat_cancel':assert signals[0]>=3
        if mode.startswith('stop_') or mode.startswith('first_restore'):assert signals[0]
        if mode=='cancel_overflow':assert stats['invalid']
        print('RESULT '+json.dumps(dict(mode=mode,outcome=outcome,kind=kind,restored=restored,signals=signals[0],**stats)),flush=True)
        return 0
    finally:
        if control is not None:
            termios.tcsetattr(control,termios.TCSAFLUSH,old_control);os.close(control)
        termios.tcsetattr(0,termios.TCSAFLUSH,original_stdin)
        signal.signal(signal.SIGINT,before)


def parent(mode):
    master,slave=pty.openpty();extra=[];input_fd=slave
    if mode=='two_terminals':other_master,input_fd=pty.openpty();extra=[other_master,input_fd]
    def control():
        os.setsid()
        if mode!='no_controlling':fcntl.ioctl(slave,termios.TIOCSCTTY,0)
    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],stdin=input_fd,stdout=slave,stderr=slave,
        preexec_fn=control,pass_fds=(slave,),env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    os.close(slave)
    if mode=='two_terminals':os.close(input_fd);extra.remove(input_fd)
    os.set_blocking(master,False)
    payload=CASES[mode][0];written=0;data=bytearray();ready=False;signaled=False;started=time.monotonic();deadline=started+10;next_write=started
    try:
        while time.monotonic()<deadline:
            reads,writes,_=select.select([master],[master] if ready and written<len(payload) and time.monotonic()>=next_write else [],[],0.005)
            if reads:
                try:block=os.read(master,65536)
                except OSError:block=b''
                if not block:break
                data.extend(block)
                ready=b'INPUT_READY' in data
            if writes:
                size=1 if mode=='split_utf8' else 64 if mode=='paced_over5000' else 4096
                try:count=os.write(master,payload[written:written+size])
                except BlockingIOError:count=0
                written+=count
                next_write=time.monotonic()+(0.002 if mode in ('split_utf8','paced_over5000') else 0)
            if ready and not signaled and (mode in ('cancel_empty','repeat_cancel') or (mode=='cancel_overflow' and written==len(payload) and b'Input rejected' in data)):
                os.kill(process.pid,signal.SIGINT);signaled=True
            if process.poll() is not None and not reads:break
        process.wait(timeout=max(0.1,deadline-time.monotonic()))
        text=data.decode(errors='replace')
        assert process.returncode==0,(mode,text)
        result=json.loads(next(line[7:] for line in text.splitlines() if line.startswith('RESULT ')))
        if mode not in ('istrip','no_controlling') and not mode.startswith(('stop_acquired','stop_snapshot','stop_hidden')):
            assert written==len(payload),(mode,written,len(payload))
        for secret in ('private-probe-value','éπ💬','second-private-value','x'*30):assert secret not in text,(mode,'input echo')
        result.update(producer_written=written,producer_requested=len(payload),seconds=round(time.monotonic()-started,4))
        return result
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=2)
        os.close(master)
        for fd in extra:os.close(fd)


def main():
    results=[]
    for mode in CASES:
        row=parent(mode);results.append(row);print(json.dumps(row),flush=True)
    (HERE/'stream-result.json').write_text(json.dumps(dict(result='PASS',cases=results),indent=2)+'\n')

if __name__=='__main__':
    if len(sys.argv)>1:raise SystemExit(child(sys.argv[2]))
    main()
