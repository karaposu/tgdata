"""Pre-plan SDK observations for revision3; no production code changes or network."""
import asyncio
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from telethon import errors
from telethon.tl import functions, types
from tgdata import ReadBudget
from tgdata.smoke_tests import test_20_group_operations as g


class FailingStage(g.Sender):
    def __init__(self, request_type):
        super().__init__()
        self.request_type = request_type
        self.failure = errors.ServerError(None, 'synthetic temporary failure')
        self.failures = 0

    def send(self, request, ordered=False):
        inner = g.f.unwrap(request)
        if isinstance(inner, self.request_type):
            self.requests.append(inner)
            self.failures += 1
            future = asyncio.get_running_loop().create_future()
            future.set_exception(self.failure)
            return future
        return super().send(request, ordered)


async def no_wait(_):
    pass


async def strict_sdk_policy():
    original = g.StandIn.__init__

    def configured(self, *args, **kwargs):
        # Only a supported constructor input is changed. The SDK's real retry
        # loop, factory MRO, exception selection and facade all still execute.
        kwargs['raise_last_call_error'] = True
        original(self, *args, **kwargs)

    cases = [
        ('authorization', functions.updates.GetStateRequest, 'lookup_group', 'synthetic_room'),
        ('identity', functions.users.GetUsersRequest, 'lookup_group', 'synthetic_room'),
        ('numeric', functions.channels.GetChannelsRequest, 'lookup_group', -1000000000007),
        ('handle', functions.contacts.ResolveUsernameRequest, 'lookup_group', 'synthetic_room'),
        ('history', functions.messages.GetHistoryRequest, 'check_group_access', 'synthetic_room'),
        ('join', functions.messages.ImportChatInviteRequest, 'join_group', g.LINK),
    ]
    for name, request_type, method, target in cases:
        sender = FailingStage(request_type)
        join, _ = g.ledger(10)
        read = ReadBudget(g.TMP / (name + '_read.sqlite'), clock=g.f.Clock())
        read.configure(g.f.ACCOUNT, 10)
        with g.rig(join, read=read, senders=[sender], seed=[g.room()]) as r, patch.object(
                g.StandIn, '__init__', configured), patch('telethon.client.users.asyncio.sleep', no_wait):
            caught = await g.expect(errors.ServerError, getattr(r.tg, method)(target))
            assert caught is sender.failure and sender.failures == 6
            assert r.clients[0]._raise_last_call_error is True
            assert join.status(g.f.ACCOUNT).used == (6 if name == 'join' else 0)
            assert read.status(g.f.ACCOUNT).used == (6 if name == 'history' else 0)
        print('PASS strict SDK policy:', name, 'retains final RPC object after6 attempts')


async def health_identity_source():
    sender = g.Sender(222)
    with g.rig(senders=[sender], cached=111) as r:
        client = r.tg.connection_engine._new_client()
        r.tg.connection_engine._primary_client = client
        result = await r.tg.health_check()
        self_requests = [req for req in sender.requests if isinstance(req, functions.users.GetUsersRequest)]
        assert len(self_requests) == 1 and len(self_requests[0].id) == 1
        assert isinstance(self_requests[0].id[0], types.InputUserSelf)
        assert client._self_id == 111 and result['health']['account']['user_id'] == 111
        # The real SDK already queried self; its verified reply can be consumed
        # without adding a new identity RPC to health_check's success path.
        print('OBSERVED health_check: one existing self RPC for222; cached/snapshot ID remains111')


async def main():
    await strict_sdk_policy()
    await health_identity_source()


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp, patch.object(
            socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
        g.TMP = g.f.TMP = Path(tmp)
        asyncio.run(main())
