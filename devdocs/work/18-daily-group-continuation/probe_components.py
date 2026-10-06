"""Pre-plan component observations, real SDK/files/SQLite; never contacts Telegram."""
import asyncio
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tgdata import MessageBatch
from tgdata.smoke_tests import test_19_message_batches as b


def sqlite_observations(root):
    path = root / 'atomic.sqlite3'
    pending = {'after_id': 100, 'pending': json.loads(b.GOLDEN)}
    accepted = {'after_id': 101, 'pending': None}
    with sqlite3.connect(str(path)) as db:
        db.execute('CREATE TABLE state (key INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
        db.execute('INSERT INTO state VALUES (?, ?)', (7, json.dumps(pending)))
    script = '''import os,sqlite3,sys
db=sqlite3.connect(sys.argv[1], isolation_level=None)
db.execute('BEGIN IMMEDIATE')
db.execute('UPDATE state SET payload = ? WHERE key = 7', (sys.argv[2],))
if sys.argv[3] == 'commit': db.commit()
os._exit(19)
'''
    for mode, expected in [('abort', pending), ('commit', accepted)]:
        result = subprocess.run([sys.executable, '-c', script, str(path), json.dumps(accepted), mode])
        assert result.returncode == 19
        with sqlite3.connect(str(path)) as db:
            actual = json.loads(db.execute('SELECT payload FROM state WHERE key = 7').fetchone()[0])
        assert actual == expected
        print('PASS sqlite process exit', mode, actual['after_id'], actual['pending'] is None)
    with sqlite3.connect(str(path), isolation_level=None) as db:
        db.execute('BEGIN IMMEDIATE')
        count = db.execute('UPDATE state SET payload = ? WHERE key = 7 AND payload = ?',
                           (json.dumps(pending), json.dumps(pending))).rowcount
        db.commit()
        assert count == 0
    print('PASS stale expected payload refuses replacement')
    nested = json.loads(json.dumps(pending))['pending']
    replay = MessageBatch(nested)
    assert replay.to_json() == b.GOLDEN and replay.batch_id == b.GOLDEN_ID
    print('PASS pending nested JSON preserves exact canonical batch')


async def sdk_observations(root):
    b.f.TMP = root
    try:
        tg, _, sender = b.instance()
        batch = await tg.get_message_batch(-1000000000007, after_id=100, limit=2)
        assert batch.chat_id == -1000000000007
        assert batch.after_id == 100 and batch.next_after_id == 102
        assert [row['id'] for row in batch.messages] == ['101', '102']
        print('PASS real SDK canonical group and exclusive continuation')
        await b.test_budget_prefix_empty_and_resume()
        print('PASS real SDK/read-budget interrupted prefix and resume')
        await b.test_saved_replay_and_ack_order()
        print('PASS immutable replay after lost receiver acknowledgment')
    finally:
        for client in b.f.CLIENTS:
            await client.disconnect()
        b.f.CLIENTS.clear()


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='tgdata18_components_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        root = Path(tmp)
        sqlite_observations(root)
        asyncio.run(sdk_observations(root))
