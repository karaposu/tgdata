"""Opt-in Gate A instrument. Preflight is offline; a matching scan is not a gate PASS.

Run --help. Source writes, discovery of other groups and policy resets are forbidden.
This diagnostic raw-reader scan never acknowledges or advances lifecycle progress.
"""

import argparse
import asyncio
import contextvars
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import telethon
from telethon import functions, types, utils
from tgdata import TgData, SQLiteSyncStore, ReadBudget
from tgdata.backfill import BackfillRunRef, BackfillStartRequest, _keys, _wire_integer, _json_load, _canonical
from tgdata.backfill_engine import BackfillEngine
from tgdata.history_window import _decode_date, _encode_date


_PAGE = contextvars.ContextVar('backfill_probe_page', default=None)


class ProbeStop(RuntimeError):
    def __init__(self, code):
        super().__init__(code)
        self.__suppress_context__ = True


def require(value, code):
    if not value:
        raise ProbeStop(code)


def number(value, name, low, high):
    require(type(value) is int and low <= value <= high, 'invalid_'+name)
    return value


def seconds(value, name, low, high):
    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
            'invalid_'+name)
    return float(value)


def manifest_from_text(text):
    value = _json_load(text)
    _keys(value, ('schema', 'version', 'run', 'start_request', 'window', 'expected_account_id',
                  'oracle', 'limits'), 'probe manifest')
    require(value['schema'] == 'tgdata.backfill-probe' and type(value['version']) is int
            and value['version'] == 1, 'unsupported_manifest')
    ref = BackfillRunRef.from_dict(value['run'])
    request = BackfillStartRequest.from_dict(value['start_request'])
    require((ref.collection_id, ref.chat_id, ref.run_id) ==
            (request.collection_id, request.chat_id, request.run_id), 'manifest_identity_mismatch')
    _wire_integer(value['expected_account_id'], 'expected_account_id', 1)
    _keys(value['window'], ('start_date', 'end_date'), 'probe window')
    start, end = (_decode_date(value['window'][key]) for key in ('start_date', 'end_date'))
    require(start < end, 'invalid_window')
    oracle = value['oracle']
    _keys(oracle, ('method', 'reference', 'captured_at', 'complete', 'messages'), 'oracle')
    require(oracle['method'] in ('manual', 'independent_export', 'independent_client'), 'oracle_not_independent')
    require(type(oracle['reference']) is str and bool(oracle['reference'].strip()), 'missing_oracle_reference')
    _decode_date(oracle['captured_at'])
    require(oracle['complete'] is True, 'oracle_not_complete')
    require(type(oracle['messages']) is list and len(oracle['messages']) <= 10000, 'invalid_oracle_messages')
    previous = request.after_id
    for row in oracle['messages']:
        _keys(row, ('id', 'date', 'blob'), 'oracle message')
        ident = _wire_integer(row['id'], 'message id', 1, (1 << 31)-1)
        require(ident > previous and start <= _decode_date(row['date']) < end, 'oracle_scope_or_order')
        previous = ident
        if row['blob'] is not None:
            _keys(row['blob'], ('sha256', 'size'), 'oracle blob')
            require(type(row['blob']['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['blob']['sha256']) is not None,
                    'invalid_oracle_hash')
            number(row['blob']['size'], 'oracle_blob_size', 0, 1 << 31)
            require(request.media_mode == 'download', 'blob_oracle_requires_download_mode')
    limits = value['limits']
    _keys(limits, ('max_rpc_requests', 'max_history_requests', 'max_requested_slots',
                  'max_media_bytes', 'timeout_seconds', 'spacing_seconds'), 'probe limits')
    number(limits['max_rpc_requests'], 'rpc_cap', 1, 10000)
    number(limits['max_history_requests'], 'history_cap', 1, 10000)
    number(limits['max_requested_slots'], 'slot_cap', 1, 1000000)
    number(limits['max_media_bytes'], 'media_cap', 0, 1 << 31)
    seconds(limits['timeout_seconds'], 'timeout', 0.001, 3600)
    seconds(limits['spacing_seconds'], 'spacing', 0, 3600)
    if request.media_mode == 'references':
        require(limits['max_media_bytes'] == 0, 'references_have_no_media_allowance')
    else:
        require(limits['max_media_bytes'] > 0, 'download_requires_media_allowance')
    return value


def forbidden_clock():
    raise AssertionError('probe retry/status must not observe a new enrollment clock')


async def preflight(manifest, state_path):
    require(telethon.__version__ == '1.45.0', 'unsupported_telethon')
    ref = BackfillRunRef.from_dict(manifest['run'])
    request = BackfillStartRequest.from_dict(manifest['start_request'])
    store = SQLiteSyncStore(state_path, create=False)
    original = await store.load(ref.chat_id)
    engine = BackfillEngine(store, ref.collection_id, clock=forbidden_clock)
    status = await engine.status(ref)
    retry = await engine.start(request, submission='retry')
    require(not retry.applied and retry.status.run == ref, 'creation_retry_changed_identity')
    require(status.to_dict()['start_date'] == manifest['window']['start_date'] and
            status.to_dict()['end_date'] == manifest['window']['end_date'], 'saved_window_differs_from_oracle')
    require(status.after_id == request.after_id and status.pending_batch_id is None and
            status.attempt_id is None and status.terminal_outcome is None and
            status.control_revision == 0 and not status.history_limited, 'probe_requires_unadvanced_stage2_run')
    require(await store.load(ref.chat_id) == original, 'preflight_mutated_state')
    return store, status, original


def peer_id(peer):
    if isinstance(peer, (types.InputPeerChannel, types.InputChannel, types.PeerChannel)):
        return utils.get_peer_id(types.PeerChannel(peer.channel_id))
    if isinstance(peer, (types.InputPeerChat, types.PeerChat)):
        return utils.get_peer_id(types.PeerChat(peer.chat_id))
    raise ProbeStop('unapproved_peer_kind')


def present_classes(module, names):
    return tuple(getattr(module, n) for n in names if hasattr(module, n))


_WRAPPERS = present_classes(functions, ('InvokeWithLayerRequest', 'InitConnectionRequest',
    'InvokeWithoutUpdatesRequest', 'InvokeAfterMsgRequest', 'InvokeAfterMsgsRequest',
    'InvokeWithMessagesRangeRequest', 'InvokeWithTakeoutRequest', 'InvokeWithBusinessConnectionRequest'))
_MEDIA = present_classes(functions.upload, ('GetFileRequest', 'GetFileHashesRequest',
    'GetCdnFileRequest', 'GetCdnFileHashesRequest'))
_AUTH_MEDIA = present_classes(functions.auth, ('ExportAuthorizationRequest', 'ImportAuthorizationRequest'))


class ReadOnlyGuard:
    """Counts SDK sends/retries inside _call, not MTProto packets/housekeeping."""

    def __init__(self, chat_id, limits, allow_media=False):
        self.chat_id, self.limits, self.allow_media = chat_id, limits, allow_media
        self.rpc = []
        self.history_count = self.slots = self.media_bytes = 0
        self.turn = 0
        self.iterators = 0

    def before_send(self, request):
        require(not isinstance(request, (list, tuple)), 'batched_rpc_not_allowed')
        raw = request
        for _ in range(9):
            if not isinstance(raw, _WRAPPERS):
                break
            raw = raw.query
        else:
            raise ProbeStop('wrapper_depth')
        info = dict(kind=type(raw).__name__, turn=self.turn, page=_PAGE.get(),
                    sent_at=_encode_date(datetime.now(timezone.utc)), monotonic=time.monotonic(),
                    outcome='pending')
        require(len(self.rpc) < self.limits['max_rpc_requests'], 'rpc_cap_reached')
        if isinstance(raw, functions.messages.GetHistoryRequest):
            require(peer_id(raw.peer) == self.chat_id, 'wrong_history_group')
            amount = number(raw.limit, 'history_bound', 1, 10000)
            require(self.history_count < self.limits['max_history_requests'], 'history_cap_reached')
            require(self.slots + amount <= self.limits['max_requested_slots'], 'slot_cap_reached')
            self.history_count += 1
            self.slots += amount
            info.update(limit=amount, offset_id=str(raw.offset_id), min_id=str(raw.min_id),
                        add_offset=raw.add_offset,
                        offset_date=_encode_date(raw.offset_date) if raw.offset_date else None)
        elif isinstance(raw, functions.channels.GetChannelsRequest):
            require(bool(raw.id) and all(peer_id(p) == self.chat_id for p in raw.id), 'wrong_metadata_group')
        elif isinstance(raw, functions.messages.GetChatsRequest):
            require(bool(raw.id) and all(-int(p) == self.chat_id for p in raw.id), 'wrong_metadata_group')
        elif isinstance(raw, functions.users.GetUsersRequest):
            require(bool(raw.id) and all(isinstance(p, types.InputUserSelf) for p in raw.id), 'only_self_identity_allowed')
        elif isinstance(raw, (functions.updates.GetStateRequest, functions.help.GetConfigRequest)):
            pass
        elif isinstance(raw, _MEDIA):
            require(self.allow_media, 'media_not_allowed')
            amount = getattr(raw, 'limit', 0)
            number(amount, 'file_bound', 0, 1 << 31)
            require(self.media_bytes + amount <= self.limits['max_media_bytes'], 'media_cap_reached')
            self.media_bytes += amount
        elif isinstance(raw, _AUTH_MEDIA):
            require(self.allow_media, 'media_dc_auth_not_allowed')
        else:
            # Includes writes, joins, invites, login codes, dialog discovery and
            # unsupported source reads. Unknown behavior is not silently allowed.
            raise ProbeStop('unapproved_rpc_'+type(raw).__name__)
        self.rpc.append(info)
        return info

    def instrument(self, client):
        original_call = client._call
        original_iter = client.iter_messages
        guard = self

        async def call(sender, request, ordered=False, flood_sleep_threshold=None):
            return await original_call(ObservedSender(sender, guard), request, ordered=ordered,
                                       flood_sleep_threshold=flood_sleep_threshold)

        def iterate(*args, **kwargs):
            iterator = original_iter(*args, **kwargs)
            self.iterators += 1
            identity = self.iterators
            count = 0
            original_load = iterator._load_next_chunk

            async def load():
                nonlocal count
                count += 1
                token = _PAGE.set((identity, count))
                try:
                    return await original_load()
                finally:
                    _PAGE.reset(token)
            iterator._load_next_chunk = load
            return iterator

        client._call = call
        client.iter_messages = iterate
        # Telethon 1.45's receive_updates=False representation; install before
        # connect. It scopes this diagnostic connection, not account settings.
        client._no_updates = True


class ObservedSender:
    def __init__(self, sender, guard):
        self.sender, self.guard = sender, guard

    def __getattr__(self, name):
        return getattr(self.sender, name)

    def send(self, request, ordered=False):
        entry = self.guard.before_send(request)
        try:
            future = self.sender.send(request, ordered=ordered)
        except BaseException as error:
            entry['outcome'] = type(error).__name__
            raise

        async def observe():
            try:
                result = await future
            except BaseException as error:
                entry['outcome'] = type(error).__name__
                raise
            entry['outcome'] = 'answered'
            entry['answered_at'] = _encode_date(datetime.now(timezone.utc))
            if hasattr(result, 'messages'):
                entry['returned_slots'] = len(result.messages)
                entry['response_type'] = type(result).__name__
            return result
        return observe()


def compare_observations(manifest, observations):
    expected = manifest['oracle']['messages']
    actual_ids = [row['id'] for row in observations]
    expected_ids = [row['id'] for row in expected]
    by_id = {row['id']: row for row in observations}
    date_errors, media_errors = [], []
    for wanted in expected:
        actual = by_id.get(wanted['id'])
        if actual is None:
            continue
        if wanted['date'] != actual['date']:
            date_errors.append(wanted['id'])
        if wanted['blob'] != actual['blob']:
            media_errors.append(wanted['id'])
    return dict(exact_match=actual_ids == expected_ids and not date_errors and not media_errors,
                expected_count=len(expected), observed_count=len(observations),
                missing_ids=sorted(set(expected_ids)-set(actual_ids), key=int),
                unexpected_ids=sorted(set(actual_ids)-set(expected_ids), key=int),
                date_mismatches=date_errors, media_mismatches=media_errors)


async def live_scan(manifest, state_path, config_path, budget_path, media_directory=None):
    store, status, original = await preflight(manifest, state_path)
    require(Path(config_path).is_file(), 'selected_config_missing')
    require(Path(budget_path).is_file(), 'authoritative_budget_missing')
    budget = ReadBudget(budget_path)
    expected_account = int(manifest['expected_account_id'])
    before_budget = budget.status(expected_account)  # require existing policy; never configure it
    download = status.media_mode == 'download'
    require((media_directory is not None) == download, 'media_directory_mode_mismatch')
    guard = ReadOnlyGuard(status.run.chat_id, manifest['limits'], download)
    tg = TgData(str(config_path), connection_pool_size=1, interactive_login=False, read_budget=budget)
    factory = tg.connection_engine._new_client

    def instrumented(*args, **kwargs):
        client = factory(*args, **kwargs)
        guard.instrument(client)
        return client
    tg.connection_engine._new_client = instrumented
    observations, stops = [], []
    report = dict(scope='Gate A diagnostic raw scan; no lifecycle prepare/ack',
                  oracle_sha256=hashlib.sha256(_canonical(manifest['oracle']).encode()).hexdigest(),
                  run=status.run.to_dict(), window=manifest['window'], telethon=telethon.__version__,
                  budget_used_before=before_budget.used,
                  comparison='UNFINISHED', gate_verdict='INCONCLUSIVE')
    old_logging_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)  # third-party errors can contain paths/account details
    primary = None
    try:
        async def scan():
            client = await tg.connection_engine.get_client()
            me = await client.get_me(input_peer=False)
            require(me is not None and me.id == expected_account, 'wrong_authenticated_account')
            report['account_verified'] = True
            cursor = status.after_id
            while True:
                guard.turn += 1
                batch = await tg.get_message_batch(
                    status.run.chat_id, after_id=cursor, limit=status.batch_size,
                    start_date=status.start_date, end_date=status.end_date,
                    download_media_to=media_directory)
                require(batch.chat_id == status.run.chat_id and batch.after_id == cursor, 'reader_context_mismatch')
                for row in batch.messages:
                    blob = row['media']['blob'] if row['media'] else None
                    observations.append(dict(id=row['id'], date=row['date'],
                                             blob=dict(sha256=blob['sha256'],size=blob['size']) if blob else None))
                stops.append(batch.stop_reason)
                if batch.stop_reason == 'end':
                    break
                require(batch.stop_reason == 'limit' and batch.next_after_id > cursor, 'unexpected_scan_outcome')
                cursor = batch.next_after_id
                await asyncio.sleep(manifest['limits']['spacing_seconds'])
        await asyncio.wait_for(scan(), timeout=manifest['limits']['timeout_seconds'])
        comparison = compare_observations(manifest, observations)
        report.update(comparison)
        report['comparison'] = 'MATCH' if comparison['exact_match'] else 'MISMATCH'
        report['gate_verdict'] = 'INCONCLUSIVE' if comparison['exact_match'] else 'FAIL'
    except asyncio.CancelledError:
        primary = 'CancelledError'
        raise
    except Exception as error:
        primary = type(error).__name__
        report['error_type'] = primary
        if isinstance(error, ProbeStop):
            report['stop_code'] = str(error)  # only owned, fixed diagnostic codes
    finally:
        try:
            await asyncio.wait_for(tg.close(), 10)
        except Exception as error:
            report['cleanup_error_type'] = type(error).__name__
            if report['gate_verdict'] != 'FAIL':
                report['gate_verdict'] = 'INCONCLUSIVE'
        finally:
            logging.disable(old_logging_disable)
    try:
        unchanged = await store.load(status.run.chat_id) == original
    except Exception as error:
        unchanged = None
        report['state_check_error_type'] = type(error).__name__
        if report['gate_verdict'] != 'FAIL':
            report['gate_verdict'] = 'INCONCLUSIVE'
    if unchanged is False:
        report['gate_verdict'] = 'FAIL'
        report['stop_code'] = 'diagnostic_scan_mutated_lifecycle_state'
    try:
        report['budget_used_after'] = budget.status(expected_account).used
    except Exception as error:
        report['budget_check_error_type'] = type(error).__name__
        if report['gate_verdict'] != 'FAIL':
            report['gate_verdict'] = 'INCONCLUSIVE'
    histories = [r for r in guard.rpc if r['kind'] == 'GetHistoryRequest']
    pages = {}
    for row in histories:
        if row['outcome'] == 'answered' and row['page']:
            ident, page = row['page']
            pages.setdefault(ident,set()).add(page)
    report.update(rpc=guard.rpc, requested_slots=guard.slots, requested_media_bytes=guard.media_bytes,
                  history_requests=len(histories), source_turns=guard.turn, stop_reasons=stops,
                  sdk_page_boundary_observed=any(len(p) >= 2 for p in pages.values()),
                  lifecycle_state_unchanged=unchanged,
                  remaining_gate_review=['independent oracle completeness/visibility',
                      'required empty/full/boundary/relative/media cases',
                      'actual creation/commit/restart receipts', 'source interruption characterization'])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--state', type=Path)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--budget', type=Path)
    parser.add_argument('--media', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.manifest is None or args.state is None:
        parser.error('--manifest and --state are required; default mode is offline preflight')
    try:
        if args.output is not None:
            require(not args.output.exists() and args.output.parent.is_dir(), 'output_must_be_new_in_existing_directory')
        manifest = manifest_from_text(args.manifest.read_text(encoding='utf-8'))
        if args.live:
            require(args.config is not None and args.budget is not None and args.output is not None,
                    'live_requires_config_budget_and_output')
            report = asyncio.run(live_scan(manifest,args.state,args.config,args.budget,args.media))
        else:
            _, status, _ = asyncio.run(preflight(manifest,args.state))
            report = dict(mode='OFFLINE_PREFLIGHT', run=status.run.to_dict(), window=manifest['window'],
                          live_started=False, gate_verdict='INCONCLUSIVE',
                          reason='preflight is not live Gate A evidence')
    except Exception as error:
        report = dict(gate_verdict='BLOCKED', error_type=type(error).__name__,
                      live_requested=args.live, live_activity='UNKNOWN' if args.live else 'NONE')
        if isinstance(error,ProbeStop):report['stop_code']=str(error)
    text = json.dumps(report,sort_keys=True,indent=2,allow_nan=False)
    if args.output is not None:
        try:
            with args.output.open('x',encoding='utf-8') as output:output.write(text+'\n')
        except OSError:
            report['report_write_error_type'] = 'ReportWriteError'
            print(json.dumps(report,sort_keys=True,allow_nan=False))
            return 2
    print(text)
    successful_scan = (report.get('comparison') == 'MATCH'
                       and report.get('lifecycle_state_unchanged') is True
                       and not any(key.endswith('error_type') for key in report))
    return 0 if report.get('mode') == 'OFFLINE_PREFLIGHT' or successful_scan else 2


if __name__ == '__main__':
    sys.exit(main())
