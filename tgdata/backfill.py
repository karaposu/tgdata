"""Typed values for the staged backfill lifecycle (no Telegram operations)."""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Context, Decimal, ROUND_CEILING, localcontext
import json
import math
import numbers
import operator
import re
import unicodedata
from typing import Optional

from .history_window import _HistoryWindow, _decode_date, _encode_date, _utc
from .message_batch import MessageBatch, BatchFormatError, MAX_BATCH_MESSAGES, MAX_MESSAGE_ID, MAX_LONG, MIN_LONG


class BackfillError(RuntimeError):
    """A local lifecycle error, never itself Telegram health evidence."""

    def __init__(self, message):
        super().__init__(message)
        self.read_error = None
        self.__suppress_context__ = True


class BackfillConfigurationError(BackfillError):
    pass


class BackfillConflictError(BackfillError):
    pass


class BackfillUnknownRun(BackfillError):
    pass


class BackfillUnknownCommand(BackfillError):
    pass


class BackfillStateError(BackfillError):
    pass


class BackfillStorageError(BackfillError):
    pass


class BackfillUnknownReceipt(BackfillError):
    pass


class BackfillRecoveryRequired(BackfillError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class BackfillMediaError(BackfillError):
    pass


class BackfillClockError(BackfillConfigurationError):
    pass


def _integer(value, name, minimum=0, maximum=MAX_LONG):
    try:
        if isinstance(value, bool):
            raise TypeError
        result = int(operator.index(value))
        if not minimum <= result <= maximum:
            raise ValueError
        return result
    except (TypeError, ValueError, OverflowError):
        raise BackfillConfigurationError('{} must be an integer in {}..{}'.format(
            name, minimum, maximum)) from None


def _wire_integer(value, name, minimum=0, maximum=MAX_LONG):
    if (type(value) is not str or len(value) > 20
            or re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value) is None):
        raise BackfillConfigurationError('{} must be a canonical decimal string'.format(name))
    result = _integer(int(value), name, minimum, maximum)
    if str(result) != value:
        raise BackfillConfigurationError('{} is not canonical'.format(name))
    return result


def _token(value, name):
    try:
        if (type(value) is not str or not value or len(value.encode('utf-8')) > 256
                or any(c.isspace() or unicodedata.category(c).startswith('C') for c in value)):
            raise ValueError
    except (ValueError, UnicodeError):
        raise BackfillConfigurationError('{} must be a nonempty identity token (max 256 UTF-8 bytes)'.format(name)) from None
    return value


def _keys(value, expected, name):
    if type(value) is not dict or value.keys() != set(expected):
        raise BackfillConfigurationError('{} has missing or unsupported fields'.format(name))


def _choice(value, choices, name):
    if type(value) is not str or value not in choices:
        raise BackfillConfigurationError('{} has an unsupported value'.format(name))
    return value


def _seconds(value):
    try:
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError
        result = float(value)
        if not math.isfinite(result) or result < 0:
            raise ValueError
        result = result if result else 0.0
        _pause_delta(result)
        return result
    except (ValueError, TypeError, OverflowError):
        raise BackfillConfigurationError('pause_seconds must be finite, nonnegative and representable') from None


def _pause_delta(seconds):
    # Datetime stores whole microseconds. A minimum duration must never round down.
    # Do not inherit an application's unrelated Decimal precision/rounding policy.
    with localcontext(Context(prec=50, Emin=-999999, Emax=999999)):
        micros = int((Decimal(str(seconds)) * 1000000).to_integral_value(rounding=ROUND_CEILING))
    return timedelta(microseconds=micros)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def _nonfinite(_):
    raise ValueError('nonfinite JSON value')


def _json_load(data):
    if type(data) is not str:
        raise TypeError('state must be text')
    data.encode('utf-8')
    return json.loads(data, object_pairs_hook=_unique_pairs, parse_constant=_nonfinite)


def _canonical(value):
    result = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    result.encode('utf-8')
    return result


@dataclass(frozen=True)
class BackfillRunRef:
    collection_id: str
    chat_id: int
    generation: int
    run_id: str

    def __post_init__(self):
        object.__setattr__(self, 'collection_id', _token(self.collection_id, 'collection_id'))
        object.__setattr__(self, 'chat_id', _integer(self.chat_id, 'chat_id', MIN_LONG, -1))
        object.__setattr__(self, 'generation', _integer(self.generation, 'generation', 1))
        object.__setattr__(self, 'run_id', _token(self.run_id, 'run_id'))

    def to_dict(self):
        return dict(collection_id=self.collection_id, chat_id=str(self.chat_id),
                    generation=str(self.generation), run_id=self.run_id)

    @classmethod
    def from_dict(cls, value):
        _keys(value, ('collection_id', 'chat_id', 'generation', 'run_id'), 'run reference')
        return cls(value['collection_id'], _wire_integer(value['chat_id'], 'chat_id', MIN_LONG, -1),
                   _wire_integer(value['generation'], 'generation', 1), value['run_id'])


@dataclass(frozen=True)
class BackfillStartRequest:
    collection_id: str
    chat_id: int
    run_id: str
    destination_id: str
    pause_seconds: float
    expected_predecessor: Optional[BackfillRunRef]
    origin: str = 'fresh'
    after_id: int = 0
    media_mode: str = 'references'
    batch_size: int = 200
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    last_days: Optional[int] = None

    def __post_init__(self):
        for name in ('collection_id', 'run_id', 'destination_id'):
            object.__setattr__(self, name, _token(getattr(self, name), name))
        object.__setattr__(self, 'chat_id', _integer(self.chat_id, 'chat_id', MIN_LONG, -1))
        object.__setattr__(self, 'after_id', _integer(self.after_id, 'after_id', 0, MAX_MESSAGE_ID))
        object.__setattr__(self, 'batch_size', _integer(self.batch_size, 'batch_size', 1, MAX_BATCH_MESSAGES))
        object.__setattr__(self, 'pause_seconds', _seconds(self.pause_seconds))
        _choice(self.origin, ('fresh', 'imported'), 'origin')
        _choice(self.media_mode, ('references', 'download'), 'media_mode')
        if self.origin == 'fresh' and self.after_id:
            raise BackfillConfigurationError('fresh origin requires after_id=0')
        previous = self.expected_predecessor
        if previous is not None:
            if not isinstance(previous, BackfillRunRef):
                raise BackfillConfigurationError('expected_predecessor must be a RunRef or None')
            if (previous.collection_id != self.collection_id or previous.chat_id != self.chat_id
                    or previous.run_id == self.run_id):
                raise BackfillConfigurationError('predecessor must be a different run in this group/collection')
        if self.last_days is not None:
            if self.start_date is not None or self.end_date is not None:
                raise BackfillConfigurationError('use explicit dates or last_days, not both')
            object.__setattr__(self, 'last_days', _integer(self.last_days, 'last_days', 1, MAX_MESSAGE_ID))
        else:
            try:
                window = _HistoryWindow.from_dates(self.start_date, self.end_date)
                if window is None:
                    raise ValueError
                object.__setattr__(self, 'start_date', window.start_date)
                object.__setattr__(self, 'end_date', window.end_date)
            except (BatchFormatError, ValueError, OverflowError):
                raise BackfillConfigurationError('a supported fixed window or last_days is required') from None

    def to_dict(self):
        window = ({'kind': 'relative', 'last_days': str(self.last_days)} if self.last_days is not None
                  else {'kind': 'explicit', 'start_date': _encode_date(self.start_date),
                        'end_date': _encode_date(self.end_date)})
        return dict(collection_id=self.collection_id, chat_id=str(self.chat_id), run_id=self.run_id,
                    destination_id=self.destination_id, pause_seconds=self.pause_seconds,
                    expected_predecessor=(self.expected_predecessor.to_dict() if self.expected_predecessor else None),
                    origin=self.origin, after_id=str(self.after_id), media_mode=self.media_mode,
                    batch_size=self.batch_size, window_input=window)

    @classmethod
    def from_dict(cls, value):
        _keys(value, ('collection_id', 'chat_id', 'run_id', 'destination_id', 'pause_seconds',
                      'expected_predecessor', 'origin', 'after_id', 'media_mode', 'batch_size',
                      'window_input'), 'start request')
        window = value['window_input']
        if type(window) is not dict:
            raise BackfillConfigurationError('window_input must be an object')
        try:
            if window.get('kind') == 'relative':
                _keys(window, ('kind', 'last_days'), 'relative window')
                dates = dict(last_days=_wire_integer(window['last_days'], 'last_days', 1, MAX_MESSAGE_ID))
            else:
                _keys(window, ('kind', 'start_date', 'end_date'), 'explicit window')
                _choice(window['kind'], ('explicit',), 'window kind')
                dates = dict(start_date=_decode_date(window['start_date']), end_date=_decode_date(window['end_date']))
        except BatchFormatError:
            raise BackfillConfigurationError('window_input dates must be canonical UTC') from None
        previous = value['expected_predecessor']
        if type(value['batch_size']) is not int:
            raise BackfillConfigurationError('stored batch_size must be an integer')
        return cls(value['collection_id'], _wire_integer(value['chat_id'], 'chat_id', MIN_LONG, -1),
                   value['run_id'], value['destination_id'], value['pause_seconds'],
                   BackfillRunRef.from_dict(previous) if previous is not None else None,
                   origin=value['origin'], after_id=_wire_integer(value['after_id'], 'after_id', 0, MAX_MESSAGE_ID),
                   media_mode=value['media_mode'], batch_size=value['batch_size'], **dates)


@dataclass(frozen=True)
class BackfillStatus:
    """Validated, content-free snapshot produced by the engine, not a readiness grant."""

    run: BackfillRunRef
    state_revision: int
    destination_id: str
    origin: str
    initial_after_id: int
    after_id: int
    start_date: datetime
    end_date: datetime
    last_days: Optional[int]
    created_at: datetime
    media_mode: str
    batch_size: int
    pause_seconds: float
    control_revision: int
    operator_intent: str
    terminal_outcome: Optional[str]
    pending_batch_id: Optional[str]
    pending_message_count: int
    pending_next_after_id: Optional[int]
    source_exhausted: bool
    attempt_id: Optional[str]
    pacing_not_before: Optional[datetime]
    clock_uncertain: bool
    last_acked_batch_id: Optional[str]
    last_control_id: Optional[str]
    last_failure_kind: Optional[str]
    last_failure_type: Optional[str]
    last_failure_at: Optional[datetime]
    last_failure_retry_at: Optional[datetime]
    last_failure_account_id: Optional[int]
    delivery_abandoned: bool
    history_limited: bool
    pacing_attempt_id: Optional[str] = None
    pacing_ended_at: Optional[datetime] = None
    last_recovery_id: Optional[str] = None
    last_recovered_attempt_id: Optional[str] = None
    last_recovery_at: Optional[datetime] = None

    def to_dict(self):
        result = asdict(self)
        result['run'] = self.run.to_dict()
        for name in ('state_revision', 'initial_after_id', 'after_id', 'control_revision',
                     'pending_next_after_id', 'last_failure_account_id'):
            if result[name] is not None:
                result[name] = str(result[name])
        for name in ('start_date', 'end_date', 'created_at', 'pacing_not_before',
                     'last_failure_at', 'last_failure_retry_at', 'pacing_ended_at',
                     'last_recovery_at'):
            if result[name] is not None:
                result[name] = _encode_date(result[name])
        return result


@dataclass(frozen=True)
class BackfillStartResult:
    applied: bool
    status: BackfillStatus

    def to_dict(self):
        return {'applied': self.applied, 'status': self.status.to_dict()}


@dataclass(frozen=True)
class BackfillRecoveryResult:
    command_id: str
    attempt_id: str
    applied: bool
    outcome: str
    status: BackfillStatus

    def __post_init__(self):
        _token(self.command_id, 'command_id')
        _token(self.attempt_id, 'attempt_id')
        _choice(self.outcome, ('recovered', 'settled'), 'recovery outcome')
        if type(self.applied) is not bool or not isinstance(self.status, BackfillStatus):
            raise BackfillConfigurationError('recovery result requires boolean applied and status')
        if self.outcome == 'recovered':
            if (self.status.last_recovery_id != self.command_id or
                    self.status.last_recovered_attempt_id != self.attempt_id):
                raise BackfillConfigurationError('recovery result differs from retained command')
        elif (self.applied or self.status.attempt_id is not None or
              self.status.pacing_attempt_id != self.attempt_id):
            raise BackfillConfigurationError('settled result requires the addressed source observation')

    def to_dict(self):
        return dict(command_id=self.command_id, attempt_id=self.attempt_id,
                    applied=self.applied, outcome=self.outcome, status=self.status.to_dict())


def _owned_ref(value):
    if not isinstance(value, BackfillRunRef):
        raise BackfillConfigurationError('a complete BackfillRunRef is required')
    return BackfillRunRef.from_dict(value.to_dict())


@dataclass(frozen=True)
class BackfillPrepareContext:
    run: BackfillRunRef
    expected_after_id: int
    expected_control_revision: int

    def __post_init__(self):
        object.__setattr__(self, 'run', _owned_ref(self.run))
        object.__setattr__(self, 'expected_after_id', _integer(
            self.expected_after_id, 'expected_after_id', 0, MAX_MESSAGE_ID))
        object.__setattr__(self, 'expected_control_revision', _integer(
            self.expected_control_revision, 'expected_control_revision'))

    def to_dict(self):
        return dict(run=self.run.to_dict(), expected_after_id=str(self.expected_after_id),
                    expected_control_revision=str(self.expected_control_revision))

    @classmethod
    def from_dict(cls, value):
        _keys(value, ('run', 'expected_after_id', 'expected_control_revision'), 'prepare context')
        return cls(BackfillRunRef.from_dict(value['run']),
                   _wire_integer(value['expected_after_id'], 'expected_after_id', 0, MAX_MESSAGE_ID),
                   _wire_integer(value['expected_control_revision'], 'expected_control_revision'))

    @classmethod
    def from_status(cls, status):
        if not isinstance(status, BackfillStatus):
            raise BackfillConfigurationError('prepare context requires BackfillStatus')
        return cls(status.run, status.after_id, status.control_revision)


@dataclass(frozen=True)
class BackfillDeliveryRef:
    run: BackfillRunRef
    destination_id: str
    batch_id: str

    def __post_init__(self):
        object.__setattr__(self, 'run', _owned_ref(self.run))
        object.__setattr__(self, 'destination_id', _token(self.destination_id, 'destination_id'))
        if type(self.batch_id) is not str or re.fullmatch('[0-9a-f]{64}', self.batch_id) is None:
            raise BackfillConfigurationError('batch_id must be a lowercase SHA-256 identifier')

    def to_dict(self):
        return dict(run=self.run.to_dict(), destination_id=self.destination_id, batch_id=self.batch_id)

    @classmethod
    def from_dict(cls, value):
        _keys(value, ('run', 'destination_id', 'batch_id'), 'delivery reference')
        return cls(BackfillRunRef.from_dict(value['run']), value['destination_id'], value['batch_id'])


@dataclass(frozen=True)
class BackfillTurn:
    status: BackfillStatus
    batch: Optional[MessageBatch] = None
    delivery: Optional[BackfillDeliveryRef] = None
    replayed: bool = False
    wait_seconds: Optional[float] = None

    def __post_init__(self):
        if not isinstance(self.status, BackfillStatus) or type(self.replayed) is not bool:
            raise BackfillConfigurationError('turn requires a status and boolean replay marker')
        if self.wait_seconds is not None:
            seconds = _seconds(self.wait_seconds)
            if (seconds <= 0 or self.batch is not None or self.delivery is not None or self.replayed
                    or self.status.pending_batch_id is not None or self.status.attempt_id is not None
                    or self.status.terminal_outcome is not None or self.status.operator_intent != 'active'
                    or self.status.clock_uncertain or self.status.pacing_not_before is None):
                raise BackfillConfigurationError('a pacing wait requires active quiescent nonterminal state')
            object.__setattr__(self, 'wait_seconds', seconds)
        if self.batch is None:
            if self.delivery is not None or self.status.pending_batch_id is not None or self.replayed:
                raise BackfillConfigurationError('a no-data turn cannot claim pending delivery')
            return
        if not isinstance(self.batch, MessageBatch) or not isinstance(self.delivery, BackfillDeliveryRef):
            raise BackfillConfigurationError('a data turn requires a batch and full delivery reference')
        batch = MessageBatch(self.batch.to_dict())
        delivery = BackfillDeliveryRef.from_dict(self.delivery.to_dict())
        value = batch.to_dict()
        if (delivery.run != self.status.run or delivery.destination_id != self.status.destination_id
                or delivery.batch_id != value['batch_id'] or self.status.pending_batch_id != value['batch_id']
                or int(value['chat_id']) != self.status.run.chat_id
                or int(value['after_id']) != self.status.after_id
                or value['media_mode'] != self.status.media_mode
                or int(value['next_after_id']) != self.status.pending_next_after_id
                or len(value['messages']) != self.status.pending_message_count):
            raise BackfillConfigurationError('turn data differs from its addressed pending status')
        object.__setattr__(self, 'batch', batch)
        object.__setattr__(self, 'delivery', delivery)

    def to_dict(self):
        return dict(status=self.status.to_dict(), batch=self.batch.to_dict() if self.batch else None,
                    delivery=self.delivery.to_dict() if self.delivery else None,
                    replayed=self.replayed, wait_seconds=self.wait_seconds)
