"""Portable captured input and deterministic, descriptive raw-message samples."""

from dataclasses import dataclass, field
from datetime import timedelta
import hashlib
import json

from telethon.tl import types

from .group_operations import GroupMetadata, GroupReferenceError, _canonical as _peer_id, _parse_target
from .history_window import _HistoryWindow, _decode_date, _encode_date
from .message_batch import (
    BatchFormatError, MAX_MESSAGE_ID, MAX_LONG, _canonical, _digest, _identifier,
    _invalid_constant, _json_pairs, _keys, _text, _validate_record,
)


MAX_CAPTURE_MESSAGES = 10000
MAX_CAPTURE_REQUESTS = 10000
DEFAULT_LOAD_BYTES = 64 * 1024 * 1024
CAPTURE_ALGORITHM = 'utc-day-round-robin/v1'
SAMPLE_ALGORITHM = 'utc-day-even-rank/v1'
_CAPTURE_KEYS = frozenset({
    'schema', 'version', 'capture_id', 'algorithm', 'account_id', 'target', 'group',
    'start_date', 'end_date', 'collection_started_at', 'collection_finished_at',
    'limits', 'stop_reason', 'buckets',
})
_GROUP_KEYS = frozenset({'id', 'peer_id', 'title', 'username', 'kind', 'participants_count'})
_BUCKET_KEYS = frozenset({'start_date', 'end_date', 'requests', 'pages', 'scanned_messages',
                         'unavailable_messages', 'end_reason', 'records'})
_STOPS = ('finished', 'message_limit', 'request_limit', 'error', 'cancelled')


class HistorySampleError(ValueError):
    """Local capture/selection/format refusal, not a Telegram health event."""

    def __init__(self, message):
        super().__init__(message)
        self.__suppress_context__ = True


def _number(value, name, minimum=0, maximum=MAX_CAPTURE_MESSAGES):
    if type(value) is not int or not minimum <= value <= maximum:
        raise HistorySampleError('{} must be an integer from {} to {}'.format(name, minimum, maximum))
    return value


def _limits(max_messages, max_requests):
    _number(max_messages, 'max_messages', 1)
    _number(max_requests, 'max_requests', 1, MAX_CAPTURE_REQUESTS)


def _days(window):
    current = window.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    result = []
    while current < window.end_date:
        following = current + timedelta(days=1)
        result.append(_HistoryWindow(max(current, window.start_date), min(following, window.end_date)))
        current = following
    return result


def _identity(document, name):
    body = {key: value for key, value in document.items() if key != name}
    return hashlib.sha256(_canonical(body).encode('utf-8')).hexdigest()


def _metadata(account_id, target, group):
    _number(account_id, 'account_id', 1, MAX_LONG)
    _keys(group, _GROUP_KEYS, 'capture.group')
    _number(group['id'], 'group.id', 1, MAX_LONG)
    if group['kind'] not in ('group', 'megagroup', 'channel'):
        raise HistorySampleError('Unsupported capture group kind')
    namespace = types.PeerChat if group['kind'] == 'group' else types.PeerChannel
    if type(group['peer_id']) is not int or _peer_id(group['id'], namespace) != group['peer_id']:
        raise HistorySampleError('Capture group identity is inconsistent')
    _text(group['title'], 'group.title', nullable=False)
    _text(group['username'], 'group.username')
    if group['participants_count'] is not None:
        _number(group['participants_count'], 'group.participants_count', 0, MAX_LONG)
    if type(target) is str and target.startswith('invite:'):
        _digest(target[7:], 'capture.target invite label')
    else:
        try:
            if _parse_target(target).label != target:
                raise GroupReferenceError()
        except GroupReferenceError:
            raise HistorySampleError('Capture target must be a normalized safe reference') from None


def _complete(bucket):
    return bucket['end_reason'] is not None and bucket['unavailable_messages'] == 0


def _summary(document):
    buckets = document['buckets']
    result = {name: sum(b[name] for b in buckets)
              for name in ('requests', 'pages', 'scanned_messages', 'unavailable_messages')}
    result.update(stop_reason=document['stop_reason'],
        coverage_complete=document['stop_reason'] == 'finished' and all(map(_complete, buckets)),
        collection_started_at=document['collection_started_at'],
        collection_finished_at=document['collection_finished_at'], limits=dict(document['limits']))
    return result


def _validate(document):
    _keys(document, _CAPTURE_KEYS, 'history capture')
    if (document['schema'] != 'tgdata.history-capture' or type(document['version']) is not int
            or document['version'] != 1 or document['algorithm'] != CAPTURE_ALGORITHM):
        raise HistorySampleError('Unsupported history capture schema, version or algorithm')
    _digest(document['capture_id'], 'capture_id')
    _metadata(document['account_id'], document['target'], document['group'])
    window = _HistoryWindow(_decode_date(document['start_date']), _decode_date(document['end_date']))
    started = _decode_date(document['collection_started_at'])
    _decode_date(document['collection_finished_at'])  # Local wall clocks need not be monotone.
    if window.end_date > started:
        raise HistorySampleError('Capture window ends after invocation time')
    _keys(document['limits'], frozenset({'max_messages', 'max_requests'}), 'capture.limits')
    max_messages, max_requests = document['limits']['max_messages'], document['limits']['max_requests']
    _limits(max_messages, max_requests)
    if document['stop_reason'] not in _STOPS:
        raise HistorySampleError('Unsupported capture stop reason')
    buckets = document['buckets']
    windows = _days(window)
    if type(buckets) is not list or len(buckets) != len(windows):
        raise HistorySampleError('Capture must contain exactly its requested UTC day buckets')
    seen = set()
    for bucket, day in zip(buckets, windows):
        _keys(bucket, _BUCKET_KEYS, 'capture bucket')
        if (bucket['start_date'], bucket['end_date']) != (_encode_date(day.start_date), _encode_date(day.end_date)):
            raise HistorySampleError('Capture bucket does not match its UTC day intersection')
        requests = _number(bucket['requests'], 'bucket.requests', 0, max_requests)
        pages = _number(bucket['pages'], 'bucket.pages', 0, requests)
        scanned = _number(bucket['scanned_messages'], 'bucket.scanned_messages', 0, max_messages)
        unknown = _number(bucket['unavailable_messages'], 'bucket.unavailable_messages', 0, scanned)
        records = bucket['records']
        reason = bucket['end_reason']
        if reason not in (None, 'window_start', 'history_end'):
            raise HistorySampleError('Invalid bucket end evidence')
        if type(records) is not list or len(records) > scanned-unknown or scanned > pages*100:
            raise HistorySampleError('Capture records and source counts are inconsistent')
        if pages == 0 and (scanned or records or reason is not None):
            raise HistorySampleError('Unaccepted bucket cannot contain source evidence')
        if reason is not None and (pages == 0 or requests != pages):
            raise HistorySampleError('Terminal bucket requires accepted source evidence')
        if pages and scanned == 0 and reason != 'history_end':
            raise HistorySampleError('Empty source evidence must terminate the bucket')
        if reason == 'window_start' and scanned-unknown <= len(records):
            raise HistorySampleError('Start-boundary evidence requires an excluded dated row')
        previous = None
        for record in records:
            ident = _validate_record(record, 'references')
            date = _decode_date(record['date'])
            key = date, ident
            if not day.contains(date) or (previous is not None and key <= previous):
                raise HistorySampleError('Capture records must be ordered inside their day')
            if ident in seen:
                raise HistorySampleError('Capture contains a repeated message ID')
            seen.add(ident)
            previous = key
    summary = _summary(document)
    if summary['scanned_messages'] > max_messages or summary['requests'] > max_requests:
        raise HistorySampleError('Capture exceeds its source limits')
    gap = summary['requests']-summary['pages']
    reason = document['stop_reason']
    unfinished = any(b['end_reason'] is None for b in buckets)
    if gap > (1 if reason in ('error', 'cancelled') else 0):
        raise HistorySampleError('Capture contains inconsistent request outcomes')
    if reason == 'finished' and unfinished:
        raise HistorySampleError('Finished capture has unresolved buckets')
    if reason == 'message_limit' and (not unfinished or summary['scanned_messages'] != max_messages):
        raise HistorySampleError('Message-limit capture requires an exhausted bound')
    if reason == 'request_limit' and (not unfinished or summary['requests'] != max_requests
                                      or summary['scanned_messages'] == max_messages):
        raise HistorySampleError('Request-limit capture requires an exhausted bound')
    if document['capture_id'] != _identity(document, 'capture_id'):
        raise HistorySampleError('Capture identity does not match its content')


def _ranks(n, k):
    if k == 0:
        return []
    if k == 1:
        return [(n-1)//2]
    return [j*(n-1)//(k-1) for j in range(k)]


def _quotas(capacities, size):
    total = sum(capacities)
    target = min(size, total)
    if target == 0:
        return [0]*len(capacities)
    if target == total:
        return list(capacities)
    low, high = 0, max(capacities)
    while low < high:
        level = (low+high+1)//2
        if sum(min(capacity, level) for capacity in capacities) <= target:
            low = level
        else:
            high = level-1
    result = [min(capacity, low) for capacity in capacities]
    available = [i for i, capacity in enumerate(capacities) if capacity > result[i]]
    for index in _ranks(len(available), target-sum(result)):
        result[available[index]] += 1
    return result


def _eligible(value, ordinary):
    if value is None:
        return set(ordinary)
    if type(value) not in (list, tuple, set, frozenset) or len(value) > MAX_CAPTURE_MESSAGES:
        raise HistorySampleError('eligible_ids must be a concrete collection of at most 10000 IDs')
    result = set()
    for item in value:
        if type(item) is int:
            _number(item, 'eligible ID', 1, MAX_MESSAGE_ID)
            item = str(item)
        else:
            _identifier(item, 'eligible ID', 1, MAX_MESSAGE_ID)
        if item not in ordinary:
            raise HistorySampleError('eligible_ids contains an unknown or service message ID')
        result.add(item)
    return result


@dataclass(frozen=True, init=False)
class HistoryCapture:
    """Immutable observed input; replay locally, never acknowledge from its IDs."""

    _encoded: str = field(repr=False)

    def __init__(self, document):
        try:
            encoded = _canonical(document)
            owned = json.loads(encoded)
            _validate(owned)
        except BatchFormatError as error:
            raise HistorySampleError(str(error)) from None
        object.__setattr__(self, '_encoded', encoded)

    @classmethod
    def _from_document(cls, document):
        document = dict(document)
        document['capture_id'] = _identity(document, 'capture_id')
        return cls(document)

    @classmethod
    def from_json(cls, data, *, max_bytes=DEFAULT_LOAD_BYTES):
        _number(max_bytes, 'max_bytes', 1, MAX_LONG)
        if type(data) not in (str, bytes):
            raise HistorySampleError('Capture JSON must be text or UTF-8 bytes')
        try:
            if len(data) > max_bytes or (isinstance(data, str) and len(data.encode('utf-8')) > max_bytes):
                raise HistorySampleError('Capture JSON exceeds max_bytes')
            value = json.loads(data, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
        except (BatchFormatError, ValueError, UnicodeError, RecursionError) as error:
            if isinstance(error, HistorySampleError):
                raise
            raise HistorySampleError('Invalid capture JSON') from None
        return cls(value)

    def to_json(self):
        return self._encoded

    def to_dict(self):
        return json.loads(self._encoded)

    @property
    def capture_id(self):
        return self.to_dict()['capture_id']

    @property
    def account_id(self):
        return self.to_dict()['account_id']

    @property
    def group(self):
        return GroupMetadata(**self.to_dict()['group'])

    @property
    def start_date(self):
        return _decode_date(self.to_dict()['start_date'])

    @property
    def end_date(self):
        return _decode_date(self.to_dict()['end_date'])

    @property
    def messages(self):
        return [record for bucket in self.to_dict()['buckets'] for record in bucket['records']]

    @property
    def buckets(self):
        return self.to_dict()['buckets']

    @property
    def stop_reason(self):
        return self.to_dict()['stop_reason']

    @property
    def coverage(self):
        return _summary(self.to_dict())

    @property
    def coverage_complete(self):
        return self.coverage['coverage_complete']

    def sample(self, *, size=300, eligible_ids=None):
        """Select raw messages by UTC-day quotas and even ranks, without I/O."""
        _number(size, 'size')
        document = self.to_dict()
        ordinary = {r['id']: r for b in document['buckets'] for r in b['records'] if r['kind'] == 'message'}
        try:
            eligible = _eligible(eligible_ids, ordinary)
        except BatchFormatError as error:
            raise HistorySampleError(str(error)) from None
        candidates = [[r for r in b['records'] if r['id'] in eligible] for b in document['buckets']]
        quotas = _quotas([len(rows) for rows in candidates], size)
        selected, buckets = [], []
        for bucket, rows, quota in zip(document['buckets'], candidates, quotas):
            selected.extend(rows[index] for index in _ranks(len(rows), quota))
            total = sum(r['kind'] == 'message' for r in bucket['records'])
            info = {key: value for key, value in bucket.items() if key != 'records'}
            info.update(visited=bucket['requests'] > 0, coverage_complete=_complete(bucket),
                        ordinary_messages=total, service_messages=len(bucket['records'])-total,
                        eligible_messages=len(rows), selected_messages=quota,
                        excluded_messages=total-len(rows), omitted_messages=len(rows)-quota)
            buckets.append(info)
        selected_ids = {r['id'] for r in selected}
        selected_groups = {r['grouped_id'] for r in selected if r['grouped_id'] is not None}
        groups = {key: [] for key in selected_groups}
        for record in ordinary.values():
            if record['grouped_id'] in groups:
                groups[record['grouped_id']].append(record['id'])
        albums = []
        for key in sorted(groups, key=int):
            ids = sorted(groups[key], key=int)
            albums.append(dict(grouped_id=key, membership='unconfirmed', captured_member_ids=ids,
                selected_member_ids=[ident for ident in ids if ident in selected_ids],
                omitted_member_ids=[ident for ident in ids if ident not in selected_ids]))
        output = dict(schema='tgdata.history-sample', version=1, algorithm=SAMPLE_ALGORITHM,
            sampling_unit='raw_message', capture_id=document['capture_id'],
            account_id=document['account_id'], target=document['target'], group=document['group'],
            start_date=document['start_date'], end_date=document['end_date'],
            policy=dict(size=size, eligible_ids=sorted(eligible, key=int)),
            source=_summary(document), buckets=buckets, messages=selected, albums=albums)
        return HistorySample._from_document(output)


@dataclass(frozen=True, init=False)
class HistorySample:
    """Immutable selected output; reproduce it from its capture and policy."""

    _encoded: str = field(repr=False)

    def __init__(self):
        raise HistorySampleError('Create samples with HistoryCapture.sample')

    @classmethod
    def _from_document(cls, document):
        document = dict(document)
        document['sample_id'] = _identity(document, 'sample_id')
        instance = object.__new__(cls)
        object.__setattr__(instance, '_encoded', _canonical(document))
        return instance

    def to_json(self):
        return self._encoded

    def to_dict(self):
        return json.loads(self._encoded)

    @property
    def sample_id(self):
        return self.to_dict()['sample_id']

    @property
    def capture_id(self):
        return self.to_dict()['capture_id']

    @property
    def messages(self):
        return self.to_dict()['messages']

    @property
    def selected_ids(self):
        return tuple(int(r['id']) for r in self.messages)

    @property
    def coverage_complete(self):
        return self.to_dict()['source']['coverage_complete']
