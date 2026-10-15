"""Check real wheel/sdist payloads against the qualified release candidate."""
import configparser
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import zipfile
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

ROOT = Path(sys.argv[1]).resolve()
VERSION = sys.argv[2]
EXPECTED = {str(path.relative_to(ROOT)): path.read_bytes() for path in (ROOT / 'tgdata').rglob('*.py')}
RUNTIME = {name: value for name, value in EXPECTED.items() if '/smoke_tests/' not in name}

def metadata(raw):
    parsed = BytesParser().parsebytes(raw)
    assert parsed['Name'] == 'tgdata'
    assert parsed['Version'] == VERSION
    assert parsed['Requires-Python'] == '>=3.7'
    reqs = [Requirement(raw) for raw in parsed.get_all('Requires-Dist', [])]
    assert len(reqs) == 3
    reqmap = {canonicalize_name(req.name): req for req in reqs}
    assert reqmap['telethon'].specifier == SpecifierSet('>=1.45,<2.0')
    assert reqmap['pandas'].specifier == SpecifierSet('>=1.0')
    assert reqmap['python-socks'].specifier == SpecifierSet('>=2.0')
    assert reqmap['python-socks'].extras == {'asyncio'}
    assert str(reqmap['python-socks'].marker) == 'extra == "proxy"'
    assert parsed.get_payload(decode=True).decode('utf-8').strip() == (ROOT / 'README.md').read_text().strip()
    return dict(name=parsed['Name'], version=parsed['Version'],
                requires_python=parsed['Requires-Python'], requires_dist=parsed.get_all('Requires-Dist'))

def entrypoints(raw):
    cp = configparser.ConfigParser()
    cp.read_string(raw.decode())
    assert cp['console_scripts']['tgdata-worker'] == 'tgdata.worker:main'

def check(path):
    if path.suffix == '.whl':
        with zipfile.ZipFile(path) as wheel:
            names = wheel.namelist()
            assert not any('/duncan/' in name or '/devdocs/work/' in name or name.endswith(('.session', '/.env', '/config.ini')) for name in names)
            package = {name: wheel.read(name) for name in names if name.startswith('tgdata/') and name.endswith('.py')}
            meta_name = next(name for name in names if name.endswith('.dist-info/METADATA'))
            ep_name = next(name for name in names if name.endswith('.dist-info/entry_points.txt'))
            info = metadata(wheel.read(meta_name)); entrypoints(wheel.read(ep_name))
    else:
        with tarfile.open(path) as archive:
            members = [member for member in archive.getmembers() if member.isfile()]
            assert not any('/duncan/' in m.name or '/devdocs/work/' in m.name or m.name.endswith(('.session', '/.env', '/config.ini')) for m in members)
            prefix = members[0].name.split('/')[0] + '/'
            package = {member.name[len(prefix):]: archive.extractfile(member).read()
                       for member in members if member.name.startswith(prefix + 'tgdata/') and member.name.endswith('.py')}
            meta = next(member for member in members if member.name == prefix + 'PKG-INFO')
            ep = next(member for member in members if member.name.endswith('tgdata.egg-info/entry_points.txt'))
            info = metadata(archive.extractfile(meta).read()); entrypoints(archive.extractfile(ep).read())
            readme = next(member for member in members if member.name == prefix + 'README.md')
            setup = next(member for member in members if member.name == prefix + 'setup.py')
            assert archive.extractfile(readme).read() == (ROOT / 'README.md').read_bytes()
            assert archive.extractfile(setup).read() == (ROOT / 'setup.py').read_bytes()
    assert package.keys() == EXPECTED.keys(), {'missing': sorted(EXPECTED.keys() - package.keys()), 'unexpected': sorted(package.keys() - EXPECTED.keys())}
    assert all(package[name] == value for name, value in EXPECTED.items()), 'Artifact source does not match the qualified candidate'
    assert not any('duncan' in name or name.endswith(('.session', '.env')) for name in package)
    return dict(file=path.name, result='PASS', sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                python_files=len(package), runtime_files=len(RUNTIME), metadata=info,
                worker_entry_point='tgdata.worker:main')

if __name__ == '__main__':
    reports = [check(Path(name)) for name in sys.argv[3:]]
    assert len(reports) == 2
    print(json.dumps(reports, indent=2))
