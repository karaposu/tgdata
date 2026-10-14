"""Offline fixed-window selection and durable continuation on Telethon 1.45.0.

Run: python -m tgdata.smoke_tests.test_23_fixed_windows
Synthetic transport supplies replies; actual SDK, budget and SQLite paths run.
"""

import asyncio
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import telethon
from telethon import errors
from telethon.tl import functions
from tgdata import (
    TgData, MessageBatch, SQLiteSyncStore, BatchFormatError, ReadBudgetExceeded,
    SyncConfigurationError, SyncConflictError, SyncStorageError,
)
from tgdata import health
import tgdata.sync_engine as sync_engine
from tgdata.smoke_tests import test_22_daily_continuation as d

b, f, CHAT = d.b, d.f, d.CHAT
START = b.NOW
END = START + timedelta(seconds=10)
DATES = dict(start_date=START, end_date=END)


def message(mid, seconds=0, *, date=None, media=False):
    value = b.document(mid) if media else f.message(mid)
    value.date = START + timedelta(seconds=seconds) if date is None else date
    return value


def pages(sender, *groups):
    sender.script = [f.response(list(reversed(group))) for group in groups]


def instance(progress=None, budget=None, events=None):
    tg, client, sender = d.instance(progress, budget, events)
    requests = []
    original = sender.send

    def send(request, ordered=False):
        raw = f.unwrap(request)
        if isinstance(raw, functions.messages.GetHistoryRequest):
            requests.append((raw.offset_id, raw.offset_date, raw.add_offset, raw.limit))
        return original(request, ordered=ordered)

    sender.send = send
    return tg, client, sender, requests


async def enrolled(progress=None, budget=None, events=None, mode='references'):
    progress = progress or d.store()
    tg, client, sender, requests = instance(progress, budget, events)
    await tg.initialize_sync(CHAT, after_id=0, media_mode=mode, **DATES)
    return progress, tg, client, sender, requests


async def test_invalid_dates_before_connection_or_files():
    tg = TgData('/missing-fixed-window-test-config.ini')
    naive = START.replace(tzinfo=None)
    cases = [dict(start_date=START), dict(end_date=END),
             dict(start_date=naive, end_date=END),
             dict(start_date=START, end_date=naive),
             dict(start_date=END, end_date=START),
             dict(start_date=START, end_date=START),
             dict(start_date='2023-11-14', end_date=END),
             dict(start_date=True, end_date=END),
             dict(start_date=datetime(1969, 1, 1, tzinfo=timezone.utc), end_date=END),
             dict(start_date=START, end_date=datetime(2039, 1, 1, tzinfo=timezone.utc))]
    root = f.TMP / 'must-not-be-created'
    for kwargs in cases:
        error = await f.expect(BatchFormatError, tg.get_message_batch(
            CHAT, download_media_to=root, **kwargs))
        assert error.partial_result is None and not root.exists()
    assert tg.connection_engine._primary_client is None


async def test_half_open_window_and_timezone_normalization():
    tg, _, sender, requests = instance()
    pages(sender, [message(101, -1), message(102), message(103)], [message(104, 10)])
    local_zone = timezone(timedelta(hours=3))
    batch = await tg.get_message_batch(
        CHAT, limit=3, start_date=START.astimezone(local_zone), end_date=END.astimezone(local_zone))
    assert [m['id'] for m in batch.messages] == ['102', '103']
    assert batch.after_id == 0 and batch.next_after_id == 103 and batch.stop_reason == 'end'
    assert requests == [(0, START-timedelta(seconds=1), -3, 3), (104, None, -1, 1)]


async def test_timestamp_ties_across_sdk_pages():
    tg, _, sender, requests = instance()
    pages(sender, [message(i) for i in range(101, 201)],
          [message(i) for i in range(201, 301)], [message(i) for i in range(301, 306)])
    batch = await tg.get_message_batch(CHAT, limit=205, **DATES)
    assert [int(m['id']) for m in batch.messages] == list(range(101, 306))
    assert [r[3] for r in requests] == [100, 100, 5] and batch.stop_reason == 'limit'
    assert [r[0] for r in requests] == [0, 201, 301]


async def test_full_excluded_pages_and_fractional_start():
    tg, _, sender, requests = instance()
    pages(sender, [message(101), message(102)], [message(103), message(104, 1)], [message(105, 2)])
    batch = await tg.get_message_batch(CHAT, limit=2,
                                       start_date=START+timedelta(microseconds=500000), end_date=END)
    assert [m['id'] for m in batch.messages] == ['104', '105']
    assert batch.stop_reason == 'limit' and batch.after_id == 0
    assert [r[3] for r in requests] == [2, 2, 1]
    assert requests[0][1] == START-timedelta(seconds=1)
    assert [r[0] for r in requests[1:]] == [103, 105]


async def test_empty_end_exact_limit_and_max_cursor():
    progress, tg, _, sender, requests = await enrolled()
    pages(sender, [message(101, 10)])
    assert await tg.sync_group(CHAT, limit=3) is None
    assert (await tg.get_sync_status(CHAT)).pending_batch_id is None
    assert (await tg.get_sync_status(CHAT)).after_id == 0
    pages(sender, [])
    assert await tg.sync_group(CHAT, limit=3) is None
    pages(sender, [message(101)])
    batch = await tg.sync_group(CHAT, limit=1)
    assert batch.stop_reason == 'limit'
    await tg.acknowledge_sync(CHAT, batch.batch_id)
    pages(sender, [])
    assert await tg.sync_group(CHAT) is None
    count = len(requests)
    batch = await tg.get_message_batch(CHAT, after_id=(1 << 31)-1, **DATES)
    assert not batch.messages and batch.stop_reason == 'end' and len(requests) == count


async def test_nonzero_cursor_intersects_window_and_gaps():
    tg, _, sender, requests = instance()
    pages(sender, [message(102, -1), message(107)], [message(140, 1)])
    batch = await tg.get_message_batch(CHAT, after_id=100, limit=2, **DATES)
    assert batch.after_id == 100 and [m['id'] for m in batch.messages] == ['107', '140']
    assert requests == [(101, None, -2, 2), (108, None, -1, 1)]


async def test_wire_date_extremes():
    tg, _, sender, requests = instance()
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    last = epoch + timedelta(seconds=(1 << 31)-1)
    for start, end, offset in ((epoch, epoch+timedelta(seconds=2), None),
                                (last-timedelta(seconds=1), last, last-timedelta(seconds=2))):
        pages(sender, [message(101, date=start), message(102, date=end)])
        batch = await tg.get_message_batch(CHAT, limit=2, start_date=start, end_date=end)
        assert [m['id'] for m in batch.messages] == ['101'] and batch.stop_reason == 'end'
        assert requests[-1][1] == offset
    assert requests[0][0] == 1  # SDK's oldest-history offset when the date is unset


async def test_relative_enrollment_freezes_once():
    progress = d.store()
    tg = d.offline(progress)
    end = START + timedelta(days=30, microseconds=123456)
    with patch.object(sync_engine, '_utc_now', return_value=end) as clock:
        first = await tg.initialize_sync(CHAT, after_id=0, last_days=30)
    assert clock.call_count == 1
    assert first.start_date == end-timedelta(days=30) and first.end_date == end and first.last_days == 30
    raw = await progress.load(CHAT)
    with patch.object(sync_engine, '_utc_now', side_effect=AssertionError('must reuse saved dates')):
        for _ in range(2):
            resumed = d.offline(SQLiteSyncStore(progress.path))
            assert await resumed.initialize_sync(CHAT, after_id=0, last_days=30) == first
            assert await resumed.get_sync_status(CHAT) == first
        for kwargs in (dict(after_id=0, last_days=31), dict(after_id=1, last_days=30),
                       dict(after_id=0, last_days=30, media_mode='download'),
                       dict(after_id=0, start_date=first.start_date, end_date=first.end_date)):
            await f.expect(SyncConflictError, resumed.initialize_sync(CHAT, **kwargs))
    assert await progress.load(CHAT) == raw
    assert first.to_dict()['end_date'].endswith('.123456Z')
    f.rejected(FrozenInstanceError, lambda: setattr(first, 'end_date', END))
    reader, _, sender, _ = instance(progress)
    pages(sender, [message(101, 1)])
    with patch.object(sync_engine, '_utc_now', side_effect=AssertionError('must retain dates after ack')):
        batch = await reader.sync_group(CHAT, limit=1)
        await reader.acknowledge_sync(CHAT, batch.batch_id)
        advanced = await reader.initialize_sync(CHAT, after_id=0, last_days=30)
    assert advanced.after_id == 101 and advanced.start_date == first.start_date and advanced.end_date == end


async def test_initialization_conflicts_and_bad_durations():
    progress, tg, _, sender, _ = await enrolled()
    raw = await progress.load(CHAT)
    for kwargs in ({}, dict(last_days=30), dict(start_date=START+timedelta(seconds=1), end_date=END),
                   dict(start_date=START, end_date=END+timedelta(seconds=1))):
        await f.expect(SyncConflictError, tg.initialize_sync(CHAT, after_id=0, **kwargs))
    await f.expect(SyncConflictError, tg.initialize_sync(CHAT, after_id=1, **DATES))
    await f.expect(SyncConflictError, tg.initialize_sync(CHAT, after_id=0, media_mode='download', **DATES))
    for kwargs in (dict(start_date=START), dict(end_date=END),
                   dict(start_date=START.replace(tzinfo=None), end_date=END),
                   dict(last_days=30, **DATES)):
        await f.expect(SyncConfigurationError, tg.initialize_sync(CHAT, after_id=0, **kwargs))
    assert await progress.load(CHAT) == raw and not sender.calls
    empty = d.store()
    for value in (True, False, 0, -1, 1.5, '30', (1 << 31), (1 << 31)-1, 100000):
        await f.expect(SyncConfigurationError, d.offline(empty).initialize_sync(CHAT, after_id=0, last_days=value))
        assert await empty.load(CHAT) is None
    zone = timezone(timedelta(hours=-7))
    same = await tg.initialize_sync(CHAT, after_id=0,
                                     start_date=START.astimezone(zone), end_date=END.astimezone(zone))
    assert same.start_date == START and await progress.load(CHAT) == raw


async def test_restart_replay_ack_and_timestamp_ties():
    progress, tg, _, sender, requests = await enrolled()
    pages(sender, [message(101), message(102)])
    batch = await tg.sync_group(CHAT, limit=2)
    before = len(requests)
    local = d.offline(SQLiteSyncStore(progress.path))
    with patch.object(sync_engine, '_utc_now', side_effect=AssertionError('unexpected clock')):
        replay = await local.sync_group(CHAT, limit=1)
        assert replay.to_json() == batch.to_json() and len(requests) == before
        await f.expect(SyncConflictError, local.acknowledge_sync(CHAT, 'a'*64))
        accepted = await local.acknowledge_sync(CHAT, replay.batch_id)
        assert accepted.after_id == 102 and accepted.start_date == START and accepted.end_date == END
        assert await local.acknowledge_sync(CHAT, replay.batch_id) == accepted
    pages(sender, [message(107), message(140)])
    following = await tg.sync_group(CHAT, limit=2)
    assert [m['id'] for m in following.messages] == ['107', '140']
    assert requests[-1] == (103, None, -2, 2)
    assert (await tg.acknowledge_sync(CHAT, batch.batch_id)).pending_batch_id == following.batch_id
    assert (await tg.get_sync_status(CHAT)).after_id == 102


async def test_media_selection_and_pending_replay():
    progress, tg, _, sender, _ = await enrolled(mode='download')
    sender.files[b.ASSET_ID] = b.PAYLOAD
    pages(sender, [message(101, -1, media=True), message(102, media=True), message(103, 10, media=True)])
    root = b.directory()
    batch = await tg.sync_group(CHAT, limit=3, download_media_to=root)
    assert [m['id'] for m in batch.messages] == ['102'] and len(sender.file_calls) == 1
    local = d.offline(SQLiteSyncStore(progress.path))
    assert (await local.sync_group(CHAT, download_media_to=root)).to_json() == batch.to_json()
    assert len(sender.file_calls) == 1
    await local.acknowledge_sync(CHAT, batch.batch_id)
    assert (await local.get_sync_status(CHAT)).end_date == END


async def test_budget_counts_excluded_slots_and_preserves_prefix():
    budget, _ = f.ledger(2)
    progress, tg, _, sender, requests = await enrolled(budget=budget)
    pages(sender, [message(101, -1), message(102)])
    error = await f.expect(ReadBudgetExceeded, tg.sync_group(CHAT, limit=3))
    assert [m['id'] for m in error.partial_result.messages] == ['102']
    assert error.partial_result.stop_reason == 'interrupted'
    assert budget.status(f.ACCOUNT).used == 2 and requests[0][3] == 2
    local = d.offline(SQLiteSyncStore(progress.path))
    assert (await local.sync_group(CHAT)).to_json() == error.partial_result.to_json()
    assert (await local.get_sync_status(CHAT)).after_id == 0
    await local.acknowledge_sync(CHAT, error.partial_result.batch_id)
    budget.configure(f.ACCOUNT, 6)
    pages(sender, [message(103), message(104, 10)])
    following = await tg.sync_group(CHAT, limit=3)
    assert [m['id'] for m in following.messages] == ['103'] and following.stop_reason == 'end'
    assert budget.status(f.ACCOUNT).used == 4


async def test_budget_before_any_included_record_is_not_end():
    budget, _ = f.ledger(2)
    _, tg, _, sender, _ = await enrolled(budget=budget)
    pages(sender, [message(101, -1), message(102, -1)])
    error = await f.expect(ReadBudgetExceeded, tg.sync_group(CHAT, limit=3))
    assert not error.partial_result.messages and error.partial_result.next_after_id == 0
    state = await tg.get_sync_status(CHAT)
    assert state.after_id == 0 and state.pending_batch_id is None and state.start_date == START


async def test_read_failure_and_failed_prefix_persistence():
    for save_fails in (False, True):
        actual = d.store()
        fault = d.FaultStore(actual)
        _, tg, _, sender, _ = await enrolled(progress=fault)
        original = ConnectionError('synthetic read failure')
        sender.script = [f.response([message(i) for i in range(200, 100, -1)]), original]
        if save_fails:
            fault.write_error = OSError('synthetic storage failure')
        caught = await f.expect(SyncStorageError if save_fails else ConnectionError, tg.sync_group(CHAT, limit=101))
        state = await d.offline(actual).get_sync_status(CHAT)
        assert state.after_id == 0 and state.start_date == START
        assert original.partial_result.next_after_id == 200
        if save_fails:
            assert caught.read_error is original and state.pending_batch_id is None
        else:
            assert caught is original and state.pending_batch_id == original.partial_result.batch_id


async def test_invalid_message_date_and_local_health():
    events = []
    _, tg, _, sender, _ = await enrolled(events=events)
    bad = message(102)
    bad.date = None
    pages(sender, [message(101), bad])
    try:
        raise errors.ChannelPrivateError(request=None)
    except errors.ChannelPrivateError:
        caught = await f.expect(BatchFormatError, tg.sync_group(CHAT, limit=2))
    assert caught.partial_result.next_after_id == 101
    assert (await tg.get_sync_status(CHAT)).pending_batch_id == caught.partial_result.batch_id
    assert not events and health.classify(caught) is None


async def test_v1_state_and_default_reader_are_unchanged():
    progress = d.store()
    tg, _, sender, _ = instance(progress)
    status = await tg.initialize_sync(CHAT, after_id=100)
    expected = json.dumps(dict(version=1, chat_id=str(CHAT), initial_after_id='100', after_id='100',
                               media_mode='references', pending=None, last_acked_batch_id=None),
                          ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    assert await progress.load(CHAT) == expected
    assert status.start_date is None and status.end_date is None and status.last_days is None
    assert set(status.to_dict()) == {'chat_id', 'initial_after_id', 'after_id', 'media_mode',
                                    'pending_batch_id', 'pending_message_count',
                                    'pending_next_after_id', 'last_acked_batch_id'}
    local = d.offline(SQLiteSyncStore(progress.path))
    assert await local.initialize_sync(CHAT, after_id=100) == status
    assert await progress.load(CHAT) == expected
    batch = await tg.sync_group(CHAT, limit=1)
    assert batch.next_after_id == 101 and 'window' not in batch.to_dict()
    await local.acknowledge_sync(CHAT, batch.batch_id)
    assert json.loads(await progress.load(CHAT))['version'] == 1
    await f.expect(SyncConflictError, local.initialize_sync(CHAT, after_id=100, **DATES))


async def test_corrupt_window_state_and_pending_refused():
    actual, tg, _, sender, _ = await enrolled()
    pages(sender, [message(101)])
    await tg.sync_group(CHAT, limit=1)
    original = await actual.load(CHAT)
    mutations = [lambda x: x.update(version=1), lambda x: x.pop('window'),
                 lambda x: x.update(window=None), lambda x: x['window'].update(extra=1),
                 lambda x: x['window'].pop('last_days'),
                 lambda x: x['window'].update(start_date=x['window']['end_date']),
                 lambda x: x['window'].update(start_date='2023-11-14T22:13:20Z'),
                 lambda x: x['window'].update(last_days=True),
                 lambda x: x['window'].update(last_days=1),
                 lambda x: x['window'].update(last_days=2147483647)]
    raws = []
    for mutate in mutations:
        value = json.loads(original)
        mutate(value)
        raws.append(json.dumps(value))
    for date in (None, '2023-11-14T22:13:19.000000Z', '2023-11-14T22:13:30.000000Z'):
        value = json.loads(original)
        value['pending']['messages'][0]['date'] = date
        value['pending'] = json.loads(b.signed(value['pending']))
        raws.append(json.dumps(value))
    raws.append(original.replace('"last_days":null', '"last_days":null,"last_days":null'))
    local = d.offline(actual)
    current = original
    for raw in raws:
        assert await actual.compare_and_swap(CHAT, current, raw)
        await f.expect(SyncStorageError, local.get_sync_status(CHAT))
        await f.expect(SyncStorageError, local.sync_group(CHAT))
        assert await actual.load(CHAT) == raw
        current = raw
    assert local.connection_engine._primary_client is None


async def test_reader_output_must_match_window():
    for date in (None, '2023-11-14T22:13:19.000000Z', '2023-11-14T22:13:30.000000Z'):
        _, tg, _, sender, _ = await enrolled()
        value = json.loads(b.GOLDEN)
        value['after_id'] = '0'
        value['messages'][0]['date'] = date
        wrong = MessageBatch.from_json(b.signed(value))

        async def read(*args, **kwargs):
            return wrong

        tg.batch_engine.fetch_batch = read
        await f.expect(SyncStorageError, tg.sync_group(CHAT))
        assert (await tg.get_sync_status(CHAT)).pending_batch_id is None and not sender.calls


async def test_daily_and_history_collections_stay_independent():
    daily = d.offline(d.store())
    await daily.initialize_sync(CHAT, after_id=500)
    before = await daily.get_sync_status(CHAT)
    _, historical, _, sender, _ = await enrolled()
    pages(sender, [message(101), message(102)])
    batch = await historical.sync_group(CHAT, limit=2)
    await historical.acknowledge_sync(CHAT, batch.batch_id)
    assert await daily.get_sync_status(CHAT) == before
    assert (await historical.get_sync_status(CHAT)).after_id == 102


async def test_uncertain_initialization_reuses_committed_window():
    actual = d.store()
    fault = d.FaultStore(actual)
    fault.raise_after_commit = OSError('commit response lost')
    local = d.offline(fault)
    with patch.object(sync_engine, '_utc_now', return_value=END):
        await f.expect(SyncStorageError, local.initialize_sync(CHAT, after_id=0, last_days=30))
    with patch.object(sync_engine, '_utc_now', side_effect=AssertionError('window rolled')):
        restored = await d.offline(SQLiteSyncStore(actual.path)).initialize_sync(CHAT, after_id=0, last_days=30)
    assert restored.end_date == END and restored.start_date == END-timedelta(days=30)
    second = d.store()
    fault = d.FaultStore(second)
    fault.hold_commit = True
    with patch.object(sync_engine, '_utc_now', return_value=END):
        task = asyncio.create_task(d.offline(fault).initialize_sync(CHAT, after_id=0, last_days=30))
        await fault.entered.wait()
        task.cancel()
        await f.expect(asyncio.CancelledError, task)
    with patch.object(sync_engine, '_utc_now', side_effect=AssertionError('window rolled')):
        assert await d.offline(SQLiteSyncStore(second.path)).initialize_sync(CHAT, after_id=0, last_days=30) == restored


async def test_process_exit_at_window_ack_commit():
    actual, tg, _, sender, _ = await enrolled()
    pages(sender, [message(101)])
    batch = await tg.sync_group(CHAT, limit=1)
    for mode, code, cursor, pending in (('before', 31, 0, batch.batch_id), ('after', 32, 101, None)):
        result = subprocess.run([sys.executable, d.__file__, '--crash-ack', actual.path, batch.batch_id, mode],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        assert result.returncode == code, result.stderr
        state = await d.offline(SQLiteSyncStore(actual.path)).get_sync_status(CHAT)
        assert state.after_id == cursor and state.pending_batch_id == pending
        assert state.start_date == START and state.end_date == END


async def test_cancelled_read_retains_window_and_releases_guard():
    _, tg, _, sender, requests = await enrolled()
    sender.script = [f.PENDING]
    task = asyncio.create_task(tg.sync_group(CHAT, limit=1))
    await d.wait_for_sender(sender, task)
    await f.expect(SyncConflictError, tg.sync_group(CHAT, limit=1))
    task.cancel()
    await f.expect(asyncio.CancelledError, task)
    state = await tg.get_sync_status(CHAT)
    assert state.after_id == 0 and state.pending_batch_id is None and state.start_date == START
    pages(sender, [message(101)])
    assert (await tg.sync_group(CHAT, limit=1)).next_after_id == 101
    assert requests[0] == requests[1]


async def main():
    tests = [test_invalid_dates_before_connection_or_files, test_half_open_window_and_timezone_normalization,
             test_timestamp_ties_across_sdk_pages, test_full_excluded_pages_and_fractional_start,
             test_empty_end_exact_limit_and_max_cursor, test_nonzero_cursor_intersects_window_and_gaps,
             test_wire_date_extremes, test_relative_enrollment_freezes_once,
             test_initialization_conflicts_and_bad_durations, test_restart_replay_ack_and_timestamp_ties,
             test_media_selection_and_pending_replay, test_budget_counts_excluded_slots_and_preserves_prefix,
             test_budget_before_any_included_record_is_not_end, test_read_failure_and_failed_prefix_persistence,
             test_invalid_message_date_and_local_health, test_v1_state_and_default_reader_are_unchanged,
             test_corrupt_window_state_and_pending_refused, test_reader_output_must_match_window,
             test_daily_and_history_collections_stay_independent, test_uncertain_initialization_reuses_committed_window,
             test_process_exit_at_window_ack_commit, test_cancelled_read_retains_window_and_releases_guard]
    print('Fixed Window Tests — Telethon {}; offline SDK/SQLite'.format(telethon.__version__))
    logging.getLogger('tgdata').addHandler(logging.NullHandler())
    passed = 0
    with tempfile.TemporaryDirectory(prefix='tgdata_window_test_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        f.TMP = Path(tmp)
        try:
            for test in tests:
                print('\nTEST:', test.__name__[5:])
                try:
                    await asyncio.wait_for(test(), timeout=40)
                except Exception:
                    traceback.print_exc()
                    print('✗ Failed')
                else:
                    passed += 1
                    print('✓ Passed')
        finally:
            for client in f.CLIENTS:
                await client.disconnect()
            f.CLIENTS.clear()
    print('\nPassed: {}/{}'.format(passed, len(tests)))
    return 0 if passed == len(tests) else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
