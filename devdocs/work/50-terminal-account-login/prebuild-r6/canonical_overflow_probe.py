"""Diagnose canonical buffering independently of the candidate and its harness."""
import json,os,pty,select,termios
from pathlib import Path
rows=[]
for length in (128,129,5000):
    master,slave=pty.openpty()
    old=termios.tcgetattr(slave)
    try:
        attrs=termios.tcgetattr(slave)
        attrs[0]|=termios.ICRNL
        attrs[3]=(attrs[3]|termios.ICANON|termios.ISIG)&~(termios.ECHO|termios.ECHONL)
        termios.tcsetattr(slave,termios.TCSANOW,attrs)
        data=b'x'*length+b'\n'
        written=os.write(master,data)
        ready=bool(select.select([slave],[],[],0.25)[0])
        observed=os.read(slave,8192) if ready else None
        row=dict(payload_bytes=len(data),accepted_by_write=written,max_canon=os.fpathconf(slave,'PC_MAX_CANON'),
                 readable_after_newline=ready,observed_bytes=None if observed is None else len(observed),
                 ends_in_newline=None if observed is None else observed.endswith(b'\n'))
        assert written==len(data)
        if length<5000:assert ready and observed==data
        else:assert not ready
        rows.append(row)
    finally:
        termios.tcflush(slave,termios.TCIFLUSH)
        termios.tcsetattr(slave,termios.TCSANOW,old)
        os.close(slave);os.close(master)
print(json.dumps(rows,indent=2))
Path(__file__).with_name('canonical-overflow-result.json').write_text(json.dumps(rows,indent=2)+'\n')
