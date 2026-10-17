"""Download actual PyPI0.1.3 files and validate the advertised hashes."""
import hashlib,json,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEST=Path('/private/tmp/tgdata-release-0.1.3-evidence/published');DEST.mkdir(exist_ok=True)
with urllib.request.urlopen('https://pypi.org/pypi/tgdata/0.1.3/json',timeout=25) as response:info=json.load(response)
assert info['info']['name']=='tgdata' and info['info']['version']=='0.1.3'
expected={'tgdata-0.1.3-py3-none-any.whl','tgdata-0.1.3.tar.gz'}
assert {item['filename'] for item in info['urls']}==expected
rows=[]
for item in info['urls']:
 assert not item['yanked']
 assert item['url'].startswith('https://files.pythonhosted.org/')
 with urllib.request.urlopen(item['url'],timeout=40) as response:content=response.read()
 digest=hashlib.sha256(content).hexdigest();assert digest==item['digests']['sha256']
 (DEST/item['filename']).write_bytes(content)
 rows.append(dict(filename=item['filename'],url=item['url'],sha256=digest,uploaded=item['upload_time_iso_8601'],yanked=item['yanked'],bytes=len(content)))
(HERE/'published').mkdir(exist_ok=True)
(HERE/'published/pypi-downloads.json').write_text(json.dumps(dict(result='PASS',version='0.1.3',files=rows),indent=2)+'\n')
print(json.dumps(rows,indent=2))
