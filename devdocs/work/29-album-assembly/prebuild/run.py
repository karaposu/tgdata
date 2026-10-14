"""Build a temporary real package from current sources and the exact candidate."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    candidate = Path(tempfile.mkdtemp(prefix='tgdata-29-prebuild-', dir='/private/tmp'))
    for name in ('tgdata', 'examples'):
        shutil.copytree(ROOT / name, candidate / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    mapping = {'album.py': 'tgdata/album.py', 'album_assembly.py': 'examples/album_assembly.py',
               'test_42_album_assembly.py': 'tgdata/smoke_tests/test_42_album_assembly.py'}
    for source, target in mapping.items():
        shutil.copyfile(HERE / source, candidate / target)
    init = candidate / 'tgdata/__init__.py'
    init.write_text(init.read_text() + '\nfrom .album import TelegramPost, AlbumAssemblyError, album_post_ids, assemble_albums\n'
                    '__all__ += ["TelegramPost", "AlbumAssemblyError", "album_post_ids", "assemble_albums"]\n')
    env = dict(os.environ, PYTHONPATH=str(candidate), PYTHONDONTWRITEBYTECODE='1')
    log = HERE / 'combined.txt'
    with log.open('w') as stream:
        result = subprocess.run([sys.executable, '-m', 'tgdata.smoke_tests.test_42_album_assembly', '-v'],
                                cwd=candidate, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
    report = dict(result='PASS' if result.returncode == 0 else 'FAIL', exit_code=result.returncode,
                  candidate=str(candidate), runtime=sys.version.split()[0],
                  sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in mapping},
                  network='socket connect/connect_ex forbidden in tests; no live Telegram claim')
    (HERE / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(log.read_text())
    print(json.dumps(report, indent=2))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
