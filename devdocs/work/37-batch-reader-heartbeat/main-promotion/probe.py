"""Fresh promotion provenance/import probes; never creates a release or tag."""
from pathlib import Path
import hashlib
import inspect
import json
import re
import socket
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(sys.argv[1]).resolve();HERE=Path(__file__).resolve().parent
WORK=HERE.parent
BASE='1ddfb4ec7d43a05e36f464646fd4f867e5076c0c'
HEAD='7d9840fa725fada9592051fa561a2f901b8e154e'
CANDIDATE='865e0951a187ad8641b3e81ab4dca4e70ece405b'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
prior=json.loads((WORK/'verification-merge/result.json').read_text())
assert prior['result']=='PASS'
assert git('rev-parse','HEAD')==CANDIDATE
assert git('show','-s','--format=%P','HEAD').split()==[BASE,HEAD]
assert git('rev-parse','HEAD^{tree}')==git('rev-parse',HEAD+'^{tree}')==prior['merged_tree']
assert git('diff',HEAD,'HEAD')==''
assert git('diff','e5cdad77ff6af41f21503fc43fe3180d5213a41e',BASE)==''
for name,digest in prior['source_sha256'].items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
changed=set(git('diff','--name-only',BASE,'HEAD').splitlines())
expected=set()
for merge in ('35c4362d4e6a8fc92e695def67bffcac192dc073','38dee0bbde3259cd2d34a91206afe483132eca59',HEAD):
 subprocess.run(['git','merge-base','--is-ancestor',merge,HEAD],cwd=ROOT,check=True)
 expected.update(git('diff','--name-only',merge+'^1',merge).splitlines())
assert changed==expected and len(changed)==21
assert not any(p.startswith(('devdocs/','duncan/','.github/')) for p in changed)
workflow=git('show','HEAD:.github/workflows/python-publish.yml')
assert workflow==git('show',BASE+':.github/workflows/python-publish.yml')
assert 'on:\n  release:\n    types: [published]' in workflow and '\n  push:' not in workflow
assert git('show','HEAD:setup.py')==git('show',BASE+':setup.py')
get_version=lambda text:re.search(r'^__version__\s*=\s*[\'\"]([^\'\"]+)',text,re.M).group(1)
assert get_version(git('show','HEAD:tgdata/__init__.py'))==get_version(git('show',BASE+':tgdata/__init__.py'))=='0.1'
sys.path.insert(0,str(ROOT))
with patch.object(socket.socket,'connect',side_effect=AssertionError('no network')),patch.object(socket.socket,'connect_ex',side_effect=AssertionError('no network')):
 import tgdata
 from examples.photo_trails import _demo_batch
 assert Path(tgdata.__file__).resolve()==ROOT/'tgdata/__init__.py'
 assert not tgdata.PhotoTrailPolicy().enabled
 for owner,names in ((tgdata.TgData,('get_message_batch','sync_group','prepare_backfill')),
                     (tgdata.AccountPool,('read','get_message_batch','sync_group','prepare_backfill'))):
  for name in names:assert inspect.signature(getattr(owner,name)).parameters['heartbeat'].default is None
 raw=_demo_batch(0,3)
 originals=tgdata.assemble_albums(raw,previous={key:None for key in tgdata.album_post_ids(raw)})
 old=tgdata.fold_photo_trails(originals,policy=tgdata.PhotoTrailPolicy(enabled=True))
 assert len(old.groups)==1 and old.folded_photos==2
 later=_demo_batch(3,1);by_key={p.post_id:p for p in originals}
 changed_posts=tgdata.assemble_albums(later,previous={key:by_key[key] for key in tgdata.album_post_ids(later)})
 for post in changed_posts:by_key[post.post_id]=post
 current=tgdata.fold_photo_trails(list(by_key.values()),policy=tgdata.PhotoTrailPolicy(enabled=True))
 assert len(current.groups)==2 and current.folded_photos==0 and old.folded_photos==2
 assert sum(len(p.member_ids) for p in current.posts)==4
report=dict(result='PASS',base=BASE,head=HEAD,candidate=CANDIDATE,tree=prior['merged_tree'],
 whole_tree_equal=True,matching_tested_python_files=len(prior['source_sha256']),changed_paths=sorted(changed),
 reviewed_feature_merges=3,prior_full_offline=prior['executed_offline'],prior_demos=prior['demos'],prior_live_skips=prior['live_skips'],
 version='0.1',publishing_trigger='published GitHub release only',new_tag_or_release=False,
 fresh_import='actual merge checkout',heartbeat_signatures=7,album_and_photo_replacement='PASS')
(HERE/'candidate-proof.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
