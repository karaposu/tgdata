"""Bounded profile observations inside the existing verified-account operation."""

import asyncio
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Optional, Tuple, Union

from telethon.tl import functions, types

from .group_operations import (
    GroupMetadata, GroupReferenceError, GroupResponseError,
    _identity, _integer, _matching, _project, _resolve,
)


_SUPPORTED = ('group', 'megagroup', 'channel')
_MAX_COUNT = 2 ** 31 - 1


def _iso(value):
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


@dataclass(frozen=True)
class GroupPinnedMessage:
    """One returned pin: message, service, or an unavailable placeholder."""

    id: int
    kind: str
    date: Optional[datetime]
    text: Optional[str] = field(repr=False)

    def to_dict(self):
        return dict(id=self.id, kind=self.kind, date=_iso(self.date), text=self.text)


@dataclass(frozen=True)
class GroupProfile:
    """Account-qualified metadata and a separately timed optional pin response."""

    account_id: int
    target: Union[str, int]
    group: GroupMetadata
    about: str = field(repr=False)
    online_count: Optional[int]
    observed_at: datetime
    pinned_messages: Tuple[GroupPinnedMessage, ...] = ()
    pins_status: str = 'not_requested'
    pins_total: Optional[int] = None
    pins_total_exact: Optional[bool] = None
    pins_observed_at: Optional[datetime] = None

    def to_dict(self):
        return dict(
            account_id=self.account_id, target=self.target, group=self.group.to_dict(),
            about=self.about, online_count=self.online_count, observed_at=_iso(self.observed_at),
            pinned_messages=[message.to_dict() for message in self.pinned_messages],
            pins_status=self.pins_status, pins_total=self.pins_total,
            pins_total_exact=self.pins_total_exact, pins_observed_at=_iso(self.pins_observed_at),
        )


def _pin_limit(value):
    if not _integer(value, 0, 100):
        raise ValueError('pinned_limit must be an integer between 0 and 100')
    return value


def _count(value):
    if value is not None and not _integer(value, 0, _MAX_COUNT):
        raise GroupResponseError('Invalid group profile count')
    return value


def _date(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise GroupResponseError('Invalid pinned message date')
    return value.astimezone(timezone.utc)


def _full_profile(reply, lookup, peer):
    basic = isinstance(peer, types.InputPeerChat)
    expected_full = types.ChatFull if basic else types.ChannelFull
    if not isinstance(reply, types.messages.ChatFull):
        raise GroupResponseError('Unexpected full group response')
    full = reply.full_chat
    if (not isinstance(full, expected_full) or not _integer(full.id, 1)
            or full.id != lookup.group.id):
        raise GroupResponseError('Full group response does not match the requested peer')
    namespace = types.PeerChat if basic else types.PeerChannel
    entity = _matching(reply.chats, lookup.group.id, namespace)
    group, _, _, _ = _project(entity)
    if group.peer_id != lookup.group.peer_id or group.kind not in _SUPPORTED:
        raise GroupResponseError('Unexpected full group metadata')
    if not isinstance(full.about, str):
        raise GroupResponseError('Invalid group description')
    count = _count(group.participants_count if basic else full.participants_count)
    online = None if basic else _count(full.online_count)
    return GroupProfile(
        lookup.account_id, lookup.target, replace(group, participants_count=count),
        full.about, online, datetime.now(timezone.utc),
    )


def _pins(reply, expected_peer, limit):
    if not isinstance(reply, (types.messages.Messages, types.messages.MessagesSlice,
                              types.messages.ChannelMessages)):
        raise GroupResponseError('Unexpected pinned message response')
    rows = reply.messages
    if not isinstance(rows, (list, tuple)) or len(rows) > limit:
        raise GroupResponseError('Invalid pinned message vector')
    if isinstance(reply, types.messages.Messages):
        total, exact = len(rows), True
    else:
        total = _count(reply.count)
        inexact = reply.inexact
        if total is None or (inexact is not None and type(inexact) is not bool):
            raise GroupResponseError('Invalid pinned message count evidence')
        exact = not bool(inexact)
        if exact and total < len(rows):
            raise GroupResponseError('Pinned message count is smaller than its response')
    result, seen, unavailable = [], set(), False
    for message in rows:
        if not isinstance(message, (types.Message, types.MessageService, types.MessageEmpty)):
            raise GroupResponseError('Invalid pinned message')
        if not _integer(message.id, 1, _MAX_COUNT) or message.id in seen:
            raise GroupResponseError('Invalid or duplicate pinned message ID')
        seen.add(message.id)
        peer = message.peer_id
        if not (peer is None and isinstance(message, types.MessageEmpty)):
            if not isinstance(peer, (types.PeerChat, types.PeerChannel)):
                raise GroupResponseError('Invalid pinned message peer')
            if _identity(peer)[2] != expected_peer:
                raise GroupResponseError('Pinned message belongs to another peer')
        if isinstance(message, types.MessageEmpty):
            unavailable = True
            result.append(GroupPinnedMessage(message.id, 'unavailable', None, None))
        elif isinstance(message, types.MessageService):
            result.append(GroupPinnedMessage(message.id, 'service', _date(message.date), None))
        else:
            if not isinstance(message.message, str):
                raise GroupResponseError('Invalid pinned message text')
            result.append(GroupPinnedMessage(message.id, 'message', _date(message.date),
                                             message.message))
    if exact and not unavailable and total == len(rows):
        status = 'complete'
    elif exact and not unavailable and total > len(rows) and len(rows) == limit:
        status = 'limited'
    else:
        status = 'incomplete'
    return tuple(result), status, total, exact


async def _get_group_profile(operation, target, pinned_limit, beat=None):
    lookup, peer = await _resolve(operation, target)
    if lookup.group.kind not in _SUPPORTED or not isinstance(
            peer, (types.InputPeerChat, types.InputPeerChannel)):
        raise GroupReferenceError(
            'Group profile requires a supported group with a usable peer; '
            'use lookup_group for an invite-only preview')
    request = (functions.messages.GetFullChatRequest(peer.chat_id)
               if isinstance(peer, types.InputPeerChat) else
               functions.channels.GetFullChannelRequest(
                   types.InputChannel(peer.channel_id, peer.access_hash)))
    profile = _full_profile(await operation.client(request), lookup, peer)
    if beat is not None:
        beat('profile done')
    if not pinned_limit:
        return profile
    try:
        reply = await operation.client(functions.messages.SearchRequest(
            peer=peer, q='', filter=types.InputMessagesFilterPinned(),
            min_date=None, max_date=None, offset_id=0, add_offset=0,
            limit=pinned_limit, max_id=0, min_id=0, hash=0))
        messages, status, total, exact = _pins(reply, profile.group.peer_id, pinned_limit)
        result = replace(profile, pinned_messages=messages, pins_status=status,
                         pins_total=total, pins_total_exact=exact,
                         pins_observed_at=datetime.now(timezone.utc))
    except (Exception, asyncio.CancelledError) as error:
        # The source exception remains authoritative; annotating it is secondary.
        try:
            error.partial_result = replace(profile, pins_status='failed')
        except (Exception, asyncio.CancelledError):
            pass
        raise
    if beat is not None:
        beat('pins done')
    return result
