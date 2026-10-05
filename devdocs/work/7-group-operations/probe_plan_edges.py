"""Plan-critic counterexamples, real SDK/session/health, synthetic replies only."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from telethon import errors
from telethon.sessions import SQLiteSession
from telethon.tl import types, functions
from tgdata import health
from tgdata.smoke_tests import test_18_read_budget as fixture

async def main(root):
    folder=root/'session';folder.mkdir()
    session=SQLiteSession(str(folder/'synthetic'))
    session.close()
    (folder/'synthetic.session').unlink();folder.rmdir()
    reply=types.messages.ChatInviteJoinResultOk(types.Updates(
        [],[],[fixture.room()],datetime.now(timezone.utc),1))
    session.process_entities(reply)  # Actual SDK's normal response-cache call is a no-op.
    try:
        session.process_entities(reply.updates)
    except Exception as exc:
        assert type(exc).__name__=='OperationalError'
        print('OBSERVED: post-ack nested cache enrichment can fail locally:',type(exc).__name__)
    else:raise AssertionError('missing parent should fail')
    events=[]
    tg, client, sender=fixture.instance(cached=111,account=222,events=events)
    assert (await client.get_me()).id==222
    request=functions.channels.GetChannelsRequest([types.InputChannel(7,7)])
    try:
        async with tg._health.call('new_operation',group=7):
            raise errors.ChannelPrivateError(request)
    except errors.ChannelPrivateError:pass
    assert events[-1]['account']['user_id']==111
    print('OBSERVED: health identity uses primary cached111 although fresh authenticated ID is222')
    try:
        raise errors.ChannelPrivateError(request)
    except errors.ChannelPrivateError:
        try:
            client.session.get_input_entity(99999)
        except ValueError as exc:
            assert health.classify(exc).verdict==health.NO_ACCESS
            print('OBSERVED: native missing-ID ValueError inherits unrelated RPC health context')
        else:raise AssertionError('expected missing peer')

if __name__=='__main__':
    with tempfile.TemporaryDirectory() as tmp,patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
        fixture.TMP=Path(tmp)
        asyncio.run(main(Path(tmp)))
