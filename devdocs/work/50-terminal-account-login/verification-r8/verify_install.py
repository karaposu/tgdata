"""Isolated offline setuptools installation; does not alter the user's environment."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def main():
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PIP_NO_INDEX='1')
    with tempfile.TemporaryDirectory(prefix='tgdata-login-install-') as tmp:
        root=Path(tmp);source=root/'source';source.mkdir()
        for name in ('setup.py','README.md'):
            shutil.copy2(ROOT/name,source/name)
        shutil.copytree(ROOT/'tgdata',source/'tgdata',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        library=root/'installed-lib';scripts=root/'installed-bin'
        # Existing setuptools65.5 is available offline; wheel/build are absent.
        # This managed install emits the real console scripts without dependencies.
        command=[sys.executable,'setup.py','install','--single-version-externally-managed',
            '--record',str(root/'installed-files.txt'),'--install-lib',str(library),
            '--install-scripts',str(scripts),'--install-data',str(root/'data'),
            '--install-headers',str(root/'headers')]
        with (HERE/'install-build.txt').open('w') as log:
            built=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
        assert built.returncode==0,'offline managed installation failed; see install-build.txt'
        assert (scripts/'tgdata-login').exists() and (scripts/'tgdata-worker').exists()
        env['PYTHONPATH']=str(library)
        probe=subprocess.run([sys.executable,'-c',
            'import tgdata,json; from importlib.metadata import distribution; '
            'print(json.dumps({"path":tgdata.__file__,"entry":[e.value for e in distribution("tgdata").entry_points if e.name=="tgdata-login"]}))'],
            cwd=root,env=env,capture_output=True,text=True,timeout=10)
        assert probe.returncode==0,probe.stderr
        result=json.loads(probe.stdout)
        assert Path(result['path']).resolve().parent==(library/'tgdata').resolve()
        assert result['entry']==['tgdata.login_cli:main']
        help_result=subprocess.run([str(scripts/'tgdata-login'),'--help'],cwd=root,env=env,
            stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10)
        assert help_result.returncode==0 and '--replace' in help_result.stdout
        headless=subprocess.run([str(scripts/'tgdata-login'),'--config','missing.ini'],cwd=root,env=env,
            stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10)
        assert headless.returncode==2 and 'interactive terminal' in headless.stderr
        module_help=subprocess.run([sys.executable,'-m','tgdata.login_cli','--help'],cwd=root,env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=10)
        assert module_help.returncode==0 and '--replace' in module_help.stdout
        env['LOGIN_INSTALL_LIB']=str(library)
        env['LOGIN_INSTALL_ENTRY']=str(scripts/'tgdata-login')
        interrupted=subprocess.run([sys.executable,str(HERE/'installed_probe.py')],cwd=root,env=env,
            stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=25)
        (HERE/'installed-interruption.txt').write_text(interrupted.stdout+interrupted.stderr)
        assert interrupted.returncode==0 and 'INSTALLED_NATIVE_SRP_STOP_PASS' in interrupted.stdout
        hashes={target:hashlib.sha256(path.read_bytes()).hexdigest() for target,path in [('login_cli.py',ROOT/'tgdata/login_cli.py'),('_terminal_input.py',ROOT/'tgdata/_terminal_input.py'),('login_file.py',ROOT/'tgdata/login_file.py')]}
        assert all(hashlib.sha256((library/'tgdata'/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
        report=dict(result='PASS',runtime=sys.version.split()[0],entry_point=result['entry'][0],
            isolated_import=True,console_help=help_result.returncode,headless_exit=headless.returncode,
            native_srp_interruption=True,native_files_match=hashes,network=False,method='offline setuptools managed install')
        (HERE/'install-result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)


if __name__=='__main__':main()
