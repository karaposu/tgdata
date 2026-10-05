"""The explicit, portable v1 message-batch value.

The identity covers canonical payload bytes without the batch_id field. It is
an identity for a saved observation, not for a query against changing history.
"""

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re

from .batch_files import save_manifest


SCHEMA = 'tgdata.message-batch'
VERSION = 1
MAX_BATCH_MESSAGES = 10000
MAX_MESSAGE_ID = (1 << 31) - 1
MAX_LONG = (1 << 63) - 1
MIN_LONG = -(1 << 63)

_ENVELOPE_KEYS = frozenset({
    'schema', 'version', 'batch_id', 'chat_id', 'after_id', 'next_after_id',
    'media_mode', 'stop_reason', 'messages',
})
_RECORD_KEYS = frozenset({
    'id', 'kind', 'date', 'edit_date', 'text', 'sender', 'post_author',
    'reply_to_id', 'forward_from_id', 'grouped_id', 'service_action', 'media',
})
_MEDIA_KEYS = frozenset({'kind', 'id', 'mime_type', 'file_name', 'size', 'downloadable', 'blob'})
_MEDIA_KINDS = frozenset({
    'photo', 'video', 'video_note', 'gif', 'audio', 'voice', 'document', 'sticker',
    'webpage', 'contact', 'geo', 'poll', 'other',
})
DOWNLOAD_KINDS = frozenset({'photo', 'video', 'video_note', 'gif', 'audio', 'voice', 'document', 'sticker'})


class BatchFormatError(ValueError):
    """A local batch-format error, not a Telegram account-health verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.partial_result = None
        self.__suppress_context__ = True


def _keys(value, expected, name):
    if type(value) is not dict or value.keys() != expected:
        raise BatchFormatError('{} has missing or unsupported fields'.format(name))


def _text(value, name, nullable=True):
    if value is None and nullable:
        return
    if type(value) is not str:
        raise BatchFormatError('{} must be a string{}'.format(name, ' or null' if nullable else ''))
    try:
        value.encode('utf-8')
    except UnicodeError:
        raise BatchFormatError('{} must be valid UTF-8 text'.format(name)) from None


def _identifier(value, name, minimum=MIN_LONG, maximum=MAX_LONG, nullable=False, nonzero=True):
    if value is None and nullable:
        return None
    if type(value) is not str or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value):
        raise BatchFormatError('{} must be a canonical decimal string'.format(name))
    if len(value) > 20 or value == '-0':
        raise BatchFormatError('{} is outside its identifier range'.format(name))
    number = int(value)
    if not minimum <= number <= maximum or (nonzero and number == 0):
        raise BatchFormatError('{} is outside its identifier range'.format(name))
    return number


def _size(value, name, nullable=False):
    if value is None and nullable:
        return
    if type(value) is not int or not 0 <= value <= MAX_LONG:
        raise BatchFormatError('{} must be a nonnegative integer{}'.format(
            name, ' or null' if nullable else ''))


def _digest(value, name):
    if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise BatchFormatError('{} must be a lowercase SHA-256 digest'.format(name))


def _date(value, name):
    if value is None:
        return
    _text(value, name, nullable=False)
    try:
        if not value.endswith('Z'):
            raise ValueError
        parsed = datetime.fromisoformat(value[:-1] + '+00:00')
        canonical = parsed.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')
        if canonical != value:
            raise ValueError
    except (ValueError, OverflowError):
        raise BatchFormatError('{} must be a canonical UTC timestamp or null'.format(name)) from None


def _validate_record(record, media_mode):
    """Validate one prepared record before it can advance a read's cursor."""
    _keys(record, _RECORD_KEYS, 'message')
    ident = _identifier(record['id'], 'message.id', 1, MAX_MESSAGE_ID)
    if record['kind'] not in ('message', 'service'):
        raise BatchFormatError('message.kind is unsupported')
    _date(record['date'], 'message.date')
    _date(record['edit_date'], 'message.edit_date')
    _text(record['text'], 'message.text')
    _text(record['post_author'], 'message.post_author')
    _keys(record['sender'], frozenset({'id', 'name', 'username'}), 'message.sender')
    _identifier(record['sender']['id'], 'sender.id', nullable=True)
    _text(record['sender']['name'], 'sender.name')
    _text(record['sender']['username'], 'sender.username')
    _identifier(record['reply_to_id'], 'message.reply_to_id', 1, MAX_MESSAGE_ID, nullable=True)
    _identifier(record['forward_from_id'], 'message.forward_from_id', nullable=True)
    _identifier(record['grouped_id'], 'message.grouped_id', nullable=True)
    if record['kind'] == 'service':
        _text(record['service_action'], 'message.service_action', nullable=False)
        if not record['service_action']:
            raise BatchFormatError('service messages require an action type name')
    elif record['service_action'] is not None:
        raise BatchFormatError('ordinary messages must not contain a service action')

    media = record['media']
    if media is None:
        return ident
    _keys(media, _MEDIA_KEYS, 'message.media')
    if type(media['kind']) is not str or media['kind'] not in _MEDIA_KINDS:
        raise BatchFormatError('media.kind is unsupported')
    _identifier(media['id'], 'media.id', nullable=True)
    _text(media['mime_type'], 'media.mime_type')
    _text(media['file_name'], 'media.file_name')
    _size(media['size'], 'media.size', nullable=True)
    if type(media['downloadable']) is not bool:
        raise BatchFormatError('media.downloadable must be a boolean')
    if media['downloadable'] and (media['kind'] not in DOWNLOAD_KINDS or media['id'] is None):
        raise BatchFormatError('downloadable media requires a supported kind and asset ID')
    blob = media['blob']
    required = media_mode == 'download' and media['downloadable']
    if (blob is not None) != required:
        raise BatchFormatError('media blob does not match the batch mode and downloadability')
    if blob is not None:
        _keys(blob, frozenset({'sha256', 'size', 'path'}), 'media.blob')
        _digest(blob['sha256'], 'blob.sha256')
        _size(blob['size'], 'blob.size')
        if blob['path'] != blob['sha256']:
            raise BatchFormatError('blob.path must be its SHA-256 basename')
        if media['size'] is not None and blob['size'] != media['size']:
            raise BatchFormatError('blob size differs from the declared media size')
    return ident


def _canonical(value):
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
        text.encode('utf-8')
        return text
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise BatchFormatError('batch contains a value that cannot be encoded as canonical JSON') from None


def _payload_digest(document):
    payload = {key: value for key, value in document.items() if key != 'batch_id'}
    return hashlib.sha256(_canonical(payload).encode('utf-8')).hexdigest()


def _validate_document(document):
    _keys(document, _ENVELOPE_KEYS, 'batch')
    if document['schema'] != SCHEMA or type(document['version']) is not int or document['version'] != VERSION:
        raise BatchFormatError('unsupported message-batch schema or version')
    _digest(document['batch_id'], 'batch_id')
    _identifier(document['chat_id'], 'chat_id', MIN_LONG, -1)
    after = _identifier(document['after_id'], 'after_id', 0, MAX_MESSAGE_ID, nonzero=False)
    following = _identifier(document['next_after_id'], 'next_after_id', 0, MAX_MESSAGE_ID, nonzero=False)
    if document['media_mode'] not in ('references', 'download'):
        raise BatchFormatError('unsupported media_mode')
    if document['stop_reason'] not in ('limit', 'end', 'interrupted'):
        raise BatchFormatError('unsupported stop_reason')
    messages = document['messages']
    if type(messages) is not list or len(messages) > MAX_BATCH_MESSAGES:
        raise BatchFormatError('messages must be a list of at most 10000 records')
    last = after
    for record in messages:
        ident = _validate_record(record, document['media_mode'])
        if ident <= last:
            raise BatchFormatError('message IDs must increase strictly after the input cursor')
        last = ident
    if following != last:
        raise BatchFormatError('next_after_id must equal the last prepared ID or the input cursor')
    if document['stop_reason'] == 'limit' and not messages:
        raise BatchFormatError('a limit batch must contain messages')
    if document['batch_id'] != _payload_digest(document):
        raise BatchFormatError('batch_id does not match the payload')


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BatchFormatError('duplicate JSON field')
        result[key] = value
    return result


def _invalid_constant(_):
    raise BatchFormatError('nonfinite JSON values are not supported')


@dataclass(frozen=True, init=False)
class MessageBatch:
    """An immutable v1 snapshot; dictionary/message access returns copies.

    Use get_message_batch() to read or from_json() to reload. The constructor
    validates a full envelope, including its supplied batch_id.
    """

    _encoded: str = field(repr=False)

    def __init__(self, document):
        try:
            owned = copy.deepcopy(document)
        except (TypeError, ValueError, RecursionError):
            raise BatchFormatError('batch must contain plain JSON values') from None
        _validate_document(owned)
        object.__setattr__(self, '_encoded', _canonical(owned))

    @classmethod
    def _from_records(cls, chat_id, after_id, records, media_mode, stop_reason):
        document = {
            'schema': SCHEMA, 'version': VERSION, 'chat_id': str(chat_id),
            'after_id': str(after_id),
            'next_after_id': records[-1]['id'] if records else str(after_id),
            'media_mode': media_mode, 'stop_reason': stop_reason, 'messages': records,
        }
        document['batch_id'] = _payload_digest(document)
        return cls(document)

    @classmethod
    def from_json(cls, data):
        """Load a supported, correctly hashed batch without contacting Telegram."""
        if not isinstance(data, (str, bytes)):
            raise BatchFormatError('batch JSON must be text or UTF-8 bytes')
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            document = json.loads(data, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
        except BatchFormatError:
            raise
        except (ValueError, UnicodeError, RecursionError):
            raise BatchFormatError('invalid message-batch JSON') from None
        return cls(document)

    def to_json(self):
        """Canonical UTF-8-compatible JSON text, including batch_id."""
        return self._encoded

    def to_dict(self):
        return json.loads(self._encoded)

    def save(self, directory):
        """Save/reuse <batch_id>.json and return its Path; media stays separate."""
        return save_manifest(directory, self.batch_id, self._encoded.encode('utf-8'))

    @property
    def batch_id(self):
        return self.to_dict()['batch_id']

    @property
    def chat_id(self):
        return int(self.to_dict()['chat_id'])

    @property
    def after_id(self):
        return int(self.to_dict()['after_id'])

    @property
    def next_after_id(self):
        return int(self.to_dict()['next_after_id'])

    @property
    def messages(self):
        return self.to_dict()['messages']

    @property
    def stop_reason(self):
        return self.to_dict()['stop_reason']

    @property
    def media_mode(self):
        return self.to_dict()['media_mode']
