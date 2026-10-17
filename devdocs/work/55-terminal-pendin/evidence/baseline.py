"""Observe released CLI refusal and native PENDIN transitions; no real login."""
import json,os,pty,sys,termios
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from tgdata.smoke_tests._terminal_login_modes import parent
row=parent('pendin');assert row['exit']==2 and row['codes']==0 and not row['saved']
m,s=pty.openpty();states=[]
try:
 def observe(phase):states.append(dict(phase=phase,pendin=bool(termios.tcgetattr(s)[3]&termios.PENDIN)))
 observe('fresh');a=termios.tcgetattr(s);a[3]|=termios.PENDIN;termios.tcsetattr(s,termios.TCSANOW,a);observe('set')
 a=termios.tcgetattr(s);a[3]&=~termios.PENDIN;termios.tcsetattr(s,termios.TCSANOW,a);observe('attempt_clear')
 termios.tcflush(s,termios.TCIFLUSH);observe('flush')
finally:os.close(s);os.close(m)
result=dict(system=os.uname().sysname,released_cli=row,transitions=states)
Path(__file__).with_name('baseline.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
