"""Native canonical input transformation; no authentication or real credentials."""
import json, os, pty, termios
from pathlib import Path
master, slave = pty.openpty()
original = termios.tcgetattr(slave)
try:
    attrs = termios.tcgetattr(slave)
    attrs[0] |= termios.ISTRIP | termios.ICRNL
    attrs[3] = (attrs[3] | termios.ICANON | termios.ISIG) & ~termios.ECHO
    termios.tcsetattr(slave, termios.TCSANOW, attrs)
    source = 'é\n'.encode('utf-8')
    os.write(master, source)
    actual = os.read(slave, 130)
    result = dict(input_utf8=list(source), observed=list(actual),
                  decoded=actual.decode('utf-8'), silently_changed=actual!=source,
                  max_canon=os.fpathconf(slave,'PC_MAX_CANON'))
    assert result['silently_changed'] and result['decoded']=='C)\n',result
    print(json.dumps(result))
    Path(__file__).with_name('istrip-result.json').write_text(json.dumps(result,indent=2)+'\n')
finally:
    termios.tcsetattr(slave,termios.TCSANOW,original)
    os.close(slave);os.close(master)
