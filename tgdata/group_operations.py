"""Group observations and joining on an already verified account operation."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import re
from typing import Optional, Union
from urllib.parse import urlsplit

from telethon import utils
from telethon.errors import RPCError
from telethon.tl import functions, types

from . import health
from .join_client import _join_error_matches


class GroupReferenceError(ValueError):
    """A reference is unsupported, ambiguous, unavailable or not a group."""
    def __init__(self, message='Cannot resolve this group reference'):
        super().__init__(message)
        self.__suppress_context__ = True


class GroupResponseError(RuntimeError):
    """Telegram's reply cannot support a consistent group observation."""
    def __init__(self, message='Unexpected Telegram group response'):
        super().__init__(message)
        self.__suppress_context__ = True


@dataclass(frozen=True)
class GroupMetadata:
    id: Optional[int]
    peer_id: Optional[int]
    title: str
    username: Optional[str]
    kind: str
    participants_count: Optional[int]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class GroupLookup:
    account_id: int
    target: Union[str, int]
    group: GroupMetadata
    member: Optional[bool]
    request_needed: Optional[bool] = None
    requires_payment: Optional[bool] = None
    preview_expires_at: Optional[datetime] = None

    def to_dict(self):
        result = asdict(self)
        if self.preview_expires_at is not None:
            result['preview_expires_at'] = self.preview_expires_at.astimezone(timezone.utc).isoformat()
        return result


@dataclass(frozen=True)
class GroupAccess:
    account_id: int
    target: Union[str, int]
    status: str
    lookup: Optional[GroupLookup] = None
    reason: Optional[str] = None

    @property
    def group(self):
        return self.lookup.group if self.lookup is not None else None

    @property
    def member(self):
        return self.lookup.member if self.lookup is not None else None

    @property
    def readable(self):
        return {'readable': True, 'denied': False, 'unprobed': None}[self.status]

    def to_dict(self):
        return dict(account_id=self.account_id, target=self.target, status=self.status,
                    lookup=self.lookup.to_dict() if self.lookup is not None else None,
                    reason=self.reason, readable=self.readable)


@dataclass(frozen=True)
class GroupJoin:
    account_id: int
    target: Union[str, int]
    group: GroupMetadata
    status: str
    bot_id: Optional[int] = None
    query_id: Optional[int] = None

    @property
    def member(self):
        return True if self.status in ('joined', 'already_joined') else None

    def to_dict(self):
        return dict(account_id=self.account_id, target=self.target,
                    group=self.group.to_dict(), status=self.status, member=self.member,
                    bot_id=self.bot_id, query_id=self.query_id)


@dataclass(frozen=True)
class _Target:
    kind: str
    value: Union[str, int] = field(repr=False)
    label: Union[str, int]


_MIN, _MAX = -(2 ** 63), 2 ** 63 - 1
_HANDLE = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,31}\Z')
_INVITE = re.compile(r'[A-Za-z0-9_-]{1,256}\Z')
_DECIMAL = re.compile(r'[+-]?[0-9]+\Z')
_BASIC = (types.Chat, types.ChatForbidden, types.ChatEmpty)
_CHANNEL = (types.Channel, types.ChannelForbidden, types.Community, types.CommunityForbidden)
_FULL = (types.Chat, types.Channel, types.Community)
_HOSTS = {'t.me', 'telegram.me', 'www.t.me', 'www.telegram.me'}


def _integer(value, minimum=_MIN, maximum=_MAX):
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def _parse_target(value):
    if _integer(value) and value != 0:
        return _Target('id', value, value)
    if not isinstance(value, str):
        raise GroupReferenceError('Group reference must be a name, link or nonzero integer')
    text = value.strip()
    if any(character.isspace() or ord(character) < 32 for character in text):
        raise GroupReferenceError('Unsupported group reference')
    if _DECIMAL.fullmatch(text):
        try:
            number = int(text)
        except ValueError:
            raise GroupReferenceError('Group ID is outside the supported range') from None
        if not _integer(number) or number == 0:
            raise GroupReferenceError('Group ID is outside the supported range')
        return _Target('id', number, number)
    # Bare handles do not enter Telethon's general string resolver (me/self/phones).
    name = text[1:] if text.startswith('@') else text
    if _HANDLE.fullmatch(name):
        return _Target('handle', name.lower(), name.lower())
    try:
        url = urlsplit(text if '://' in text else 'https://' + text)
    except ValueError:
        raise GroupReferenceError('Unsupported Telegram group link') from None
    if (url.scheme.lower() not in ('http', 'https') or url.netloc.lower() not in _HOSTS
            or url.query or url.fragment or '?' in text or '#' in text):
        raise GroupReferenceError('Unsupported Telegram group link')
    path = url.path
    if path.endswith('/'):
        path = path[:-1]
    if path == '/joinchat':
        raise GroupReferenceError('Unsupported Telegram invite link')
    if path.startswith('/+'):
        token = path[2:]
    elif path.startswith('/joinchat/'):
        token = path[len('/joinchat/'):]
    else:
        name = path[1:] if path.startswith('/') else ''
        if not _HANDLE.fullmatch(name):
            raise GroupReferenceError('Unsupported Telegram group link')
        return _Target('handle', name.lower(), name.lower())
    if not _INVITE.fullmatch(token):
        raise GroupReferenceError('Unsupported Telegram invite link')
    return _Target('invite', token, 'invite:' + hashlib.sha256(token.encode('ascii')).hexdigest())


def _canonical(number, namespace):
    """Return a representable marked ID only if marking preserves its namespace."""
    if not _integer(number, 1):
        return None
    marked = utils.get_peer_id(namespace(number))
    if not _integer(marked) or utils.resolve_id(marked) != (number, namespace):
        return None
    return marked


def _identity(entity):
    if isinstance(entity, _BASIC):
        number, namespace = entity.id, types.PeerChat
    elif isinstance(entity, _CHANNEL):
        number, namespace = entity.id, types.PeerChannel
    elif isinstance(entity, types.PeerChat):
        number, namespace = entity.chat_id, types.PeerChat
    elif isinstance(entity, types.PeerChannel):
        number, namespace = entity.channel_id, types.PeerChannel
    else:
        raise GroupResponseError()
    marked = _canonical(number, namespace)
    if marked is None:
        raise GroupResponseError()
    return number, namespace, marked


def _matching(chats, number, namespace):
    if not isinstance(chats, (list, tuple)):
        raise GroupResponseError()
    matches = []
    for entity in chats:
        if not isinstance(entity, _BASIC + _CHANNEL):
            raise GroupResponseError()
        actual, kind, _ = _identity(entity)
        if actual == number and kind is namespace:
            matches.append(entity)
    if len(matches) != 1:
        raise GroupResponseError()
    return matches[0]


def _row(session, marked):
    row = session.get_entity_rows_by_id(marked, exact=True)
    if row is None:
        return None
    if (not isinstance(row, (list, tuple)) or len(row) != 2
            or not _integer(row[0]) or row[0] != marked):
        raise GroupReferenceError('Invalid cached group reference')
    return row


def _numeric_peer(session, number):
    if number < 0:
        raw, namespace = utils.resolve_id(number)
        if _canonical(raw, namespace) != number:
            raise GroupReferenceError('Unsupported group ID')
        if namespace is types.PeerChat:
            return raw, namespace, None
        row = _row(session, number)
    else:
        candidates = []
        for namespace in (types.PeerChat, types.PeerChannel):
            marked = _canonical(number, namespace)
            row = _row(session, marked) if marked is not None else None
            if row is not None:
                candidates.append((namespace, row))
        if len(candidates) != 1:
            raise GroupReferenceError('Group ID requires one unambiguous cached group')
        namespace, row = candidates[0]
        raw = number
        if namespace is types.PeerChat:
            return raw, namespace, None
    if row is None or not _integer(row[1]):
        raise GroupReferenceError('Channel ID requires a cached access hash')
    return raw, namespace, row[1]


def _text_count(source):
    title = source.title
    username = getattr(source, 'username', None)
    count = getattr(source, 'participants_count', None)
    if (not isinstance(title, str) or (username is not None and not isinstance(username, str))
            or (count is not None and not _integer(count, 0))):
        raise GroupResponseError()
    return title, username, count


def _channel_kind(source):
    if getattr(source, 'megagroup', False):
        return 'megagroup'
    if getattr(source, 'broadcast', False):
        return 'channel'
    return 'unknown'


def _project(entity):
    number, namespace, marked = _identity(entity)
    if isinstance(entity, types.ChatEmpty) or (isinstance(entity, types.Chat) and
            (entity.deactivated or entity.migrated_to is not None)):
        raise GroupReferenceError('Group is unavailable or has migrated')
    title, username, count = _text_count(entity)
    minimal = bool(getattr(entity, 'min', False))
    member = not bool(entity.left) if isinstance(entity, _FULL) and not minimal else None
    request_needed = (bool(entity.join_request)
                      if isinstance(entity, types.Channel) and not minimal else None)
    if namespace is types.PeerChat:
        kind, peer = 'group', types.InputPeerChat(number)
    else:
        kind = ('community' if isinstance(entity, (types.Community, types.CommunityForbidden))
                else _channel_kind(entity))
        access_hash = entity.access_hash
        if access_hash is not None and not _integer(access_hash):
            raise GroupResponseError()
        peer = (types.InputPeerChannel(number, access_hash)
                if access_hash is not None and not minimal else None)
    return GroupMetadata(number, marked, title, username, kind, count), member, request_needed, peer


async def _resolve(operation, target):
    client = operation.client
    if target.kind == 'handle':
        result = await client(functions.contacts.ResolveUsernameRequest(target.value))
        if not isinstance(result, types.contacts.ResolvedPeer):
            raise GroupResponseError()
        if isinstance(result.peer, types.PeerUser):
            raise GroupReferenceError('Reference identifies a user, not a group')
        if not isinstance(result.peer, (types.PeerChat, types.PeerChannel)):
            raise GroupResponseError()
        number, namespace, _ = _identity(result.peer)
        entity = _matching(result.chats, number, namespace)
    elif target.kind == 'id':
        number, namespace, access_hash = _numeric_peer(client.session, target.value)
        request = (functions.messages.GetChatsRequest([number]) if namespace is types.PeerChat
                   else functions.channels.GetChannelsRequest([types.InputChannel(number, access_hash)]))
        result = await client(request)
        if not isinstance(result, (types.messages.Chats, types.messages.ChatsSlice)):
            raise GroupResponseError()
        entity = _matching(result.chats, number, namespace)
    else:
        result = await client(functions.messages.CheckChatInviteRequest(target.value))
        if isinstance(result, types.ChatInvite):
            title, _, count = _text_count(result)
            kind = _channel_kind(result) if result.channel else 'group'
            metadata = GroupMetadata(None, None, title, None, kind, count)
            return GroupLookup(operation.account_id, target.label, metadata, False,
                               bool(result.request_needed), result.subscription_pricing is not None), None
        if not isinstance(result, (types.ChatInviteAlready, types.ChatInvitePeek)):
            raise GroupResponseError()
        entity = result.chat
    metadata, member, request_needed, peer = _project(entity)
    expires = None
    if target.kind == 'invite':
        member = isinstance(result, types.ChatInviteAlready)
        if isinstance(result, types.ChatInvitePeek) and result.expires is not None:
            if not isinstance(result.expires, datetime) or result.expires.utcoffset() is None:
                raise GroupResponseError()
            expires = result.expires.astimezone(timezone.utc)
    return GroupLookup(operation.account_id, target.label, metadata, member,
                       request_needed=request_needed, preview_expires_at=expires), peer


async def _lookup_group(operation, target):
    lookup, _ = await _resolve(operation, target)
    return lookup


def _validate_history(result, expected_peer):
    if not isinstance(result, (types.messages.Messages, types.messages.MessagesSlice,
                               types.messages.ChannelMessages)):
        raise GroupResponseError()
    if not isinstance(result.messages, (list, tuple)) or len(result.messages) > 1:
        raise GroupResponseError()
    for message in result.messages:
        if not isinstance(message, (types.Message, types.MessageService, types.MessageEmpty)):
            raise GroupResponseError()
        peer = message.peer_id
        if peer is None and isinstance(message, types.MessageEmpty):
            continue
        if not isinstance(peer, (types.PeerChat, types.PeerChannel)):
            raise GroupResponseError()
        if _identity(peer)[2] != expected_peer:
            raise GroupResponseError()


async def _check_group_access(operation, target):
    lookup = None
    try:
        lookup, peer = await _resolve(operation, target)
        if peer is None:
            return GroupAccess(operation.account_id, target.label, 'unprobed', lookup, 'NO_PEER')
        result = await operation.client(functions.messages.GetHistoryRequest(
            peer=peer, offset_id=0, offset_date=None, add_offset=0,
            limit=1, max_id=0, min_id=0, hash=0))
        _validate_history(result, lookup.group.peer_id)
        return GroupAccess(operation.account_id, target.label, 'readable', lookup)
    except RPCError as exc:
        finding = health.classify(exc, include_reported=True)
        if finding is not None and finding.verdict == health.NO_ACCESS and finding.scope == 'group':
            return GroupAccess(operation.account_id, target.label, 'denied', lookup, finding.error)
        raise


_UPDATES = (types.UpdateShort, types.UpdateShortChatMessage, types.UpdateShortMessage,
            types.UpdateShortSentMessage, types.Updates, types.UpdatesCombined,
            types.UpdatesTooLong)


async def _join_group(operation, target):
    """One logical join; admission is at the SDK send boundary, not here."""
    lookup, peer = await _resolve(operation, target)

    def outcome(status, bot_id=None, query_id=None):
        # Metadata is explicitly the preflight observation, not post-join enrichment.
        return GroupJoin(operation.account_id, target.label, lookup.group, status, bot_id, query_id)

    if lookup.member is True:
        return outcome('already_joined')
    if lookup.requires_payment is True:
        return outcome('payment_required')
    if target.kind == 'invite':
        request = functions.messages.ImportChatInviteRequest(target.value)
    else:
        if not isinstance(peer, types.InputPeerChannel) or lookup.group.kind == 'community':
            raise GroupReferenceError('This group has no supported direct join peer; use an invite link')
        request = functions.channels.JoinChannelRequest(types.InputChannel(peer.channel_id, peer.access_hash))
    try:
        reply = await operation.client(request)
    except RPCError as exc:
        # Fresh self proof and SDK resolution can also fail inside this await.
        # A name such as INVITE_REQUEST_SENT is meaningful only for this mutation.
        if not _join_error_matches(exc, request):
            raise
        name = health.telegram_error_name(exc)
        if name == 'USER_ALREADY_PARTICIPANT':
            return outcome('already_joined')
        if name == 'INVITE_REQUEST_SENT':
            return outcome('requested')
        if name == 'STARS_PAYMENT_REQUIRED':
            return outcome('payment_required')
        raise
    if isinstance(reply, types.messages.ChatInviteJoinResultOk):
        if not isinstance(getattr(reply, 'updates', None), _UPDATES):
            raise GroupResponseError('Invalid Telegram join acknowledgment payload')
        return outcome('joined')
    if isinstance(reply, types.messages.ChatInviteJoinResultWebView):
        if not _integer(getattr(reply, 'bot_id', None), 1) or not _integer(getattr(reply, 'query_id', None)):
            raise GroupResponseError('Invalid Telegram join interaction fields')
        return outcome('interaction_required', reply.bot_id, reply.query_id)
    raise GroupResponseError('Unexpected Telegram join response; the attempt remains charged')
