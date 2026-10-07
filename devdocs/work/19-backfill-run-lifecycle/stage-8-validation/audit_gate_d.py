"""Read-only independent audit of Gate D SQL/files/traces, beyond driver verdicts."""
import hashlib
import json
from pathlib import Path
import sqlite3

import gate_d_support as g
from tgdata import MessageBatch
from tgdata.history_window import _decode_date


def sql(path,query):
    with sqlite3.connect(Path(path).as_uri()+'?mode=ro',uri=True) as db:return db.execute(query).fetchall()


def state(root,name):
    rows=sql(root/(name+'.sqlite3'),'SELECT data FROM tgdata_sync_state')
    assert len(rows)==1;return json.loads(rows[0][0])


def ids_dates(batch):return [dict(id=r['id'],date=r['date']) for r in batch['messages']]


def receiver(root,name):
    directory=root/(name+'-receiver');path=directory/'receiver.sqlite3'
    receipts=sql(path,'SELECT receipt,batch FROM example_receipts ORDER BY rowid')
    index=sql(path,'SELECT chat_id,message_id,record FROM example_messages')
    expected={};parsed=[]
    for key,encoded in receipts:
        key=json.loads(key);batch=json.loads(encoded);validated=MessageBatch.from_json(encoded)
        assert validated.to_json()==encoded
        if key['kind']=='backfill':
            assert key['delivery']['batch_id']==batch['batch_id']
            assert key['delivery']['run']['chat_id']==batch['chat_id']
            assert key['delivery']['destination_id']==g.DESTINATION
        else:
            assert key['kind']=='daily' and key['batch_id']==batch['batch_id'] and key['chat_id']==batch['chat_id']
            assert key['namespace']=='gate-d-daily'
        for row in batch['messages']:
            expected.setdefault((batch['chat_id'],row['id']),row)
            blob=row['media']['blob'] if row['media'] else None
            if blob:
                target=directory/'media'/blob['path']
                assert target.stat().st_size==blob['size'] and g.digest(target)==blob['sha256']
        parsed.append((key,batch))
    assert {(chat,mid):json.loads(record) for chat,mid,record in index}==expected
    return parsed,dict(receipts=len(receipts),indexed_messages=len(index))


def operation(report,label):return next(r for r in report['operations'] if r['operation']==label)


def main(root=g.ROOT):
    driver=g.read(root/'driver-result.json');assert driver['result']=='EXECUTION_COMPLETE_AUDIT_PENDING'
    owned=[json.loads(x) for x in (root/'owned-workers.jsonl').read_text().splitlines()]
    assert owned==driver['workers'] and len(owned)==14
    prior=None;source_prior=None
    reports={};allocation=[json.loads(x) for x in (root/'allocations.jsonl').read_text().splitlines()]
    assert len({r['name'] for r in allocation})==len(allocation) and sum(r['slots'] for r in allocation)==1330
    byname={r['name']:r['slots'] for r in allocation}
    for item in owned:
        name=item['worker'];report=g.read(root/(name+'-result.json'));reports[name]=report
        assert item['code']==item['expected'] and item['pid']==report['pid']
        assert item['entry']['monotonic_ns']<=report['started']['monotonic_ns']<=item['end']['monotonic_ns']
        if prior:assert item['entry']['monotonic_ns']>=prior['end']['monotonic_ns']
        prior=item
        if name in byname:
            if source_prior:assert (item['entry']['monotonic_ns']-source_prior['end']['monotonic_ns'])/1e9>=5
            source_prior=item
            started=g.read(root/(name+'.started.json'))
            assert started['pid']==item['pid'] and started['allocation']['slots']==byname[name]
        else:
            assert not (root/(name+'.sends.jsonl')).exists()
            assert report.get('local_health_preserved') is True
    reports['prebuild']=g.read(root/'prebuild-result.json')
    totals=dict(allocated=sum(byname.values()),sent=0,attempted=0,returned=0,history_requests=0,requested_media_bytes=0)
    sources=[];media_migrations=[]
    for name,limit in byname.items():
        report=reports[name];rpc=report['rpc'];blocked=report.get('blocked',[])
        histories=[r for r in rpc if r['kind']=='GetHistoryRequest']
        sent=sum(r['limit'] for r in histories);attempted=sent+sum(r['limit'] for r in blocked)
        assert sent==report['sent_requested_slots'] and attempted==report['attempted_slots']<=limit
        assert all(r['operation']!='outside-public-call' for r in rpc)
        assert all(r['outcome']=='answered' for r in histories)
        # The plan explicitly permits file/DC transport. Pinned SDK downloads.py
        # follows FileMigrateError to the file's DC; it is not a history failure.
        for i,r in enumerate(rpc):
            if r['outcome']=='answered':continue
            assert r['kind']=='GetFileRequest' and r['outcome']=='FileMigrateError'
            assert any(later['kind']=='GetFileRequest' and later['outcome']=='answered'
                and later['operation']==r['operation'] for later in rpc[i+1:])
            media_migrations.append(dict(worker=name,operation=r['operation'],outcome=r['outcome']))
        assert all(not r['operation'].startswith(('local-','photo-local-','prefix-local-')) for r in rpc)
        durable=[json.loads(x) for x in (root/(name+'.sends.jsonl')).read_text().splitlines()]
        assert len(durable)==len(rpc)+len(blocked)
        assert report['budget_before']['limit']==report['budget_after']['limit']==5000
        returned=sum(r['returned_slots'] for r in histories)
        assert report['budget_after']['used']-report['budget_before']['used']==returned+sum(r['limit'] for r in blocked)
        totals['sent']+=sent;totals['attempted']+=attempted;totals['history_requests']+=len(histories)
        totals['returned']+=returned
        totals['requested_media_bytes']+=report['requested_media_bytes']
        assert report['requested_media_bytes']<=4*1024*1024
        sources.append(dict(worker=name,allocated=limit,sent=sent,attempted=attempted,returned=returned,
            history_requests=len(histories),blocked_requests=len(blocked),requested_media_bytes=report['requested_media_bytes']))

    oracle=g.read(root/'large-oracle.json');assert len(oracle['messages'])==250
    assert len({r['id'] for r in oracle['messages']})==250 and oracle['search_count']==350
    assert all(_decode_date(oracle['window']['start_date'])<=_decode_date(r['date'])<_decode_date(oracle['window']['end_date']) for r in oracle['messages'])
    assert _decode_date(oracle['captured']['utc'])<_decode_date(reports['main-seed']['started']['utc'])
    receipts,main_receiver=receiver(root,'main')
    historical=sorted([batch for key,batch in receipts if key['kind']=='backfill'],key=lambda b:int(b['after_id']))
    daily=[batch for key,batch in receipts if key['kind']=='daily']
    assert [len(b['messages']) for b in historical]==[120,120,10]
    assert sum([ids_dates(b) for b in historical],[])==oracle['messages']
    assert len(daily)==1 and ids_dates(daily[0])==oracle['daily_expected']
    for name,batch in zip(('first','second','final'),historical):
        assert batch==g.read(root/('main-'+name+'-turn.json'))['batch']
    history=state(root,'main')['current'];daily_state=state(root,'daily')
    assert history['request']['after_id']=='0' and history['request']['origin']=='fresh'
    assert history['after_id']==oracle['messages'][-1]['id'] and history['terminal_outcome']=='completed'
    assert history['attempt'] is None and history['pending'] is None and history['exhaustion']
    assert daily_state['initial_after_id']==oracle['daily_after'] and daily_state['after_id']==oracle['daily_expected'][-1]['id']
    assert daily_state['pending'] is None and reports['main-continue']['history_unchanged_by_daily'] and reports['main-continue']['daily_unchanged_by_history']
    assert main_receiver==dict(receipts=4,indexed_messages=252)
    first=g.read(root/'main-first-turn.json')['status'];second=g.read(root/'main-second-turn.json')['status']
    main_report=reports['main-continue'];spacings={}
    for label,prior_status in [('history-second-prepare',first),('history-final-prepare',second)]:
        entry=operation(main_report,label)['entry'];deadline=_decode_date(prior_status['pacing_not_before'])
        assert _decode_date(entry['utc'])>=deadline
        spacings[label]=(_decode_date(entry['utc'])-_decode_date(prior_status['pacing_ended_at'])).total_seconds()
        assert spacings[label]>=12
    daily_call=operation(main_report,'daily-source-turn')
    assert _decode_date(daily_call['entry']['utc'])<_decode_date(second['pacing_not_before'])
    assert _decode_date(daily_call['end']['utc'])<_decode_date(second['pacing_not_before'])
    assert reports['main-local']['early_wait']>0
    assert reports['main-local']['final_status']['pacing_not_before']==first['pacing_not_before']
    assert reports['main-seed']['receipts'][0]['end']['monotonic_ns']<next(x for x in owned if x['worker']=='main-seed')['end']['monotonic_ns']
    assert operation(reports['main-local'],'local-ack')['entry']['monotonic_ns']>next(x for x in owned if x['worker']=='main-seed')['end']['monotonic_ns']

    control=state(root,'controls');assert control['current']['ref']['generation']=='4'
    assert control['previous']['ref']['generation']=='3'
    for row in (control['current'],control['previous']):
        assert row['terminal_outcome']=='cancelled' and row['abandoned'] and row['after_id']=='13'
        assert row['pending'] is None and row['attempt'] is None
    turns=[g.read(root/(name+'-turn.json')) for name in ('controls-first','controls-2','controls-3','controls-4')]
    assert all(t['batch']==turns[0]['batch'] for t in turns)
    assert len({g.canonical(t['delivery']['run']) for t in turns})==4
    control_receipts,control_receiver=receiver(root,'controls');assert control_receiver==dict(receipts=2,indexed_messages=1)
    assert {k['delivery']['run']['generation'] for k,b in control_receipts}=={'1','2'}

    prefix=state(root,'prefix')['current'];prefix_turn=g.read(root/'prefix-turn.json')
    prefix_receipts,prefix_receiver=receiver(root,'prefix')
    assert ids_dates(prefix_turn['batch'])==oracle['messages'][:100] and prefix_receipts[0][1]==prefix_turn['batch']
    assert prefix['after_id']==oracle['messages'][99]['id'] and prefix['terminal_outcome'] is None and prefix['exhaustion'] is None
    assert prefix['last_failure']['error_type']=='ProbeStop' and prefix_turn['batch']['stop_reason']=='interrupted'
    assert reports['prefix']['budget_after']['reserved']-reports['prefix']['budget_before']['reserved']==20

    unknown=state(root,'unknown')['current'];assert unknown['terminal_outcome']=='completed' and unknown['after_id']=='14'
    unknown_receipts,unknown_receiver=receiver(root,'unknown');assert unknown_receiver==dict(receipts=1,indexed_messages=1)
    assert unknown_receipts[0][1]==g.read(root/'unknown-raw-result.json')==g.read(root/'unknown-final-turn.json')['batch']
    recovery=reports['recovery-exit']['committed_pacing'];retry=reports['recovery-retry']['final_status']
    assert recovery['not_before']==retry['pacing_not_before'] and reports['recovery-retry']['early_wait']>0
    recovered_call=operation(reports['unknown-follow'],'recovered-real-source')
    assert _decode_date(recovered_call['entry']['utc'])>=_decode_date(recovery['not_before'])
    recovery_entry=operation(reports['recovery-exit'],'recover-actual-commit-before-reply')['entry']['utc']
    spacings['recovery-to-next-source']=(_decode_date(recovered_call['entry']['utc'])-_decode_date(recovery_entry)).total_seconds()
    assert spacings['recovery-to-next-source']>=12

    photo=state(root,'photo')['current'];photo_turn=g.read(root/'photo-turn.json');photo_oracle=g.read(root/'small-oracle.json')['photo']
    photo_receipts,photo_receiver=receiver(root,'photo');assert photo_receiver==dict(receipts=1,indexed_messages=1)
    assert photo_receipts[0][1]==photo_turn['batch']
    blob=photo_turn['batch']['messages'][0]['media']['blob']
    assert blob['size']==photo_oracle['size'] and blob['sha256']==photo_oracle['sha256']
    assert not (root/'photo-media'/blob['path']).exists()
    assert g.digest(root/'photo-corrupt-copy'/blob['path'])!=blob['sha256']
    assert photo_turn['batch']['stop_reason']=='limit' and not photo_turn['status']['source_exhausted']
    assert reports['photo-retry']['final_status']['terminal_outcome'] is None
    failed=g.read(root/'photo-failed-status.json');assert not failed['source_exhausted'] and failed['terminal_outcome'] is None
    assert photo['terminal_outcome']=='completed' and photo['exhaustion'] and photo['pending'] is None
    follow=operation(reports['photo-follow'],'photo-real-empty-end')
    assert _decode_date(follow['entry']['utc'])>=_decode_date(failed['pacing_not_before'])
    spacings['photo-failure-to-real-end']=(_decode_date(follow['entry']['utc'])-_decode_date(failed['pacing_ended_at'])).total_seconds()
    assert spacings['photo-failure-to-real-end']>=12
    assert reports['photo-follow']['budget_after']['reserved']-reports['photo-follow']['budget_before']['reserved']==1
    preserved={
        'empty_uncommitted.sqlite3':'4d36051567f5329eb1c7379b425d39f884efe404f5c7d0b2d9037d7cccc28f14',
        'unknown_source.sqlite3':'86b7f633d006b002c4dcdb9a8cdf433a97f9c8710f2014bb0f127a192c0ca228'}
    oldroot=Path('/private/tmp/tgdata19-gate-b-live-20261007')
    assert all(g.digest(oldroot/name)==sha for name,sha in preserved.items())
    prebuild_receipts,prebuild_receiver=receiver(root,'prebuild')
    assert prebuild_receipts[0][1]==g.read(root/'prebuild-pending.json')['batch']
    result=dict(result='PASS',product_revision=driver['revision'],observed=g.stamp(),workers=len(owned),
        totals=totals,sources=sources,media_dc_migrations=media_migrations,main_batch_sizes=[120,120,10],expected_history=250,expected_daily=2,
        receiver_counts=dict(main=main_receiver,controls=control_receiver,prefix=prefix_receiver,unknown=unknown_receiver,
            photo=photo_receiver,prebuild=prebuild_receiver),measured_seconds=spacings,
        ledger_before=reports['prebuild']['budget_before'],ledger_after=reports['photo-follow']['budget_after'],
        preserved_original_gate_b_hashes=preserved,
        checks=['exact independent history/daily sets and immutable saved window','complete scoped receiver snapshots and first-observation index',
            'receiver blob digest/size and absent/corrupt disposable source copies','all owned exits confirmed before successor local/source workers',
            'same-host monotonic diagnostics qualified; no overlapping workers','durable allocations and attempted/sent separation',
            'guard RPC labels exclude local actions; local workers have no source traces','two real 12-second history waits with daily turn inside second wait',
            'same-hash successor, cancellation/retirement and retained scoped receipts','100-record failed prefix accepted without false completion',
            'unknown raw result recovered without cursor acceptance; exact recovery retry/deadline','full photo accepted before actual empty end; failure did not invent end',
            'shared 5000 policy unchanged; 21 additional uncertain claims retained','earlier unresolved Gate B originals byte-identical'])
    print(json.dumps(result,indent=2,sort_keys=True));return result


if __name__=='__main__':main()
