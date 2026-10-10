"""Fresh PR24 probes, independent of test35's fixtures. No Telegram operations."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import json
import math
import multiprocessing
from pathlib import Path
import random
import sqlite3
import sys
import tempfile
import threading
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tgdata import JoinBudget, JoinBudgetExceeded, JoinBudgetStorageError, ReadBudget
from tgdata import join_budget as module
from tgdata.health import classify
from telethon import errors

CONNECT = sqlite3.connect


def count(path):
    db = CONNECT(path)
    try:
        return db.execute('SELECT count(*) FROM tgdata_join_attempts').fetchone()[0]
    finally:
        db.close()


def creation_worker(path, barrier, output):
    barrier.wait(timeout=30)  # Before constructor, unlike the implementation race.
    budget = JoinBudget(path, create=True, clock=lambda: 1000)
    budget.configure(222, 3)
    try:
        budget._claim(222)
    except JoinBudgetExceeded:
        output.put(False)
    else:
        output.put(True)


def provision_race(root):
    path = root / 'creation.sqlite3'
    ctx = multiprocessing.get_context('spawn')
    barrier, output = ctx.Barrier(7), ctx.Queue()
    processes = [ctx.Process(target=creation_worker, args=(str(path), barrier, output)) for _ in range(6)]
    try:
        for process in processes:
            process.start()
        barrier.wait(timeout=30)
        answers = [output.get(timeout=30) for _ in processes]
        for process in processes:
            process.join(timeout=30)
            assert process.exitcode == 0
        assert sum(answers) == count(path) == 3
        return dict(workers=6, admitted=sum(answers), persisted=count(path))
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=5)
        output.close()
        output.join_thread()


def reference_model(root):
    rng = random.Random(70204)
    path = root / 'model.sqlite3'
    now = [1000.0]
    budget = JoinBudget(path, create=True, clock=lambda: now[0])
    policies, horizons, stamps = {}, {}, {}
    decisions = dict(admitted=0, denied=0, configurations=0, observations=0)
    for step in range(600):
        owner = rng.choice((222, 333, 444))
        now[0] = max(0, now[0] + rng.choice((-86401, -1, 0, 0.25, 17, 3600, 86400)))
        operation = rng.choice(('configure', 'status', 'claim'))
        if owner not in policies:
            operation = 'configure'
        cap = rng.randrange(5) if operation == 'configure' else policies[owner]
        effective = max(now[0], horizons.get(owner, 0))
        live = [at for at in stamps.get(owner, []) if effective < at + 86400]
        policies[owner], horizons[owner], stamps[owner] = cap, effective, live
        available = max(0, cap - len(live))
        next_at = None
        if not available and cap:
            # Independent simulation: expire tied times until a slot exists.
            for candidate in sorted(set(at + 86400 for at in live)):
                if sum(at + 86400 > candidate for at in live) < cap:
                    next_at = candidate
                    break
        expected = dict(account_id=owner, limit=cap, used=len(live), remaining=available,
                        observed_at=effective, next_available_at=next_at)
        if operation == 'configure':
            result = budget.configure(owner, cap)
            decisions['configurations'] += 1
        elif operation == 'status':
            result = budget.status(owner)
            decisions['observations'] += 1
        else:
            if available:
                assert budget._claim(owner) is None
                stamps[owner].append(effective)
                expected['used'] += 1
                expected['remaining'] -= 1
                if not expected['remaining']:
                    expected['next_available_at'] = min(stamps[owner]) + 86400
                result = budget.status(owner)
                decisions['admitted'] += 1
            else:
                try:
                    budget._claim(owner)
                except JoinBudgetExceeded as error:
                    result = error.status
                else:
                    raise AssertionError('admitted against the reference model')
                decisions['denied'] += 1
        assert asdict(result) == expected, (step, operation, asdict(result), expected)
        if step % 23 == 0:
            budget = JoinBudget(path, clock=lambda: now[0])
    return dict(transitions=600, accounts=3, **decisions)


def native_busy_commit(root):
    path = root / 'native-busy.sqlite3'
    budget = JoinBudget(path, create=True, clock=lambda: 1000)
    budget.configure(222, 1)
    reader = CONNECT(path, isolation_level=None)
    reader.execute('BEGIN')
    reader.execute('SELECT * FROM tgdata_join_accounts').fetchall()
    started = time.monotonic()
    try:
        try:
            budget._claim(222)  # Real SQLite COMMIT waits on the reader, then fails.
        except JoinBudgetStorageError as error:
            assert 'OperationalError' in str(error)
            assert classify(error) is None
            name = type(error).__name__
        else:
            raise AssertionError('writer unexpectedly committed past reader')
    finally:
        reader.rollback()
        reader.close()
    elapsed = time.monotonic() - started
    assert count(path) == 0
    budget._claim(222)  # Writer rollback and connection close released the lock.
    assert count(path) == 1
    return dict(error=name, native_wait_seconds=round(elapsed, 3), after_failure=0, after_retry=1)


def lost_return_competitor(root):
    path = root / 'lost-return.sqlite3'
    first = JoinBudget(path, create=True, clock=lambda: 1000)
    second = JoinBudget(path, clock=lambda: 1000)
    first.configure(222, 1)
    committed, finish = threading.Event(), threading.Event()
    worker_id = []

    class Connection(sqlite3.Connection):
        def close(self):
            super().close()
            if threading.get_ident() in worker_id:
                committed.set()
                assert finish.wait(timeout=10)
                raise OSError('synthetic secret must not escape')

    def connect(*args, **kwargs):
        return CONNECT(*args, factory=Connection, **kwargs)

    def attempt():
        worker_id.append(threading.get_ident())
        try:
            first._claim(222)
        except JoinBudgetStorageError as error:
            assert str(error) == 'Join-budget close failed (OSError)'
            return 'storage_error'
        raise AssertionError('first obtained permission')

    with patch.object(module.sqlite3, 'connect', connect), ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(attempt)
        try:
            assert committed.wait(timeout=10)
            try:
                second._claim(222)
            except JoinBudgetExceeded:
                competitor = 'denied'
            else:
                raise AssertionError('competitor reused uncertain first claim')
        finally:
            finish.set()
        first_outcome = future.result(timeout=10)
    assert count(path) == 1
    return dict(first=first_outcome, competitor=competitor, persisted=1)


def namespace_coexistence(root):
    path = root / 'coexist.sqlite3'
    join = JoinBudget(path, create=True, clock=lambda: 1000)
    read = ReadBudget(path, clock=lambda: 1000)
    join.configure(222, 4)
    read.configure(222, 10)
    db = CONNECT(path)
    db.execute('CREATE TABLE customer_data(value TEXT)')
    db.execute('INSERT INTO customer_data VALUES(?)', ('untouched',))
    db.commit()
    db.close()
    token = read._reserve(222, 5)
    for _ in range(3):
        join._claim(222)
    read._settle(token, 2)
    db = CONNECT(path)
    assert db.execute('SELECT value FROM customer_data').fetchall() == [('untouched',)]
    db.close()
    assert (read.status(222).used, join.status(222).used) == (2, 3)
    return dict(read_used=2, join_used=3, unrelated_table='untouched')


def corrupted_file_and_callback_context(root):
    path = root / 'not-a-database.sqlite3'
    raw = b'NOT SQLITE: synthetic private content' * 10
    path.write_bytes(raw)
    try:
        raise errors.AuthKeyUnregisteredError(None)
    except errors.AuthKeyUnregisteredError:
        try:
            JoinBudget(path, create=True)
        except JoinBudgetStorageError as error:
            assert str(error) == 'Join-budget storage failed (DatabaseError)'
            assert classify(error) is None
        else:
            raise AssertionError('corrupt file accepted')
    assert path.read_bytes() == raw
    return dict(error='JoinBudgetStorageError(DatabaseError)', health=None, file_unchanged=True)


def fractional_deadline(root):
    path = root / 'fractional.sqlite3'
    clock = [1000.2]
    budget = JoinBudget(path, create=True, clock=lambda: clock[0])
    budget.configure(222, 1)
    budget._claim(222)
    estimate = budget.status(222).next_available_at
    clock[0] = estimate
    at_hint = budget.status(222)
    try:
        budget._claim(222)
    except JoinBudgetExceeded as error:
        outcome = 'denied'
        assert error.retry_after == 0
    else:
        outcome = 'admitted'
    # Advance one representable step at the returned deadline.
    next_float = math.nextafter(estimate, math.inf)
    clock[0] = next_float
    after_tick = budget.status(222)
    return dict(admitted_at=1000.2, hint=estimate, observed=at_hint.observed_at,
                remaining_at_hint=at_hint.remaining, retry_after=at_hint.retry_after,
                outcome_at_hint=outcome, next_float_delta_seconds=next_float-estimate,
                remaining_after_tick=after_tick.remaining)


def main():
    with tempfile.TemporaryDirectory(prefix='tgdata24-fresh-review-') as temp:
        root = Path(temp)
        for function in (provision_race, reference_model, native_busy_commit,
                         lost_return_competitor, namespace_coexistence,
                         corrupted_file_and_callback_context, fractional_deadline):
            result = function(root)
            print(json.dumps(dict(probe=function.__name__, result=result)), flush=True)


if __name__ == '__main__':
    main()
