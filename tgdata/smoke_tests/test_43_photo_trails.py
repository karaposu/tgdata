"""Provisional photo trails: real SDK values, receiver and source engines offline."""

import asyncio
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from telethon import TelegramClient, types
from telethon.errors import ChannelPrivateError
from telethon.extensions import BinaryReader
import tgdata
from tgdata import (
    MessageBatch, TelegramPost, album_post_ids, assemble_albums, SQLiteSyncStore,
    PhotoTrailPolicy, PhotoTrailView, PhotoTrailError, fold_photo_trails, health,
)
from tgdata.album import AlbumAssemblyError
from tgdata.batch_engine import _record
from tgdata.backfill import BackfillStartRequest, BackfillPrepareContext
from tgdata.backfill_engine import BackfillEngine
from tgdata.sync_engine import SyncEngine
from tgdata.sync_store import SyncConflictError
from examples.album_assembly import AlbumReceiver, ReceiverError, collect
import examples.album_assembly as receiver_module
from examples.photo_trails import load_photo_trails, demo

CHAT = -1000000000007
GROUP = (1 << 62) + 17
NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)
ON = PhotoTrailPolicy(enabled=True)


def record(ident, text='', *, sender=88, group=None, seconds=None, photo=True, reply=None):
    date = NOW + timedelta(seconds=ident if seconds is None else seconds)
    peer = None if sender is None else types.PeerUser(sender) if sender > 0 else types.PeerChannel(-sender)
    media = None
    if photo:
        asset = types.Photo(id=ident, access_hash=7, file_reference=b'x', date=NOW,
                            sizes=[types.PhotoSize(type='x', w=1, h=1, size=1)], dc_id=1)
        media = types.MessageMediaPhoto(photo=asset)
    message = types.Message(id=ident, peer_id=types.PeerChannel(7), date=date, message=text,
                            from_id=peer, grouped_id=group, media=media,
                            reply_to=None if reply is None else types.MessageReplyHeader(reply_to_msg_id=reply))
    return _record(BinaryReader(bytes(message)).tgread_object(), TelegramClient)


def batch(*records, chat=CHAT, after=None, stop='limit', mode='references'):
    ordered = sorted(records, key=lambda row:int(row['id']))
    if after is None:
        after = int(ordered[0]['id']) - 1 if ordered else 0
    return MessageBatch._from_records(chat, after, ordered, mode, stop if records else 'end')


def posts(*records, chat=CHAT, mode='references'):
    raw = batch(*records, chat=chat, mode=mode)
    return assemble_albums(raw, previous={key:None for key in album_post_ids(raw)})


def view(*records, policy=ON, **options):
    return fold_photo_trails(posts(*records), policy=policy, **options)


def member_groups(value):
    by_id = {post.post_id:post for post in value.posts}
    return tuple(tuple(sorted(mid for key in group for mid in by_id[key].member_ids)) for group in value.groups)


def resign(document):
    payload = {key:value for key,value in document.items() if key != 'revision'}
    document['revision'] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                  separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return document


def stored(receiver):
    with sqlite3.connect(str(receiver.path)) as db:
        return (db.execute('SELECT * FROM album_members ORDER BY collection,chat_id,message_id').fetchall(),
                db.execute('SELECT * FROM album_receipts ORDER BY collection,batch_id').fetchall())


class Facade:
    def __init__(self, source):
        self.source, self.acks = source, []
    async def sync_group(self, chat, **options):
        return await self.source.prepare(chat, **options)
    async def acknowledge_sync(self, chat, ident):
        self.acks.append(ident)
        return await self.source.acknowledge(chat, ident)


class PhotoTrailTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='tgdata_photo_trail_test_')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for name in ('connect', 'connect_ex'):
            guard = patch.object(socket.socket, name, side_effect=AssertionError('network forbidden'))
            guard.start(); self.addCleanup(guard.stop)

    def receiver(self, name='one', **options):
        return AlbumReceiver(self.root/'posts.db', name, create=True, **options)

    def load(self, receiver, through, **options):
        return load_photo_trails(receiver, CHAT, after_id=0, through_id=through, policy=ON, **options)

    def test_exports_and_default_disabled(self):
        for name in ('PhotoTrailPolicy', 'PhotoTrailView', 'PhotoTrailError', 'fold_photo_trails'):
            self.assertIs(getattr(tgdata, name), globals()[name]); self.assertIn(name, tgdata.__all__)
        original = posts(record(1,'text'), record(2))
        result = fold_photo_trails(original)
        self.assertEqual(member_groups(result), ((1,), (2,)))
        self.assertFalse(result.policy.enabled)
        self.assertEqual((result.folded_posts,result.folded_photos),(0,0))
        self.assertEqual(tgdata.__version__, '0.1')

    def test_policy_validation_and_immutable_roundtrip(self):
        self.assertEqual(PhotoTrailPolicy.from_dict(ON.to_dict()), ON)
        ON.to_dict()['enabled'] = False
        with self.assertRaises(FrozenInstanceError): ON.enabled = False
        for name in ('gap_seconds','max_span_seconds','max_photos'):
            for bad in (None, True, 0, -1, 1.5, '3', 1<<31):
                with self.assertRaises(PhotoTrailError): PhotoTrailPolicy(**{name:bad})
        for bad in (0,1,None,'yes'):
            with self.assertRaises(PhotoTrailError): PhotoTrailPolicy(enabled=bad)
        for bad in ({}, dict(ON.to_dict(),extra=True), [], None):
            with self.assertRaises(PhotoTrailError): PhotoTrailPolicy.from_dict(bad)

    def test_text_and_loose_photos_chain(self):
        original = posts(record(1,'caption',photo=False),record(2),record(3))
        before = tuple(p.to_json() for p in original)
        result = fold_photo_trails(original, policy=ON)
        self.assertEqual(member_groups(result), ((1,2,3),))
        self.assertEqual((result.folded_posts,result.folded_photos),(2,2))
        self.assertEqual(tuple(p.to_json() for p in result.posts),before)
        self.assertEqual(tuple(p.to_json() for p in original),before)
        self.assertEqual(result.status,'provisional')

    def test_album_anchor_retains_all_captions(self):
        result = view(record(1,'first',group=GROUP), record(2,'second',group=GROUP),record(3))
        self.assertEqual(member_groups(result),((1,2,3),))
        self.assertEqual([r['text'] for r in result.posts[0].members],['first','second'])
        self.assertEqual(result.posts[0].membership,'unconfirmed')

    def test_whole_photo_album_follower_and_count_units(self):
        result = view(record(1,'text'),record(2,group=GROUP),record(3,group=GROUP),record(4))
        self.assertEqual(member_groups(result),((1,2,3,4),))
        self.assertEqual((result.folded_posts,result.folded_photos),(2,3))
        self.assertEqual(result.posts[1].member_ids,(2,3))

    def test_known_users_interleave_inside_albums(self):
        result=view(record(1,'A',group=GROUP),record(2,'B',sender=99),record(3,group=GROUP),
                    record(4,sender=99),record(5))
        self.assertEqual(member_groups(result),((1,3,5),(2,4)))

    def test_chat_identity_prevents_cross_chat_attachment(self):
        a=posts(record(1,'A'),record(2))
        b=posts(record(1,'B'),record(2),chat=CHAT-1)
        result=fold_photo_trails(a+b,policy=ON)
        self.assertEqual(len(result.groups),2)
        by_id={post.post_id:post for post in result.posts}
        for group in result.groups:self.assertEqual(len({by_id[key].chat_id for key in group}),1)

    def test_unknown_channel_and_mixed_post_owners(self):
        for sender in (None,-7):
            self.assertEqual(member_groups(view(record(1,'text',sender=sender),record(2,sender=sender))),((1,),(2,)))
        result=view(record(1,'text',group=GROUP),record(2,sender=99,group=GROUP),record(3))
        self.assertEqual(member_groups(result),((1,2),(3,)))

    def test_unknown_late_member_interrupts_at_its_original_position(self):
        result=view(record(1,sender=-7,group=GROUP),record(2,'text'),record(3),
                    record(5,sender=-7,group=GROUP),record(6))
        self.assertEqual(member_groups(result),((1,5),(2,3),(6,)))

    def test_same_user_overlapping_post_intervals_are_barriers(self):
        result=view(record(1,'album',group=GROUP),record(2,'text'),record(3,group=GROUP),record(4))
        self.assertEqual(member_groups(result),((1,3),(2,),(4,)))

    def test_backward_and_missing_dates_do_not_activate_anchors(self):
        result=view(record(1,'old',seconds=10),record(2,'regressed',seconds=2),record(3,seconds=3))
        self.assertEqual(member_groups(result),((1,),(2,),(3,)))
        missing=record(2,'missing');missing['date']=None
        self.assertEqual(member_groups(view(record(1,'text'),missing,record(3))),((1,),(2,),(3,)))
        result=view(record(1,'album',group=GROUP,seconds=2),record(2,group=GROUP,seconds=1),record(3))
        self.assertEqual(member_groups(result),((1,2),(3,)))

    def test_individual_chronology_survives_mixed_or_missing_post_owner(self):
        for sender in (99,None):
            result=view(record(1,group=GROUP,seconds=10),record(2,sender=sender,group=GROUP,seconds=11),
                        record(3,'regressed',seconds=2),record(4,seconds=3),
                        record(5,'later valid text',seconds=12),record(6,seconds=13))
            self.assertEqual(member_groups(result),((1,2),(3,),(4,),(5,6)))

    def test_new_text_ends_old_trail_and_can_anchor_new_photos(self):
        result=view(record(1,'first'),record(2),record(3,'second'),record(4))
        self.assertEqual(member_groups(result),((1,2),(3,4)))

    def test_nonphoto_and_service_activity_breaks_the_chain(self):
        for kind in ('video','document','sticker','webpage'):
            middle=record(2);middle['media']['kind']=kind
            middle['media']['downloadable']=kind!='webpage'
            self.assertEqual(member_groups(view(record(1,'text'),middle,record(3))),((1,),(2,),(3,)))
        service=record(2);service.update(kind='service',text=None,service_action='MessageActionChatEditTitle')
        self.assertEqual(member_groups(view(record(1,'text'),service,record(3))),((1,),(2,),(3,)))

    def test_reply_must_name_an_earlier_chain_or_candidate_member(self):
        self.assertEqual(member_groups(view(record(1,'text'),record(2,reply=1),record(3,reply=2))),((1,2,3),))
        self.assertEqual(member_groups(view(record(1,'text'),record(2,group=GROUP,reply=1),
                                                   record(3,group=GROUP,reply=2))),((1,2,3),))
        for reply in (999,2,3):
            self.assertEqual(member_groups(view(record(1,'text'),record(2,reply=reply),record(3))),((1,),(2,),(3,)))

    def test_exact_gap_and_span_boundaries(self):
        anchor=record(1,'text',seconds=0)
        exact=record(2,seconds=30)
        self.assertEqual(member_groups(view(anchor,exact)),((1,2),))
        late=dict(exact,date='2026-10-15T00:00:30.000001Z')
        self.assertEqual(member_groups(view(anchor,late)),((1,),(2,)))
        policy=PhotoTrailPolicy(enabled=True,gap_seconds=3,max_span_seconds=4)
        result=view(anchor,record(2,seconds=2),record(3,seconds=4),record(4,seconds=5),policy=policy)
        self.assertEqual(member_groups(result),((1,2,3),(4,)))

    def test_span_begins_at_anchor_last_original_member(self):
        policy=PhotoTrailPolicy(enabled=True,gap_seconds=2,max_span_seconds=2)
        result=view(record(1,'album',group=GROUP,seconds=0),record(2,group=GROUP,seconds=100),
                    record(3,seconds=102),policy=policy)
        self.assertEqual(member_groups(result),((1,2,3),))

    def test_photo_count_refuses_a_whole_follower_without_partial_fold(self):
        policy=PhotoTrailPolicy(enabled=True,max_photos=1)
        result=view(record(1,'text'),record(2,group=GROUP),record(3,group=GROUP),record(4),policy=policy)
        self.assertEqual(member_groups(result),((1,),(2,3,4)))
        self.assertEqual((result.folded_posts,result.folded_photos),(1,1))

    def test_photos_before_text_never_merge_backwards(self):
        self.assertEqual(member_groups(view(record(1),record(2,'text'),record(3))),((1,),(2,3)))

    def test_late_caption_withdraws_link_and_preserves_old_value(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'text'),record(2,group=GROUP),record(3,group=GROUP)))
        old=self.load(receiver,3);encoded=old.to_json()
        receiver.accept(batch(record(4,'later caption',group=GROUP)))
        latest=self.load(receiver,4)
        self.assertEqual(member_groups(old),((1,2,3),));self.assertEqual(member_groups(latest),((1,),(2,3,4)))
        self.assertNotEqual(old.revision,latest.revision);self.assertEqual(old.to_json(),encoded)

    def test_late_mixed_identity_and_extent_recompute_relations(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'album',group=GROUP),record(2)))
        old=self.load(receiver,2);self.assertEqual(member_groups(old),((1,2),))
        receiver.accept(batch(record(3,sender=99,group=GROUP)))
        self.assertEqual(member_groups(self.load(receiver,3)),((1,3),(2,)))

    def test_view_copies_getters_hash_and_repr(self):
        result=view(record(1,'PRIVATE TEXT'),record(2));wire=result.to_json()
        result.to_dict()['posts'][0]['members'][0]['text']='changed'
        result.posts[0].members[0]['text']='changed'
        with self.assertRaises(FrozenInstanceError): result._encoded='{}'
        with self.assertRaises(FrozenInstanceError): result.policy.enabled=False
        self.assertEqual(result.to_json(),wire)
        self.assertEqual(PhotoTrailView.from_json(wire.encode()),result)
        self.assertEqual(hash(PhotoTrailView.from_json(wire)),hash(result))
        self.assertIsInstance(result.groups,tuple);self.assertIsInstance(result.groups[0],tuple)
        self.assertNotIn('PRIVATE TEXT',repr(result))

    def test_large_ids_and_utf8_preserve_exact_originals(self):
        original=posts(record(2147483646,'ğ🙂',sender=(1<<62)+7,group=-GROUP),
                       record(2147483647,sender=(1<<62)+7))
        result=fold_photo_trails(original,policy=ON)
        self.assertEqual(result.posts[0].grouped_id,-GROUP)
        self.assertEqual(result.posts[0].members[0]['sender']['id'],str((1<<62)+7))
        self.assertEqual(PhotoTrailView.from_json(result.to_json()).to_json(),result.to_json())

    def test_original_media_modes_and_blob_references_survive(self):
        anchor=posts(record(1,'text',photo=False))
        row=record(2);digest=hashlib.sha256(b'x').hexdigest()
        row['media']['blob']=dict(sha256=digest,size=1,path=digest)
        photo=posts(row,mode='download')
        result=fold_photo_trails(anchor+photo,policy=ON)
        self.assertEqual(member_groups(result),((1,2),))
        self.assertEqual(result.posts[1].media_mode,'download')
        self.assertEqual(result.posts[1].members[0]['media']['blob'],row['media']['blob'])

    def test_strict_json_and_value_format(self):
        result=view(record(1,'text'),record(2))
        for raw in ('','{','null','[]','{"a":1,"a":1}','{"a":NaN}',b'\xff','\ud800',1):
            with self.assertRaises(PhotoTrailError):PhotoTrailView.from_json(raw)
        duplicate=result.to_json().replace('"version":1','"version":1,"version":1',1)
        with self.assertRaises(PhotoTrailError):PhotoTrailView.from_json(duplicate)
        changes=[lambda d:d.update(version=True),lambda d:d.update(schema='other'),
                 lambda d:d.update(algorithm='other'),lambda d:d.update(status='final'),
                 lambda d:d.update(extra=1),lambda d:d.update(folded_posts=True),
                 lambda d:d.update(folded_photos=-1),lambda d:d['policy'].update(extra=1),
                 lambda d:d['posts'].reverse(),lambda d:d['posts'].append(d['posts'][0]),
                 lambda d:d['posts'][0]['members'][0].update(text='changed')]
        for change in changes:
            doc=result.to_dict();change(doc)
            with self.assertRaises(PhotoTrailError):PhotoTrailView(resign(doc))

    def test_rehashed_forged_relation_and_counts_refuse(self):
        result=view(record(1,'text'),record(2,sender=99))
        doc=result.to_dict();ids=[p.post_id for p in result.posts]
        doc.update(groups=[dict(anchor_post_id=ids[0],post_ids=ids)],folded_posts=1,folded_photos=1)
        with self.assertRaises(PhotoTrailError):PhotoTrailView(resign(doc))
        good=view(record(1,'text'),record(2)).to_dict();good['policy']['enabled']=False
        with self.assertRaises(PhotoTrailError):PhotoTrailView(resign(good))
        good=view(record(1,'text'),record(2)).to_dict();good['groups'][0]['extra']=True
        with self.assertRaises(PhotoTrailError):PhotoTrailView(resign(good))

    def test_exact_utf8_work_and_saved_value_limits(self):
        original=posts(record(1,'ğ🙂'),record(2));result=fold_photo_trails(original,policy=ON)
        input_size=sum(len(p.to_json().encode()) for p in original);output_size=len(result.to_json().encode())
        self.assertEqual(fold_photo_trails(original,policy=ON,max_bytes=input_size+output_size),result)
        with self.assertRaises(PhotoTrailError):fold_photo_trails(original,policy=ON,max_bytes=input_size+output_size-1)
        self.assertEqual(PhotoTrailView.from_json(result.to_json(),max_bytes=output_size),result)
        with self.assertRaises(PhotoTrailError):PhotoTrailView.from_json(result.to_json(),max_bytes=output_size-1)

    def test_concrete_input_conflicts_duplicates_and_visit_bounds(self):
        original=posts(record(1,'text'),record(2));same=fold_photo_trails(original,policy=ON)
        self.assertEqual(fold_photo_trails(original+original,policy=ON),same)
        with self.assertRaises(PhotoTrailError):fold_photo_trails(original+original,policy=ON,max_members=3)
        for bad in (None,{},'posts',iter(original),[{}]):
            with self.assertRaises(PhotoTrailError):fold_photo_trails(bad)
        for bad in (True,0,-1,1.5,'4',None):
            for name in ('max_members','max_bytes'):
                with self.assertRaises(PhotoTrailError):fold_photo_trails(original,**{name:bad})
        with self.assertRaises(PhotoTrailError):fold_photo_trails(original,policy={})
        changed=posts(record(1,'edited'))
        with self.assertRaises(PhotoTrailError):fold_photo_trails(original+changed,policy=ON)
        reassigned=posts(record(1,'text',group=GROUP))
        with self.assertRaises(PhotoTrailError):fold_photo_trails(original+reassigned,policy=ON)

    def test_permutations_and_all_batch_partitions_have_same_current_view(self):
        records=[record(1,'text'),record(2,group=GROUP),record(3,group=GROUP),record(4)]
        expected=view(*records)
        for mask in range(8):
            pieces=[];piece=[]
            for i,row in enumerate(records):
                piece.append(row)
                if i==3 or mask&(1<<i):pieces.append(batch(*piece));piece=[]
            for reverse in (False,True):
                path=self.root/('partition-{}-{}.db'.format(mask,reverse))
                receiver=AlbumReceiver(path,'one',create=True)
                for raw in pieces[::-1] if reverse else pieces:receiver.accept(raw)
                result=self.load(receiver,4)
                self.assertEqual(result,expected)
                self.assertEqual(fold_photo_trails(tuple(reversed(result.posts)),policy=ON),expected)

    def test_local_errors_do_not_leak_content_or_inherit_rpc_health(self):
        original=posts(record(1,'PRIVATE TEXT'))
        try:raise ChannelPrivateError(request=None)
        except ChannelPrivateError:
            with self.assertRaises(PhotoTrailError) as caught:fold_photo_trails(original,max_bytes=1)
        self.assertIsNone(health.classify(caught.exception));self.assertNotIn('PRIVATE TEXT',str(caught.exception))
        before=original[0].to_json()
        with patch('builtins.open',side_effect=AssertionError('pure function performed I/O')):
            self.assertEqual(member_groups(fold_photo_trails(original,policy=ON)),((1,),))
        self.assertEqual(original[0].to_json(),before)

    def test_raised_10001_member_limit_survives_load_and_getters(self):
        template=record(1,'album',group=GROUP,seconds=0)
        rows=[dict(template,id=str(i),text='album' if i==1 else '') for i in range(1,10002)]
        receiver=self.receiver(max_members=10001)
        receiver.accept(batch(*rows[:10000]));receiver.accept(batch(rows[-1]))
        result=self.load(receiver,10001)
        loaded=PhotoTrailView.from_json(result.to_json(),max_members=10001)
        self.assertEqual(loaded.posts[0].member_ids,tuple(range(1,10002)))
        self.assertEqual(member_groups(loaded),(tuple(range(1,10002)),))
        self.assertEqual(loaded,result)
        with self.assertRaises(PhotoTrailError):PhotoTrailView.from_json(result.to_json())

    def test_adapter_default_empty_and_argument_refusal_before_open(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'text'),record(2)))
        disabled=load_photo_trails(receiver,CHAT,after_id=0,through_id=2)
        self.assertEqual(member_groups(disabled),((1,),(2,)))
        self.assertEqual(member_groups(self.load(receiver,0)),())
        with patch.object(receiver,'_open',side_effect=AssertionError('invalid argument opened storage')):
            for chat,after,through in ((True,0,2),(CHAT,True,2),(CHAT,0,True),(CHAT,-1,2),
                                       (CHAT,3,2),(CHAT,0,1<<31),('chat',0,2),(0,0,2)):
                with self.assertRaises(PhotoTrailError):load_photo_trails(receiver,chat,after_id=after,through_id=through)
            with self.assertRaises(PhotoTrailError):load_photo_trails(receiver,CHAT,after_id=0,through_id=2,policy={})
        with self.assertRaises(PhotoTrailError):load_photo_trails(None,CHAT,after_id=0,through_id=2)

    def test_split_lower_and_upper_bounds_refuse_without_state_change(self):
        receiver=self.receiver();raw=batch(record(1,'album',group=GROUP),record(2,group=GROUP),record(3))
        receiver.accept(raw);before=stored(receiver)
        for after,through in ((0,1),(1,3)):
            with self.assertRaises(PhotoTrailError):load_photo_trails(receiver,CHAT,after_id=after,through_id=through,policy=ON)
        self.assertEqual(stored(receiver),before)
        self.assertIsNone(receiver.accept(raw))

    def test_scope_counterexample_cannot_hide_saved_intervening_text(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'first'),record(2,group=GROUP),
                                                      record(3,'new text'),record(4,group=GROUP)))
        with self.assertRaises(PhotoTrailError):self.load(receiver,2)
        self.assertEqual(member_groups(self.load(receiver,4)),((1,),(2,4),(3,)))

    def test_missing_known_file_collection_or_schema_never_becomes_empty(self):
        receiver=self.receiver();path=receiver.path
        path.unlink()
        with self.assertRaises(ReceiverError):self.load(receiver,2)
        self.assertFalse(path.exists())
        receiver=self.receiver()
        with sqlite3.connect(str(path)) as db:db.execute('DELETE FROM album_collections')
        with self.assertRaises(ReceiverError):self.load(receiver,2)
        with sqlite3.connect(str(path)) as db:db.execute('DROP TABLE album_members')
        with self.assertRaises(ReceiverError):self.load(receiver,2)

    def test_selected_corrupt_records_and_metadata_refuse_without_repair(self):
        cases=[('UPDATE album_members SET record=?',('{}',)),
               ('UPDATE album_members SET record_sha256=?',('0'*64,)),
               ('UPDATE album_members SET post_id=?',('wrong',)),
               ('UPDATE album_members SET record=?',(sqlite3.Binary(b'broken'),)),
               ('UPDATE album_members SET post_id=?',(sqlite3.Binary(b'broken'),))]
        for index,(sql,args) in enumerate(cases):
            receiver=AlbumReceiver(self.root/('bad-{}.db'.format(index)),'one',create=True)
            receiver.accept(batch(record(1,'private text')))
            with sqlite3.connect(str(receiver.path)) as db:db.execute(sql,args)
            before=stored(receiver)
            with self.assertRaises((ReceiverError,PhotoTrailError,AlbumAssemblyError)) as caught:self.load(receiver,1)
            self.assertNotIn('private text',str(caught.exception));self.assertEqual(stored(receiver),before)

    def test_selected_post_with_wrong_chat_is_not_loaded_as_a_valid_view(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'text',group=GROUP),record(2,group=GROUP)))
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute('UPDATE album_members SET chat_id=? WHERE message_id=2',(CHAT-1,))
        with self.assertRaises(ReceiverError):self.load(receiver,2)

    def test_exact_namespaces_with_foreign_column_collations(self):
        path=self.root/'foreign.db'
        with sqlite3.connect(str(path)) as db:
            for table,columns in receiver_module._SCHEMA.items():
                if table=='album_collections':
                    columns='collection TEXT COLLATE NOCASE NOT NULL, PRIMARY KEY(collection COLLATE BINARY)'
                else:
                    columns=columns.replace('collection TEXT NOT NULL','collection TEXT COLLATE NOCASE NOT NULL')
                    columns=columns.replace('PRIMARY KEY(collection,','PRIMARY KEY(collection COLLATE BINARY,')
                    columns=columns.replace('post_id TEXT NOT NULL','post_id TEXT COLLATE NOCASE NOT NULL')
                db.execute('CREATE TABLE {} ({})'.format(table,columns))
            db.execute('CREATE INDEX album_members_by_post ON album_members(collection COLLATE BINARY,post_id COLLATE BINARY,message_id)')
            db.execute('INSERT INTO album_meta VALUES (?,?)',('album-receiver',2))
        a=AlbumReceiver(path,'Tenant',create=True);b=AlbumReceiver(path,'tenant',create=True)
        a.accept(batch(record(1,'A'),record(2)));b.accept(batch(record(1,'B'),record(2)))
        self.assertEqual(self.load(a,2).posts[0].members[0]['text'],'A')
        self.assertEqual(self.load(b,2).posts[0].members[0]['text'],'B')
        with sqlite3.connect(str(path)) as db:
            db.execute('UPDATE album_members SET post_id=upper(post_id) WHERE collection COLLATE BINARY=? AND message_id=2',('Tenant',))
        with self.assertRaises(ReceiverError):self.load(a,2)
        self.assertEqual(self.load(b,2).folded_photos,1)

    def test_count_key_and_record_bounds_precede_payload(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'a'*1000),record(2,'b'*1000)))
        for options in ({'max_members':1},{'max_bytes':1000}):
            limited=AlbumReceiver(receiver.path,'one',**options)
            with patch.object(limited,'_read_members',side_effect=AssertionError('payload materialized')):
                with self.assertRaises(PhotoTrailError):self.load(limited,2)
        with sqlite3.connect(str(receiver.path)) as db:
            db.execute('UPDATE album_members SET post_id=? WHERE message_id=1',('x'*10000,))
        limited=AlbumReceiver(receiver.path,'one',max_bytes=3000)
        with patch.object(limited,'_stats',side_effect=AssertionError('giant key materialized')):
            with self.assertRaises(PhotoTrailError):self.load(limited,2)

    def test_actual_post_json_overhead_is_charged_before_next_payload(self):
        receiver=self.receiver();a,b=record(1,'a'*1000),record(2,'b'*1000)
        receiver.accept(batch(a,b))
        encoded=lambda r:json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        cap=len(encoded(a))+len(encoded(b))+1
        reader=AlbumReceiver(receiver.path,'one',max_bytes=cap);reads=[];actual=reader._read_members
        def read(db,key):reads.append(key);return actual(db,key)
        with patch.object(reader,'_read_members',side_effect=read):
            with self.assertRaises((PhotoTrailError,AlbumAssemblyError)):self.load(reader,2)
        self.assertEqual(len(reads),1)

    def test_view_uses_consistent_snapshot_during_late_album_growth(self):
        receiver=self.receiver();raw=batch(record(1,'text'),record(2,group=GROUP));receiver.accept(raw)
        with sqlite3.connect(str(receiver.path)) as db:db.execute('PRAGMA journal_mode=WAL')
        writer=AlbumReceiver(receiver.path,'one');actual=receiver._load;written=[]
        def grow(db,key,**options):
            if not written:writer.accept(batch(record(3,'caption',group=GROUP)));written.append(True)
            return actual(db,key,**options)
        with patch.object(receiver,'_load',side_effect=grow):old=self.load(receiver,2)
        self.assertEqual(member_groups(old),((1,2),))
        with self.assertRaises(PhotoTrailError):self.load(receiver,2)
        self.assertEqual(member_groups(self.load(receiver,3)),((1,),(2,3)))
        self.assertIsNone(receiver.accept(raw))

    def test_view_has_no_writes_and_policy_changes_do_not_change_originals(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'text'),record(2)))
        before=stored(receiver);actual=receiver._open
        @contextmanager
        def readonly():
            with actual() as db:
                db.set_authorizer(lambda op,*args:sqlite3.SQLITE_DENY if op in
                    (sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE) else sqlite3.SQLITE_OK)
                yield db
                self.assertEqual(db.total_changes,0)
        with patch.object(receiver,'_open',side_effect=readonly):
            enabled=self.load(receiver,2)
            disabled=load_photo_trails(receiver,CHAT,after_id=0,through_id=2)
        self.assertNotEqual(enabled.revision,disabled.revision)
        self.assertEqual(stored(receiver),before)

    def test_storage_contention_and_cleanup_preserve_failures(self):
        receiver=self.receiver();receiver.accept(batch(record(1,'text')))
        blocker=sqlite3.connect(str(receiver.path),isolation_level=None)
        try:
            blocker.execute('BEGIN EXCLUSIVE')
            with self.assertRaises(sqlite3.OperationalError):self.load(receiver,1)
        finally:blocker.rollback();blocker.close()
        real=sqlite3.connect
        class BadClose(sqlite3.Connection):
            def close(self):super().close();raise OSError('secondary close error')
        def connect(*args,**kwargs):return real(*args,factory=BadClose,**kwargs)
        with patch.object(receiver_module.sqlite3,'connect',side_effect=connect):
            with patch.object(receiver,'_stats',side_effect=RuntimeError('primary read error')):
                with self.assertRaisesRegex(RuntimeError,'primary read error'):self.load(receiver,1)
            with self.assertRaisesRegex(OSError,'secondary close error'):self.load(receiver,1)
        self.assertEqual(member_groups(self.load(receiver,1)),((1,),))

    def test_original_confirmation_survives_unchanged_policy_view_refusal(self):
        receiver=self.receiver(max_members=3)
        first=batch(record(1,'one'),record(2,'two'));receiver.accept(first)
        receiver.accept(batch(record(3,'three'),record(4,'four')))
        before=stored(receiver)
        with self.assertRaises(PhotoTrailError):self.load(receiver,4)
        with patch.object(receiver,'_load',side_effect=AssertionError('confirmation loaded growing views')):
            self.assertIsNone(receiver.accept(first))
        self.assertEqual(stored(receiver),before)

    def test_daily_restart_lost_ack_and_later_photo(self):
        async def run():
            calls=[]
            async def read(chat,**options):
                calls.append(options);ident=options['after_id']+1
                return batch(record(ident,'text' if ident==1 else ''),after=options['after_id'])
            store=SQLiteSyncStore(self.root/'source.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0);receiver=self.receiver()
            first=await source.prepare(CHAT,limit=1);wire=first.to_json();receiver.accept(first)
            source=SyncEngine(read,SQLiteSyncStore(store.path,create=False));receiver=AlbumReceiver(receiver.path,'one')
            replay=await source.prepare(CHAT,limit=1);self.assertEqual(replay.to_json(),wire)
            receiver.accept(replay);await source.acknowledge(CHAT,replay.batch_id)
            second=await source.prepare(CHAT,limit=1);receiver.accept(second)
            await source.acknowledge(CHAT,second.batch_id)
            self.assertEqual(member_groups(self.load(receiver,2)),((1,2),))
            self.assertEqual(len(calls),2);self.assertEqual((await source.status(CHAT)).after_id,2)
        asyncio.run(run())

    def test_backfill_keeps_original_delivery_reference_and_window(self):
        async def run():
            calls=[];start,end=NOW-timedelta(hours=1),NOW+timedelta(hours=1)
            async def read(chat,**options):
                calls.append(options);self.assertEqual((options['start_date'],options['end_date']),(start,end))
                ident=options['after_id']+1
                return batch(record(ident,'text' if ident==1 else ''),after=options['after_id'],stop='end' if ident==2 else 'limit')
            store=SQLiteSyncStore(self.root/'history.db')
            source=BackfillEngine(store,'jobs',read_batch=read,clock=lambda:NOW+timedelta(hours=2))
            request=BackfillStartRequest(collection_id='jobs',chat_id=CHAT,run_id='one',destination_id='one',
                     origin='fresh',after_id=0,expected_predecessor=None,start_date=start,end_date=end,batch_size=1,pause_seconds=0)
            state=(await source.start(request,submission='new')).status
            first=await source.prepare(BackfillPrepareContext.from_status(state));receiver=self.receiver();receiver.accept(first.batch)
            source=BackfillEngine(SQLiteSyncStore(store.path,create=False),'jobs',read_batch=read,clock=lambda:NOW+timedelta(hours=2))
            replay=await source.prepare(BackfillPrepareContext.from_status(first.status))
            self.assertEqual(replay.delivery,first.delivery);receiver.accept(replay.batch)
            accepted=await source.acknowledge(replay.delivery)
            last=await source.prepare(BackfillPrepareContext.from_status(accepted));receiver.accept(last.batch)
            done=await source.acknowledge(last.delivery)
            self.assertEqual((done.after_id,done.terminal_outcome),(2,'completed'))
            self.assertEqual(member_groups(self.load(receiver,2)),((1,2),));self.assertEqual(len(calls),2)
        asyncio.run(run())

    def test_source_publication_failure_does_not_invent_a_receipt(self):
        async def run():
            raw=batch(record(1,'text'),after=0)
            async def read(*args,**options):return raw
            store=SQLiteSyncStore(self.root/'source.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0)
            class Refuse:
                async def load(self,chat):return await store.load(chat)
                async def compare_and_swap(self,*args):return False
            facade=Facade(SyncEngine(read,Refuse()));receiver=self.receiver()
            with self.assertRaises(SyncConflictError):await collect(facade,CHAT,receiver,max_batches=1)
            self.assertEqual(facade.acks,[]);self.assertIsNone((await source.status(CHAT)).pending_batch_id)
            self.assertEqual(member_groups(self.load(receiver,1)),());self.assertEqual(stored(receiver),( [], [] ))
        asyncio.run(run())

    def test_read_failure_waits_for_normal_pending_replay(self):
        async def run():
            raw=batch(record(1,'text'),record(2),after=0,stop='interrupted');calls=[]
            async def read(*args,**options):
                calls.append(options);error=RuntimeError('read failed');error.partial_result=raw;raise error
            store=SQLiteSyncStore(self.root/'source.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0);receiver=self.receiver();facade=Facade(source)
            with self.assertRaises(RuntimeError):await collect(facade,CHAT,receiver,max_batches=1)
            self.assertEqual(facade.acks,[]);self.assertEqual(stored(receiver),([],[]))
            self.assertEqual((await source.status(CHAT)).pending_batch_id,raw.batch_id)
            await collect(facade,CHAT,receiver,max_batches=1)
            self.assertEqual(facade.acks,[raw.batch_id]);self.assertEqual(len(calls),1)
            self.assertEqual(member_groups(self.load(receiver,2)),((1,2),))
        asyncio.run(run())

    def test_receiver_commit_response_loss_recovers_without_inference_on_ack(self):
        async def run():
            raw=batch(record(1,'text'),record(2),after=0);calls=[]
            async def read(*args,**options):calls.append(options);return raw
            store=SQLiteSyncStore(self.root/'source.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0);owed=await source.prepare(CHAT,limit=2)
            receiver=self.receiver();real=sqlite3.connect
            class LostReply(sqlite3.Connection):
                def commit(self):
                    super().commit()
                    if self.total_changes:raise OSError('committed; reply lost')
            def connect(*args,**kwargs):return real(*args,factory=LostReply,**kwargs)
            with patch.object(receiver_module.sqlite3,'connect',side_effect=connect):
                with self.assertRaises(OSError):receiver.accept(owed)
            self.assertEqual((await source.status(CHAT)).after_id,0)
            replay=await source.prepare(CHAT,limit=2)
            with patch.object(receiver,'_load',side_effect=AssertionError('confirmation loaded a view')):
                receiver.accept(replay);await source.acknowledge(CHAT,replay.batch_id)
            self.assertEqual(member_groups(self.load(receiver,2)),((1,2),));self.assertEqual(len(calls),1)
        asyncio.run(run())

    def test_read_transaction_closes_before_pure_projection(self):
        import examples.photo_trails as example
        receiver=self.receiver();receiver.accept(batch(record(1,'text'),record(2)))
        writer=AlbumReceiver(receiver.path,'one');actual=example.fold_photo_trails
        def project(originals,**options):
            writer.accept(batch(record(3))) # DELETE-journal commit fails if reader still holds its lock.
            return actual(originals,**options)
        with patch.object(example,'fold_photo_trails',side_effect=project):old=self.load(receiver,2)
        self.assertEqual(member_groups(old),((1,2),))
        self.assertEqual(member_groups(self.load(receiver,3)),((1,2,3),))

    def test_cancellation_after_original_commit_keeps_pending_replay(self):
        async def run():
            calls=[];raw=batch(record(1,'text'),record(2),after=0)
            async def read(*args,**options):calls.append(options);return raw
            store=SQLiteSyncStore(self.root/'source.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0);receiver=self.receiver();actual=receiver.accept
            def accept(value):actual(value);asyncio.current_task().cancel()
            class Cancellable(Facade):
                async def acknowledge_sync(self,chat,ident):
                    await asyncio.sleep(0)
                    return await super().acknowledge_sync(chat,ident)
            facade=Cancellable(source)
            with patch.object(receiver,'accept',side_effect=accept):
                task=asyncio.create_task(collect(facade,CHAT,receiver,max_batches=1,batch_size=2))
                with self.assertRaises(asyncio.CancelledError):await task
            state=await source.status(CHAT);self.assertEqual(state.after_id,0);self.assertEqual(state.pending_batch_id,raw.batch_id)
            replay=await source.prepare(CHAT,limit=2);receiver.accept(replay)
            self.assertEqual(member_groups(self.load(receiver,2)),((1,2),))
            await source.acknowledge(CHAT,replay.batch_id);self.assertEqual(len(calls),1)
        asyncio.run(run())

    def test_real_process_loss_after_acceptance_before_view_and_ack(self):
        async def run():
            calls=[];raw=batch(record(1,'text'),record(2),after=0)
            async def read(*args,**options):calls.append(options);return raw
            store=SQLiteSyncStore(self.root/'source.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0);owed=await source.prepare(CHAT,limit=2)
            receiver=self.receiver();wire=self.root/'batch.json';wire.write_text(owed.to_json())
            child=subprocess.run([sys.executable,__file__,'--accept-exit',str(receiver.path),str(wire)],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
            self.assertEqual(child.returncode,51,child.stderr.decode())
            source=SyncEngine(read,SQLiteSyncStore(store.path,create=False));receiver=AlbumReceiver(receiver.path,'one')
            replay=await source.prepare(CHAT,limit=2);self.assertEqual(replay.to_json(),owed.to_json())
            receiver.accept(replay);self.assertEqual(member_groups(self.load(receiver,2)),((1,2),))
            await source.acknowledge(CHAT,replay.batch_id)
            self.assertEqual((await source.status(CHAT)).after_id,2);self.assertEqual(len(calls),1)
        asyncio.run(run())

    def test_offline_demo_uses_actual_storage_and_source_engine(self):
        asyncio.run(demo(self.root))


def child_accept(path, wire):
    raw=MessageBatch.from_json(Path(wire).read_text())
    AlbumReceiver(path,'one').accept(raw)
    os._exit(51)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--accept-exit':
        with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
            child_accept(*sys.argv[2:])
    else:
        unittest.main()
