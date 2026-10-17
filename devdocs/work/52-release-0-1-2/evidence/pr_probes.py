"""Fresh artifact/provenance refusal probes for the release version PR."""
from pathlib import Path
import hashlib,io,json,runpy,subprocess,sys,tarfile,tempfile,zipfile
HERE=Path(__file__).resolve().parent
ROOT=Path('/private/tmp/tgdata-release-0.1.2-evidence/candidate')
DIST=ROOT.parent/'dist';HEAD=sys.argv[1]
manifest=json.loads((HERE/'candidate.json').read_text())
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',HEAD]))) as archive:
 for name,digest in manifest['tracked_sha256'].items():assert hashlib.sha256(archive.extractfile(name).read()).hexdigest()==digest,name
sys.argv=[str(HERE/'check_artifacts.py'),str(ROOT),'0.1.2']
check=runpy.run_path(str(HERE/'check_artifacts.py'),run_name='release_checker')['check']
positive=[check(DIST/'tgdata-0.1.2-py3-none-any.whl'),check(DIST/'tgdata-0.1.2.tar.gz')]
negative=[]
def refuse(label,path):
 try:check(path)
 except (AssertionError,StopIteration) as error:negative.append(dict(case=label,result='REFUSED',error=type(error).__name__))
 else:raise AssertionError('bad artifact accepted: '+label)
refuse('actual published0.1.1 wheel',Path('/private/tmp/tgdata-release-0.1.1-evidence/published/tgdata-0.1.1-py3-none-any.whl'))
with tempfile.TemporaryDirectory(prefix='tgdata012-negative-') as tmp:
 for mode in ('missing_input','changed_login','wrong_entry','wrong_version'):
  bad=Path(tmp)/(mode+'.whl')
  with zipfile.ZipFile(DIST/'tgdata-0.1.2-py3-none-any.whl') as source,zipfile.ZipFile(bad,'w') as target:
   for item in source.infolist():
    data=source.read(item.filename)
    if mode=='missing_input' and item.filename=='tgdata/_terminal_input.py':continue
    if mode=='changed_login' and item.filename=='tgdata/login_cli.py':data+=b'\n# unexpected mutation\n'
    if mode=='wrong_entry' and item.filename.endswith('entry_points.txt'):data=data.replace(b'tgdata.login_cli:main',b'tgdata.worker:main')
    if mode=='wrong_version' and item.filename.endswith('/METADATA'):data=data.replace(b'Version: 0.1.2',b'Version: 0.1.1')
    target.writestr(item,data)
  refuse(mode,bad)
 bad=Path(tmp)/'missing-profile.tar.gz'
 with tarfile.open(DIST/'tgdata-0.1.2.tar.gz') as source,tarfile.open(bad,'w:gz') as target:
  for item in source.getmembers():
   if item.name.endswith('/tgdata/group_profile.py'):continue
   target.addfile(item,source.extractfile(item) if item.isfile() else None)
 refuse('sdist_missing_profile',bad)
report=dict(result='PASS',head=HEAD,tracked_source_hashes=len(manifest['tracked_sha256']),positive_artifacts=len(positive),negative=negative)
(HERE/'fresh-pr-probes.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
