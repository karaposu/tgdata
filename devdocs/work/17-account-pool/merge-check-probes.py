"""Plan-fidelity checks for #17; actual offline composition, no Telegram sockets."""
import ast
import asyncio
import json
import logging
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tgdata.smoke_tests import test_31_account_pool as t


def git(*args):
    return subprocess.check_output(['git', *args], cwd=str(ROOT))


def methods(source, name):
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    return {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def executable(node):
    node = ast.parse(ast.unparse(node)).body[0]
    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) \
            and isinstance(node.body[0].value.value, str):
        node.body.pop(0)
    return ast.dump(node, include_attributes=False)


def static_checks():
    for commit in ('95ed4c7', '03d02c7', 'd1daa84', '1254253', 'f7c4870', '188228c',
                   'a0bdcf9', '1cd56b7', '964d082', '8d3db76', 'bacde95', '4f0ddb0',
                   '3963b67', 'c251ca4', '6bb40f2', '15f0b8a', '4854464', '67ffb2c', '68f6bbd'):
        subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=str(ROOT), check=True)
    foundations = ['connection_engine', 'account_operation', 'owned_health', 'group_operations',
                   'join_budget', 'join_client', 'health', 'read_budget', 'sync_engine', 'backfill_engine']
    for module in foundations:
        path = 'tgdata/' + module + '.py'
        assert git('show', '68f6bbd:' + path) == (ROOT / path).read_bytes(), path
    for module in ('pool_state', 'progress_facade', 'batch_engine'):
        path = 'tgdata/' + module + '.py'
        assert git('show', '8d3db76:' + path) == (ROOT / path).read_bytes(), path
    original = methods(git('show', '68f6bbd:tgdata/tgdata.py'), 'TgData')
    current = methods((ROOT / 'tgdata/tgdata.py').read_text(), 'TgData')
    facade = methods((ROOT / 'tgdata/progress_facade.py').read_text(), 'ProgressFacade')
    public = [name for name in facade if not name.startswith('_')]
    for name in public:
        assert executable(original[name]) == executable(facade[name]), name
    for name in set(original) & set(current):
        assert executable(original[name]) == executable(current[name]), name
    # _backfill_for changes only its construction seam, preserving the old
    # TgData-module factory through TgData._new_backfill_engine.
    old = original['_backfill_for']
    class Factory(ast.NodeTransformer):
        def visit_Call(self, node):
            self.generic_visit(node)
            if isinstance(node.func, ast.Name) and node.func.id == 'BackfillEngine':
                return ast.Call(func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()),
                    attr='_new_backfill_engine', ctx=ast.Load()), args=[ast.Name(id='collection', ctx=ast.Load())], keywords=[])
            return node
    assert executable(ast.fix_missing_locations(Factory().visit(old))) == executable(facade['_backfill_for'])
    print(json.dumps(dict(case='static_fidelity', artifact_ancestors=19,
        unchanged_dev_foundations=len(foundations), identical_public_progress_methods=len(public),
        retained_TgData_methods=len(set(original) & set(current)), factory_seam='only permitted substitution')))


async def main():
    static_checks()
    groups = [
        ('original_critic_completed_outcomes', [t.test_observer_timeout_preserves_original_flood_and_prefix,
                                              t.test_success_observer_timeout_keeps_successful_batch]),
        ('original_critic_credential_reload', [t.test_recheck_reloads_repaired_stored_credential,
                                             t.test_cancelled_retirement_cannot_overwrite_repaired_credential_later]),
        ('rework_retirement', [t.test_recheck_cancellation_holds_ownership_until_sdk_disconnect,
                              t.test_retirement_failure_refuses_reuse_until_explicit_recheck]),
        ('rework_source_and_shutdown', [t.test_repeated_read_cancellation_retains_the_actual_child,
                                       t.test_cancelled_close_waits_for_actual_source_child,
                                       t.test_close_cancellation_settles_all_sdk_cleanup_and_stays_closed]),
        ('identity_at_admission', [t.test_changed_identity_at_admission_never_sends_history]),
        ('restriction_and_recovery', [t.test_flood_failover_and_restart_wait,
                                     t.test_stale_settlement_cannot_erase_newer_stored_facts]),
        ('source_free_progress', [t.test_settlement_failure_preserves_data_and_daily_replay,
                                  t.test_backfill_failover_replay_ack_are_public_and_source_free]),
    ]
    with tempfile.TemporaryDirectory(prefix='tgdata17-merge-check-') as directory, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        t.f.TMP = t.d.TMP = Path(directory)
        try:
            for name, tests in groups:
                for test in tests:
                    await asyncio.wait_for(test(), 25)
                print(json.dumps(dict(case=name, passed=len(tests))))
        finally:
            for pool in t.POOLS:
                await pool.close()
            t.POOLS.clear()
    print('PASS: static fidelity plus 7 behavioral groups (14 existing composition cases).')


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    asyncio.run(main())
