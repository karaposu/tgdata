import io
from pathlib import Path
import subprocess
import tarfile

ROOT = Path('/private/tmp/tgdata-release-0.1-evidence/candidate')
BASE = 'f92749688b7d544da55249459c489164497d47ed'
ROOT.mkdir()
raw = subprocess.check_output(['git', 'archive', '--format=tar', BASE], cwd='/private/tmp/tgdata-release-0.1')
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
    archive.extractall(ROOT, filter='data')
path = ROOT / 'tgdata/__init__.py'
body = path.read_text()
assert body.count('__version__ = "0.0.8"') == 1
path.write_text(body.replace('__version__ = "0.0.8"', '__version__ = "0.1"'))
print('Candidate:', ROOT, 'from', BASE, 'with only the 0.1 version substitution')
