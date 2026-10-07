"""Local checks for durable launch/send accounting; no source connection."""
import json
from pathlib import Path
import tempfile

import gate_support as g
from telethon import functions, types, utils


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);g.allocate(root,'one',2)
        assert g.begin_worker(root,'one')==2
        try:g.begin_worker(root,'one')
        except FileExistsError:pass
        else:raise AssertionError('worker allocation reused')
        guard=g.DurableGuard(root,'one',2);cid,_=utils.resolve_id(g.CHAT)
        req=functions.messages.GetHistoryRequest(types.InputPeerChannel(cid,1),0,None,0,2,0,0,0)
        guard.before_send(req)
        saved=json.loads(guard.trace.read_text())
        assert saved['limit']==2 and saved['outcome']=='pending'
        try:guard.before_send(req)
        except g.p.ProbeStop:pass
        else:raise AssertionError('guard exceeded allocation')
        assert len(guard.trace.read_text().splitlines())==1 and guard.slots==2
        req.peer=types.InputPeerChannel(7,1)
        try:guard.before_send(req)
        except g.p.ProbeStop:pass
        else:raise AssertionError('foreign group allowed')
    print('Passed: 3/3 durable launch/send-guard checks; local only')


if __name__=='__main__':main()
