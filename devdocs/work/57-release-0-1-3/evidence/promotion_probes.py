"""Observe actual GitHub promotion merge and reject wrong source authorities."""
from pathlib import Path
import hashlib,io,json,re,subprocess,tarfile
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'candidate.json').read_text())['tracked_sha256']
expected=json.loads((HERE/'promotion-candidate.json').read_text())
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def check(rev):
 assert git('rev-parse',rev+'^{tree}')==expected['tree']
 assert set(git('ls-tree','-r','--name-only',rev).splitlines())==set(manifest)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',rev]))) as archive:
  for name,digest in manifest.items():assert hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest,name
 return git('rev-parse',rev)
merge=git('rev-parse','FETCH_HEAD');parents=git('show','-s','--format=%P',merge).split()
assert parents==[expected['main'],expected['dev']]
positive=[check(expected['dev']),check(merge)]
negative=[]
for label,rev in [('unbumped_dev','aec2592'),('archive_with_work_docs','HEAD'),('stale_user_checkout','a47ba80')]:
 try:check(rev)
 except AssertionError:negative.append(label)
 else:raise AssertionError('incorrect authority accepted: '+label)
remote=subprocess.check_output(['gh','pr','diff','59','--repo','karaposu/tgdata'],text=True)
local=subprocess.check_output(['git','diff',expected['main']+'...'+expected['dev']],text=True)
norm=lambda s:re.sub(r'(@@ [^\n]*? @@)[^\n]*',r'\1',s)
assert norm(remote)==norm(local)
paths=git('diff','--name-only',expected['main'],expected['dev']).splitlines()
assert not any(p.startswith('devdocs/') for p in paths)
result=dict(result='PASS',main=expected['main'],dev=expected['dev'],merge_candidate=merge,parents=parents,tree=expected['tree'],positive=positive,refused=negative,tracked_hashes=len(manifest),published_diff_equal=True,paths=paths)
(HERE/'promotion-probes.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
