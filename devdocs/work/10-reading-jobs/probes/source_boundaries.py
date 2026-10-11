"""Worker design premises on current dev; actual owned SDK/health/batch composition."""
import asyncio
from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from telethon import errors, types
from tgdata import TgData
from tgdata.batch_engine import BatchEngine
from tgdata.smoke_tests import test_32_account_operation as f
from tgdata.smoke_tests import test_19_message_batches as b


class Bound:
    def __init__(self, operation):
        self.operation = operation

    @asynccontextmanager
    async def session(self):
        yield self.operation.client


async def main():
    with tempfile.TemporaryDirectory(prefix='tgdata10-source-premises-') as directory:
        f.TMP = Path(directory)
        room = b.f.room()
        fixture = f.Fixture(accounts=(222,), cached=111, budget=True, responses={
            'ResolveUsernameRequest': types.contacts.ResolvedPeer(types.PeerChannel(7), [room], []),
            'GetChannelsRequest': types.messages.Chats([room]),
            'GetHistoryRequest': b.f.response([b.f.message(102), b.f.message(101)]),
        })
        events = []
        app = TgData(str(fixture.config), interactive_login=False, health_callback=events.append,
                     read_budget=fixture.budget, session_store=fixture.store)
        app.connection_engine = fixture.engine  # Actual engine; synthetic wire factory only.
        try:
            async with app._account_health_operation(222, 'worker_read', -1000000000007) as (op, obs):
                batch = await BatchEngine(Bound(op)).fetch_batch('@synthetic_room', after_id=100, limit=2)
                obs.confirm_group_access()
            assert len(batch.messages) == 2 and fixture.budget.status(222).used == 2
            assert fixture.budget.status(111).used == 0 and fixture.wire.closed
            print(json.dumps(dict(case='verified_batch_composition', cached=111, verified=222,
                                  records=2, charges=[0, 2], actual_disconnect_completed=True)))
            fixture.responses['GetHistoryRequest'] = errors.FloodWaitError(request=None, capture=7200)
            original = fixture.responses['GetHistoryRequest']
            try:
                async with app._account_health_operation(222, 'worker_read', -1000000000007) as (op, obs):
                    await BatchEngine(Bound(op)).fetch_batch('@synthetic_room', after_id=100, limit=2)
            except errors.FloodWaitError as caught:
                assert caught is original
            else:
                raise AssertionError('Expected actual SDK wait')
            pending = [task for m in app._account_health.values() for task in m._tasks]
            await asyncio.gather(*pending)
            assert events[-1]['account']['user_id'] == 222 and fixture.wire.closed
            assert events[-1]['wait_seconds'] == 7200
            print(json.dumps(dict(case='post_cleanup_notification', queued_tasks=len(pending),
                                  account_id=222, wait=7200, native_disconnect_completed=True)))
            fixture.responses['GetHistoryRequest'] = b.f.response([b.f.message(102), b.f.message(101)])
            async with fixture.engine._account_operation(222) as op:
                fixture.wire.close_error = OSError('synthetic teardown failure')
                result = 'completed body'
            assert result == 'completed body' and fixture.wire.is_connected()
            print(json.dumps(dict(case='cleanup_attempt_is_not_closure', body_completed=True,
                                  context_raised=False, transport_still_connected=True)))
        finally:
            for client in fixture.clients:
                client._sender.close_error = None
                await client.disconnect()
            await app.close()


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(main())
