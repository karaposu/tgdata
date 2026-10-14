"""Run the recorded full verifier against the actual document-excluding merge."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MERGED = Path('/private/tmp/tgdata-28-merge-verification')
EXPECTED_BASE = 'c4e6eac89341b204b2749e9d15add578e0706965'
EXPECTED_REVIEW = '99ea00123c98218cb47e8f391ef00c8add162fea'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=MERGED, text=True).strip()


def main():
    commit = git('rev-parse', 'HEAD')
    assert git('show', '-s', '--format=%P', 'HEAD').split() == [EXPECTED_BASE, EXPECTED_REVIEW]
    assert not git('diff', EXPECTED_BASE, 'HEAD', '--', 'devdocs/work', 'devdocs/archaeology')
    assert not git('diff', EXPECTED_REVIEW, 'HEAD', '--', '.',
                   ':(exclude)devdocs/work', ':(exclude)devdocs/archaeology')
    spec = importlib.util.spec_from_file_location('tgdata8_merge_verifier', HERE/'verify.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    # Keep candidate/evidence under the archive; import and execute the merge.
    verifier.ROOT = MERGED
    verifier.OUT = HERE/'merged-verification'
    result = verifier.main()
    import tgdata
    assert Path(tgdata.__file__).resolve() == MERGED/'tgdata/__init__.py'
    assert git('rev-parse', 'HEAD') == commit
    output = verifier.OUT/'result.json'
    report = json.loads(output.read_text())
    report.update(merge_commit=commit, base=EXPECTED_BASE, reviewed_head=EXPECTED_REVIEW,
                  worktree=str(MERGED), imported_package=tgdata.__file__,
                  archive_excluded=True, reviewed_product_parity=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print('Verified actual merge:', commit, flush=True)
    return result


if __name__ == '__main__':
    raise SystemExit(main())
