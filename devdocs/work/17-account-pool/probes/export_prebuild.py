"""Export the explicitly resolved #17/current-dev composition without branch edits."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[4]
PRODUCT = '71502e5993315354ca3d97afe607d5f4be776af3'
DEV = '2ddb852d917998d003f9db863fce09a92e9c5712'
EVIDENCE = ROOT / 'devdocs/work/17-account-pool/evidence/replan-r3'


def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=ROOT, **kwargs)


def main():
    merged = subprocess.run(['git', 'merge-tree', '--write-tree', PRODUCT, DEV],
                            cwd=ROOT, capture_output=True, text=True)
    assert merged.returncode == 1, merged.stdout + merged.stderr
    lines = merged.stdout.splitlines()
    tree = lines[0]
    conflicts = {line.split('\t', 1)[1] for line in lines if '\t' in line}
    assert conflicts == {'tgdata/batch_engine.py'}, conflicts
    directory = Path(tempfile.mkdtemp(prefix='tgdata17-prebuild-', dir='/private/tmp'))
    env = dict(os.environ, GIT_INDEX_FILE=str(directory / 'isolated.index'))
    subprocess.run(['git', 'read-tree', tree], cwd=ROOT, env=env, check=True)
    blob = git('rev-parse', PRODUCT + ':tgdata/batch_engine.py', text=True).strip()
    subprocess.run(['git', 'update-index', '--cacheinfo', '100644,' + blob + ',tgdata/batch_engine.py'],
                   cwd=ROOT, env=env, check=True)
    resolved = git('write-tree', env=env, text=True).strip()
    archive = directory / 'source.tar'
    subprocess.run(['git', 'archive', '--format=tar', '-o', str(archive), resolved,
                    'tgdata', 'docs', 'examples', 'README.md', 'setup.py'], cwd=ROOT, check=True)
    export = directory / 'source'
    export.mkdir()
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            assert member.isfile() or member.isdir(), member.name
        bundle.extractall(export)
    hashes = {str(file.relative_to(export)): hashlib.sha256(file.read_bytes()).hexdigest()
              for file in sorted((export / 'tgdata').rglob('*.py'))}
    manifest = dict(product=PRODUCT, dev=DEV, merge_tree=tree, resolved_tree=resolved,
                    export=str(export), conflicts=sorted(conflicts),
                    resolution='pool batch_engine blob retains the common resolver plus opt-in cancellation prefix',
                    batch_blob=blob, runtime_sha256=hashes)
    EVIDENCE.mkdir(exist_ok=True, parents=True)
    (EVIDENCE / 'export-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (EVIDENCE / 'merge-preview.txt').write_text(merged.stdout)
    print(json.dumps(dict(export=str(export), resolved_tree=resolved, runtime_files=len(hashes))))


if __name__ == '__main__':
    main()
