"""Native queue observations only; no candidate input policy or Telegram code."""
import json,os,pty,select,termios
from pathlib import Path
rows=[]
for canonical,length,newline in ((True,10,False),(False,10,False),(True,5000,True),(False,5000,True)):
    master,slave=pty.openpty();old=termios.tcgetattr(slave)
    try:
        attrs=termios.tcgetattr(slave)
        attrs[3]&=~(termios.ECHO|termios.ECHONL|termios.IEXTEN)
        if canonical:attrs[3]|=termios.ICANON
        else:attrs[3]&=~termios.ICANON
        attrs[6][termios.VMIN]=1;attrs[6][termios.VTIME]=0
        termios.tcsetattr(slave,termios.TCSANOW,attrs)
        os.set_blocking(master,False);os.set_blocking(slave,False)
        payload=b'x'*length+(b'\n' if newline else b'')
        written=os.write(master,payload)
        out=bytearray()
        while select.select([slave],[],[],0.05)[0]:
            try:part=os.read(slave,8192)
            except BlockingIOError:break
            if not part:break
            out.extend(part)
        row=dict(canonical=canonical,sent=written,requested=len(payload),observed=len(out),newline_observed=b'\n' in out,max_input=os.fpathconf(slave,'PC_MAX_INPUT'))
        if not canonical:assert len(out)>0
        rows.append(row)
        termios.tcflush(slave,termios.TCIFLUSH)
        os.write(master,b'tail\n')
        assert select.select([slave],[],[],0.1)[0]
        assert os.read(slave,8192)==b'tail\n'
        row['future_write_survives_prior_flush']=True
    finally:
        termios.tcflush(slave,termios.TCIFLUSH)
        termios.tcsetattr(slave,termios.TCSANOW,old)
        os.close(slave);os.close(master)
print(json.dumps(rows,indent=2))
Path(__file__).with_name('delivery-result.json').write_text(json.dumps(rows,indent=2)+'\n')
