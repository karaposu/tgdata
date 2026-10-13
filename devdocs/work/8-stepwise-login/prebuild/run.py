"""Run the full isolated candidate; production files remain untouched."""
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import textwrap
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from tgdata import connection_engine


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


source = textwrap.dedent(inspect.getsource(connection_engine.ConnectionEngine._new_client))
assert 'session_file: Optional[str] = None, **client_options' in source
source = source.replace('session_file: Optional[str] = None, **client_options',
                        'session_file: Optional[str] = None, *, _client_base=None, **client_options')
assert source.count('_client_class(TelegramClient)') == 1
source = source.replace('_client_class(TelegramClient)', '_client_class(_client_base or TelegramClient)')
namespace = {}
exec(compile(source, '<planned-private-factory-seam>', 'exec'),
     connection_engine.__dict__, namespace)
load('tgdata.login', HERE / 'candidate.py')
suite = load('tgdata8_candidate_tests', HERE / 'test_login.py')
manifest = dict(runtime='Telethon 1.45.0 / Python3.11',
                scope='native SDK/SRP/codec with controlled wire; no live provider qualification',
                sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                        for name in ('candidate.py', 'test_login.py', 'run.py')},
                factory_source_sha256=hashlib.sha256(source.encode()).hexdigest())
(HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
with patch.object(connection_engine.ConnectionEngine, '_new_client', namespace['_new_client']):
    failures = suite.run()
raise SystemExit(bool(failures))
