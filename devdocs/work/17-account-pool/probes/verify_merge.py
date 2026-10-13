"""Run the unchanged complete verifier on the isolated, archive-free PR26 merge."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

WORK = Path(__file__).resolve().parents[1]
MERGE = Path('/private/tmp/tgdata-26-merge-verification')
BASE = '2ddb852d917998d003f9db863fce09a92e9c5712'
REVIEWED = '6e500f9015a08867f0dc187f7972ea3061fd88e4'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=MERGE, text=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    audit = json.loads((WORK/'evidence/review3/merge-audit.json').read_text())
    assert git('rev-parse', 'HEAD').strip() == BASE
    assert git('rev-parse', 'MERGE_HEAD').strip() == REVIEWED
    assert not git('diff', '--name-only')
    paths = git('diff', '--cached', '--name-only').splitlines()
    assert paths == audit['product_paths'] and len(paths) == 23
    assert not git('diff', '--cached', '--', 'devdocs')
    for path, digest in audit['product_sha256'].items():
        assert sha(MERGE/path) == digest, path
    source = WORK/'probes/outcome/verify.py'
    spec = importlib.util.spec_from_file_location('qualified_verifier', source)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verifier.ROOT = MERGE
    verifier.OUT = WORK/'evidence/merge-verification'
    verifier.OUT.mkdir(parents=True, exist_ok=True)
    initial = dict(base=BASE, reviewed_head=REVIEWED, merge_checkout=str(MERGE),
                   product_paths=paths, product_sha256=audit['product_sha256'],
                   devdocs_unchanged=True, conflict_free=True,
                   verifier_sha256=sha(source), adapter_sha256=sha(Path(__file__)))
    (verifier.OUT/'merge-audit.json').write_text(json.dumps(initial, indent=2)+'\n')
    result = verifier.main()
    assert not git('diff', '--name-only')
    assert git('diff', '--cached', '--name-only').splitlines() == paths
    assert all(sha(MERGE/path) == digest for path, digest in audit['product_sha256'].items())
    return result


if __name__ == '__main__':
    sys.exit(main())
