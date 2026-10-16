"""Actual generated installed entry point, controlled source and real native-SRP PTY."""
import os,runpy,socket,sys
from pathlib import Path
from unittest.mock import patch
import tgdata
from tgdata import login_cli as cli
from tgdata.smoke_tests import test_48_terminal_login as t
library=Path(os.environ['LOGIN_INSTALL_LIB']).resolve();entry=Path(os.environ['LOGIN_INSTALL_ENTRY'])
assert Path(tgdata.__file__).resolve().parent==library/'tgdata'
assert Path(cli.__file__).resolve().parent==library/'tgdata'
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
    if len(sys.argv)>1 and sys.argv[1]=='--phase-child':
        with patch.object(cli,'main',installed_main):
            raise SystemExit(t.phase_child(sys.argv[2],Path(sys.argv[3])))
    t.__file__=__file__
    t.phase_terminal_case('native_srp')
    print('INSTALLED_NATIVE_SRP_STOP_PASS',flush=True)
