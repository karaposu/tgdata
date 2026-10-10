"""Stage4 inquiry evidence: actual SQLite/processes and the old isolated ledger.

No proposed Stage4 implementation, no Telegram source calls or project database.
"""
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import subprocess
import types
import tempfile


def connect(path):
    db = sqlite3.connect(Path(path).as_uri() + '?mode=rw', uri=True,
                         timeout=5, isolation_level=None)
    db.execute('PRAGMA synchronous=FULL')
    return db


def provision(path):
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE claims(id INTEGER PRIMARY KEY)')
    db.commit()
    db.close()


def claim_worker(path, barrier, output):
    db = connect(path)
    barrier.wait(timeout=10)
    db.execute('BEGIN IMMEDIATE')
    used = db.execute('SELECT COUNT(*) FROM claims').fetchone()[0]
    accepted = used < 3
    if accepted:
        db.execute('INSERT INTO claims DEFAULT VALUES')
    db.commit()
    db.close()
    output.put(accepted)


def crash_worker(path, when):
    db = connect(path)
    db.execute('BEGIN IMMEDIATE')
    db.execute('INSERT INTO claims DEFAULT VALUES')
    if when == 'after':
        db.commit()
    os._exit(17)


def count(path):
    db = connect(path)
    try:
        return db.execute('SELECT COUNT(*) FROM claims').fetchone()[0]
    finally:
        db.close()


def process_evidence(root):
    ctx = multiprocessing.get_context('spawn')
    path = root / 'race.sqlite3'
    provision(path)
    barrier, output = ctx.Barrier(7), ctx.Queue()
    workers = [ctx.Process(target=claim_worker, args=(str(path), barrier, output)) for _ in range(6)]
    for worker in workers:
        worker.start()
    barrier.wait(timeout=15)
    answers = [output.get(timeout=15) for _ in workers]
    for worker in workers:
        worker.join(timeout=15)
        assert worker.exitcode == 0
    assert sum(answers) == count(path) == 3
    output.close()
    exits = {}
    for phase in ('before', 'after'):
        path = root / ('exit-' + phase + '.sqlite3')
        provision(path)
        worker = ctx.Process(target=crash_worker, args=(str(path), phase))
        worker.start()
        worker.join(timeout=15)
        assert worker.exitcode == 17
        exits[phase] = count(path)
    assert exits == {'before': 0, 'after': 1}
    return dict(concurrent_workers=6, admitted=sum(answers), cap=3, recovered_after_exit=exits)


def missing_and_uncertain(root):
    missing = root / 'missing.sqlite3'
    try:
        connect(missing)
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError('rw created missing file')
    assert not missing.exists()
    path = root / 'lost-reply.sqlite3'
    provision(path)
    class LostReply(sqlite3.Connection):
        def commit(self):
            super().commit()
            raise sqlite3.OperationalError('injected after actual commit')
    db = sqlite3.connect(path, isolation_level=None, factory=LostReply)
    db.execute('PRAGMA synchronous=FULL')
    db.execute('BEGIN IMMEDIATE')
    db.execute('INSERT INTO claims DEFAULT VALUES')
    try:
        db.commit()
    except sqlite3.OperationalError:
        db.rollback()
    finally:
        db.close()
    assert count(path) == 1
    return dict(missing_rw_created=False, after_real_commit_error_used=1,
                error_is_injected=True)


def historical_ledger():
    source = subprocess.check_output(
        ['git', 'show', '8a43d23:tgdata/join_budget.py'],
        cwd=str(Path(__file__).resolve().parents[4]), text=True)
    module = types.ModuleType('historical_join_budget')
    sys.modules[module.__name__] = module
    exec(compile(source, '8a43d23/tgdata/join_budget.py', 'exec'), module.__dict__)
    return module


def old_ledger_evidence(root):
    module = historical_ledger()
    clock = [1000.0]
    path = root / 'old-window.sqlite3'
    ledger = module.JoinBudget(path, clock=lambda: clock[0])
    ledger.configure(222, 3)
    for moment in (1000.0, 1010.0, 1020.0):
        clock[0] = moment
        ledger._claim(222)
    reduced = ledger.configure(222, 1)
    assert reduced.next_available_at == 87420.0
    clock[0] = 900.0
    backwards = ledger.status(222)
    assert backwards.used == 3 and backwards.observed_at == 1020.0
    clock[0] = 87420.0
    assert ledger.status(222).remaining == 1

    damaged = root / 'old-damaged.sqlite3'
    prior = module.JoinBudget(damaged, clock=lambda: 1000.0)
    prior.configure(222, 1)
    prior._claim(222)
    before = prior.status(222).used
    db = sqlite3.connect(damaged)
    db.execute('DROP TABLE tgdata_join_attempts')
    db.commit()
    db.close()
    reopened = module.JoinBudget(damaged, clock=lambda: 1000.0)
    after = reopened.status(222).used
    reopened._claim(222)
    assert before == 1 and after == 0
    return dict(lowered_cap_next=87420.0, backwards_used=3, backwards_observed=1020.0,
                exact_boundary_remaining=1, dropped_attempt_table=dict(
                    before=before, after_reopen=after, another_claim_admitted=True))


def malformed_time_evidence(root):
    module = historical_ledger()
    observed = []
    for stamp in (-100000.0, 2000.0):
        path = root / ('bad-past.sqlite3' if stamp < 0 else 'bad-future.sqlite3')
        ledger = module.JoinBudget(path, clock=lambda: 1000.0)
        ledger.configure(222, 1)
        ledger._claim(222)
        db = sqlite3.connect(path)
        db.execute('UPDATE tgdata_join_attempts SET admitted_at=?', (stamp,))
        db.commit()
        db.close()
        status = ledger.status(222)
        observed.append(dict(stored_admitted_at=stamp, stored_clock=1000.0,
                             status_used=status.used, remaining=status.remaining,
                             next_available_at=status.next_available_at))
    assert observed[0]['remaining'] == 1 and observed[1]['next_available_at'] == 88400.0
    return observed


def main():
    with tempfile.TemporaryDirectory(prefix='tgdata-stage4-contract-') as temp:
        root = Path(temp)
        print(json.dumps({'sqlite_processes': process_evidence(root)}), flush=True)
        print(json.dumps({'open_commit_boundaries': missing_and_uncertain(root)}), flush=True)
        print(json.dumps({'historical_ledger': old_ledger_evidence(root)}), flush=True)
        print(json.dumps({'historical_corrupt_time': malformed_time_evidence(root)}), flush=True)


if __name__ == '__main__':
    main()
