"""Build the actual PR source distribution and exercise its built public package.

No wheel/build frontend is installed in this environment. Use installed setuptools'
real sdist/build commands, entirely offline, in a disposable git-archive checkout.
"""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkout',type=Path,required=True)
parser.add_argument('--log',type=Path,required=True)
args=parser.parse_args()


def unpack(data,root):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for item in archive.getmembers():
            target=(root/item.name).resolve()
            assert target==root or root in target.parents
            assert not item.issym() and not item.islnk()
        archive.extractall(root)


code=r'''
import asyncio,json,socket,sys,tempfile
from pathlib import Path
from unittest.mock import patch
lib=Path(sys.argv[1]).resolve();sys.path.insert(0,str(lib))
import tgdata
from tgdata import TgData,SQLiteSyncStore,BackfillStartRequest,BackfillPrepareContext,SyncStorageError
assert lib in Path(tgdata.__file__).resolve().parents
async def run():
 with tempfile.TemporaryDirectory() as tmp, patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
  store=SQLiteSyncStore(Path(tmp)/'run.sqlite3');tg=TgData('/forbidden-package-config.ini',backfill_store=store)
  req=BackfillStartRequest('package-check',-1000000000007,'run','archive',12,None,last_days=1)
  with patch.object(tg.connection_engine,'_load_config',side_effect=AssertionError('config forbidden')):
   status=(await tg.start_backfill(req,submission='new')).status
   assert not (await tg.start_backfill(req,submission='retry')).applied
   assert await tg.get_backfill_status(status.run)==status
   paused=await tg.control_backfill(status.run,command_id='pause',expected_control_revision=0,action='pause')
   turn=await tg.prepare_backfill(BackfillPrepareContext.from_status(paused.status))
   assert turn.batch is None and turn.status.operator_intent=='paused'
   assert tg.connection_engine._config is None
   await tg.close()
  assert not any(k.startswith('tgdata.smoke_tests') for k in sys.modules)
 print(json.dumps(dict(result='PASS',package_version=tgdata.__version__,operations='public create/retry/status/pause/prepare/close',source='actual built sdist package',source_requests=0,repository_test_imports=0)))
asyncio.run(run())
'''

with tempfile.TemporaryDirectory(prefix='tgdata_pr20_package_') as tmp:
    root=Path(tmp).resolve();source=root/'source';source.mkdir()
    archive=subprocess.check_output(['git','archive','HEAD'],cwd=args.checkout)
    unpack(archive,source);assert not (source/'devdocs/work/19-backfill-run-lifecycle').exists()
    dist=root/'dist';dist.mkdir()
    with args.log.open('w') as log:
        subprocess.run([sys.executable,'setup.py','sdist','--dist-dir',str(dist)],cwd=source,
            stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
        packages=list(dist.glob('*.tar.gz'));assert len(packages)==1
        expanded=root/'sdist';expanded.mkdir();unpack(packages[0].read_bytes(),expanded)
        package_source=next(expanded.iterdir());lib=root/'built'
        subprocess.run([sys.executable,'setup.py','build','--build-base',str(root/'build'),'--build-lib',str(lib)],
            cwd=package_source,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
        assert not (lib/'devdocs').exists() and not (lib/'examples').exists()
        result=subprocess.run([sys.executable,'-c',code,str(lib)],cwd=root,capture_output=True,text=True,timeout=30)
        log.write(result.stdout);log.write(result.stderr)
        assert result.returncode==0,result.stderr
        print(result.stdout.strip())
print('Passed: 1/1 actual sdist/build/import/public-local-API probe; no network or repository work files')
