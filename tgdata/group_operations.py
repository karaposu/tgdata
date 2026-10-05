"""Portable observations for short-lived group operations (issue #7)."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import logging
import re
from typing import Optional, Union
from urllib.parse import urlsplit

from telethon import errors, utils
from telethon.tl import functions, types

from . import health

logger = logging.getLogger(__name__)


class GroupOperationError(RuntimeError):
    """A local operation failure, never an inherited Telegram verdict."""

    def __init__(self, message):
        super().__init__(message)
        self.__suppress_context__ = True


class GroupReferenceError(GroupOperationError, ValueError):
    pass


class GroupResponseError(GroupOperationError):
    pass


@dataclass(frozen=True)
class _Target:
    kind: str
    value: Union[str, int] = field(repr=False)
    label: Union[str, int]


_HANDLE = re.compile(r'[A-Za-z][A-Za-z0-9_]{3,31}\Z')
_INVITE = re.compile(r'[A-Za-z0-9_-]{1,256}\Z')
_HOSTS = {'t.me', 'telegram.me', 'www.t.me', 'www.telegram.me'}


def _parse_target(value, *, joining=False):
    if isinstance(value, bool):
        raise GroupReferenceError('A group reference must be a handle, invite link or group ID')
    if isinstance(value, str):
        value = value.strip()
        if re.fullmatch(r'-?\d+', value):
            try:
                value = int(value)
            except ValueError:
                raise GroupReferenceError('Group ID is outside the supported range') from None
    if isinstance(value, int):
        if joining or value == 0 or not -(2 ** 63) < value < 2 ** 63:
            raise GroupReferenceError('Joining requires a handle or invite link; lookup IDs must be nonzero signed integers')
        return _Target('id', value, value)
    if not isinstance(value, str) or not value:
        raise GroupReferenceError('A group reference must be a handle, invite link or group ID')
    if value.startswith('@'):
        handle = value[1:]
    elif _HANDLE.fullmatch(value):
        handle = value
    else:
        url = value
        if re.match(r'^(?:www\.)?(?:t\.me|telegram\.me)/', url, re.I):
            url = 'https://' + url
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme.lower() in ('http', 'https')
                     and parsed.netloc.lower() in _HOSTS
                     and parsed.hostname in _HOSTS
                     and not parsed.query and not parsed.fragment)
        except (ValueError, TypeError):
            raise GroupReferenceError('Invalid Telegram group link') from None
        if not valid:
            raise GroupReferenceError('Expected a Telegram group handle or invite link')
        path = parsed.path
        invite = (path[2:] if path.startswith('/+') else
                  path[len('/joinchat/'):] if path.startswith('/joinchat/') else None)
        if invite is not None:
            if not _INVITE.fullmatch(invite):
                raise GroupReferenceError('Invalid Telegram invite link')
            label = 'invite:' + hashlib.sha256(invite.encode('ascii')).hexdigest()[:16]
            return _Target('invite', invite, label)
        handle = path[1:] if path.startswith('/') else ''
    if not _HANDLE.fullmatch(handle):
        raise GroupReferenceError('Invalid Telegram group handle')
    return _Target('handle', handle.lower(), handle.lower())


class _Portable:
    def to_dict(self):
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.astimezone(timezone.utc).isoformat()
        return result


@dataclass(frozen=True)
class GroupMetadata(_Portable):
    id: Optional[int]
    peer_id: Optional[int]
    title: Optional[str]
    username: Optional[str]
    kind: str
    participants_count: Optional[int] = None


@dataclass(frozen=True)
class GroupLookup(_Portable):
    target: Union[str, int]
    group: GroupMetadata
    member: Optional[bool]
    request_needed: Optional[bool] = None
    requires_payment: bool = False
    preview_expires_at: Optional[datetime] = None


@dataclass(frozen=True)
class GroupAccess(_Portable):
    target: Union[str, int]
    group: Optional[GroupMetadata]
    member: Optional[bool]
    status: str
    reason: Optional[str] = None

    @property
    def readable(self):
        return {'readable': True, 'denied': False, 'unprobed': None}[self.status]

    def to_dict(self):
        result = super().to_dict()
        result['readable'] = self.readable
        return result


@dataclass(frozen=True)
class GroupJoin(_Portable):
    target: Union[str, int]
    group: Optional[GroupMetadata]
    status: str
    bot_id: Optional[int] = None
    query_id: Optional[int] = None

    @property
    def member(self):
        return True if self.status in ('joined', 'already_joined') else None

    def to_dict(self):
        result = super().to_dict()
        result['member'] = self.member
        return result


_GROUPS = (types.Chat, types.Channel, types.ChatForbidden, types.ChannelForbidden)
_CHANNELS = (types.Channel, types.ChannelForbidden)
_MESSAGES = (types.messages.Messages, types.messages.MessagesSlice, types.messages.ChannelMessages)


def _metadata(entity):
    if not isinstance(entity, _GROUPS):
        raise GroupReferenceError('The reference does not identify a group or channel')
    if isinstance(entity, types.Chat) and (entity.deactivated or entity.migrated_to):
        raise GroupReferenceError('The basic group is inactive or migrated; use its current reference')
    kind = ('group' if not isinstance(entity, _CHANNELS) else
            'megagroup' if entity.megagroup else
            'channel' if entity.broadcast else 'unknown')
    return GroupMetadata(entity.id, utils.get_peer_id(entity), entity.title,
                         getattr(entity, 'username', None), kind,
                         getattr(entity, 'participants_count', None))


def _member(entity):
    if isinstance(entity, (types.ChatForbidden, types.ChannelForbidden)) or getattr(entity, 'min', False):
        return None
    return not bool(entity.left)


def _input_peer(entity):
    if entity is None:
        return None
    if isinstance(entity, _CHANNELS) and (not entity.access_hash or getattr(entity, 'min', False)):
        return None
    try:
        return utils.get_input_peer(entity)
    except (TypeError, ValueError):
        return None


def _cached_peer(client, ident):
    # A positive ID carries no peer kind. Refuse collisions instead of relying
    # on a session set's iteration order to choose between chat/channel/user.
    candidates = ([types.PeerChat(ident), types.PeerChannel(ident), types.PeerUser(ident)]
                  if ident > 0 else [ident])
    peers = []
    for candidate in candidates:
        try:
            marked = candidate if isinstance(candidate, int) else utils.get_peer_id(candidate)
            if client.session.get_entity_rows_by_id(marked, exact=True) is None:
                continue
            peers.append(client.session.get_input_entity(candidate))
        except (ValueError, TypeError):
            continue
        except Exception as exc:
            raise GroupOperationError('Group cache lookup failed ({})'.format(type(exc).__name__)) from None
    if len(peers) != 1:
        raise GroupReferenceError('Group ID is missing or ambiguous in this session; use a handle or marked ID')
    if not isinstance(peers[0], (types.InputPeerChat, types.InputPeerChannel)):
        raise GroupReferenceError('The reference does not identify a group or channel')
    return peers[0]


class GroupEngine:
    """Operation behavior on the single client owned by its facade call."""

    def __init__(self, connection_engine):
        self.connection_engine = connection_engine

    async def _resolve(self, client, target):
        if target.kind == 'invite':
            reply = await client(functions.messages.CheckChatInviteRequest(target.value), flood_sleep_threshold=0)
            if isinstance(reply, types.ChatInvite):
                kind = ('megagroup' if reply.megagroup else
                        'channel' if reply.broadcast or reply.channel else 'group')
                group = GroupMetadata(None, None, reply.title, None, kind, reply.participants_count)
                return GroupLookup(target.label, group, False, bool(reply.request_needed),
                                   reply.subscription_pricing is not None), None
            if isinstance(reply, (types.ChatInviteAlready, types.ChatInvitePeek)):
                group = _metadata(reply.chat)
                already = isinstance(reply, types.ChatInviteAlready)
                return GroupLookup(target.label, group, already,
                                   preview_expires_at=None if already else reply.expires), reply.chat
            raise GroupResponseError('Unexpected Telegram invite preview response')
        if target.kind == 'handle':
            reply = await client(functions.contacts.ResolveUsernameRequest(target.value), flood_sleep_threshold=0)
            peer = getattr(reply, 'peer', None)
            if not isinstance(peer, (types.PeerChat, types.PeerChannel)):
                raise GroupReferenceError('The handle does not identify a group or channel')
            matches = [chat for chat in reply.chats if isinstance(chat, _GROUPS)
                       and utils.get_peer_id(chat) == utils.get_peer_id(peer)]
            if len(matches) != 1:
                raise GroupResponseError('Telegram did not return the resolved group')
            entity = matches[0]
        else:
            peer = _cached_peer(client, target.value)
            try:
                entity = await client.get_entity(peer)
            except (ValueError, TypeError, KeyError):
                raise GroupReferenceError('Telegram did not resolve the cached group peer') from None
        group = _metadata(entity)
        return GroupLookup(target.label, group, _member(entity),
                           getattr(entity, 'join_request', None)), entity

    async def lookup_group(self, client, target):
        lookup, _ = await self._resolve(client, target)
        return lookup

    async def check_group_access(self, client, target):
        lookup = None
        try:
            lookup, entity = await self._resolve(client, target)
            peer = _input_peer(entity)
            if peer is None:
                return GroupAccess(target.label, lookup.group, lookup.member, 'unprobed', 'NO_PEER')
            result = await client(functions.messages.GetHistoryRequest(
                peer, 0, None, 0, 1, 0, 0, 0), flood_sleep_threshold=0)
            if not isinstance(result, _MESSAGES):
                raise GroupResponseError('Unexpected Telegram history response')
            return GroupAccess(target.label, lookup.group, lookup.member, 'readable')
        except errors.RPCError as exc:
            finding = health.classify(exc, include_reported=True)
            if finding is None or finding.verdict != health.NO_ACCESS or finding.scope != 'group':
                raise
            await health.report(exc, 'handled')
            return GroupAccess(target.label, lookup.group if lookup else None,
                               lookup.member if lookup else None, 'denied', finding.error)

    async def join_group(self, client, target):
        # Public facade already requires a configured budget object. Require an
        # account policy even for a no-op; a zero cap may still observe membership.
        budget = self.connection_engine.join_budget
        budget.status(await client._join_budget_account())
        lookup, entity = await self._resolve(client, target)
        if lookup.member is True:
            return GroupJoin(target.label, lookup.group, 'already_joined')
        if lookup.requires_payment:
            return GroupJoin(target.label, lookup.group, 'payment_required')
        if target.kind == 'invite':
            request = functions.messages.ImportChatInviteRequest(target.value)
        else:
            if not isinstance(entity, _CHANNELS) or _input_peer(entity) is None:
                raise GroupReferenceError('This handle does not provide a joinable channel peer')
            request = functions.channels.JoinChannelRequest(utils.get_input_channel(entity))
        try:
            reply = await client(request, flood_sleep_threshold=0)
        except errors.UserAlreadyParticipantError:
            return GroupJoin(target.label, lookup.group, 'already_joined')
        except errors.InviteRequestSentError:
            return GroupJoin(target.label, lookup.group, 'requested')
        except errors.RPCError as exc:
            if health.telegram_error_name(exc) == 'STARS_PAYMENT_REQUIRED':
                return GroupJoin(target.label, lookup.group, 'payment_required')
            raise
        if isinstance(reply, types.messages.ChatInviteJoinResultWebView):
            return GroupJoin(target.label, lookup.group, 'interaction_required', reply.bot_id, reply.query_id)
        if not isinstance(reply, types.messages.ChatInviteJoinResultOk):
            raise GroupResponseError('Unexpected Telegram join response; attempt remains charged')
        group = lookup.group
        # An acknowledged join stays acknowledged even if optional local cache
        # writes or metadata projection fail. No network enrichment follows it.
        try:
            await utils.maybe_async(client.session.process_entities(reply.updates))
            chats = [chat for chat in getattr(reply.updates, 'chats', []) if isinstance(chat, _GROUPS)]
            if group.peer_id is not None:
                chats = [chat for chat in chats if utils.get_peer_id(chat) == group.peer_id]
            if len(chats) == 1:
                group = _metadata(chats[0])
        except Exception as exc:
            try:
                logger.warning('Joined group; optional local enrichment failed (%s)', type(exc).__name__)
            except Exception:
                pass  # A caller's logging handler cannot erase the acknowledgment either.
        return GroupJoin(target.label, group, 'joined')
