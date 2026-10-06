"""Strict, owned lifecycle snapshots. Later stages own their transition operations."""

import copy
from dataclasses import dataclass, field
from datetime import timedelta
import re

from .backfill import (
    BackfillRunRef, BackfillStartRequest, BackfillStatus, BackfillStateError,
    _canonical, _json_load, _keys, _token, _wire_integer, _choice, _pause_delta,
)
from .history_window import _HistoryWindow, _decode_date, _encode_date
from .message_batch import MessageBatch, MAX_MESSAGE_ID, MAX_LONG, MIN_LONG


SCHEMA = 'tgdata.backfill-state'
VERSION = 1
_RECORD_KEYS = {
    'ref', 'request', 'created_at', 'window', 'after_id', 'control_revision',
    'operator_intent', 'terminal_outcome', 'pending', 'last_ack', 'exhaustion',
    'attempt', 'pacing', 'last_control', 'last_recovery', 'last_failure', 'abandoned',
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(value):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'invalid batch hash')
    return value


def _date(value, nullable=False):
    return None if nullable and value is None else _decode_date(value)


def _number(value, name='stored number', minimum=0, maximum=MAX_LONG):
    return _wire_integer(value, name, minimum, maximum)


def _same_scope(a, b):
    return a.collection_id == b.collection_id and a.chat_id == b.chat_id


def _record(row, collection_id, chat_id, state_revision):
    _keys(row, _RECORD_KEYS, 'run record')
    ref = BackfillRunRef.from_dict(row['ref'])
    request = BackfillStartRequest.from_dict(row['request'])
    _require(ref.collection_id == collection_id and ref.chat_id == chat_id, 'run scope differs from key')
    _require((request.collection_id, request.chat_id, request.run_id) ==
             (ref.collection_id, ref.chat_id, ref.run_id), 'request differs from run')
    prior = request.expected_predecessor
    if ref.generation == 1:
        _require(prior is None, 'initial generation has predecessor')
    else:
        _require(prior is not None and _same_scope(ref, prior) and
                 prior.generation == ref.generation - 1, 'generation does not follow predecessor')
    created = _date(row['created_at'])
    _keys(row['window'], ('start_date', 'end_date'), 'resolved window')
    window = _HistoryWindow(_date(row['window']['start_date']), _date(row['window']['end_date']))
    _require(window.end_date <= created, 'historical window ends after creation')
    if request.last_days is not None:
        _require(window.end_date == created and
                 window.end_date - window.start_date == timedelta(days=request.last_days),
                 'relative input differs from resolved window')
    else:
        _require(window.start_date == request.start_date and window.end_date == request.end_date,
                 'explicit input differs from resolved window')
    created + _pause_delta(request.pause_seconds)  # refuse unrepresentable accepted policy
    after = _number(row['after_id'], 'after_id', request.after_id, MAX_MESSAGE_ID)
    control_revision = _number(row['control_revision'], 'control_revision')
    _require(state_revision >= ref.generation + control_revision, 'revision precedes recorded changes')
    intent = _choice(row['operator_intent'], ('active', 'paused', 'cancelled', 'abandoned'), 'operator intent')
    terminal = row['terminal_outcome']
    if terminal is not None:
        _choice(terminal, ('completed', 'cancelled', 'abandoned'), 'terminal outcome')
    if terminal in ('cancelled', 'abandoned'):
        _require(intent == terminal, 'terminal outcome differs from operator intent')
    else:
        _require(intent in ('active', 'paused'), 'stopped intent lacks corresponding outcome')

    ack = row['last_ack']
    if ack is not None:
        _keys(ack, ('batch_id', 'next_after_id', 'observed_at'), 'latest acknowledgment')
        _hash(ack['batch_id'])
        _require(_number(ack['next_after_id'], maximum=MAX_MESSAGE_ID) == after, 'ack differs from cursor')
        _date(ack['observed_at'])
    _require((after > request.after_id) == (ack is not None), 'cursor lacks acceptance evidence')

    pending = None
    if row['pending'] is not None:
        pending = MessageBatch(row['pending'])
        _require(bool(pending.messages) and pending.chat_id == chat_id and pending.after_id == after
                 and pending.media_mode == request.media_mode, 'pending observation differs from run')
        _require(ack is None or pending.batch_id != ack['batch_id'], 'pending was already accepted')
        for record in pending.messages:
            _require(record['date'] is not None and window.contains(_date(record['date'])),
                     'pending record outside declared window')

    attempt = row['attempt']
    if attempt is not None:
        _keys(attempt, ('attempt_id', 'after_id', 'control_revision', 'admitted_at'), 'attempt')
        _token(attempt['attempt_id'], 'attempt_id')
        _require(_number(attempt['after_id'], maximum=MAX_MESSAGE_ID) == after, 'attempt cursor differs')
        _require(_number(attempt['control_revision']) <= control_revision, 'attempt control from future')
        _date(attempt['admitted_at'])
        _require(pending is None and row['exhaustion'] is None and row['abandoned'] is None,
                 'unresolved attempt conflicts with settled output')
        _require(terminal in (None, 'cancelled'), 'terminal run has an unresolved attempt')

    abandoned = row['abandoned']
    if abandoned is not None:
        _keys(abandoned, ('batch_id', 'next_after_id', 'observed_at'), 'abandoned delivery')
        if abandoned['batch_id'] is not None:
            _hash(abandoned['batch_id'])
        abandoned_next = _number(abandoned['next_after_id'], minimum=after, maximum=MAX_MESSAGE_ID)
        _require((abandoned_next > after) == (abandoned['batch_id'] is not None), 'abandoned scope differs')
        _date(abandoned['observed_at'])
        _require(pending is None and attempt is None and terminal in ('cancelled', 'abandoned'),
                 'abandonment did not retire the obligation')
    if terminal == 'abandoned':
        _require(abandoned is not None, 'abandoned run lacks explicit withdrawal')

    end = row['exhaustion']
    if end is not None:
        _keys(end, ('attempt_id', 'after_id', 'next_after_id', 'observed_at'), 'source exhaustion')
        _token(end['attempt_id'], 'exhaustion attempt_id')
        start = _number(end['after_id'], minimum=request.after_id, maximum=MAX_MESSAGE_ID)
        following = _number(end['next_after_id'], minimum=start, maximum=MAX_MESSAGE_ID)
        _date(end['observed_at'])
        _require(start <= after, 'exhaustion starts after accepted cursor')
        target = (pending.next_after_id if pending is not None else
                  int(abandoned['next_after_id']) if abandoned is not None else after)
        _require(following == target and attempt is None, 'exhaustion differs from current obligation')
        if pending is not None:
            _require(start == after and pending.stop_reason == 'end', 'pending does not establish end')
    if pending is not None:
        _require((pending.stop_reason == 'end') == (end is not None), 'pending/end evidence disagree')
    if terminal == 'completed':
        _require(end is not None and pending is None and attempt is None and abandoned is None,
                 'completion lacks fulfilled exhaustion')
    if end is not None and pending is None and attempt is None and abandoned is None:
        _require(terminal in ('completed', 'cancelled'), 'fulfilled exhaustion has no terminal outcome')
    if terminal == 'abandoned' and end is not None:
        _require(abandoned['batch_id'] is not None, 'abandonment replaced an already fulfilled end')

    control = row['last_control']
    _require((control_revision > 0) == (control is not None), 'control revision lacks recognition')
    if control is not None:
        _keys(control, ('command_id', 'action', 'expected_revision', 'accepted_revision', 'state_revision'),
              'latest control')
        _token(control['command_id'], 'control command_id')
        action = _choice(control['action'], ('pause', 'resume', 'cancel', 'abandon'), 'control action')
        expected = _number(control['expected_revision'])
        _require(_number(control['accepted_revision'], minimum=1) == expected + 1 == control_revision,
                 'control revision chain differs')
        _require(control_revision < _number(control['state_revision'], minimum=1) <= state_revision,
                 'control has invalid state revision')
        _require((action == 'pause' and intent == 'paused') or
                 (action == 'resume' and intent == 'active') or
                 (action == 'cancel' and terminal == 'cancelled' and abandoned is None) or
                 (action == 'abandon' and abandoned is not None), 'control disagrees with facts')
    elif intent != 'active' or terminal in ('cancelled', 'abandoned'):
        raise ValueError('operator decision has no command')

    pacing = row['pacing']
    recovery = row['last_recovery']
    if recovery is not None:
        _keys(recovery, ('command_id', 'attempt_id', 'expected_control_revision', 'state_revision',
                         'recovered_at'), 'latest recovery')
        _token(recovery['command_id'], 'recovery command_id')
        _token(recovery['attempt_id'], 'recovered attempt_id')
        _require(_number(recovery['expected_control_revision']) <= control_revision, 'recovery control from future')
        _require(1 < _number(recovery['state_revision'], minimum=1) <= state_revision, 'recovery revision from future')
        _date(recovery['recovered_at'])
        _require(pacing is not None and recovery['attempt_id'] == pacing.get('attempt_id'),
                 'recovery differs from pacing context')
    if pacing is not None:
        _keys(pacing, ('attempt_id', 'ended_at', 'not_before', 'clock_uncertain'), 'pacing')
        _token(pacing['attempt_id'], 'pacing attempt_id')
        _require(type(pacing['clock_uncertain']) is bool, 'invalid clock uncertainty')
        ended = _date(pacing['ended_at'], nullable=True)
        deadline = _date(pacing['not_before'], nullable=True)
        if not pacing['clock_uncertain']:
            anchor = ended if ended is not None else _date(recovery['recovered_at']) if recovery else None
            _require(anchor is not None and deadline is not None, 'known pacing lacks clock evidence')
            _require(deadline >= anchor + _pause_delta(request.pause_seconds), 'pacing is shorter than policy')
        if end is not None:
            _require(pacing['attempt_id'] == end['attempt_id'], 'end/pacing attempt differs')
        if attempt is not None:
            _require(attempt['attempt_id'] != pacing['attempt_id'], 'settled attempt is still unresolved')
    _require((pending is None and end is None and recovery is None) or pacing is not None,
             'settled source result lacks pacing evidence')

    failure = row['last_failure']
    if failure is not None:
        _keys(failure, ('category', 'error_type', 'observed_at', 'retry_at', 'account_id'), 'source failure')
        _choice(failure['category'], ('budget', 'source', 'storage', 'clock', 'media'), 'failure category')
        _require(type(failure['error_type']) is str and
                 re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', failure['error_type']) is not None,
                 'failure type must be a class name, not error text')
        _date(failure['observed_at'])
        _date(failure['retry_at'], nullable=True)
        if failure['account_id'] is not None:
            _number(failure['account_id'], minimum=1)
    return ref, request


def initial_record(request, generation, created, window):
    ref = BackfillRunRef(request.collection_id, request.chat_id, generation, request.run_id)
    return dict(ref=ref.to_dict(), request=request.to_dict(), created_at=_encode_date(created),
                window=window.to_dict(), after_id=str(request.after_id), control_revision='0',
                operator_intent='active', terminal_outcome=None, pending=None, last_ack=None,
                exhaustion=None, attempt=None, pacing=None, last_control=None, last_recovery=None,
                last_failure=None, abandoned=None)


@dataclass(frozen=True, init=False)
class _BackfillState:
    _encoded: str = field(repr=False)

    def __init__(self, document):
        try:
            value = copy.deepcopy(document)
            _keys(value, ('schema', 'version', 'collection_id', 'chat_id', 'state_revision',
                          'current', 'previous'), 'lifecycle state')
            _require(value['schema'] == SCHEMA and type(value['version']) is int
                     and value['version'] == VERSION, 'unsupported lifecycle schema/version')
            collection = _token(value['collection_id'], 'collection_id')
            chat = _number(value['chat_id'], 'chat_id', MIN_LONG, -1)
            revision = _number(value['state_revision'], 'state_revision', 1)
            ref, request = _record(value['current'], collection, chat, revision)
            previous = value['previous']
            if previous is None:
                _require(ref.generation == 1, 'successor lacks retained predecessor')
            else:
                prior, _ = _record(previous, collection, chat, revision)
                _require(request.expected_predecessor == prior and prior.generation + 1 == ref.generation,
                         'retained predecessor differs')
                _require(previous['terminal_outcome'] is not None and previous['pending'] is None
                         and previous['attempt'] is None, 'predecessor has unsettled work')
            object.__setattr__(self, '_encoded', _canonical(value))
        except BackfillStateError:
            raise
        except Exception as error:
            raise BackfillStateError('Invalid backfill state ({})'.format(type(error).__name__)) from None

    @classmethod
    def from_json(cls, data, collection_id, chat_id):
        try:
            result = cls(_json_load(data))
            value = result.to_dict()
            _require(value['collection_id'] == collection_id and int(value['chat_id']) == chat_id,
                     'state scope differs from backend key')
            return result
        except BackfillStateError:
            raise
        except Exception as error:
            raise BackfillStateError('Invalid backfill state ({})'.format(type(error).__name__)) from None

    def to_json(self):
        return self._encoded

    def to_dict(self):
        return _json_load(self._encoded)

    def status(self, previous=False):
        value = self.to_dict()
        row = value['previous'] if previous else value['current']
        if row is None:
            raise BackfillStateError('No retained previous record')
        request = BackfillStartRequest.from_dict(row['request'])
        pending = row['pending']
        pacing = row['pacing']
        failure = row['last_failure']
        return BackfillStatus(
            run=BackfillRunRef.from_dict(row['ref']), state_revision=int(value['state_revision']),
            destination_id=request.destination_id, origin=request.origin,
            initial_after_id=request.after_id, after_id=int(row['after_id']),
            start_date=_date(row['window']['start_date']), end_date=_date(row['window']['end_date']),
            last_days=request.last_days, created_at=_date(row['created_at']), media_mode=request.media_mode,
            batch_size=request.batch_size, pause_seconds=request.pause_seconds,
            control_revision=int(row['control_revision']), operator_intent=row['operator_intent'],
            terminal_outcome=row['terminal_outcome'], pending_batch_id=pending['batch_id'] if pending else None,
            pending_message_count=len(pending['messages']) if pending else 0,
            pending_next_after_id=int(pending['next_after_id']) if pending else None,
            source_exhausted=row['exhaustion'] is not None,
            attempt_id=row['attempt']['attempt_id'] if row['attempt'] else None,
            pacing_not_before=_date(pacing['not_before'], nullable=True) if pacing else None,
            clock_uncertain=pacing['clock_uncertain'] if pacing else False,
            last_acked_batch_id=row['last_ack']['batch_id'] if row['last_ack'] else None,
            last_control_id=row['last_control']['command_id'] if row['last_control'] else None,
            last_failure_kind=failure['category'] if failure else None,
            last_failure_type=failure['error_type'] if failure else None,
            last_failure_at=_date(failure['observed_at']) if failure else None,
            last_failure_retry_at=_date(failure['retry_at'], nullable=True) if failure else None,
            last_failure_account_id=int(failure['account_id']) if failure and failure['account_id'] else None,
            delivery_abandoned=row['abandoned'] is not None, history_limited=previous,
        )
