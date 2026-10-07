"""Durable historical-run delivery, completion and exact write confirmation.

Positive timing eligibility, controls, recovery and the public facade retain their
later stages. A source callback never runs before confirmed durable admission.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import os
import re
from uuid import uuid4

from .backfill import (
    BackfillRunRef, BackfillStartRequest, BackfillStartResult,
    BackfillPrepareContext, BackfillDeliveryRef, BackfillTurn, BackfillError,
    BackfillConfigurationError, BackfillConflictError, BackfillStorageError,
    BackfillUnknownRun, BackfillUnknownCommand, BackfillUnknownReceipt,
    BackfillRecoveryRequired, BackfillMediaError, BackfillClockError, BackfillStateError,
    _token, _choice, _pause_delta,
)
from .batch_files import prepare_directory, _verify_existing, BatchStorageError
from .backfill_state import _BackfillState, initial_record, SCHEMA, VERSION
from .history_window import _HistoryWindow, _utc, _encode_date, _decode_date
from .message_batch import MessageBatch, MAX_LONG
from .read_budget import ReadBudgetExceeded, ReadBudgetError, ReadBudgetStorageError


def _utc_now():
    return datetime.now(timezone.utc)


class BackfillEngine:
    """Internal staged engine over an isolated async opaque-text store namespace."""

    def __init__(self, store, collection_id, *, read_batch=None, clock=_utc_now):
        self._store = store
        self.collection_id = _token(collection_id, 'collection_id')
        if not callable(clock):
            raise BackfillConfigurationError('clock must be callable')
        if read_batch is not None and not callable(read_batch):
            raise BackfillConfigurationError('read_batch must be callable or None')
        self._clock = clock
        self._read_batch = read_batch
        self._preparing = set()

    async def _backend(self, operation, *args):
        try:
            method = getattr(self._store, operation, None)
        except asyncio.CancelledError as error:
            raise error from None
        except Exception as error:
            raise BackfillStorageError('Backfill store {} failed ({})'.format(
                operation, type(error).__name__)) from None
        if not callable(method):
            raise BackfillConfigurationError('configure an async load/compare_and_swap backfill store')
        try:
            return await method(*args)
        except asyncio.CancelledError as error:
            raise error from None
        except Exception as error:
            raise BackfillStorageError('Backfill store {} failed ({})'.format(
                operation, type(error).__name__)) from None

    def _scope(self, ref):
        if ref.collection_id != self.collection_id:
            raise BackfillConfigurationError('reference/request differs from the configured collection')

    async def _load(self, chat_id):
        raw = await self._backend('load', chat_id)
        return raw, (_BackfillState.from_json(raw, self.collection_id, chat_id)
                     if raw is not None else None)

    async def _known(self, run):
        self._scope(run)
        raw, state = await self._load(run.chat_id)
        if state is not None:
            value = state.to_dict()
            for key in ('current', 'previous'):
                row = value[key]
                if row is not None and row['ref'] == run.to_dict():
                    return raw, state, value, key
        raise BackfillUnknownRun('run is missing or no longer retained; restore its context')

    @staticmethod
    def _revision(value, reserve=1):
        current = int(value['state_revision'])
        if current > MAX_LONG - reserve:
            raise BackfillConflictError('lifecycle revision capacity is insufficient for this transition')
        return current + 1

    async def _commit(self, chat_id, raw, state, *, reconcile=True):
        """Confirm one CAS, optionally reading back its exact candidate on error.

        A different/absent snapshot does not prove rollback: the write may still
        be unknown or later state may have superseded it. Never write again here.
        Admission opts out; its ambiguous reply must not authorize a source call.
        """
        encoded = state.to_json()
        try:
            written = await self._backend('compare_and_swap', chat_id, raw, encoded)
            if type(written) is not bool:
                raise BackfillStorageError(
                    'backfill compare_and_swap must return a boolean; outcome may be unknown')
            return written
        except BackfillStorageError as write_error:
            if not reconcile:
                raise
            try:
                _, observed = await self._load(chat_id)
            except BackfillStorageError:
                raise write_error from None
            if observed is not None and observed.to_json() == encoded:
                return True
            raise write_error from None

    async def _write(self, raw, value, reserve=1, *, reconcile=True):
        value['state_revision'] = str(self._revision(value, reserve))
        next_state = _BackfillState(value)
        written = await self._commit(int(value['chat_id']), raw, next_state, reconcile=reconcile)
        return written, next_state

    def _now(self):
        try:
            return _utc(self._clock(), 'clock')
        except asyncio.CancelledError as error:
            raise error from None
        except Exception as error:
            raise BackfillClockError('backfill clock failed ({})'.format(type(error).__name__)) from None

    @staticmethod
    def _context_matches(context, row):
        if (context.expected_after_id != int(row['after_id']) or
                context.expected_control_revision != int(row['control_revision'])):
            raise BackfillConflictError('prepare context is stale; obtain current context deliberately')

    @staticmethod
    def _directory(mode, directory, needed=False):
        if mode == 'references':
            if directory is not None:
                raise BackfillConfigurationError('reference mode does not accept a media directory')
            return None
        if directory is None and not needed:
            return None
        if (not isinstance(directory, (str, os.PathLike)) or isinstance(directory, bool)
                or directory == ''):
            raise BackfillConfigurationError('download preparation requires an explicit media directory')
        if not needed:
            return None
        try:
            return prepare_directory(directory)
        except asyncio.CancelledError as error:
            raise error from None
        except Exception as error:
            raise BackfillMediaError('backfill media directory failed ({})'.format(type(error).__name__)) from None

    @staticmethod
    def _verify_media(batch, directory):
        try:
            checked = set()
            for record in batch.messages:
                blob = record['media']['blob'] if record['media'] is not None else None
                if blob is None:
                    continue
                key = (blob['sha256'], blob['size'])
                if key not in checked:
                    _verify_existing(directory / blob['path'], *key)
                    checked.add(key)
        except asyncio.CancelledError as error:
            raise error from None
        except Exception as error:
            raise BackfillMediaError('backfill artifact verification failed ({})'.format(
                type(error).__name__)) from None

    @staticmethod
    def _batch(batch, row, interrupted=False):
        try:
            if not isinstance(batch, MessageBatch):
                raise TypeError
            owned = MessageBatch(batch.to_dict())
            value = owned.to_dict()
            if (value['chat_id'] != row['ref']['chat_id'] or value['after_id'] != row['after_id']
                    or value['media_mode'] != row['request']['media_mode']
                    or len(value['messages']) > row['request']['batch_size']
                    or value['stop_reason'] not in (('interrupted',) if interrupted else ('limit', 'end'))):
                raise ValueError
            window = _HistoryWindow(_decode_date(row['window']['start_date']),
                                    _decode_date(row['window']['end_date']))
            if any(record['date'] is None or not window.contains(_decode_date(record['date']))
                   for record in value['messages']):
                raise ValueError
            return owned
        except asyncio.CancelledError as error:
            raise error from None
        except Exception as error:
            raise BackfillStateError('reader observation differs from the admitted run ({})'.format(
                type(error).__name__)) from None

    @staticmethod
    def _turn(state, previous=False, replayed=False):
        status = state.status(previous=previous)
        row = state.to_dict()['previous' if previous else 'current']
        batch = MessageBatch(row['pending']) if row['pending'] is not None else None
        delivery = (BackfillDeliveryRef(status.run, status.destination_id, batch.batch_id)
                    if batch is not None else None)
        return BackfillTurn(status, batch, delivery, replayed)

    async def _admit(self, raw, value, context, directory):
        row = value['current']
        pacing = row['pacing']
        if pacing is not None:
            if pacing['clock_uncertain']:
                raise BackfillRecoveryRequired('saved timing is uncertain; later recovery is required',
                                               _BackfillState(value).status())
            if (row['request']['pause_seconds'] > 0 or pacing['ended_at'] is None
                    or pacing['not_before'] != pacing['ended_at']):
                raise BackfillConfigurationError(
                    'further paced source admission requires Stage 5; replay and acknowledgment remain available')
        if self._read_batch is None:
            raise BackfillConfigurationError('configure read_batch for new source preparation')
        self._revision(value, reserve=3)
        root = self._directory(row['request']['media_mode'], directory, needed=True)
        admitted = self._now()
        if (admitted < _decode_date(row['created_at']) or
                (pacing is not None and admitted < _decode_date(pacing['not_before']))):
            raise BackfillClockError('clock precedes saved lifecycle evidence; no source admission')
        row['attempt'] = dict(attempt_id=uuid4().hex, after_id=row['after_id'],
                              control_revision=row['control_revision'], admitted_at=_encode_date(admitted))
        written, state = await self._write(raw, value, reserve=3, reconcile=False)
        if not written:
            raise BackfillConflictError('state changed before source admission; no read was started')
        return state.to_dict()['current'], root

    def _ended(self, admitted):
        ended = self._now()
        if ended < _decode_date(admitted['attempt']['admitted_at']):
            raise BackfillClockError('clock regressed during the source attempt; settlement is unconfirmed')
        try:
            deadline = ended + _pause_delta(admitted['request']['pause_seconds'])
        except (ValueError, OverflowError) as error:
            raise BackfillClockError('attempt deadline is unrepresentable ({})'.format(
                type(error).__name__)) from None
        return ended, deadline

    @staticmethod
    def _failure(error, ended):
        category = ('storage' if isinstance(error, ReadBudgetStorageError) else
                    'budget' if isinstance(error, ReadBudgetError) else
                    'media' if isinstance(error, BatchStorageError) else 'source')
        # "source" means the reader call failed, not a Telegram health verdict.
        name = type(error).__name__
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', name) is None:
            name = 'Exception'
        account_id = retry_at = None
        if isinstance(error, ReadBudgetExceeded):
            try:
                ident = error.account_id
                if type(ident) is int and 0 < ident <= MAX_LONG:
                    account_id = str(ident)
                at = error.next_available_at
                if at is not None and not isinstance(at, bool):
                    retry_at = _encode_date(datetime.fromtimestamp(at, timezone.utc))
            except asyncio.CancelledError as cancelled:
                raise cancelled from None
            except (ValueError, TypeError, OverflowError, OSError):
                retry_at = None
        return dict(category=category, error_type=name, observed_at=_encode_date(ended),
                    retry_at=retry_at, account_id=account_id)

    @staticmethod
    def _complete_if_fulfilled(row):
        # Empty-end settlement and final acknowledgment share this closure.
        # End evidence alone cannot discharge owed work or supersede cancellation.
        if (row['terminal_outcome'] is None and row['exhaustion'] is not None
                and row['pending'] is None and row['attempt'] is None and row['abandoned'] is None):
            row['terminal_outcome'] = 'completed'

    async def _settle(self, admitted, batch, timing, failure=None):
        run = BackfillRunRef.from_dict(admitted['ref'])
        ended, deadline = timing
        value = batch.to_dict() if batch is not None else None
        for _ in range(4):
            raw, _, document, key = await self._known(run)
            row = document[key]
            if (key != 'current' or row['attempt'] != admitted['attempt']
                    or row['after_id'] != admitted['after_id']
                    or row['request'] != admitted['request'] or row['window'] != admitted['window']
                    or row['pending'] is not None or row['exhaustion'] is not None):
                raise BackfillConflictError('source result no longer owns the addressed attempt and intent')
            row['pending'] = value if value is not None and value['messages'] else None
            row['attempt'] = None
            row['last_recovery'] = None
            row['pacing'] = dict(attempt_id=admitted['attempt']['attempt_id'],
                                 ended_at=_encode_date(ended), not_before=_encode_date(deadline),
                                 clock_uncertain=False)
            if failure is not None:
                row['last_failure'] = failure
            if failure is None and value is not None and value['stop_reason'] == 'end':
                row['exhaustion'] = dict(attempt_id=admitted['attempt']['attempt_id'],
                    after_id=admitted['after_id'], next_after_id=value['next_after_id'],
                    observed_at=_encode_date(ended))
            self._complete_if_fulfilled(row)
            written, state = await self._write(raw, document, reserve=2 if row['pending'] else 1)
            if written:
                return self._turn(state)
        raise BackfillConflictError('source settlement kept conflicting; inspect the authoritative attempt')

    async def prepare(self, context, *, download_media_to=None):
        """Prepare/replay one exact delivery using current run/cursor/control intent.

        Further positive-pause timing and explicit recovery are later-stage work.
        Pending replay remains local, including while paused or cancelled. The
        caller excludes other source readers in separate collections/daily jobs.
        """
        if not isinstance(context, BackfillPrepareContext):
            raise BackfillConfigurationError('prepare requires BackfillPrepareContext')
        context = BackfillPrepareContext.from_dict(context.to_dict())
        self._scope(context.run)
        chat_id = context.run.chat_id
        if chat_id in self._preparing:
            raise BackfillConflictError('preparation is already active for this group on this engine')
        self._preparing.add(chat_id)
        try:
            raw, state, document, key = await self._known(context.run)
            row = document[key]
            self._context_matches(context, row)
            self._directory(row['request']['media_mode'], download_media_to)
            if row['pending'] is not None:
                root = self._directory(row['request']['media_mode'], download_media_to, needed=True)
                batch = MessageBatch(row['pending'])
                self._verify_media(batch, root)
                return self._turn(state, previous=key == 'previous', replayed=True)
            if row['terminal_outcome'] is not None or row['operator_intent'] == 'paused':
                return self._turn(state, previous=key == 'previous')
            if row['attempt'] is not None:
                raise BackfillRecoveryRequired('source attempt is unresolved; inspect/recover before reading',
                                               state.status(previous=key == 'previous'))
            admitted, root = await self._admit(raw, document, context, download_media_to)
            options = dict(after_id=int(admitted['after_id']), limit=admitted['request']['batch_size'],
                           download_media_to=root,
                           start_date=_decode_date(admitted['window']['start_date']),
                           end_date=_decode_date(admitted['window']['end_date']))
            try:
                result = await self._read_batch(chat_id, **options)
            except asyncio.CancelledError as error:
                raise error from None
            except Exception as read_error:
                try:
                    timing = self._ended(admitted)
                    partial = getattr(read_error, 'partial_result', None)
                    batch = self._batch(partial, admitted, interrupted=True) if partial is not None else None
                    if batch is not None:
                        self._verify_media(batch, root)
                    await self._settle(admitted, batch, timing, self._failure(read_error, timing[0]))
                except asyncio.CancelledError as error:
                    raise error from None
                except BackfillError as local_error:
                    local_error.read_error = read_error
                    raise local_error from None
                except Exception as error:
                    local_error = BackfillStateError('cannot validate source failure prefix ({})'.format(
                        type(error).__name__))
                    local_error.read_error = read_error
                    raise local_error from None
                raise
            timing = self._ended(admitted)
            batch = self._batch(result, admitted)
            self._verify_media(batch, root)
            return await self._settle(admitted, batch, timing)
        except asyncio.CancelledError as error:
            raise error from None
        finally:
            self._preparing.discard(chat_id)

    async def acknowledge(self, delivery):
        """Assert durable receiver acceptance of this exact scoped obligation.

        Only the saved pending next ID advances progress. This never reads the
        source or verifies/removes local media; acceptance is the caller's assertion.
        """
        if not isinstance(delivery, BackfillDeliveryRef):
            raise BackfillConfigurationError('acknowledge requires BackfillDeliveryRef')
        delivery = BackfillDeliveryRef.from_dict(delivery.to_dict())
        self._scope(delivery.run)
        for _ in range(4):
            raw, state, value, key = await self._known(delivery.run)
            row = value[key]
            if row['request']['destination_id'] != delivery.destination_id:
                raise BackfillConflictError('delivery destination differs from its retained run')
            latest = row['last_ack']
            if latest is not None and latest['batch_id'] == delivery.batch_id:
                return state.status(previous=key == 'previous')
            pending = row['pending']
            if key != 'current' or pending is None or pending['batch_id'] != delivery.batch_id:
                raise BackfillUnknownReceipt('delivery is not owed or its receipt is no longer retained')
            self._revision(value)
            observed = self._now()
            row['after_id'] = pending['next_after_id']
            row['pending'] = None
            row['last_ack'] = dict(batch_id=delivery.batch_id, next_after_id=row['after_id'],
                                   observed_at=_encode_date(observed))
            self._complete_if_fulfilled(row)
            written, accepted = await self._write(raw, value)
            if written:
                return accepted.status()
        raise BackfillConflictError('acknowledgment kept conflicting; inspect or retry the same receipt')

    async def start(self, request, *, submission):
        """Create explicit new intent or recognize a retained creation request.

        Unknown retry never creates. Retained matching requests do not read time or
        write. Ambiguous replies get one exact-state read-back; otherwise inspect
        or retry the same request. A confirmed false CAS remains a conflict.
        """
        if not isinstance(request, BackfillStartRequest):
            raise BackfillConfigurationError('start requires BackfillStartRequest')
        # Revalidate the portable snapshot, not caller-owned mutable structures.
        request = BackfillStartRequest.from_dict(request.to_dict())
        self._scope(request)
        _choice(submission, ('new', 'retry'), 'submission')
        raw, state = await self._load(request.chat_id)
        value = state.to_dict() if state is not None else None
        if value is not None:
            for key in ('current', 'previous'):
                row = value[key]
                if row is not None and row['ref']['run_id'] == request.run_id:
                    if row['request'] != request.to_dict():
                        raise BackfillConflictError('creation identity was accepted with different input')
                    return BackfillStartResult(False, state.status(previous=key == 'previous'))
        if submission == 'retry':
            raise BackfillUnknownCommand('creation request is not retained; retry cannot create')

        previous = None
        if value is None:
            if request.expected_predecessor is not None:
                raise BackfillConflictError('expected predecessor is missing; restore known state')
            generation, revision = 1, 1
        else:
            current = value['current']
            current_ref = BackfillRunRef.from_dict(current['ref'])
            if request.expected_predecessor != current_ref:
                raise BackfillConflictError('new intent does not address the current predecessor')
            if (current['terminal_outcome'] is None or current['attempt'] is not None
                    or current['pending'] is not None):
                raise BackfillConflictError('predecessor is not terminal, quiescent and settled')
            if current_ref.generation >= MAX_LONG or int(value['state_revision']) >= MAX_LONG:
                raise BackfillConflictError('lifecycle counter limit reached; context cannot wrap')
            generation = current_ref.generation + 1
            revision = int(value['state_revision']) + 1
            previous = current

        try:
            created = _utc(self._clock(), 'clock')
            created + _pause_delta(request.pause_seconds)
            if request.last_days is not None:
                window = _HistoryWindow(created - timedelta(days=request.last_days), created)
            else:
                window = _HistoryWindow(request.start_date, request.end_date)
                if window.end_date > created:
                    raise ValueError('future end')
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise BackfillConfigurationError('cannot create a closed UTC run ({})'.format(
                type(error).__name__)) from None

        next_state = _BackfillState(dict(
            schema=SCHEMA, version=VERSION, collection_id=self.collection_id,
            chat_id=str(request.chat_id), state_revision=str(revision),
            current=initial_record(request, generation, created, window), previous=previous,
        ))
        written = await self._commit(request.chat_id, raw, next_state)
        if not written:
            raise BackfillConflictError('backfill state changed; reload before retrying')
        return BackfillStartResult(True, next_state.status())

    async def status(self, run):
        """Return only the addressed current/retained run; absence is never bootstrap."""
        if not isinstance(run, BackfillRunRef):
            raise BackfillConfigurationError('status requires BackfillRunRef')
        run = BackfillRunRef.from_dict(run.to_dict())
        self._scope(run)
        _, state = await self._load(run.chat_id)
        if state is not None:
            value = state.to_dict()
            for key in ('current', 'previous'):
                row = value[key]
                if row is not None and BackfillRunRef.from_dict(row['ref']) == run:
                    return state.status(previous=key == 'previous')
        raise BackfillUnknownRun('run is missing or no longer retained; restore its context')
