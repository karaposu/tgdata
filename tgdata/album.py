"""Pure, opt-in assembly of observed Telegram album members.

Posts describe observed data, never source receipts or globally complete albums.
Callers retain prior posts and commit them before acknowledging raw deliveries.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json

from .message_batch import (
    MessageBatch, BatchFormatError, MIN_LONG, _canonical, _digest, _identifier,
    _invalid_constant, _json_pairs, _keys, _validate_record,
)


DEFAULT_MAX_MEMBERS = 10000
DEFAULT_MAX_BYTES = 16 * 1024 * 1024
_KEYS = frozenset({'schema', 'version', 'post_id', 'revision', 'chat_id',
                   'grouped_id', 'media_mode', 'membership', 'members'})


class AlbumAssemblyError(ValueError):
    """Local format, conflict or resource refusal; never an account-health event."""

    def __init__(self, message):
        super().__init__(message)
        self.__suppress_context__ = True


def _limits(max_members, max_bytes):
    for value, name in ((max_members, 'max_members'), (max_bytes, 'max_bytes')):
        if type(value) is not int or value <= 0:
            raise AlbumAssemblyError('{} must be a positive integer'.format(name))


def _bytes(text, maximum):
    try:
        size = len(text.encode('utf-8')) if isinstance(text, str) else len(text)
    except UnicodeError:
        raise AlbumAssemblyError('post data must be valid UTF-8') from None
    if size > maximum:
        raise AlbumAssemblyError('max_bytes exceeded')
    return size


def _identity(chat_id, member):
    grouped = member['grouped_id']
    return 'tg:{}:{}:{}'.format(chat_id, 'album' if grouped is not None else 'message',
                                grouped if grouped is not None else member['id'])


def _revision(value):
    body = {key: item for key, item in value.items() if key != 'revision'}
    return hashlib.sha256(_canonical(body).encode('utf-8')).hexdigest()


def _validate(value, max_members):
    _keys(value, _KEYS, 'post')
    if value['schema'] != 'tgdata.telegram-post' or type(value['version']) is not int or value['version'] != 1:
        raise AlbumAssemblyError('unsupported post schema or version')
    _identifier(value['chat_id'], 'post.chat_id', MIN_LONG, -1)
    _identifier(value['grouped_id'], 'post.grouped_id', nullable=True)
    _digest(value['revision'], 'post.revision')
    if value['media_mode'] not in ('references', 'download'):
        raise AlbumAssemblyError('unsupported post media_mode')
    members = value['members']
    if type(members) is not list or not members or len(members) > max_members:
        raise AlbumAssemblyError('members must be nonempty and within max_members')
    grouped = value['grouped_id'] is not None
    if value['membership'] != ('unconfirmed' if grouped else 'single'):
        raise AlbumAssemblyError('post membership must reflect observed album or singleton data')
    if not grouped and len(members) != 1:
        raise AlbumAssemblyError('an ungrouped post must have one member')
    last = 0
    for member in members:
        ident = _validate_record(member, value['media_mode'])
        if ident <= last:
            raise AlbumAssemblyError('member IDs must increase strictly')
        last = ident
        if member['grouped_id'] != value['grouped_id'] or _identity(value['chat_id'], member) != value['post_id']:
            raise AlbumAssemblyError('member does not match post identity')
    if value['revision'] != _revision(value):
        raise AlbumAssemblyError('post revision does not match content')


@dataclass(frozen=True, init=False)
class TelegramPost:
    """Immutable observed post; getters return copies, albums stay unconfirmed.

    The revision hashes canonical content, independently of raw batch partitions.
    Loading validates the entire value. Limits can be raised explicitly; they
    are a serialized-work policy, not a promise about total process memory.
    """

    _encoded: str = field(repr=False)

    def __init__(self, document, *, max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
        _limits(max_members, max_bytes)
        if type(document) is not dict:
            raise AlbumAssemblyError('post must be a JSON object')
        members = document.get('members')
        if type(members) is list and len(members) > max_members:
            raise AlbumAssemblyError('max_members exceeded')
        try:
            encoded = _canonical(document)
            _bytes(encoded, max_bytes)
            owned = json.loads(encoded)
            _validate(owned, max_members)
        except BatchFormatError as error:
            raise AlbumAssemblyError(str(error)) from None
        object.__setattr__(self, '_encoded', encoded)

    @classmethod
    def from_json(cls, data, *, max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
        _limits(max_members, max_bytes)
        if type(data) not in (str, bytes):
            raise AlbumAssemblyError('post JSON must be text or UTF-8 bytes')
        _bytes(data, max_bytes)
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            value = json.loads(data, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
        except (BatchFormatError, ValueError, UnicodeError, RecursionError):
            raise AlbumAssemblyError('invalid post JSON') from None
        return cls(value, max_members=max_members, max_bytes=max_bytes)

    def to_json(self):
        return self._encoded

    def to_dict(self):
        return json.loads(self._encoded)

    @property
    def post_id(self):
        return self.to_dict()['post_id']

    @property
    def revision(self):
        return self.to_dict()['revision']

    @property
    def chat_id(self):
        return int(self.to_dict()['chat_id'])

    @property
    def grouped_id(self):
        value = self.to_dict()['grouped_id']
        return int(value) if value is not None else None

    @property
    def media_mode(self):
        return self.to_dict()['media_mode']

    @property
    def membership(self):
        return self.to_dict()['membership']

    @property
    def members(self):
        return self.to_dict()['members']

    @property
    def member_ids(self):
        return tuple(int(member['id']) for member in self.to_dict()['members'])


def _batch(batch, max_bytes):
    if type(batch) is not MessageBatch:
        raise AlbumAssemblyError('batch must be a MessageBatch')
    size = _bytes(batch.to_json(), max_bytes)
    return batch.to_dict(), size


def album_post_ids(batch, *, max_bytes=DEFAULT_MAX_BYTES):
    """Return affected post keys in first occurrence order, without any I/O."""
    _limits(DEFAULT_MAX_MEMBERS, max_bytes)
    value, _ = _batch(batch, max_bytes)
    return tuple(dict.fromkeys(_identity(value['chat_id'], row) for row in value['messages']))


def assemble_albums(batch, *, previous, max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
    """Return updated affected posts from a raw batch and authoritative prior data.

    ``previous`` must map exactly every affected key to a TelegramPost or None.
    None asserts successful lookup found no prior post; lookup errors must raise.
    Load current prior values and save results in a caller-owned transaction/CAS.
    Exact duplicates are idempotent; incompatible observations refuse entirely.

    max_members bounds total returned members; max_bytes bounds the sum of raw
    batch JSON, supplied post JSON and returned post JSON in UTF-8. No data is
    silently evicted. This function never fetches, saves or acknowledges.
    """
    _limits(max_members, max_bytes)
    value, size = _batch(batch, max_bytes)
    groups = {}
    for member in value['messages']:
        groups.setdefault(_identity(value['chat_id'], member), []).append(member)
    if not isinstance(previous, Mapping) or len(previous) != len(groups) or set(previous) != set(groups):
        raise AlbumAssemblyError('previous must contain exactly the affected post IDs')

    # Check encoded input sizes before decoding prior observations. Revalidate
    # each saved value with the caller's policy, including deliberately raised limits.
    prior_documents = {}
    for key in groups:
        post = previous[key]
        if post is None:
            continue
        if type(post) is not TelegramPost:
            raise AlbumAssemblyError('previous values must be TelegramPost or None')
        size += _bytes(post.to_json(), max_bytes)
        if size > max_bytes:
            raise AlbumAssemblyError('max_bytes exceeded')
        loaded = TelegramPost.from_json(post.to_json(), max_members=max_members, max_bytes=max_bytes).to_dict()
        if loaded['post_id'] != key or loaded['media_mode'] != value['media_mode']:
            raise AlbumAssemblyError('prior post identity or media mode differs')
        prior_documents[key] = loaded

    output, count, seen_ids = [], 0, set()
    for key, incoming in groups.items():
        prior = prior_documents.get(key)
        members = {row['id']: row for row in prior['members']} if prior is not None else {}
        for row in incoming:
            if row['id'] in members and members[row['id']] != row:
                raise AlbumAssemblyError('conflicting observations of a member')
            members[row['id']] = row
        count += len(members)
        if count > max_members:
            raise AlbumAssemblyError('max_members exceeded')
        if seen_ids.intersection(members):
            raise AlbumAssemblyError('a member appears in conflicting posts')
        seen_ids.update(members)
        ordered = sorted(members.values(), key=lambda row: int(row['id']))
        document = dict(schema='tgdata.telegram-post', version=1, post_id=key,
                        chat_id=value['chat_id'], grouped_id=incoming[0]['grouped_id'],
                        media_mode=value['media_mode'],
                        membership='unconfirmed' if incoming[0]['grouped_id'] is not None else 'single',
                        members=ordered)
        document['revision'] = _revision(document)
        post = TelegramPost(document, max_members=max_members, max_bytes=max_bytes)
        size += _bytes(post.to_json(), max_bytes)
        if size > max_bytes:
            raise AlbumAssemblyError('max_bytes exceeded')
        output.append((int(ordered[0]['id']), key, post))
    return tuple(item[2] for item in sorted(output))
