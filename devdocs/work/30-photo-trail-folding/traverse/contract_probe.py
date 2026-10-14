"""Executable contract sketch, not the full public-value/adapter prebuild.

Uses actual SDK-derived posts, schema2 receiver and daily source engine. The
public serialization/corruption/cleanup/resource matrix must still run later.
"""
import asyncio
from datetime import datetime
import json
from pathlib import Path
import socket
import tempfile
from unittest.mock import patch
from foundation_probe import AlbumReceiver,raw_record,batch,CHAT
from tgdata import SQLiteSyncStore,album_post_ids
from tgdata.sync_engine import SyncEngine


class ScopeRefusal(ValueError):pass


def load_closed(receiver,after,through):
    with receiver._open() as db:
        db.execute('BEGIN');receiver._validate(db)
        count,key_bytes=db.execute('SELECT COUNT(*),COALESCE(SUM(length(CAST(post_id AS BLOB))),0) '
                    'FROM album_members WHERE collection COLLATE BINARY=? AND chat_id=? '
                    'AND message_id>? AND message_id<=?',(receiver.collection,CHAT,after,through)).fetchone()
        if count>receiver.max_members or key_bytes>receiver.max_bytes:raise ScopeRefusal('input bound')
        keys=[r[0] for r in db.execute('SELECT DISTINCT post_id FROM album_members '
                    'WHERE collection COLLATE BINARY=? AND chat_id=? AND message_id>? AND message_id<=?',
                    (receiver.collection,CHAT,after,through))]
        stats={};total_count=total_bytes=0
        for key in keys:
            lo,hi=db.execute('SELECT MIN(message_id),MAX(message_id) FROM album_members '
                            'WHERE collection COLLATE BINARY=? AND post_id COLLATE BINARY=?',
                            (receiver.collection,key)).fetchone()
            if lo<=after or hi>through:raise ScopeRefusal('interval splits a stored post')
            stats[key]=receiver._stats(db,key);total_count+=stats[key][0];total_bytes+=stats[key][1]
            if total_count>receiver.max_members or total_bytes>receiver.max_bytes:raise ScopeRefusal('expanded bound')
        posts=[];used=0
        for key in keys:
            post=receiver._load(db,key,stats=stats[key],max_bytes=receiver.max_bytes-used)
            used+=len(post.to_json().encode());posts.append(post)
        return tuple(posts)


def infer(posts,*,gap=30,span=120,photos=20):
    meta={};events=[];seen=set();ranges={}
    for post in posts:
        value=post.to_dict();key=value['post_id'];members=value['members'];chat=int(value['chat_id'])
        owners={m['sender']['id'] for m in members}
        owner=int(next(iter(owners))) if len(owners)==1 and None not in owners else None
        if owner is not None and owner<=0:owner=None
        dates=[datetime.fromisoformat(m['date'].replace('Z','+00:00')) if m['date'] else None for m in members]
        ordinary=all(m['kind']=='message' for m in members)
        text=any((m['text'] or '').strip() for m in members)
        follower=ordinary and not text and all(m['media'] and m['media']['kind']=='photo' for m in members)
        info=dict(key=key,chat=chat,owner=owner,rows=members,dates=dates,
                  first=int(members[0]['id']),last=int(members[-1]['id']),
                  bad=not ordinary or any(d is None for d in dates),follower=follower,
                  anchor=ordinary and (text or value['grouped_id'] is not None))
        assert key not in meta;meta[key]=info
        if owner is not None:ranges.setdefault((chat,owner),[]).append(info)
        for index,row in enumerate(members):
            ident=int(row['id']);assert (chat,ident) not in seen;seen.add((chat,ident))
            events.append((chat,ident,key,index))
    # Overlapping source-post intervals for one user have ambiguous ordering.
    for values in ranges.values():
        cluster=[];end=-1
        def finish():
            if len(cluster)>1:
                for item in cluster:item['bad']=True
        for item in sorted(values,key=lambda m:m['first']):
            if item['first']>end:
                finish();cluster=[];end=-1
            cluster.append(item);end=max(end,item['last'])
        finish()
    events.sort();last_dates={}
    for chat,ident,key,index in events:
        info=meta[key];owner=info['owner'];date=info['dates'][index]
        if owner is not None and date is not None:
            previous=last_dates.get((chat,owner))
            if previous is not None and date<previous:info['bad']=True
            last_dates[(chat,owner)]=max(previous,date) if previous is not None else date
    groups={key:[key] for key in meta};active={}
    for chat,ident,key,index in events:
        info=meta[key];owner=info['owner'];address=(chat,owner)
        if owner is None:
            for address in [a for a in active if a[0]==chat]:active.pop(address)
            continue
        if info['bad']:
            active.pop(address,None);continue
        if not info['follower'] and index==0:active.pop(address,None)
        if index!=len(info['rows'])-1:continue
        old=active.get(address);attached=False
        if info['follower'] and old is not None:
            ids=set(old['ids']);last=old['last_date'];good=info['first']>old['last_id']
            good=good and old['photos']+len(info['rows'])<=photos
            for row,date in zip(info['rows'],info['dates']):
                delta=(date-last).total_seconds();good=good and 0<=delta<=gap
                good=good and (date-old['origin']).total_seconds()<=span
                good=good and (row['reply_to_id'] is None or int(row['reply_to_id']) in ids)
                ids.add(int(row['id']));last=date
            if good:
                groups[old['root']].append(key);groups.pop(key)
                old.update(ids=ids,last_date=last,last_id=info['last'],photos=old['photos']+len(info['rows']))
                attached=True
            else:active.pop(address,None)
        if not attached and info['anchor']:
            active[address]=dict(root=key,ids={int(r['id']) for r in info['rows']},
                        last_date=info['dates'][-1],last_id=info['last'],origin=info['dates'][-1],photos=0)
    result=[]
    for root,keys in sorted(groups.items(),key=lambda pair:(meta[pair[0]]['chat'],meta[pair[0]]['first'])):
        result.append(tuple(sorted(int(r['id']) for key in keys for r in meta[key]['rows'])))
    return tuple(result)


def main():
    results={}
    with tempfile.TemporaryDirectory(prefix='tgdata30-contract-') as tmp, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        root=Path(tmp)
        def receiver(name,records,**options):
            r=AlbumReceiver(root/(name+'.db'),'one',create=True,**options);r.accept(batch(*records));return r
        records=[raw_record(1,text='anchor'),raw_record(2,seconds=1,group=7),
                 raw_record(3,seconds=2,text='new anchor'),raw_record(4,seconds=3,group=7)]
        r=receiver('scope',records)
        try:load_closed(r,0,2)
        except ScopeRefusal:pass
        else:raise AssertionError('split scope accepted')
        assert infer(load_closed(r,0,4))==((1,),(2,4),(3,))
        results['closed_scope']='split refused; widened scope retains known text and overlapping posts stay separate'
        r=receiver('late',[raw_record(1,text='anchor'),raw_record(2,seconds=1,group=7),raw_record(3,seconds=2,group=7)])
        old=load_closed(r,0,3);before=[p.to_json() for p in old]
        assert infer(old)==((1,2,3),)
        r.accept(batch(raw_record(4,seconds=3,text='new caption',group=7)))
        assert infer(load_closed(r,0,4))==((1,),(2,3,4))
        assert [p.to_json() for p in old]==before
        results['late_caption']='prior attachment withdraws; all originals survive unchanged'
        r=receiver('unknown',[raw_record(1,sender=-7,group=9),raw_record(2,seconds=1,text='anchor'),
                     raw_record(3,seconds=2),raw_record(5,seconds=4,sender=-7,group=9),raw_record(6,seconds=5)])
        assert infer(load_closed(r,0,6))==((1,5),(2,3),(6,))
        results['late_unknown_barrier']='unknown member5 breaks the trail before photo6'
        r=receiver('interleave',[raw_record(1,text='A',group=7),raw_record(2,seconds=1,text='B',sender=99),
                     raw_record(3,seconds=2,group=7),raw_record(4,seconds=3,sender=99),raw_record(5,seconds=4)])
        posts=load_closed(r,0,5);expected=((1,3,5),(2,4))
        assert infer(posts)==infer(tuple(reversed(posts)))==expected
        results['known_user_interleaving']='two independent trails; post-list permutation identical'
        r=receiver('bounds',[raw_record(1,text='anchor'),raw_record(2,seconds=2),raw_record(3,seconds=4)])
        posts=load_closed(r,0,3)
        assert infer(posts,photos=1)==infer(posts,span=3)==((1,2),(3,))
        results['chain_limits']='whole followers remain separate on count/span limit'
        foreign=raw_record(2,seconds=1);foreign['reply_to_id']='999'
        r=receiver('reply',[raw_record(1,text='anchor'),foreign,raw_record(3,seconds=2)])
        assert infer(load_closed(r,0,3))==((1,),(2,),(3,))
        results['reply_barrier']='unknown reply target prevents attachment and clears old anchor'
        r=receiver('clock',[raw_record(1,seconds=10,text='one'),raw_record(2,seconds=2,text='two'),raw_record(3,seconds=3)])
        assert infer(load_closed(r,0,3))==((1,),(2,),(3,))
        results['backward_chronology']='regressed text cannot become a fresh anchor'
        r=AlbumReceiver(root/'large.db','one',create=True,max_members=3)
        first=batch(raw_record(1,text='one'),raw_record(2,seconds=1,text='two'))
        r.accept(first);r.accept(batch(raw_record(3,seconds=2,text='three'),raw_record(4,seconds=3,text='four')))
        with patch.object(r,'_load',side_effect=AssertionError('payload read before refusal')):
            try:load_closed(r,0,4)
            except ScopeRefusal:pass
            else:raise AssertionError('view exceeded its cap')
            assert r.accept(first) is None
        results['view_refusal_replay']='view cap refuses before payload; original input confirms unchanged'
        async def daily():
            calls=[]
            async def read(chat,**options):
                calls.append(options);i=options['after_id']+1
                return batch(raw_record(i,seconds=i,text='anchor' if i==1 else ''))
            store=SQLiteSyncStore(root/'daily.db');source=SyncEngine(read,store)
            await source.initialize(CHAT,after_id=0)
            dest=AlbumReceiver(root/'daily-dest.db','one',create=True)
            one=await source.prepare(CHAT,limit=1);dest.accept(one)
            source=SyncEngine(read,SQLiteSyncStore(store.path,create=False));dest=AlbumReceiver(dest.path,'one')
            replay=await source.prepare(CHAT,limit=1);assert replay.to_json()==one.to_json()
            dest.accept(replay);await source.acknowledge(CHAT,replay.batch_id)
            two=await source.prepare(CHAT,limit=1);dest.accept(two)
            assert infer(load_closed(dest,0,2))==((1,2),)
            await source.acknowledge(CHAT,two.batch_id)
            assert len(calls)==2 and (await source.status(CHAT)).after_id==2
        asyncio.run(daily());results['daily_restart']='two source reads; lost ack replays; original cursor settles through2'
    output=dict(result='PASS',histories=results,
                limits='contract sketch only; public value/schema/options and full adapter corruption/cleanup matrix remain for complete prebuild')
    Path(__file__).with_suffix('.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))

if __name__=='__main__':main()
