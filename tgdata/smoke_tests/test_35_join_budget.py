"""Offline join allowance: real SQLite, spawned processes and injected faults.

Run with python -m tgdata.smoke_tests.test_35_join_budget. No repository history,
credentials or Telegram connection is needed. Process exits are not power-loss tests.
"""

import asyncio
from dataclasses import FrozenInstanceError
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tgdata import ReadBudget
from tgdata import join_budget as j
from tgdata.health import classify
from telethon import errors


REAL_CONNECT = sqlite3.connect
SECRET = 'private-path-or-callback-content'


class Clock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


class FaultConnection:
    """Delegate every real operation; hooks inject before/after failures only."""
    def __init__(self, db, hook):
        self.db, self.hook = db, hook

    def run(self, operation, *args):
        self.hook(operation, 'before', args)
        value = getattr(self.db, operation)(*args)
        self.hook(operation, 'after', args)
        return value

    def execute(self, *args):
        return self.run('execute', *args)

    def commit(self):
        return self.run('commit')

    def rollback(self):
        return self.run('rollback')

    def close(self):
        return self.run('close')


def faults(hook):
    def connect(*args, **kwargs):
        return FaultConnection(REAL_CONNECT(*args, **kwargs), hook)
    return patch.object(j.sqlite3, 'connect', connect)


def compete(path, owner, barrier, output):
    budget = j.JoinBudget(path, clock=lambda: 1000)
    barrier.wait(timeout=30)
    try:
        budget._claim(owner)
    except j.JoinBudgetExceeded:
        output.put((owner, False))
    else:
        output.put((owner, True))


def exit_during_commit(path, phase):
    budget = j.JoinBudget(path, clock=lambda: 1000)

    def hook(operation, when, args):
        if operation == 'commit' and when == phase:
            os._exit(23)

    with faults(hook):
        budget._claim(222)
    raise AssertionError('process did not exit at commit')


class JoinBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tgdata-join-budget-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'allowance.sqlite3'
        self.clock = Clock()
        self.budget = j.JoinBudget(self.path, create=True, clock=self.clock)

    def sql(self, command, parameters=()):
        db = REAL_CONNECT(self.path)
        try:
            rows = db.execute(command, parameters).fetchall()
            db.commit()
            return rows
        finally:
            db.close()

    def state(self):
        return (self.sql('SELECT * FROM tgdata_join_accounts ORDER BY account_id'),
                self.sql('SELECT * FROM tgdata_join_attempts ORDER BY id'))

    def filled(self, cap=1):
        self.budget.configure(222, cap)
        for _ in range(cap):
            self.budget._claim(222)

    def assert_refuses_without_change(self, call, error=j.JoinBudgetStorageError):
        before = self.state()
        with self.assertRaises(error):
            call()
        self.assertEqual(self.state(), before)

    def test_explicit_creation_and_reopen(self):
        path = self.root / 'new.sqlite3'
        with self.assertRaises(j.JoinBudgetStorageError):
            j.JoinBudget(path)
        self.assertFalse(path.exists())
        budget = j.JoinBudget(path, create=True, clock=self.clock)
        budget.configure(222, 2)
        budget._claim(222)
        for create in (False, True):
            reopened = j.JoinBudget(path, create=create, clock=self.clock)
            self.assertEqual((reopened.status(222).used, reopened.status(222).remaining), (1, 1))

    def test_missing_namespace_needs_explicit_creation(self):
        path = self.root / 'read.sqlite3'
        read = ReadBudget(path, clock=self.clock)
        read.configure(222, 10)
        with self.assertRaises(j.JoinBudgetStorageError):
            j.JoinBudget(path)
        j.JoinBudget(path, create=True).configure(222, 0)
        self.assertEqual(read.status(222).remaining, 10)

    def test_paths_and_constructor_options(self):
        for bad in (None, True, 7, b'bytes', '', ':memory:', 'file:test?mode=memory'):
            with self.subTest(bad=bad), self.assertRaises(j.JoinBudgetConfigError):
                j.JoinBudget(bad, create=True)
        for kwargs in ({'create': 1}, {'create': None}, {'clock': None}):
            with self.subTest(kwargs=kwargs), self.assertRaises(j.JoinBudgetConfigError):
                j.JoinBudget(self.path, **kwargs)
        with self.assertRaises(j.JoinBudgetStorageError):
            j.JoinBudget(self.root / 'missing-parent' / 'file', create=True)
        self.assertFalse((self.root / 'missing-parent').exists())
        odd = self.root / 'spaces ? # % ü.sqlite3'
        budget = j.JoinBudget(odd, create=True, clock=self.clock)
        budget.configure(222, 0)
        self.assertEqual(j.JoinBudget(odd, clock=self.clock).status(222).limit, 0)

    def test_missing_state_after_open_is_not_recreated(self):
        self.path.unlink()
        for method in (lambda: self.budget.configure(222, 1), lambda: self.budget.status(222),
                       lambda: self.budget._claim(222)):
            with self.assertRaises(j.JoinBudgetStorageError):
                method()
            self.assertFalse(self.path.exists())

    def test_partial_schemas_are_not_repaired(self):
        for name in ('tgdata_join_meta', 'tgdata_join_accounts', 'tgdata_join_attempts', j._INDEX):
            with self.subTest(name=name):
                path = self.root / (name + '.sqlite3')
                j.JoinBudget(path, create=True)
                db = REAL_CONNECT(path)
                db.execute('DROP {} {}'.format('INDEX' if name == j._INDEX else 'TABLE', name))
                before = db.execute('SELECT type,name,sql FROM sqlite_master ORDER BY name').fetchall()
                db.close()
                for create in (False, True):
                    with self.assertRaises(j.JoinBudgetStorageError):
                        j.JoinBudget(path, create=create)
                db = REAL_CONNECT(path)
                self.assertEqual(before, db.execute('SELECT type,name,sql FROM sqlite_master ORDER BY name').fetchall())
                db.close()

    def test_schema_damage_refuses(self):
        changes = [
            ['UPDATE tgdata_join_meta SET version=2'],
            ['DELETE FROM tgdata_join_meta'],
            ['PRAGMA ignore_check_constraints=ON', 'INSERT INTO tgdata_join_meta VALUES(2,1)'],
            ['DROP TABLE tgdata_join_meta', 'CREATE VIEW tgdata_join_meta AS SELECT 1 AS id, 1 AS version'],
            ['ALTER TABLE tgdata_join_accounts ADD COLUMN extra TEXT'],
            ['DROP TABLE tgdata_join_accounts', 'CREATE TABLE tgdata_join_accounts '
             '(account_id INTEGER, daily_limit INTEGER NOT NULL, last_clock REAL NOT NULL)'],
            ['DROP TABLE tgdata_join_attempts', 'CREATE TABLE tgdata_join_attempts '
             '(id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL, admitted_at REAL NOT NULL)',
             'CREATE INDEX tgdata_join_attempts_time ON tgdata_join_attempts(account_id,admitted_at)'],
            ['DROP INDEX tgdata_join_attempts_time', 'CREATE UNIQUE INDEX tgdata_join_attempts_time '
             'ON tgdata_join_attempts(account_id,admitted_at)'],
            ['DROP INDEX tgdata_join_attempts_time', 'CREATE INDEX tgdata_join_attempts_time '
             'ON tgdata_join_attempts(admitted_at,account_id)'],
            ['DROP INDEX tgdata_join_attempts_time', 'CREATE INDEX tgdata_join_attempts_time '
             'ON tgdata_join_attempts(account_id,admitted_at) WHERE account_id=222'],
        ]
        for number, statements in enumerate(changes):
            with self.subTest(number=number):
                path = self.root / ('damage{}.sqlite3'.format(number))
                ledger = j.JoinBudget(path, create=True)
                db = REAL_CONNECT(path)
                for statement in statements:
                    db.execute(statement)
                db.commit()
                db.close()
                for call in (lambda: j.JoinBudget(path, create=True), lambda: ledger.configure(222, 1)):
                    with self.assertRaises(j.JoinBudgetStorageError):
                        call()

    def test_orphaned_claims_cannot_be_reenrolled(self):
        self.filled()
        self.sql('DELETE FROM tgdata_join_accounts')  # Deliberate external damage, FK off.
        for call in (lambda: self.budget.configure(222, 1), lambda: self.budget.status(222),
                     lambda: self.budget._claim(222), lambda: j.JoinBudget(self.path, create=True)):
            self.assert_refuses_without_change(call)

    def test_integer_inputs_and_large_account_id(self):
        for bad in (0, -1, True, 1.0, '222', None, 1 << 63):
            for method in (self.budget.status, self.budget._claim, lambda a: self.budget.configure(a, 1)):
                with self.subTest(bad=bad), self.assertRaises(j.JoinBudgetConfigError):
                    method(bad)
        for bad in (-1, False, 1.0, '1', None, 1 << 63):
            with self.subTest(bad=bad), self.assertRaises(j.JoinBudgetConfigError):
                self.budget.configure(222, bad)
        account = (1 << 63) - 1
        self.budget.configure(account, (1 << 63) - 1)
        self.budget._claim(account)
        self.assertEqual(self.budget.status(account).account_id, account)

    def test_clock_value_bounds(self):
        for bad in (None, True, '1000', -1, float('nan'), float('inf'), -float('inf'), 253402214400):
            self.clock.value = bad
            self.assert_refuses_without_change(lambda: self.budget.configure(222, 1), j.JoinBudgetConfigError)
        self.clock.value = 253402214399
        self.filled()
        value = self.budget.status(222).to_dict()
        self.assertEqual(value['next_available_at'], '9999-12-31T23:59:59+00:00')

    def test_missing_policy_and_zero_limit(self):
        for method in (self.budget.status, self.budget._claim):
            with self.assertRaises(j.JoinBudgetConfigError):
                method(222)
        value = self.budget.configure(222, 0)
        self.assertEqual((value.used, value.remaining, value.retry_after, value.next_available_at), (0, 0, None, None))
        with self.assertRaises(j.JoinBudgetExceeded) as caught:
            self.budget._claim(222)
        self.assertEqual(caught.exception.status, value)
        self.assertEqual(caught.exception.account_id, 222)
        self.assertIsNone(caught.exception.retry_after)

    def test_status_is_frozen_and_dict_is_fresh(self):
        status = self.budget.configure(222, 1)
        with self.assertRaises(FrozenInstanceError):
            status.used = 9
        output = status.to_dict()
        self.assertEqual(json.loads(json.dumps(output)), output)
        self.assertEqual(output['window_seconds'], 86400)
        self.assertEqual(output['observed_at'], '1970-01-01T00:16:40+00:00')
        output['used'] = 99
        self.assertEqual(status.to_dict()['used'], 0)
        self.assertEqual(status.retry_after, 0)

    def test_status_reserves_nothing_and_each_claim_counts(self):
        self.budget.configure(222, 2)
        observation = self.budget.status(222)
        self.assertIsNone(self.budget._claim(222))
        self.assertIsNone(self.budget._claim(222))
        self.assertEqual(observation.remaining, 2)
        with self.assertRaises(j.JoinBudgetExceeded):
            self.budget._claim(222)
        self.assertEqual(j.JoinBudget(self.path, clock=self.clock).status(222).used, 2)

    def test_cap_changes_retain_usage_and_wait_for_enough_expiry(self):
        self.budget.configure(222, 3)
        for at in (1000, 1010, 1020):
            self.clock.value = at
            self.budget._claim(222)
        reduced = self.budget.configure(222, 1)
        self.assertEqual((reduced.used, reduced.remaining, reduced.next_available_at), (3, 0, 87420))
        paused = self.budget.configure(222, 0)
        self.assertEqual(paused.used, 3)
        self.assertIsNone(paused.next_available_at)
        raised = self.budget.configure(222, 4)
        self.assertEqual((raised.used, raised.remaining), (3, 1))

    def test_exact_expiry_and_fractional_retry(self):
        self.clock.value = 1000.25
        self.filled(2)
        self.clock.value = 87400.24
        status = self.budget.status(222)
        self.assertEqual((status.used, status.retry_after), (2, 1))
        self.clock.value = 87400.25
        self.assertEqual((self.budget.status(222).used, self.budget.status(222).remaining), (0, 2))
        self.budget._claim(222)
        self.assertEqual(self.budget.status(222).used, 1)

    def test_backward_clock_and_denial_horizon_persist(self):
        self.filled()
        self.clock.value = 2000
        with self.assertRaises(j.JoinBudgetExceeded):
            self.budget._claim(222)
        self.clock.value = 900
        reopened = j.JoinBudget(self.path, clock=self.clock)
        status = reopened.status(222)
        self.assertEqual((status.used, status.observed_at, status.retry_after), (1, 2000, 85400))
        self.assertEqual(reopened.configure(222, 2).observed_at, 2000)

    def test_account_policy_and_clock_are_independent(self):
        self.filled()
        self.clock.value = 900
        second = self.budget.configure(333, 2)
        self.assertEqual((second.used, second.observed_at), (0, 900))
        self.budget._claim(333)
        self.assertEqual(self.budget.status(333).remaining, 1)
        self.assertEqual(self.budget.status(222).remaining, 0)

    def test_clock_runs_inside_writer_transaction(self):
        observations = []

        def clock():
            db = REAL_CONNECT(self.path, timeout=0, isolation_level=None)
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    db.execute('BEGIN IMMEDIATE')
                observations.append(True)
            finally:
                db.close()
            return 1000

        ledger = j.JoinBudget(self.path, clock=clock)
        ledger.configure(222, 2)
        ledger.status(222)
        ledger._claim(222)
        self.assertEqual(len(observations), 3)

    def test_invalid_attempts_refuse_before_pruning_or_clock_advance(self):
        self.filled()
        for bad in (-100000, 2000, 'text', sqlite3.Binary(b'blob'), float('inf')):
            self.sql('UPDATE tgdata_join_attempts SET admitted_at=?', (bad,))
            self.clock.value = 200000  # Even now > bad future time must not conceal it.
            for call in (lambda: self.budget.status(222), lambda: self.budget.configure(222, 9),
                         lambda: self.budget._claim(222)):
                with self.subTest(bad=bad):
                    self.assert_refuses_without_change(call)
        self.sql('UPDATE tgdata_join_attempts SET admitted_at=1000, id=-1')
        self.assert_refuses_without_change(lambda: self.budget.status(222))

    def test_invalid_policies_cannot_be_overwritten(self):
        self.filled()
        for column, value in (('daily_limit', -1), ('daily_limit', 'bad'), ('daily_limit', 1.5),
                              ('last_clock', -1), ('last_clock', 'bad'), ('last_clock', float('inf'))):
            db = REAL_CONNECT(self.path)
            db.execute('PRAGMA ignore_check_constraints=ON')
            db.execute('UPDATE tgdata_join_accounts SET daily_limit=1,last_clock=1000')
            db.execute('UPDATE tgdata_join_accounts SET {}=?'.format(column), (value,))
            db.commit()
            db.close()
            self.assert_refuses_without_change(lambda: self.budget.configure(222, 5))
            self.assert_refuses_without_change(lambda: self.budget._claim(222))

    def test_invalid_owner_is_detected_globally(self):
        self.filled()
        self.sql('UPDATE tgdata_join_attempts SET account_id=?', ('bad',))
        self.assert_refuses_without_change(lambda: self.budget.configure(333, 1))

    def test_bad_timestamp_is_scoped_to_affected_account(self):
        self.filled()
        self.budget.configure(333, 1)
        self.sql('UPDATE tgdata_join_attempts SET admitted_at=-1')
        self.budget._claim(333)
        self.assertEqual(self.budget.status(333).used, 1)
        self.assert_refuses_without_change(lambda: self.budget.status(222))

    def test_real_read_budget_coexistence(self):
        self.filled()
        read = ReadBudget(self.path, clock=self.clock)
        read.configure(222, 10)
        token = read._reserve(222, 5)
        read._settle(token, 2)
        self.budget.configure(222, 2)
        self.budget._claim(222)
        self.assertEqual(read.status(222).used, 2)
        self.assertEqual(j.JoinBudget(self.path, clock=self.clock).status(222).used, 2)
        self.clock.value += 86400
        self.assertEqual(self.budget.status(222).used, 0)
        self.assertEqual(read.status(222).used, 0)

    def run_race(self, owners):
        ctx = multiprocessing.get_context('spawn')
        barrier, output = ctx.Barrier(len(owners) + 1), ctx.Queue()
        processes = [ctx.Process(target=compete, args=(str(self.path), owner, barrier, output)) for owner in owners]
        try:
            for process in processes:
                process.start()
            barrier.wait(timeout=30)
            answers = [output.get(timeout=30) for _ in processes]
            for process in processes:
                process.join(timeout=30)
                self.assertEqual(process.exitcode, 0)
            return answers
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=5)
            output.close()
            output.join_thread()

    def test_competing_processes_share_one_cap(self):
        self.budget.configure(222, 3)
        answers = self.run_race([222] * 6)
        self.assertEqual(sum(accepted for _, accepted in answers), 3)
        self.assertEqual(self.budget.status(222).used, 3)

    def test_competing_processes_keep_accounts_separate(self):
        self.budget.configure(222, 1)
        self.budget.configure(333, 2)
        answers = self.run_race([222, 222, 333, 333, 333])
        self.assertEqual(sum(ok for owner, ok in answers if owner == 222), 1)
        self.assertEqual(sum(ok for owner, ok in answers if owner == 333), 2)
        self.assertEqual((self.budget.status(222).used, self.budget.status(333).used), (1, 2))

    def test_process_exit_brackets_real_commit(self):
        self.budget.configure(222, 2)
        ctx = multiprocessing.get_context('spawn')
        for phase, expected in (('before', 0), ('after', 1)):
            process = ctx.Process(target=exit_during_commit, args=(str(self.path), phase))
            process.start()
            try:
                process.join(timeout=30)
                self.assertEqual(process.exitcode, 23)
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            self.assertEqual(j.JoinBudget(self.path, clock=self.clock).status(222).used, expected)

    def test_sql_failures_roll_back_uncommitted_claims(self):
        self.budget.configure(222, 2)
        for operation, fragment in (('execute', 'BEGIN IMMEDIATE'),
                                    ('execute', 'INSERT INTO tgdata_join_attempts'), ('commit', '')):
            def hook(op, phase, args):
                if op == operation and phase == 'before' and (not fragment or args[0].startswith(fragment)):
                    raise sqlite3.OperationalError(SECRET)
            with faults(hook), self.assertRaises(j.JoinBudgetStorageError) as caught:
                self.budget._claim(222)
            self.assertNotIn(SECRET, str(caught.exception))
            self.assertIsNone(caught.exception.__cause__)
            self.assertEqual(self.budget.status(222).used, 0)

    def test_error_after_real_commit_retains_charge(self):
        self.budget.configure(222, 1)

        def hook(op, phase, args):
            if op == 'commit' and phase == 'after':
                raise sqlite3.OperationalError(SECRET)

        with faults(hook), self.assertRaises(j.JoinBudgetStorageError):
            self.budget._claim(222)
        with self.assertRaises(j.JoinBudgetExceeded):
            self.budget._claim(222)
        self.assertEqual(self.budget.status(222).used, 1)

    def test_close_only_failure_grants_nothing_retains_charge(self):
        self.budget.configure(222, 1)

        def hook(op, phase, args):
            if op == 'close' and phase == 'after':
                raise OSError(SECRET)

        with faults(hook), self.assertRaises(j.JoinBudgetStorageError) as caught:
            self.budget._claim(222)
        self.assertNotIn(SECRET, str(caught.exception))
        self.assertEqual(self.budget.status(222).used, 1)

    def test_secondary_cleanup_preserves_primary_and_sanitizes_logs(self):
        primary = j.JoinBudgetConfigError('primary')

        def hook(op, phase, args):
            if op in ('rollback', 'close') and phase == 'after':
                raise OSError(SECRET)

        # A caller error inside the transaction must survive both cleanup failures.
        with faults(hook), self.assertLogs(j.logger, level='WARNING') as log:
            with self.assertRaises(j.JoinBudgetConfigError) as caught:
                with self.budget._transaction():
                    raise primary
        self.assertIs(caught.exception, primary)
        self.assertEqual(len(log.output), 2)
        self.assertNotIn(SECRET, ''.join(log.output))
        self.assertIn('OSError', ''.join(log.output))
        self.assertEqual(self.budget.configure(222, 1).remaining, 1)

    def test_primary_cancellation_survives_cleanup_and_logger_failure(self):
        self.budget.configure(222, 1)
        primary = asyncio.CancelledError()

        def hook(op, phase, args):
            if op == 'commit' and phase == 'before':
                raise primary
            if op in ('rollback', 'close') and phase == 'after':
                raise asyncio.CancelledError()

        with faults(hook), patch.object(j.logger, 'warning', side_effect=RuntimeError(SECRET)):
            with self.assertRaises(asyncio.CancelledError) as caught:
                self.budget._claim(222)
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.budget.status(222).used, 0)  # Rolled back, no leaked lock.

    def test_clock_exception_rolls_back_policy_and_is_local(self):
        self.filled()
        for failure in (OSError(SECRET), errors.AuthKeyUnregisteredError(None)):
            def clock():
                raise failure
            self.budget._clock = clock
            before = self.state()
            with self.assertRaises(j.JoinBudgetConfigError) as caught:
                self.budget.configure(222, 8)
            self.assertEqual(self.state(), before)
            self.assertNotIn(SECRET, str(caught.exception))
            self.assertIsNone(classify(caught.exception))

    def check_cancellation_boundaries(self, cls):
        primary = cls()

        def fail():
            raise primary

        class BadIndex:
            def __index__(self):
                raise primary

        class BadPath:
            def __fspath__(self):
                raise primary

        class BadTime(float):
            def __float__(self):
                raise primary

        ledger = j.JoinBudget(self.path, clock=fail)
        bad_time = j.JoinBudget(self.path, clock=lambda: BadTime(1000))
        for call in (lambda: ledger.configure(222, 1), lambda: self.budget.status(BadIndex()),
                     lambda: j.JoinBudget(BadPath()), lambda: bad_time.configure(222, 1)):
            with self.assertRaises(cls) as caught:
                call()
            self.assertIs(caught.exception, primary)

        self.budget.configure(222, 2)

        def hook(op, phase, args):
            if op == 'close' and phase == 'after':
                raise primary

        with faults(hook), self.assertRaises(cls) as caught:
            self.budget._claim(222)
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.budget.status(222).used, 1)

    def test_native_cancellation_boundaries(self):
        self.check_cancellation_boundaries(asyncio.CancelledError)

    def test_exception_derived_cancellation_compatibility_fixture(self):
        class OldStyleCancelledError(Exception):
            pass
        # Explicit fixture for the older hierarchy, not a Python3.7 runtime test.
        with patch.object(j.asyncio, 'CancelledError', OldStyleCancelledError):
            self.check_cancellation_boundaries(OldStyleCancelledError)

    def test_local_errors_do_not_inherit_telegram_health(self):
        self.filled()
        for call in (lambda: self.budget.status(True), lambda: self.budget._claim(222),
                     lambda: j.JoinBudget(self.root / 'absent')):
            try:
                raise errors.AuthKeyUnregisteredError(None)
            except errors.AuthKeyUnregisteredError:
                with self.assertRaises(j.JoinBudgetError) as caught:
                    call()
                self.assertIsNone(classify(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)

    def test_public_exports(self):
        import tgdata
        for name in ('JoinBudget', 'JoinBudgetStatus', 'JoinBudgetError', 'JoinBudgetConfigError',
                     'JoinBudgetStorageError', 'JoinBudgetExceeded'):
            self.assertIs(getattr(tgdata, name), getattr(j, name))
            self.assertIn(name, tgdata.__all__)


if __name__ == '__main__':
    unittest.main(verbosity=2)
