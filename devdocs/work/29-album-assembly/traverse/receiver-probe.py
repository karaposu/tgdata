"""Probe existing SQLite/value seams; no new album implementation or Telegram calls."""
import asyncio
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata import SQLiteSyncStore, SyncStorageError


async def main():
    results = {}
    with tempfile.TemporaryDirectory(prefix='tgdata29-existing-seams-') as temporary:
        root = Path(temporary)
        missing = root / 'known-missing.sqlite3'
        try:
            SQLiteSyncStore(missing, create=False)
        except SyncStorageError:
            assert not missing.exists()
            results['existing_store_reopen_missing_refuses_without_creation'] = True
        else:
            raise AssertionError('missing known store was recreated')

        path = root / 'known.sqlite3'
        first = SQLiteSyncStore(path)
        before = json.dumps({'retained': [101], 'revision': 1})
        after = json.dumps({'retained': [101, 102], 'revision': 2})
        assert await first.compare_and_swap(-1001, None, before)
        reopened = SQLiteSyncStore(path, create=False)
        assert await reopened.load(-1001) == before
        assert await reopened.load(-1002) is None
        assert await reopened.compare_and_swap(-1001, before, after)
        assert not await first.compare_and_swap(-1001, before, 'stale overwrite')
        assert await first.load(-1001) == after
        results['existing_store_absence_and_stale_cas_are_distinct'] = True
        with sqlite3.connect(path) as db:
            db.execute('DROP TABLE tgdata_sync_state')
        try:
            SQLiteSyncStore(path, create=False)
        except SyncStorageError:
            with sqlite3.connect(path) as db:
                assert db.execute("SELECT name FROM sqlite_master WHERE name='tgdata_sync_state'").fetchone() is None
            results['partial_known_schema_refuses_without_repair'] = True
        else:
            raise AssertionError('partial schema silently repaired')

        receiver = root / 'receiver.sqlite3'
        db = sqlite3.connect(receiver, isolation_level=None)
        db.execute('CREATE TABLE collections (name TEXT PRIMARY KEY)')
        db.execute('CREATE TABLE posts (collection TEXT, key TEXT, value TEXT, PRIMARY KEY(collection,key))')
        db.execute('CREATE TABLE receipts (collection TEXT, batch TEXT, PRIMARY KEY(collection,batch))')
        db.execute("INSERT INTO collections VALUES ('daily')")
        db.execute("INSERT INTO collections VALUES ('history')")
        try:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO posts VALUES (?,?,?)', ('daily', 'album', before))
            db.execute('INSERT INTO receipts VALUES (?,?)', ('daily', 'batch-a'))
            raise RuntimeError('synthetic pre-commit failure')
        except RuntimeError:
            db.rollback()
        assert db.execute('SELECT COUNT(*) FROM posts').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0] == 0
        results['actual_transaction_rolls_back_data_and_receipt'] = True

        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO posts VALUES (?,?,?)', ('daily', 'album', before))
        db.execute('INSERT INTO receipts VALUES (?,?)', ('daily', 'batch-a'))
        db.commit()
        # A lost caller reply after the real commit does not undo that commit.
        db.close()
        db = sqlite3.connect(receiver, isolation_level=None)
        assert db.execute('SELECT value FROM posts WHERE collection=?', ('daily',)).fetchone()[0] == before
        assert db.execute('SELECT batch FROM receipts WHERE collection=?', ('daily',)).fetchone()[0] == 'batch-a'
        results['committed_data_and_receipt_survive_reopen'] = True

        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO posts VALUES (?,?,?)', ('history', 'album', after))
        db.execute('INSERT INTO receipts VALUES (?,?)', ('history', 'batch-a'))
        db.commit()
        assert db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0] == 2
        assert db.execute('SELECT name FROM collections WHERE name=?', ('misspelled',)).fetchone() is None
        results['same_content_receipt_is_scoped_by_collection'] = True

        second = sqlite3.connect(receiver, timeout=0, isolation_level=None)
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE posts SET value=? WHERE collection=?', (after, 'daily'))
        try:
            second.execute('BEGIN IMMEDIATE')
        except sqlite3.OperationalError:
            results['receiver_write_transaction_excludes_stale_writer'] = True
        else:
            raise AssertionError('concurrent write admitted')
        db.commit()
        second.execute('BEGIN IMMEDIATE')
        assert second.execute('SELECT value FROM posts WHERE collection=?', ('daily',)).fetchone()[0] == after
        second.rollback()
        second.close()
        db.close()
        results['lookup_inside_retried_transaction_sees_current_state'] = True

    assert len(results) == 8 and all(results.values())
    report = {'result': 'PASS', 'checks': results,
              'scope': 'actual existing SQLiteSyncStore and SQLite transaction behavior; synthetic data; no new album code or Telegram behavior claim'}
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    asyncio.run(main())
