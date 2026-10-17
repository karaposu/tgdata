"""Run generated installed tgdata-login with actual native PENDIN terminals."""
import json,os,runpy,socket,sys
from pathlib import Path
from unittest.mock import patch
import tgdata
from tgdata import login_cli as cli
from tgdata.smoke_tests import _terminal_login_modes as modes
library=Path(os.environ['LOGIN_INSTALL_LIB']).resolve();entry=Path(os.environ['LOGIN_INSTALL_ENTRY'])
assert Path(tgdata.__file__).resolve().parent==library/'tgdata'
assert Path(cli.__file__).resolve().parent==library/'tgdata'
assert Path(modes.__file__).resolve().parent==library/'tgdata/smoke_tests'
original=cli.main

def installed_main(argv=None):
    previous=sys.argv
    sys.argv=[str(entry)]+list(argv or [])
    try:
        with patch.object(cli,'main',original):
            try:runpy.run_path(str(entry),run_name='__main__')
            except SystemExit as error:return error.code
    finally:sys.argv=previous
    raise AssertionError('installed entry did not exit')

with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        with patch.object(cli,'main',installed_main):
            raise SystemExit(modes.child(sys.argv[2]))
    modes.__file__=__file__
    results=[modes.parent(case) for case in ('pendin','pendin_password')]
    for row in results:
        assert row['exit']==0 and row['saved'] and row['terminal_restored'] and row['initial_pendin']
    print('INSTALLED_PENDIN_PASS '+json.dumps(results),flush=True)
