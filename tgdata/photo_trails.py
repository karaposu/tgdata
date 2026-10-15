"""Opt-in, provisional photo-trail views over immutable Telegram observations.

The caller supplies the current observation scope and replaces its prior view.
No original post, source receipt, storage, clock or Telegram client is changed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from .album import (
    TelegramPost, AlbumAssemblyError, DEFAULT_MAX_MEMBERS, DEFAULT_MAX_BYTES,
    _limits as _album_limits, _bytes as _album_bytes, _revision,
)
from .message_batch import (
    BatchFormatError, MAX_MESSAGE_ID, _canonical, _digest, _keys,
    _json_pairs, _invalid_constant,
)


_POLICY_KEYS = frozenset({'enabled', 'gap_seconds', 'max_span_seconds', 'max_photos'})
_VIEW_KEYS = frozenset({'schema', 'version', 'revision', 'algorithm', 'policy',
                        'status', 'posts', 'groups', 'folded_posts', 'folded_photos'})
_ALGORITHM = 'same-user-photo-trail/v1'


class PhotoTrailError(ValueError):
    """Local format, conflict, scope or work-limit refusal; no health event."""

    def __init__(self, message):
        super().__init__(message)
        self.__suppress_context__ = True


def _limits(max_members, max_bytes):
    try:
        _album_limits(max_members, max_bytes)
    except AlbumAssemblyError as error:
        raise PhotoTrailError(str(error)) from None


def _bytes(value, maximum):
    try:
        return _album_bytes(value, maximum)
    except AlbumAssemblyError as error:
        raise PhotoTrailError(str(error)) from None


@dataclass(frozen=True)
class PhotoTrailPolicy:
    """Explicit heuristic policy, disabled by default.

    max_photos counts attached original photo messages, excluding anchor media.
    max_span_seconds starts at the anchor's last original member.
    """

    enabled: bool = False
    gap_seconds: int = 30
    max_span_seconds: int = 120
    max_photos: int = 20

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise PhotoTrailError('enabled must be a boolean')
        for name in ('gap_seconds', 'max_span_seconds', 'max_photos'):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= MAX_MESSAGE_ID:
                raise PhotoTrailError('{} must be an integer from 1 to {}'.format(name, MAX_MESSAGE_ID))

    def to_dict(self):
        return dict(enabled=self.enabled, gap_seconds=self.gap_seconds,
                    max_span_seconds=self.max_span_seconds, max_photos=self.max_photos)

    @classmethod
    def from_dict(cls, value):
        try:
            _keys(value, _POLICY_KEYS, 'photo-trail policy')
        except BatchFormatError as error:
            raise PhotoTrailError(str(error)) from None
        return cls(**value)


def _policy(value):
    if value is None:
        return PhotoTrailPolicy()
    if type(value) is not PhotoTrailPolicy:
        raise PhotoTrailError('policy must be a PhotoTrailPolicy or None')
    return PhotoTrailPolicy.from_dict(value.to_dict())


def _order(document):
    return int(document['chat_id']), int(document['members'][0]['id']), document['post_id']


def _positive_user(member):
    value = member['sender']['id']
    return int(value) if value is not None and int(value) > 0 else None


def _unique_members(documents):
    seen = set()
    for document in documents:
        for member in document['members']:
            key = (document['chat_id'], member['id'])
            if key in seen:
                raise PhotoTrailError('an original member appears in different posts')
            seen.add(key)


def _unsafe_overlaps(ranges):
    for values in ranges.values():
        cluster, end = [], -1
        for info in sorted(values, key=lambda item: item['first']):
            if info['first'] > end:
                if len(cluster) > 1:
                    for item in cluster:
                        item['unsafe'] = True
                cluster, end = [], -1
            cluster.append(info)
            end = max(end, info['last'])
        if len(cluster) > 1:
            for item in cluster:
                item['unsafe'] = True


def _attachment(info, chain, policy, gap, span):
    if (info['first'] <= chain['last_id'] or
            chain['photos'] + len(info['rows']) > policy.max_photos):
        return None
    earlier, previous = set(), chain['last_date']
    for member, date in zip(info['rows'], info['dates']):
        if not timedelta(0) <= date - previous <= gap or date - chain['origin'] > span:
            return None
        reply = member['reply_to_id']
        if reply is not None and int(reply) not in chain['ids'] and int(reply) not in earlier:
            return None
        earlier.add(int(member['id']))
        previous = date
    return earlier


def _relation(documents, policy):
    """One rule for both construction and saved-relation validation."""
    if not policy.enabled:
        return ([dict(anchor_post_id=d['post_id'], post_ids=[d['post_id']])
                 for d in documents], 0, 0)
    metadata, events, ranges = {}, [], {}
    for document in documents:
        key, members = document['post_id'], document['members']
        chat = int(document['chat_id'])
        owners = {_positive_user(member) for member in members}
        owner = next(iter(owners)) if len(owners) == 1 else None
        dates = [datetime.fromisoformat(member['date'][:-1] + '+00:00')
                 if member['date'] is not None else None for member in members]
        ordinary = all(member['kind'] == 'message' for member in members)
        has_text = any((member['text'] or '').strip() for member in members)
        info = dict(chat=chat, owner=owner, rows=members, dates=dates,
                    first=int(members[0]['id']), last=int(members[-1]['id']),
                    unsafe=not ordinary or any(date is None for date in dates),
                    anchor=ordinary and (has_text or document['grouped_id'] is not None),
                    follower=ordinary and not has_text and all(
                        member['media'] is not None and member['media']['kind'] == 'photo'
                        for member in members))
        metadata[key] = info
        if owner is not None:
            ranges.setdefault((chat, owner), []).append(info)
        events.extend((chat, int(member['id']), key, index) for index, member in enumerate(members))
    _unsafe_overlaps(ranges)
    events.sort()
    last_dates = {}
    for chat, ident, key, index in events:
        info = metadata[key]
        # An ineligible mixed post still contains individually known evidence.
        # Chronology must not discard it merely because the post cannot anchor.
        user = _positive_user(info['rows'][index])
        date = info['dates'][index]
        if user is not None and date is not None:
            previous = last_dates.get((chat, user))
            if previous is not None and date < previous:
                info['unsafe'] = True
            last_dates[(chat, user)] = max(previous, date) if previous is not None else date

    groups = {document['post_id']: [document['post_id']] for document in documents}
    active, current_chat = {}, None
    gap, span = timedelta(seconds=policy.gap_seconds), timedelta(seconds=policy.max_span_seconds)
    for chat, ident, key, index in events:
        if chat != current_chat:
            active.clear()
            current_chat = chat
        info = metadata[key]
        owner = info['owner']
        if owner is None:
            active.clear()
            continue
        if info['unsafe']:
            active.pop(owner, None)
            continue
        if not info['follower'] and index == 0:
            active.pop(owner, None)
        if index != len(info['rows']) - 1:
            continue
        chain, attached = active.get(owner), False
        if info['follower'] and chain is not None:
            ids = _attachment(info, chain, policy, gap, span)
            if ids is not None:
                groups[chain['root']].append(key)
                del groups[key]
                chain['ids'].update(ids)
                chain.update(last_date=info['dates'][-1], last_id=info['last'],
                             photos=chain['photos'] + len(info['rows']))
                attached = True
            else:
                active.pop(owner, None)
        if not attached and info['anchor']:
            active[owner] = dict(root=key, ids={int(row['id']) for row in info['rows']},
                                 last_date=info['dates'][-1], last_id=info['last'],
                                 origin=info['dates'][-1], photos=0)

    result, post_count, photo_count = [], 0, 0
    for document in documents:
        key = document['post_id']
        if key not in groups:
            continue
        keys = groups[key]
        result.append(dict(anchor_post_id=key, post_ids=keys))
        post_count += len(keys) - 1
        photo_count += sum(len(metadata[following]['rows']) for following in keys[1:])
    return result, post_count, photo_count


def _original(document, max_members, max_bytes):
    try:
        return TelegramPost(document, max_members=max_members, max_bytes=max_bytes)
    except (AlbumAssemblyError, BatchFormatError) as error:
        raise PhotoTrailError('invalid original post: {}'.format(error)) from None


@dataclass(frozen=True, init=False)
class PhotoTrailView:
    """Lossless, provisional full view; replace an earlier view for the same scope.

    posts retains original TelegramPost values. groups is a tuple of tuples of
    original post IDs, each beginning with its anchor. Neither is a source receipt.
    """

    _encoded: str = field(repr=False)
    _posts: tuple = field(repr=False, compare=False)
    _groups: tuple = field(repr=False, compare=False)
    _policy: PhotoTrailPolicy = field(repr=False, compare=False)
    _revision_value: str = field(repr=False, compare=False)
    _counts: tuple = field(repr=False, compare=False)

    def __init__(self, document, *, max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
        _limits(max_members, max_bytes)
        try:
            _keys(document, _VIEW_KEYS, 'photo-trail view')
            originals = document['posts']
            if type(originals) is not list or len(originals) > max_members:
                raise PhotoTrailError('posts must be a list within max_members')
            count = 0
            for original in originals:
                if type(original) is not dict or type(original.get('members')) is not list:
                    raise PhotoTrailError('posts must contain original post documents')
                count += len(original['members'])
                if count > max_members:
                    raise PhotoTrailError('max_members exceeded')
            encoded = _canonical(document)
            _bytes(encoded, max_bytes)
            value = json.loads(encoded)
            if (value['schema'] != 'tgdata.photo-trail-view' or type(value['version']) is not int
                    or value['version'] != 1 or value['algorithm'] != _ALGORITHM
                    or value['status'] != 'provisional'):
                raise PhotoTrailError('unsupported photo-trail schema, algorithm or status')
            _digest(value['revision'], 'view.revision')
            policy = PhotoTrailPolicy.from_dict(value['policy'])
            posts = tuple(_original(original, max_members, max_bytes) for original in value['posts'])
            documents = [post.to_dict() for post in posts]
            keys = [d['post_id'] for d in documents]
            if len(set(keys)) != len(keys) or documents != sorted(documents, key=_order):
                raise PhotoTrailError('original posts must be unique and canonically ordered')
            _unique_members(documents)
            groups, folded_posts, folded_photos = _relation(documents, policy)
            for name in ('folded_posts', 'folded_photos'):
                if type(value[name]) is not int or not 0 <= value[name] <= max_members:
                    raise PhotoTrailError('fold counts must be nonnegative integers within max_members')
            if (value['groups'] != groups or value['folded_posts'] != folded_posts
                    or value['folded_photos'] != folded_photos):
                raise PhotoTrailError('view associations or counts do not match original evidence and policy')
            if value['revision'] != _revision(value):
                raise PhotoTrailError('view revision does not match content')
        except BatchFormatError as error:
            raise PhotoTrailError(str(error)) from None
        object.__setattr__(self, '_encoded', encoded)
        object.__setattr__(self, '_posts', posts)
        object.__setattr__(self, '_groups', tuple(tuple(group['post_ids']) for group in groups))
        object.__setattr__(self, '_policy', policy)
        object.__setattr__(self, '_revision_value', value['revision'])
        object.__setattr__(self, '_counts', (folded_posts, folded_photos))

    @classmethod
    def from_json(cls, data, *, max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
        _limits(max_members, max_bytes)
        if type(data) not in (str, bytes):
            raise PhotoTrailError('view JSON must be text or UTF-8 bytes')
        _bytes(data, max_bytes)
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            value = json.loads(data, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
        except (BatchFormatError, ValueError, UnicodeError, RecursionError):
            raise PhotoTrailError('invalid photo-trail JSON') from None
        return cls(value, max_members=max_members, max_bytes=max_bytes)

    def to_json(self):
        return self._encoded

    def to_dict(self):
        return json.loads(self._encoded)

    @property
    def posts(self):
        return self._posts

    @property
    def groups(self):
        return self._groups

    @property
    def policy(self):
        return self._policy

    @property
    def revision(self):
        return self._revision_value

    @property
    def status(self):
        return 'provisional'

    @property
    def folded_posts(self):
        return self._counts[0]

    @property
    def folded_photos(self):
        return self._counts[1]


def fold_photo_trails(posts, *, policy=None, max_members=DEFAULT_MAX_MEMBERS, max_bytes=DEFAULT_MAX_BYTES):
    """Compute a provisional full view, with inference disabled unless opted in.

    Supply current originals for your chosen scope, not the last inferred view.
    Work bounds count input member visits (including duplicate posts) and UTF-8
    input-plus-output bytes. Exact duplicates deduplicate when admitted. Missing
    context is not discoverable here; retained lookup failures must raise.
    """
    _limits(max_members, max_bytes)
    policy = _policy(policy)
    if type(posts) not in (list, tuple) or len(posts) > max_members:
        raise PhotoTrailError('posts must be a concrete list or tuple within max_members')
    by_key, count, size = {}, 0, 0
    for post in posts:
        if type(post) is not TelegramPost:
            raise PhotoTrailError('posts must contain TelegramPost values')
        size += _bytes(post.to_json(), max_bytes)
        if size > max_bytes:
            raise PhotoTrailError('max_bytes exceeded')
        try:
            loaded = TelegramPost.from_json(post.to_json(), max_members=max_members, max_bytes=max_bytes)
        except AlbumAssemblyError as error:
            raise PhotoTrailError('invalid original post: {}'.format(error)) from None
        document = loaded.to_dict()
        count += len(document['members'])
        if count > max_members:
            raise PhotoTrailError('max_members exceeded')
        key = document['post_id']
        if key in by_key and by_key[key] != document:
            raise PhotoTrailError('conflicting current observations of a post')
        by_key[key] = document
    documents = sorted(by_key.values(), key=_order)
    _unique_members(documents)
    groups, folded_posts, folded_photos = _relation(documents, policy)
    document = dict(schema='tgdata.photo-trail-view', version=1, algorithm=_ALGORITHM,
                    status='provisional', policy=policy.to_dict(), posts=documents,
                    groups=groups, folded_posts=folded_posts, folded_photos=folded_photos)
    try:
        document['revision'] = _revision(document)
        size += _bytes(_canonical(document), max_bytes)
    except BatchFormatError as error:
        raise PhotoTrailError(str(error)) from None
    if size > max_bytes:
        raise PhotoTrailError('max_bytes exceeded')
    return PhotoTrailView(document, max_members=max_members, max_bytes=max_bytes)
