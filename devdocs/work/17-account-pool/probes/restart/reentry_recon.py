"""Observe a state provider entering actual administration on the unchanged pool."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t

async def main(directory):
    t.f.TMP = t.d.TMP = directory
    e = await t.setup()
    source = e.pool._sources[111]
    factory = source._new_client
    def rebuilt(*a, **kw):
        client = factory(*a, **kw)
        client._sender = t.b.Sender()
        client._sender.account = 111
        return client
    actual = e.store
    entered = []
    class Backend:
        async def load(self):
            if not entered:
                entered.append(True)
                await e.pool.recheck_account(111)
            return await actual.load()
        async def compare_and_swap(self, *a):
            return await actual.compare_and_swap(*a)
    e.pool._store = Backend()
    before = json.loads(await actual.load())['accounts']['111']['verified_at']
    try:
        with patch.object(source, '_new_client', side_effect=rebuilt):
            status = await e.pool.get_pool_status()
        after = json.loads(await actual.load())['accounts']['111']['verified_at']
        assert before is None and after == t.f.NOW and status.accounts[0].verified_at == after
        print(json.dumps(dict(caller='get_pool_status', provider_entered='recheck_account',
                             actual_verified_write=True, local_refusal=False)))
    finally:
        await e.pool.close()

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory() as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(main(Path(directory)))
