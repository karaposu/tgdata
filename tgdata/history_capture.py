"""Bounded source capture across UTC days; no saved progress or selection I/O."""

import asyncio
from datetime import datetime, timedelta, timezone

from telethon.tl import functions, types

from .batch_engine import _record
from .group_operations import GroupReferenceError, GroupResponseError, _resolve
from .history_observation import history_page
from .history_sample import HistoryCapture, CAPTURE_ALGORITHM, _days, _metadata, _ranks
from .history_window import _encode_date
from .message_batch import _validate_record


async def _capture_group_history(operation, target, window, max_messages, max_requests,
                                 started_at, beat=None):
    lookup, peer = await _resolve(operation, target)
    if lookup.group.kind not in ('group', 'megagroup', 'channel') or not isinstance(
            peer, (types.InputPeerChat, types.InputPeerChannel)):
        raise GroupReferenceError('History capture requires a supported group with a usable peer')
    group = lookup.group.to_dict()
    _metadata(lookup.account_id, lookup.target, group)
    windows = _days(window)
    buckets = [dict(day.to_dict(), requests=0, pages=0, scanned_messages=0,
                    unavailable_messages=0, end_reason=None, records=[]) for day in windows]
    offsets = [(None, None) for _ in windows]
    seen = set()
    scanned = requests = 0

    def result(reason):
        return HistoryCapture._from_document(dict(
            schema='tgdata.history-capture', version=1, algorithm=CAPTURE_ALGORITHM,
            account_id=lookup.account_id, target=lookup.target, group=group,
            start_date=_encode_date(window.start_date), end_date=_encode_date(window.end_date),
            collection_started_at=_encode_date(started_at),
            collection_finished_at=_encode_date(datetime.now(timezone.utc)),
            limits=dict(max_messages=max_messages, max_requests=max_requests), stop_reason=reason,
            buckets=[dict(b, records=sorted(b['records'], key=lambda r: (r['date'], int(r['id']))))
                     for b in buckets]))

    def project(row, date, observed_at):
        record = _record(row, operation.client)
        _validate_record(record, 'references')
        return record

    try:
        while True:
            active = [i for i, bucket in enumerate(buckets) if bucket['end_reason'] is None]
            if not active:
                return result('finished')
            if scanned == max_messages:
                return result('message_limit')
            if requests == max_requests:
                return result('request_limit')
            visits = min(len(active), max_messages-scanned, max_requests-requests)
            selected = [active[i] for i in _ranks(len(active), visits)]
            for position, index in enumerate(selected):
                bucket, day = buckets[index], windows[index]
                remaining_visits = len(selected)-position
                limit = min(100, max(1, (max_messages-scanned)//remaining_visits))
                if bucket['requests'] == 0 and max_requests-requests > remaining_visits:
                    limit = 1  # Cheap empty-day witness when a later depth pass can fit.
                last_id, last_date = offsets[index]
                upper = day.end_date.replace(microsecond=0)
                if day.end_date.microsecond:
                    upper += timedelta(seconds=1)
                requests += 1
                bucket['requests'] += 1
                reply = await operation.client(functions.messages.GetHistoryRequest(
                    peer, last_id or 0, upper if last_id is None else None, 0, limit, 0, 0, 0))
                accepted, _, missing, count, next_id, next_date, reason = history_page(
                    reply, lookup.group.peer_id, limit, last_id, last_date, day,
                    datetime.now(timezone.utc), project, label='Sampling')
                ids = {record['id'] for record in accepted}
                if ids & seen:
                    raise GroupResponseError('Sampling history repeats an ID across day buckets')
                # Commit the whole validated page together. Failed pages never add facts.
                bucket['records'].extend(accepted)
                bucket['pages'] += 1
                bucket['scanned_messages'] += count
                bucket['unavailable_messages'] += missing
                bucket['end_reason'] = reason
                scanned += count
                seen.update(ids)
                offsets[index] = next_id, next_date
                if beat is not None:
                    beat('history page done')
    except (Exception, asyncio.CancelledError) as error:
        try:
            error.partial_result = result('cancelled' if isinstance(error, asyncio.CancelledError)
                                          else 'error')
        except BaseException:
            pass  # Observational data cannot replace the original failure.
        raise
