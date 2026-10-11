"""Observe worker projection needs through the real Node JSON consumer."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata.group_operations import GroupJoin, GroupMetadata

JS = "let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>console.log(String(JSON.parse(s).query_id)));"
for ident in (2 ** 63 - 1, -(2 ** 63) + 1):
    result = GroupJoin(222, 'probe', GroupMetadata(7, -1000000000007, 'Probe', None,
                        'megagroup', 10), 'interaction_required', 123, ident).to_dict()
    plain = subprocess.check_output(['/usr/local/bin/node', '-e', JS],
                                    input=json.dumps(result).encode()).decode().strip()
    result['query_id'] = str(result['query_id'])
    projected = subprocess.check_output(['/usr/local/bin/node', '-e', JS],
                                        input=json.dumps(result).encode()).decode().strip()
    assert plain != str(ident) and projected == str(ident)
    print(json.dumps(dict(case='query_id_precision', original=str(ident),
                         numeric_json_received=plain, string_json_received=projected)))
print('PASS: worker wire needs decimal-string identifier projection; source Python values stay unchanged.')
