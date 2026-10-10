"""Actual shared-file ReadBudget/SQLite composition, before Stage4 runtime code."""
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tgdata import ReadBudget


def main():
    sql = re.search(r'```sql\n(.*?)```', Path(__file__).with_name('plan.md').read_text(),
                    flags=re.S).group(1)
    with tempfile.TemporaryDirectory(prefix='tgdata-stage4-prebuild-') as temp:
        path = Path(temp) / 'shared.sqlite3'
        read = ReadBudget(path, clock=lambda: 1000)
        read.configure(222, 10)
        db = sqlite3.connect(path, isolation_level=None)
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        db.executescript('BEGIN IMMEDIATE;\n' + sql)
        db.execute('INSERT INTO tgdata_join_meta VALUES(1,1)')
        db.execute('INSERT INTO tgdata_join_accounts VALUES(222,3,1000)')
        db.execute('INSERT INTO tgdata_join_attempts(account_id,admitted_at) VALUES(222,1000)')
        db.commit()
        schema = {name: db.execute('PRAGMA table_info(' + name + ')').fetchall()
                  for name in ('tgdata_join_meta', 'tgdata_join_accounts', 'tgdata_join_attempts')}
        fk = db.execute('PRAGMA foreign_key_list(tgdata_join_attempts)').fetchall()
        index = db.execute('PRAGMA index_info(tgdata_join_attempts_time)').fetchall()
        assert fk == [(0, 0, 'tgdata_join_accounts', 'account_id', 'account_id', 'NO ACTION', 'NO ACTION', 'NONE')]
        assert index == [(0, 1, 'account_id'), (1, 2, 'admitted_at')]
        try:
            db.execute('INSERT INTO tgdata_join_attempts(account_id,admitted_at) VALUES(999,1000)')
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError('orphan accepted')
        db.close()
        reservation = read._reserve(222, 5)
        read._settle(reservation, 2)
        read.configure(222, 20)
        reopened = ReadBudget(path, clock=lambda: 1000)
        status = reopened.status(222)
        assert (status.used, status.reserved, status.remaining) == (2, 0, 18)
        db = sqlite3.connect(path.as_uri() + '?mode=rw', uri=True)
        assert db.execute('SELECT count(*) FROM tgdata_join_attempts').fetchone() == (1,)
        assert db.execute('SELECT daily_limit FROM tgdata_join_accounts').fetchone() == (3,)
        db.close()
        print(json.dumps(dict(result='PASS', join_used=1, read_used=2, read_remaining=18,
                              schema=schema, foreign_key=fk, index=index)))


if __name__ == '__main__':
    main()
