"""Mandatory #10 prebuild: bounded actual source, raw pipes and cleanup receipts."""
import asyncio
from contextlib import asynccontextmanager, redirect_stdout
import inspect
import io
import json
import logging
from pathlib import Path
import runpy
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from telethon import errors, functions, types, utils
from tgdata import TgData
from tgdata import batch_engine
from tgdata.account_operation import AccountIdentityError
from tgdata.group_operations import _parse_target, _resolve, GroupReferenceError, GroupResponseError
from tgdata.smoke_tests import test_32_account_operation as f
from tgdata.smoke_tests import test_19_message_batches as b


def batch_candidate():
    code = inspect.getsource(batch_engine.BatchEngine)
    assert code.count('def __init__(self, connection_engine):') == 1
    code = code.replace('def __init__(self, connection_engine):',
                        'def __init__(self, connection_engine, *, _resolve_entity=None):')
    code = code.replace('        self.connection_engine = connection_engine',
        '        self.connection_engine = connection_engine\n        self._resolve_entity = _resolve_entity', 1)
    old = '''                try:
                    entity = await client.get_entity(group_id)
                except ValueError:
                    entity = await MessageEngine._entity_after_dialog_sync(client, group_id)'''
    assert code.count(old) == 1
    code = code.replace(old, '''                if self._resolve_entity is not None:
                    entity = await self._resolve_entity(client, group_id)
                else:
                    try:
                        entity = await client.get_entity(group_id)
                    except ValueError:
                        entity = await MessageEngine._entity_after_dialog_sync(client, group_id)''')
    namespace = dict(vars(batch_engine))
    exec(compile(code, '<bounded-batch-candidate>', 'exec'), namespace)
    return namespace['BatchEngine']


class Bound:
    def __init__(self, op): self.op = op
    @asynccontextmanager
    async def session(self): yield self.op.client


async def source_cases():
    Candidate = batch_candidate()
    with tempfile.TemporaryDirectory(prefix='tgdata10-prebuild-source-') as directory:
        f.TMP = Path(directory)
        for case in ('handle', 'cached_id', 'uncached_id', 'invite_preview', 'partial_wait',
                     'wrong_owner', 'legacy_default'):
            room = b.f.room()
            replies = {
                'ResolveUsernameRequest': types.contacts.ResolvedPeer(types.PeerChannel(7), [room], []),
                'GetChannelsRequest': types.messages.Chats([room]),
                'GetHistoryRequest': b.f.response([b.f.message(102), b.f.message(101)]),
                'GetDialogsRequest': types.messages.Dialogs([], [], [], []),
                'CheckChatInviteRequest': types.ChatInvite('Preview', types.PhotoEmpty(1), 0, 1,
                                                           channel=True, megagroup=True),
            }
            if case == 'legacy_default':
                replies['GetChannelsRequest'] = errors.ChannelInvalidError(request=None)
            fx = f.Fixture(accounts=(222,), cached=111, budget=True, responses=replies)
            fx.budget.configure(222, 1000)
            events = []
            app = TgData(str(fx.config), interactive_login=False, read_budget=fx.budget,
                         session_store=fx.store, health_callback=events.append)
            app.connection_engine = fx.engine
            group = (-1000000000007 if case in ('cached_id', 'uncached_id', 'legacy_default')
                     else 'https://t.me/+ProbeInvite' if case == 'invite_preview' else '@synthetic_room')
            original = errors.FloodWaitError(request=f.history(), capture=7200)
            value = error = None
            try:
                try:
                    async with app._account_health_operation(
                            111 if case == 'wrong_owner' else 222, 'worker_read', group) as (op, observation):
                        if case == 'cached_id':
                            op.client.session.process_entities([room])
                        if case == 'partial_wait':
                            fx.wire.script['GetHistoryRequest'] = [
                                b.f.response([b.f.message(i) for i in reversed(range(101, 201))]), original]
                        async def resolver(client, target):
                            assert client is op.client
                            lookup, peer = await _resolve(op, _parse_target(target))
                            if peer is None or lookup.group.kind == 'community':
                                raise GroupReferenceError('No supported read peer')
                            entity = await client.get_entity(peer)
                            if utils.get_peer_id(entity) != lookup.group.peer_id:
                                raise GroupResponseError()
                            return entity
                        engine = Candidate(Bound(op), _resolve_entity=None if case == 'legacy_default' else resolver)
                        value = await engine.fetch_batch(group, after_id=100,
                                                        limit=200 if case == 'partial_wait' else 2)
                except Exception as caught:
                    error = caught
                pending = [work for monitor in app._account_health.values() for work in monitor._tasks]
                await asyncio.gather(*pending)
                calls = fx.wire.calls
                assert not any('Join' in call or 'ImportChat' in call or 'GetContacts' in call for call in calls)
                assert ('GetDialogsRequest' in calls) is (case == 'legacy_default')
                if case in ('handle', 'cached_id'):
                    assert error is None and len(value.messages) == 2 and fx.budget.status(222).used == 2
                elif case in ('uncached_id', 'invite_preview'):
                    assert isinstance(error, GroupReferenceError) and 'GetHistoryRequest' not in calls
                elif case == 'wrong_owner':
                    assert isinstance(error, AccountIdentityError)
                    assert not any(call in calls for call in ('ResolveUsernameRequest','GetChannelsRequest','GetHistoryRequest'))
                elif case == 'partial_wait':
                    assert error is original and len(error.partial_result.messages) == 100
                    assert fx.budget.status(222).used == 200 and events[-1]['wait_seconds'] == 7200
                    assert events[-1]['account']['user_id'] == 222
                else:
                    assert isinstance(error, batch_engine.GroupAccessError)
                assert fx.budget.status(111).used == 0 and fx.wire.closed
                print(json.dumps(dict(case='source_'+case, error=type(error).__name__ if error else None,
                    history_requests=calls.count('GetHistoryRequest'), dialog_scan='GetDialogsRequest' in calls,
                    account222_charge=fx.budget.status(222).used, actual_cleanup=True)), flush=True)
            finally:
                for client in fx.clients: await client.disconnect()
                await app.close()


def main():
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(source_cases())
        cleanup = runpy.run_path(str(Path(__file__).with_name('cleanup_candidate.py')))
        asyncio.run(cleanup['main']())
    output = runpy.run_path(str(Path(__file__).with_name('plan_falsifiers.py')))
    captured = io.StringIO()
    with redirect_stdout(captured):
        output['output_cases']()
    rows = [json.loads(line) for line in captured.getvalue().splitlines()]
    assert len(rows) == 4
    for row in rows:
        if row['mode'] == 'raw':
            assert row['exit'] == (3 if row['case'] == 'stdout_broken' else 143)
            assert not row['stuck_until_drain'] and not row['shutdown_warning']
        elif row['case'] == 'stdout_broken':
            assert row['exit'] == 120
        else:
            assert row['stuck_until_drain']
        print(json.dumps(row), flush=True)
    print('PASS: 7 source histories + 6 cleanup cases + 4 real pipe controls; no product edits.')


if __name__ == '__main__':
    main()
