"""Check actual installed 0.1.2 artifacts, not imports from a checkout."""
from pathlib import Path
import importlib.metadata,inspect,json,os,socket,subprocess,sys,tempfile
from unittest.mock import patch
TARGET=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve();VERSION='0.1.2'
sys.path.insert(0,str(TARGET))
with patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
 import tgdata,telethon
 from tgdata import login_cli,login_file,_terminal_input
 assert Path(tgdata.__file__).resolve()==TARGET/'tgdata/__init__.py'
 for module in (login_cli,login_file,_terminal_input):assert Path(module.__file__).resolve().parent==TARGET/'tgdata'
 dist=importlib.metadata.distribution('tgdata')
 assert tgdata.__version__==dist.version==VERSION
 assert telethon.__version__=='1.45.0'
 assert len(tgdata.__all__)==len(set(tgdata.__all__)) and all(hasattr(tgdata,n) for n in tgdata.__all__)
 for name in ('GroupProfile','GroupPinnedMessage','GroupActivity','ActivityMessage','LoginFlow','TelegramPost','assemble_albums','PhotoTrailPolicy','fold_photo_trails','AccountPool','SQLiteSyncStore'):
  assert hasattr(tgdata,name),name
 for name in ('get_group_profile','measure_group_activity'):assert inspect.iscoroutinefunction(getattr(tgdata.TgData,name))
 assert not tgdata.PhotoTrailPolicy().enabled
 for owner,names in ((tgdata.TgData,('get_message_batch','sync_group','prepare_backfill')),(tgdata.AccountPool,('read','get_message_batch','sync_group','prepare_backfill'))):
  for name in names:assert inspect.signature(getattr(owner,name)).parameters['heartbeat'].default is None
 entries={e.name:e.value for e in dist.entry_points if e.group=='console_scripts'}
 assert entries=={'tgdata-worker':'tgdata.worker:main','tgdata-login':'tgdata.login_cli:main'}
 env=dict(os.environ,PYTHONPATH=str(TARGET),PYTHONDONTWRITEBYTECODE='1',LOGIN_INSTALL_LIB=str(TARGET),LOGIN_INSTALL_ENTRY=str(TARGET/'bin/tgdata-login'))
 observations={}
 with tempfile.TemporaryDirectory(prefix='tgdata012-install-check-') as cwd:
  for name in entries:
   r=subprocess.run([sys.executable,str(TARGET/'bin'/name),'--help'],cwd=cwd,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20)
   assert r.returncode==0 and 'usage:' in r.stdout.lower(),(name,r.returncode,r.stderr)
   observations[name]=r.returncode
  r=subprocess.run([sys.executable,'-m','tgdata.login_cli','--help'],cwd=cwd,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20)
  assert r.returncode==0 and '--replace' in r.stdout
  r=subprocess.run([sys.executable,str(TARGET/'bin/tgdata-login'),'--config','missing.ini'],cwd=cwd,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20)
  assert r.returncode==2 and 'interactive terminal' in r.stderr
  observations['login_headless']=r.returncode
  r=subprocess.run([sys.executable,str(Path(__file__).with_name('installed_probe.py'))],cwd=cwd,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=40)
  OUT.with_suffix('.native-srp.txt').write_text(r.stdout+r.stderr)
  assert r.returncode==0 and 'INSTALLED_NATIVE_SRP_STOP_PASS' in r.stdout,(r.returncode,r.stdout,r.stderr)
 report=dict(result='PASS',version=VERSION,origin=tgdata.__file__,target=str(TARGET),runtime=sys.version.split()[0],telethon=telethon.__version__,exports=len(tgdata.__all__),optional_heartbeat_signatures=7,entries=entries,entry_checks=observations,native_srp_interruption=True,network=False)
 OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
