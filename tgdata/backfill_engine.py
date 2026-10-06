"""Stage 2: atomic historical-run creation and storage-only status.

Preparation, acknowledgment, controls and recovery are deliberately later stages.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from .backfill import (
    BackfillRunRef, BackfillStartRequest, BackfillStartResult,
    BackfillConfigurationError, BackfillConflictError, BackfillStorageError,
    BackfillUnknownRun, BackfillUnknownCommand, _token, _choice, _pause_delta,
)
from .backfill_state import _BackfillState, initial_record, SCHEMA, VERSION
from .history_window import _HistoryWindow, _utc
from .message_batch import MAX_LONG


def _utc_now():
    return datetime.now(timezone.utc)


class BackfillEngine:
    """Internal staged engine over an isolated async opaque-text store namespace."""

    def __init__(self, store, collection_id, *, clock=_utc_now):
        self._store = store
        self.collection_id = _token(collection_id, 'collection_id')
        if not callable(clock):
            raise BackfillConfigurationError('clock must be callable')
        self._clock = clock

    async def _backend(self, operation, *args):
        try:
            method = getattr(self._store, operation, None)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            raise BackfillStorageError('Backfill store {} failed ({})'.format(
                operation, type(error).__name__)) from None
        if not callable(method):
            raise BackfillConfigurationError('configure an async load/compare_and_swap backfill store')
        try:
            return await method(*args)
        except asyncio.CancelledError:
            raise
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

    async def start(self, request, *, submission):
        """Create explicit new intent or recognize a retained creation request.

        Unknown retry never creates. Retained matching requests do not read time or
        write. A failed CAS conflicts; an uncertain commit must be retried/reloaded.
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
        written = await self._backend('compare_and_swap', request.chat_id, raw, next_state.to_json())
        if type(written) is not bool:
            raise BackfillStorageError('backfill compare_and_swap must return a boolean; outcome may be unknown')
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
