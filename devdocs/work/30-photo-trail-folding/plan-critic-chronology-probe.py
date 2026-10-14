"""Reproduce the inquiry sketch's use of post ownership for raw chronology."""
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent/'traverse'))
from contract_probe import infer,load_closed
from foundation_probe import AlbumReceiver,raw_record,batch

with tempfile.TemporaryDirectory(prefix='tgdata30-plan-critic-') as tmp, \
     patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
     patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
    receiver=AlbumReceiver(Path(tmp)/'r.db','one',create=True)
    raw=batch(raw_record(1,seconds=10,sender=88,group=7),raw_record(2,seconds=11,sender=99,group=7),
              raw_record(3,seconds=2,text='new text',sender=88),raw_record(4,seconds=3,sender=88))
    receiver.accept(raw);groups=infer(load_closed(receiver,0,4))
    assert groups==((1,2),(3,4))
    result=dict(result='COUNTEREXAMPLE',observed_groups=groups,positive_user_88_events=[(1,10),(3,2),(4,3)],
         expected='mixed post stays separate; regressed text3 must not create a trail',
         scope='current inquiry sketch; plan must specify per-member chronology independent of post ownership')
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
