"""Strict plain-data protocol for the opt-in reading worker."""

from dataclasses import dataclass
from datetime import datetime
import json
import math
import re

from telethon.errors import AuthKeyError, RPCError, UnauthorizedError

from . import health
from .account_operation import AccountIdentityError
from .connection_engine import AuthRequiredError, ProxyConfigError, _BANNED
from .group_operations import GroupReferenceError, GroupResponseError, _parse_target
from .history_window import _HistoryWindow
from .join_budget import JoinBudgetError, JoinBudgetExceeded
from .message_batch import MessageBatch, MAX_LONG, MAX_MESSAGE_ID
from .message_engine import GroupAccessError
from .read_budget import ReadBudgetError, ReadBudgetExceeded


VERSION = 1
MAX_REQUEST_BYTES = 16 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
MAX_ACCOUNTS = 1000
MAX_READ_MESSAGES = 1000
MAX_REQUEST_ID = (1 << 53) - 1
MAX_HEALTH_EVENTS = 256
MAX_HEALTH_EVENT_BYTES = 8192
OPERATIONS = ('read_batch', 'lookup_group', 'check_group_access', 'join_group')

# Unknown SDK RPC text can survive inside AuthRequiredError.reason. Only publish
# recognized authentication codes, never arbitrary text from that wrapper.
_CANONICAL_AUTH_REASONS = frozenset(
    name for cls, name in health._TELEGRAM_NAMES.items()
    if issubclass(cls, (UnauthorizedError, AuthKeyError))) | frozenset(_BANNED)

_CODES = frozenset(('invalid_json', 'invalid_envelope', 'invalid_request_id',
    'stale_request_id', 'unknown_account', 'unknown_operation', 'invalid_parameters',
    'join_disabled', 'invalid_config', 'worker_busy', 'worker_stopping',
    'delivery_failed', 'frame_too_large', 'incomplete_frame', 'input_failure',
    'output_failure', 'unsupported_sdk'))
_FIELDS = frozenset(('version', 'request_id', 'account_id', 'operation', 'params',
    'group_id', 'target', 'after_id', 'limit', 'start_date', 'end_date', 'worker_id',
    'accounts', 'config_path', 'session_store', 'label', 'read_budget', 'join_budget',
    'session', 'input', 'output'))
_IDS = frozenset(('id', 'peer_id', 'user_id', 'account_id', 'expected_account_id',
                  'actual_account_id', 'bot_id', 'query_id', 'target', 'group'))
_DECIMAL = re.compile(r'-?(?:0|[1-9][0-9]*)\Z')
_NAME = re.compile(r'[A-Za-z_][A-Za-z_0-9]{0,127}\Z')


class WorkerError(RuntimeError):
    """A fixed-code local refusal; never retains an input/credential message."""

    def __init__(self, code, *, field=None, fatal=False):
        if code not in _CODES or (field is not None and field not in _FIELDS):
            code, field = 'invalid_config', None
        super().__init__(code)
        self.code, self.field, self.fatal = code, field, fatal
        self.request_id = self.account_id = self.operation = None
        self.__suppress_context__ = True


@dataclass(frozen=True)
class Job:
    request_id: int
    account_id: int
    operation: str
    parameters: tuple

    def options(self):
        return dict(self.parameters)


def canonical_id(value, minimum=1, maximum=MAX_LONG, field='account_id'):
    if (type(value) is not str or len(value) > 20 or not _DECIMAL.fullmatch(value)
            or value == '-0'):
        raise WorkerError('invalid_parameters', field=field)
    number = int(value)
    if not minimum <= number <= maximum:
        raise WorkerError('invalid_parameters', field=field)
    return number


def _pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise WorkerError('invalid_json')
        result[key] = value
    return result


def _constant(value):
    raise WorkerError('invalid_json')


def decode_json(data):
    try:
        if type(data) is not bytes:
            raise WorkerError('invalid_json')
        return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
    except WorkerError:
        raise
    except (ValueError, UnicodeError, RecursionError, TypeError):
        raise WorkerError('invalid_json') from None


def _date(value, field):
    if value is None:
        return None
    if type(value) is not str:
        raise WorkerError('invalid_parameters', field=field)
    try:
        result = datetime.fromisoformat(value[:-1] + '+00:00' if value.endswith('Z') else value)
        if result.utcoffset() is None:
            raise ValueError
        return result
    except (ValueError, OverflowError):
        raise WorkerError('invalid_parameters', field=field) from None


def _parameters(operation, params):
    if type(params) is not dict:
        raise WorkerError('invalid_parameters', field='params')
    if operation != 'read_batch':
        if set(params) != {'target'}:
            raise WorkerError('invalid_parameters', field='params')
        _parse_target(params['target'])
        return (('target', params['target']),)
    allowed = {'group_id', 'after_id', 'limit', 'start_date', 'end_date'}
    if 'group_id' not in params or not set(params) <= allowed:
        raise WorkerError('invalid_parameters', field='params')
    target = params['group_id']
    _parse_target(target)
    after = canonical_id(params.get('after_id', '0'), 0, MAX_MESSAGE_ID, 'after_id')
    limit = params.get('limit', 200)
    if type(limit) is not int or not 1 <= limit <= MAX_READ_MESSAGES:
        raise WorkerError('invalid_parameters', field='limit')
    start, end = (_date(params.get(name), name) for name in ('start_date', 'end_date'))
    _HistoryWindow.from_dates(start, end)
    return tuple(dict(group_id=target, after_id=after, limit=limit,
                      start_date=start, end_date=end).items())


class RequestDecoder:
    """A bounded high-water mark, not a durable job/idempotency store."""

    def __init__(self):
        self.last_id = 0

    def decode(self, frame):
        if type(frame) is not bytes:
            raise WorkerError('input_failure', fatal=True)
        if len(frame) > MAX_REQUEST_BYTES:
            raise WorkerError('frame_too_large', fatal=True)
        if not frame.endswith(b'\n'):
            raise WorkerError('incomplete_frame', fatal=True)
        raw = decode_json(frame)
        if type(raw) is not dict or type(raw.get('version')) is not int or raw['version'] != VERSION:
            raise WorkerError('invalid_envelope', field='version')
        ident = raw.get('request_id')
        if type(ident) is not int or not 1 <= ident <= MAX_REQUEST_ID:
            raise WorkerError('invalid_request_id', field='request_id')
        account = operation = None
        try:
            if ident <= self.last_id:
                raise WorkerError('stale_request_id', field='request_id')
            # A recognized fresh envelope is consumed even if its job is refused.
            self.last_id = ident
            if set(raw) != {'version', 'request_id', 'account_id', 'operation', 'params'}:
                raise WorkerError('invalid_envelope')
            account = canonical_id(raw['account_id'])
            if type(raw['operation']) is not str or raw['operation'] not in OPERATIONS:
                raise WorkerError('unknown_operation', field='operation')
            operation = raw['operation']
            try:
                parameters = _parameters(operation, raw['params'])
            except WorkerError:
                raise
            except (ValueError, TypeError, OverflowError, UnicodeError):
                raise WorkerError('invalid_parameters', field='params') from None
            return Job(ident, account, operation, parameters)
        except WorkerError as error:
            error.request_id, error.account_id, error.operation = ident, account, operation
            raise


def identifiers(value):
    """Project known identifier fields, without changing counts or batch schema."""
    if type(value) is dict:
        return {key: str(item) if key in _IDS and type(item) is int else identifiers(item)
                for key, item in value.items()}
    if type(value) in (list, tuple):
        return [identifiers(item) for item in value]
    return value


def error_type(error):
    name = type(error).__name__
    return name if _NAME.fullmatch(name) else 'Error'


def _optional(action, fallback=None):
    try:
        return action()
    except BaseException:
        # Metadata inspection is secondary, including an internally cancelled
        # property. The real worker's cancellation is checked at async boundaries.
        return fallback


def _plain(value, depth=0):
    if depth > 8:
        return None
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else None
    if type(value) is dict and len(value) <= 32 and all(type(key) is str for key in value):
        return {key: _plain(item, depth + 1) for key, item in value.items()}
    return None


def describe_error(error):
    result = {'category': 'operation_error', 'type': error_type(error)}
    if isinstance(error, WorkerError):
        result.update(category='worker_error', code=error.code)
        if error.field is not None:
            result['field'] = error.field
    elif isinstance(error, AuthRequiredError):
        result['category'] = 'authentication_required'
        reason = _optional(lambda: error.reason)
        if type(reason) is str and reason in _CANONICAL_AUTH_REASONS:
            result['reason'] = reason
        for name in ('banned', 'first_login'):
            value = _optional(lambda: getattr(error, name))
            if type(value) is bool:
                result[name] = value
    elif isinstance(error, AccountIdentityError):
        result['category'] = 'identity_mismatch'
        for name in ('expected_account_id', 'actual_account_id'):
            value = _optional(lambda: getattr(error, name))
            if value is None or type(value) is int:
                result[name] = str(value) if value is not None else None
    elif isinstance(error, (ReadBudgetError, JoinBudgetError)):
        result['category'] = 'allowance_error'
        if isinstance(error, (ReadBudgetExceeded, JoinBudgetExceeded)):
            status = _optional(lambda: _plain(error.status.to_dict()))
            if status is not None:
                result['status'] = identifiers(status)
    elif isinstance(error, (GroupReferenceError, GroupResponseError, GroupAccessError)):
        result['category'] = 'group_error'
    elif isinstance(error, ProxyConfigError):
        result['category'] = 'configuration_error'
    elif isinstance(error, RPCError):
        result['category'] = 'telegram_error'
        # Named SDK classes have a bounded canonical name. Generic RPC .message
        # is intentionally not copied: it is arbitrary exception text.
        name = health._TELEGRAM_NAMES.get(type(error))
        if type(name) is str and _NAME.fullmatch(name):
            result['name'] = name
        code = _optional(lambda: error.code)
        if type(code) is int and -(1 << 31) <= code < (1 << 31):
            result['code'] = code
        seconds = _optional(lambda: error.seconds)
        if type(seconds) is int and 0 <= seconds <= MAX_LONG:
            result['wait_seconds'] = seconds
    return result


def partial_batch(error):
    value = _optional(lambda: error.partial_result)
    return value.to_dict() if isinstance(value, MessageBatch) else None


def health_event(value):
    """Keep the event schema, but never forward arbitrary RPC exception text."""
    result = identifiers(value)
    known = set(health._TELEGRAM_NAMES.values()) | set(health._TABLE)
    known.update(cls.__name__ for cls in health._REGISTERED)
    if result.get('error') not in known:
        result['error'] = None
    return result


def encode_frame(value, maximum=None):
    """Encode fully before publication, refusing excess rather than truncating."""
    if maximum is None:
        maximum = MAX_RESPONSE_BYTES
    output = bytearray()
    try:
        encoder = json.JSONEncoder(ensure_ascii=True, allow_nan=False, separators=(',', ':'))
        for part in encoder.iterencode(value):
            raw = part.encode('ascii')
            if len(output) + len(raw) + 1 > maximum:
                raise WorkerError('delivery_failed', fatal=True)
            output.extend(raw)
        output.extend(b'\n')
        return bytes(output)
    except WorkerError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise WorkerError('delivery_failed', fatal=True) from None
