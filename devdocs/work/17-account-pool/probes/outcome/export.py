"""Export the exact reviewed product/current-dev composition, without branch edits."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE.parents[1] / 'evidence/outcome'
BASE = 'f1cae2c'
DEV = '2ddb852d917998d003f9db863fce09a92e9c5712'


def main():
    subprocess.run(['git', 'merge-base', '--is-ancestor', DEV, BASE], cwd=ROOT, check=True)
    assert not subprocess.check_output(['git', 'diff', BASE, '--', 'tgdata', 'examples', 'README.md', 'docs'], cwd=ROOT)
    parent = Path(tempfile.mkdtemp(prefix='tgdata17-outcome-prebuild-', dir='/private/tmp'))
    archive = parent / 'baseline.tar'
    subprocess.run(['git', 'archive', '--format=tar', '-o', str(archive), BASE,
                    'tgdata', 'docs', 'examples', 'README.md', 'setup.py'], cwd=ROOT, check=True)
    source = parent / 'source'; source.mkdir()
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            assert member.isfile() or member.isdir()
        bundle.extractall(source)
    hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(source.rglob('*.py'))}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'export-manifest.json').write_text(json.dumps(dict(
        baseline=BASE, product='a63099e', dev=DEV,
        tree=subprocess.check_output(['git','rev-parse',BASE+'^{tree}'],cwd=ROOT,text=True).strip(),
        source=str(source), sha256=hashes),indent=2)+'\n')
    print(source)

if __name__ == '__main__': main()
