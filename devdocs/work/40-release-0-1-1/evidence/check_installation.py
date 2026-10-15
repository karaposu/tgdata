"""Verify a real locally installed release wheel, never the source checkout."""
from pathlib import Path
import importlib.metadata
import inspect
import json
import os
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

TARGET=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve()
sys.path.insert(0,str(TARGET))
with patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
 import tgdata,telethon
 assert Path(tgdata.__file__).resolve()==TARGET/'tgdata/__init__.py'
 assert tgdata.__version__==importlib.metadata.distribution('tgdata').version=='0.1.1'
 assert telethon.__version__=='1.45.0'
 assert all(hasattr(tgdata,name) for name in tgdata.__all__)
 for name in ('TelegramPost','assemble_albums','PhotoTrailPolicy','PhotoTrailView','fold_photo_trails',
              'AccountPool','PoolReadCapture','BackfillStartRequest','SQLiteSyncStore','TgData'):
  assert hasattr(tgdata,name),name
 assert not tgdata.PhotoTrailPolicy().enabled
 for owner,names in ((tgdata.TgData,('get_message_batch','sync_group','prepare_backfill')),
                     (tgdata.AccountPool,('read','get_message_batch','sync_group','prepare_backfill'))):
  for name in names:assert inspect.signature(getattr(owner,name)).parameters['heartbeat'].default is None
 entry=[e for e in importlib.metadata.distribution('tgdata').entry_points if e.group=='console_scripts' and e.name=='tgdata-worker']
 assert len(entry)==1 and entry[0].value=='tgdata.worker:main'
 command=[sys.executable,str(TARGET/'bin/tgdata-worker'),'--help']
 with tempfile.TemporaryDirectory(prefix='tgdata011-worker-help-') as cwd:
  result=subprocess.run(command,cwd=cwd,env=dict(os.environ,PYTHONPATH=str(TARGET)),capture_output=True,text=True,timeout=20)
 assert result.returncode==0 and 'usage:' in result.stdout.lower(),(result.returncode,result.stderr)
 r=dict(result='PASS',target=str(TARGET),module_path=tgdata.__file__,version=tgdata.__version__,
        runtime=sys.version.split()[0],telethon=telethon.__version__,public_exports=len(tgdata.__all__),
        optional_heartbeat_signatures=7,photo_trails_default_disabled=True,worker_entry_point=entry[0].value,
        installed_worker_help_exit=result.returncode)
 OUT.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
