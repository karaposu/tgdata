"""Offline checks of the actual Gate D allocation, guard and byte/receipt instruments."""
import asyncio
import socket
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import gate_d_support as g
from telethon import functions, types
from tgdata.smoke_tests import test_29_backfill_public as u


async def main():
    passed=0
    with tempfile.TemporaryDirectory(prefix='gate_d_instruments_') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        root=Path(tmp);u.f.TMP=u.d.TMP=root
        try:
            allocations=root/'allocations';g.allocate(allocations,'one',1000)
            u.f.rejected(AssertionError,lambda:g.allocate(allocations,'over',501))
            g.allocate(allocations,'two',500)
            u.f.rejected(AssertionError,lambda:g.allocate(allocations,'one',1))
            assert g.begin(allocations,'one')==1000
            u.f.rejected(FileExistsError,lambda:g.begin(allocations,'one'));passed+=1

            guard=g.Guard(root,'guard',g.SMALL,5)
            peer=types.InputPeerChannel(4478311025,1)
            def request(n):return functions.messages.GetHistoryRequest(peer,0,None,0,n,0,0,0)
            token=g.OP.set('instrument-source')
            try:entry=guard.before_send(request(3))
            finally:g.OP.reset(token)
            assert entry['operation']=='instrument-source' and guard.slots==3
            guard.block_after=1
            u.f.rejected(g.p.ProbeStop,lambda:guard.before_send(request(2)))
            assert guard.report()['attempted_slots']==5 and guard.history_count==1
            u.f.rejected(g.p.ProbeStop,lambda:guard.before_send(request(1)))
            u.f.rejected(g.p.ProbeStop,lambda:guard.before_send(functions.channels.JoinChannelRequest(peer)))
            wrong=functions.messages.GetHistoryRequest(types.InputPeerChannel(1,1),0,None,0,1,0,0,0)
            u.f.rejected(g.p.ProbeStop,lambda:guard.before_send(wrong));passed+=1

            e=await u.setup(media_mode='download',batch_size=1,destination_id=g.DESTINATION)
            e.sender.files[u.b.ASSET_ID]=u.b.PAYLOAD;u.b.script_messages(e.sender,[u.b.document()])
            media=u.b.directory();turn=await e.tg.prepare_backfill(u.ctx(e.initial),download_media_to=media)
            blob=turn.batch.messages[0]['media']['blob']
            receiver=g.Receiver(root/'receiver',create=True)
            assert receiver.accept(turn.batch,turn.delivery,media)
            assert receiver.observation(turn.delivery).to_json()==turn.batch.to_json()
            assert g.digest(receiver.media/blob['path'])==blob['sha256'];passed+=1
            reopened=g.Receiver(root/'receiver')
            assert not reopened.accept(turn.batch,turn.delivery,media)
            assert reopened.summary()['receipts']==1 and reopened.summary()['messages']==1;passed+=1
            (reopened.media/blob['path']).write_bytes(b'corrupt receiver bytes')
            u.f.rejected(AssertionError,lambda:reopened.accept(turn.batch,turn.delivery,media))
            assert reopened.summary()['receipts']==1;passed+=1

            empty=g.Receiver(root/'missing-source',create=True)
            u.f.rejected(FileNotFoundError,lambda:empty.accept(turn.batch,turn.delivery,root/'missing'))
            assert empty.summary()['receipts']==0;passed+=1
            sourcefile=media/blob['path'];original=sourcefile.read_bytes();sourcefile.write_bytes(b'bad')
            u.f.rejected(AssertionError,lambda:empty.accept(turn.batch,turn.delivery,media))
            assert empty.summary()['receipts']==0;sourcefile.write_bytes(original);passed+=1

            original_connect=sqlite3.connect
            class Before(sqlite3.Connection):
                def commit(self):
                    if self.total_changes:raise sqlite3.OperationalError('injected receiver pre-commit')
                    super().commit()
            def connect(*a,**kw):kw['factory']=Before;return original_connect(*a,**kw)
            with patch.object(sqlite3,'connect',side_effect=connect):
                u.f.rejected(g.app.ExampleStateError,lambda:empty.accept(turn.batch,turn.delivery,media))
            assert empty.summary()['receipts']==0
            assert g.digest(empty.media/blob['path'])==blob['sha256'];passed+=1
            class After(sqlite3.Connection):
                def close(self):
                    changed=self.total_changes;super().close()
                    if changed:raise sqlite3.OperationalError('injected receiver lost reply')
            def connect(*a,**kw):kw['factory']=After;return original_connect(*a,**kw)
            with patch.object(sqlite3,'connect',side_effect=connect):
                u.f.rejected(g.app.ExampleStateError,lambda:empty.accept(turn.batch,turn.delivery,media))
            assert empty.observation(turn.delivery).to_json()==turn.batch.to_json()
            assert not empty.accept(turn.batch,turn.delivery,media);passed+=1
        finally:
            for client in u.f.CLIENTS:await client.disconnect()
            u.f.CLIENTS.clear()
    print('Passed: {}/9 offline Gate D instrument checks'.format(passed))
    assert passed==9


if __name__=='__main__':asyncio.run(main())
