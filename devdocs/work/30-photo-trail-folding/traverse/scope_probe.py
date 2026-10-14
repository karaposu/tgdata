"""Probe the proposed selected-post view boundary on the real #29 receiver."""
import json
from pathlib import Path
import socket
import sqlite3
import tempfile
from unittest.mock import patch
from foundation_probe import AlbumReceiver,raw_record,batch,CHAT


def selected(receiver,after,through):
    with receiver._open() as db:
        db.execute('BEGIN');receiver._validate(db)
        keys=[row[0] for row in db.execute(
            'SELECT DISTINCT post_id FROM album_members WHERE collection COLLATE BINARY=? '
            'AND chat_id=? AND message_id>? AND message_id<=?',(receiver.collection,CHAT,after,through))]
        return [receiver._load(db,key) for key in keys]


def main():
    with tempfile.TemporaryDirectory(prefix='tgdata30-scope-') as directory, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        receiver=AlbumReceiver(Path(directory)/'receiver.db','one',create=True)
        raw=batch(raw_record(1,text='first text'),raw_record(2,seconds=1,group=7),
                  raw_record(3,seconds=2,text='new text ends prior trail'),raw_record(4,seconds=3,group=7))
        receiver.accept(raw)
        narrow=selected(receiver,0,2)
        narrow_ids=sorted(int(row['id']) for post in narrow for row in post.members)
        assert narrow_ids==[1,2,4] and 3 not in narrow_ids
        wide=selected(receiver,0,4)
        wide_ids=sorted(int(row['id']) for post in wide for row in post.members)
        assert wide_ids==[1,2,3,4]
        with receiver._open() as db:
            spans=[db.execute('SELECT MIN(message_id),MAX(message_id) FROM album_members '
                              'WHERE collection COLLATE BINARY=? AND post_id COLLATE BINARY=?',
                              ('one',post.post_id)).fetchone() for post in narrow]
        crosses=any(first<=0 or last>2 for first,last in spans)
        assert crosses
        # Scope refusal changes no accepted fact or receipt; exact replay still works.
        receiver.accept(raw)
        with sqlite3.connect(str(receiver.path)) as db:
            assert db.execute('SELECT COUNT(*) FROM album_members').fetchone()[0]==4
            assert db.execute('SELECT COUNT(*) FROM album_receipts').fetchone()[0]==1
        result=dict(result='COUNTEREXAMPLE',narrow_seed=[1,2],expanded_member_ids=narrow_ids,
                    omitted_known_same_sender_text_id=3,widened_member_ids=wide_ids,
                    split_album_detectable_by_metadata=crosses,original_acceptance_still_confirmable=True)
        Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))

if __name__=='__main__':main()
