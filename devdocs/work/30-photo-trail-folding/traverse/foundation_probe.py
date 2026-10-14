"""Observe existing #29 / ScrapeOps mechanisms; no proposed trail implementation."""
import hashlib
import importlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import types as pytypes
from unittest.mock import patch
from datetime import datetime,timedelta,timezone

ROOT=Path(__file__).resolve().parents[4]
CONSUMER=Path('/Users/ns/Desktop/projects/flatmir-scrapeops')
sys.path.insert(0,str(ROOT))
# Load the real pure helper files without importing the running app's config.
for name,path in [('scrapeOps',CONSUMER/'scrapeOps'),('scrapeOps.engine',CONSUMER/'scrapeOps/engine')]:
    package=pytypes.ModuleType(name);package.__path__=[str(path)];sys.modules[name]=package
from scrapeOps.engine.collapse import collapse,fold_photo_trails
from telethon import TelegramClient,types
from telethon.extensions import BinaryReader
from tgdata.batch_engine import _record
from tgdata import MessageBatch,album_post_ids,assemble_albums
from examples.album_assembly import AlbumReceiver

NOW=datetime(2026,10,15,tzinfo=timezone.utc)
CHAT=-1000000000007

def row(ident,text='',media='photo',seconds=0,sender=88,group=None):
    return dict(MessageId=ident,ChatId=CHAT,SenderId=sender,Username=None,
                Message=text,MediaType=media,GroupedId=group,MediaPath=None,
                Date=(NOW+timedelta(seconds=seconds)).isoformat(),ReplyToId=None,MessageLink=None)

def raw_record(ident,seconds=0,text='',sender=88,group=None):
    peer=types.PeerUser(sender) if sender>0 else types.PeerChannel(-sender)
    photo=types.Photo(id=ident,access_hash=7,file_reference=b'x',date=NOW,
                      sizes=[types.PhotoSize(type='x',w=1,h=1,size=1)],dc_id=1)
    message=types.Message(id=ident,peer_id=types.PeerChannel(7),date=NOW+timedelta(seconds=seconds),
                         message=text,from_id=peer,grouped_id=group,media=types.MessageMediaPhoto(photo=photo))
    return _record(BinaryReader(bytes(message)).tgread_object(),TelegramClient)

def batch(*records):
    return MessageBatch._from_records(CHAT,min(int(r['id']) for r in records)-1,
                                     sorted(records,key=lambda r:int(r['id'])),'references','limit')

def main():
    observations={}
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        for name,rows in [
            ('video_followup',[row(1,'anchor'),row(2,media='video',seconds=2)]),
            ('backwards_timestamp',[row(1,'anchor',seconds=10),row(2,seconds=2)]),
            ('channel_identity',[row(1,'anchor',sender=-1000000000007),row(2,seconds=2,sender=-1000000000007)]),
            ('missing_identity',[row(1,'anchor',sender=None),row(2,seconds=2,sender=None)])]:
            posts=collapse(rows);before=[list(p.member_ids) for p in posts]
            folded=fold_photo_trails(posts)
            observations[name]=dict(output_posts=len(folded),members=[p.member_ids for p in folded],
                                     input_mutated=before!=[p.member_ids for p in posts])
        assert observations['video_followup']['output_posts']==1
        assert observations['backwards_timestamp']['output_posts']==1
        assert observations['channel_identity']['output_posts']==1
        assert observations['missing_identity']['output_posts']==2
        fixture=[row(275100,'caption',group=7)]+[row(275100+k,group=7) for k in range(1,10)]+[row(275109,seconds=3)]
        folded=fold_photo_trails(collapse(fixture))[0]
        observations['consumer_overflow_fixture']=dict(media_count=folded.media_count,
                                    member_count=len(folded.member_ids),unique_member_count=len(set(folded.member_ids)))
        assert observations['consumer_overflow_fixture']==dict(media_count=11,member_count=11,unique_member_count=10)
        user=raw_record(1,text='anchor',sender=88,group=7)
        channel=raw_record(1,sender=-7)
        observations['actual_sdk_fields']=dict(user_sender=user['sender']['id'],
                   channel_sender=channel['sender']['id'],media_kind=user['media']['kind'])
        assert observations['actual_sdk_fields']==dict(user_sender='88',channel_sender='-1000000000007',media_kind='photo')
        with tempfile.TemporaryDirectory(prefix='tgdata30-foundation-') as tmp:
            path=Path(tmp)/'receiver.db';receiver=AlbumReceiver(path,'one',create=True)
            first=batch(user,raw_record(2,seconds=1));receiver.accept(first)
            key=album_post_ids(first)[0];prior=receiver.load(key);old=prior.to_json()
            receiver.accept(batch(raw_record(3,seconds=2,text='second caption',sender=99,group=7)))
            current=receiver.load(key)
            assert current.member_ids==(1,3) and prior.member_ids==(1,)
            assert current.post_id==prior.post_id and current.revision!=prior.revision
            assert current.membership==prior.membership=='unconfirmed'
            assert prior.to_json()==old
            # Accepted input confirms even though the related current view grew.
            with patch.object(receiver,'_load',side_effect=AssertionError('replay loaded view')):
                assert receiver.accept(first) is None
            observations['later_album_observation']=dict(post_identity_stable=True,revision_changes=True,
                  original_value_immutable=True,current_senders=[m['sender']['id'] for m in current.members],
                  membership=current.membership,old_input_confirmed_without_view=True)
            # Reverse observation arrival is accepted by the existing receiver/core.
            receiver.accept(batch(raw_record(5,seconds=5,group=8)))
            receiver.accept(batch(raw_record(4,seconds=4,text='late earlier caption',group=8)))
            reverse=receiver.load(album_post_ids(batch(raw_record(4,group=8)))[0])
            assert reverse.member_ids==(4,5)
            observations['reverse_observation_arrival']=dict(member_ids=reverse.member_ids,membership=reverse.membership)
    evidence=dict(result='PASS',runtime_components='actual Telethon1.45 values, #29 core/SQLite receiver, real consumer helpers',
                  source_responses='synthetic; no live Telegram or human-intent accuracy claim',observations=observations)
    # Explicit evidence paths avoid exporting any running consumer configuration.
    evidence['source_hashes']={str(p.relative_to(CONSUMER)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (CONSUMER/'scrapeOps/engine/collapse.py',CONSUMER/'scrapeOps/engine/bursts.py')}
    output=Path(__file__).with_suffix('.json');output.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
