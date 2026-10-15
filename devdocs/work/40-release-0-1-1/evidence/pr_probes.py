"""Fresh version-PR provenance and artifact refusal probes."""
from pathlib import Path
import hashlib,io,json,runpy,subprocess,sys,tarfile,tempfile,zipfile
HERE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/tgdata-release-0.1.1-evidence/candidate')
BUILD=ROOT.parent/'dist';CANDIDATE='d8aa8e4214535d7e201167c68dbae788945420b8'
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
assert git('show','-s','--format=%P',CANDIDATE).split()==['7d9840fa725fada9592051fa561a2f901b8e154e','f92d165d8fc6668bc6506760064be60bb2f25baa']
assert git('diff',CANDIDATE,'f92d165d8fc6668bc6506760064be60bb2f25baa')==''
manifest=json.loads((HERE/'verification/result.json').read_text())['source_sha256']
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',CANDIDATE]))) as archive:
 for name,digest in manifest.items():assert hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest,name
sys.argv=[str(HERE/'check_artifacts.py'),str(ROOT),'0.1.1']
check=runpy.run_path(str(HERE/'check_artifacts.py'),run_name='release_checker')['check']
positive=[check(BUILD/'tgdata-0.1.1-py3-none-any.whl'),check(BUILD/'tgdata-0.1.1.tar.gz')]
negative=[]
def refuse(label,path,expected=(AssertionError,)):
 try:check(path)
 except expected as error:negative.append(dict(case=label,result='REFUSED',error_type=type(error).__name__))
 else:raise AssertionError('bad artifact accepted: '+label)
refuse('old actual published0.1 wheel',Path('/private/tmp/tgdata-release-0.1-evidence/published/tgdata-0.1-py3-none-any.whl'))
refuse('wrong-source0.0.9 wheel',Path('/private/tmp/tgdata-release-0.1-evidence/tgdata-0.0.9-py3-none-any.whl'),expected=(AssertionError,StopIteration))
with tempfile.TemporaryDirectory(prefix='tgdata011-negative-') as tmp:
 for kind in ('changed','missing'):
  bad=Path(tmp)/(kind+'.whl')
  with zipfile.ZipFile(BUILD/'tgdata-0.1.1-py3-none-any.whl') as src,zipfile.ZipFile(bad,'w') as dst:
   for item in src.infolist():
    data=src.read(item.filename)
    if item.filename=='tgdata/batch_heartbeat.py':
     if kind=='missing':continue
     data+=b'\n# unexpected artifact change\n'
    dst.writestr(item,data)
  refuse(kind+' heartbeat payload under valid0.1.1 metadata',bad)
r=dict(result='PASS',candidate=CANDIDATE,tree=git('rev-parse',CANDIDATE+'^{tree}'),matching_tested_sources=len(manifest),positive_artifacts=len(positive),negative_artifacts=negative)
(HERE/'fresh-pr-probes.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
