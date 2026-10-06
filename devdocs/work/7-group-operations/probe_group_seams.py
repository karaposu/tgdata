"""Pre-plan observations of the installed SDK. All responses are synthetic.

Run with .venv/bin/python; socket.connect is forbidden. This observes SDK
dispatch/cache/retry behavior, not Telegram server acceptance or a future ledger.
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import telethon
from telethon import errors
from telethon.extensions import BinaryReader
from telethon.sessions import MemorySession
from telethon.tl import functions, types, alltlobjects
from tgdata.smoke_tests import test_18_read_budget as fixture


def updates():
    return types.Updates([], [], [fixture.room()], datetime.now(timezone.utc), 1)


class Sender(fixture.Sender):
    def __init__(self):
        super().__init__(account=222)
        self.joins = []
        self.replies = []

    def send(self, request, ordered=False):
        if isinstance(fixture.unwrap(request), functions.channels.JoinChannelRequest):
            self.joins.append(request)
            f = asyncio.get_running_loop().create_future()
            reply = self.replies.pop(0)
            if isinstance(reply, Exception):
                f.set_exception(reply)
            else:
                f.set_result(reply)
            return f
        return super().send(request, ordered)


class Observer:
    """Only records where SDK retries call send; does not implement admission."""
    def __init__(self, client, sender):
        self.client, self.sender, self.accounts = client, sender, []

    async def send(self, request, ordered=False):
        self.accounts.append((await self.client.get_me(input_peer=False)).id)
        return await self.sender.send(request, ordered)


async def main():
    assert telethon.__version__ == '1.45.0'
    print('Telethon', telethon.__version__, 'layer', alltlobjects.LAYER)
    wrapped = types.messages.ChatInviteJoinResultOk(updates())
    web = types.messages.ChatInviteJoinResultWebView(11, 22, [])
    for reply in (wrapped, web):
        with BinaryReader(bytes(reply)) as reader:
            restored = reader.tgread_object()
        assert type(restored) is type(reply)
        assert bytes(restored) == bytes(reply)
    assert not hasattr(web, 'url')
    session = MemorySession()
    session.process_entities(wrapped)
    assert not session._entities
    session.process_entities(wrapped.updates)
    assert session.get_input_entity('synthetic_room').channel_id == 7
    print('PASS: wrapped results serialize; only nested updates populate entity cache')

    tg, client, _ = fixture.instance(cached=111, events=[])
    sender = Sender()
    client._sender = sender
    observer = Observer(client, sender)
    request = functions.channels.JoinChannelRequest(types.InputChannel(7, 7))
    sender.replies = [errors.ServerError(request, 'synthetic server fault'), wrapped]
    async def immediate(_):
        pass
    with patch('telethon.client.users.asyncio.sleep', immediate):
        answer = await client._call(observer, request)
    assert answer is wrapped and len(sender.joins) == 2
    assert observer.accounts == [222, 222] and client._self_id == 111
    print('PASS: real SDK retry calls sender twice; fresh identity differs from cached self')

    client._request_retries = 0
    client._raise_last_call_error = True
    failure = errors.ServerError(request, 'synthetic server fault')
    sender.replies = [failure]
    before = len(sender.joins)
    with patch('telethon.client.users.asyncio.sleep', immediate):
        try:
            await client._call(observer, request)
        except errors.ServerError as exc:
            assert exc is failure
        else:
            raise AssertionError('expected original server fault')
    assert len(sender.joins) == before + 1
    print('PASS: retry=0 alternative makes one attempt but changes client retry semantics')

    try:
        async with tg._health.call('probe_denial', group=7):
            raise errors.ChannelPrivateError(request)
    except errors.ChannelPrivateError:
        pass
    assert '7' in tg._health._no_access
    async with tg._health.call('metadata_only', group=7):
        await client(functions.channels.GetChannelsRequest([types.InputChannel(7, 7)]))
    assert '7' not in tg._health._no_access
    print('OBSERVED: current default recovery clears group denial after metadata alone')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp, patch.object(
            socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
        fixture.TMP = Path(tmp)
        asyncio.run(main())
