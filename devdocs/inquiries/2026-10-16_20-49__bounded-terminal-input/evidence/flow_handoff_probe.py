"""Selected real-component handoffs, not the future full candidate prebuild."""
import fcntl,json,os,pty,select,signal,socket,subprocess,sys,termios,time
from pathlib import Path
from unittest.mock import patch
from stream_input_probe import read_input
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'devdocs/work/50-terminal-account-login/prebuild-r6'))
import combined_suite as base
CASES=('plain','two_factor','overflow_phone','overflow_password','overflow_retry','stop_overflow','first_restore_stop')
PROMPTS={'phone':'Phone number with country code (hidden):','code':'Telegram code (hidden):',
 'password':'Two-factor password (hidden):','replace':'Type REPLACE:','retry':'Retry saving this completed login'}


def child(mode):
    before=termios.tcgetattr(0);handler=signal.getsignal(signal.SIGINT);records=[]
    with base.fixture(two_factor=mode in ('two_factor','overflow_password'),existing=mode=='overflow_retry') as (config,service,root,target,previous):
        def reader(prompt,stop_requested):
            def point(stage,fd,stats):
                if mode=='first_restore_stop' and prompt.startswith('Phone') and stage=='restore':os.kill(os.getpid(),signal.SIGINT)
            value,stats=read_input(prompt,stop_requested,point)
            assert termios.tcgetattr(0)==before
            records.append(stats)
            return value
        prepare=base.publication._prepare_candidate
        calls=[0]
        def failed_local(*args):
            calls[0]+=1
            raise OSError('synthetic local save failure')
        with patch.object(base.cli,'read_hidden',reader),patch.object(base.publication,'_prepare_candidate',failed_local if mode=='overflow_retry' else prepare):
            status=base.cli.main(['--config',config]+(['--replace'] if mode=='overflow_retry' else []))
        expected=0 if mode in ('plain','two_factor') else 130 if mode in ('stop_overflow','first_restore_stop') else 3 if mode!='overflow_retry' else 4
        assert status==expected,(mode,status)
        assert termios.tcgetattr(0)==before and signal.getsignal(signal.SIGINT)==handler
        assert all(not w.up for w in service.wires)
        saved=expected==0
        if saved:
            base.reopen(config,service)
            assert service.calls.count('SendCodeRequest')==1
            if mode=='two_factor':assert service.srp_accepted==1
        elif previous is not None:assert target.read_bytes()==previous
        else:assert not target.exists()
        codes=service.calls.count('SendCodeRequest')
        assert codes==(0 if mode in ('overflow_phone','stop_overflow','first_restore_stop') else 1)
        if mode=='overflow_password':assert 'CheckPasswordRequest' not in service.calls
        if mode=='overflow_retry':assert calls[0]==1 and service.calls.count('SignInRequest')==1
        print('\nHANDOFF '+json.dumps(dict(mode=mode,status=status,codes=codes,saved=saved,terminal_restored=True,settled_values=len(records))),flush=True)
        return 0


def parent(mode):
    master,slave=pty.openpty()
    def control():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
    proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',mode],stdin=slave,stdout=slave,stderr=slave,
                          preexec_fn=control,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    os.close(slave);os.set_blocking(master,False)
    data=bytearray();seen={};pending=b'';sent=0;stop_sent=False;deadline=time.monotonic()+15
    try:
        while time.monotonic()<deadline:
            r,w,_=select.select([master],[master] if pending else [],[],0.005)
            if r:
                try:block=os.read(master,65536)
                except OSError:block=b''
                if not block:break
                data.extend(block)
            text=data.decode(errors='replace')
            for phase,marker in PROMPTS.items():
                if text.count(marker)>seen.get(phase,0):
                    seen[phase]=text.count(marker)
                    assert not pending
                    oversized=(mode=='overflow_'+phase or mode=='stop_overflow' and phase=='phone')
                    pending=b'x'*5000+(b'' if mode=='stop_overflow' else b'\n') if oversized else ({'phone':base.fx.PHONE,'code':base.fx.CODE,'password':base.fx.PASSWORD,'replace':'REPLACE','retry':'yes'}[phase]+'\n').encode()
            if w and pending:
                try:n=os.write(master,pending[:4096])
                except BlockingIOError:n=0
                pending=pending[n:];sent+=n
            if mode=='stop_overflow' and not pending and b'Input rejected' in data and not stop_sent:
                stop_sent=True;os.kill(proc.pid,signal.SIGINT)
            if proc.poll() is not None and not r:break
        proc.wait(timeout=max(0.1,deadline-time.monotonic()))
        text=data.decode(errors='replace');assert proc.returncode==0,(mode,text)
        base.no_secrets(text);assert 'x'*40 not in text
        return json.loads(next(s[8:] for s in text.splitlines() if s.startswith('HANDOFF ')))
    finally:
        if proc.poll() is None:proc.kill();proc.wait(timeout=2)
        os.close(master)

if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        if len(sys.argv)>1:raise SystemExit(child(sys.argv[2]))
        rows=[]
        for mode in CASES:
            row=parent(mode);rows.append(row);print(json.dumps(row),flush=True)
        (HERE/'flow-handoff-result.json').write_text(json.dumps(dict(result='PASS',cases=rows),indent=2)+'\n')
