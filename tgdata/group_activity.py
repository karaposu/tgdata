"""Bounded observations of visible history and descriptive, raw-message statistics."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Optional, Tuple, Union

from telethon.tl import functions, types

from .group_operations import (
    GroupMetadata, GroupReferenceError, GroupResponseError, _integer, _resolve,
)
from .history_observation import history_page
from .history_window import _HistoryWindow


_MAX_INT = 2**31-1


def _iso(value):
    return value.isoformat() if value is not None else None


@dataclass(frozen=True)
class ActivityMessage:
    """One in-window raw message, with counters observed when its page arrived."""

    id: int
    kind: str
    date: datetime
    observed_at: datetime
    sender_kind: str
    sender_id: Optional[int]
    grouped_id: Optional[int]
    views: Optional[int]
    reactions: Optional[int]
    forwards: Optional[int]
    replies: Optional[int]
    replies_are_comments: Optional[bool]

    def to_dict(self):
        return dict(
            id=self.id, kind=self.kind, date=_iso(self.date),
            observed_at=_iso(self.observed_at), sender_kind=self.sender_kind,
            sender_id=self.sender_id,
            grouped_id=str(self.grouped_id) if self.grouped_id is not None else None,
            views=self.views, reactions=self.reactions, forwards=self.forwards,
            replies=self.replies, replies_are_comments=self.replies_are_comments,
        )


def _population():
    return dict(messages=0, users=set(), channels=set(), unknown=0)


def _add(population, message):
    population['messages'] += 1
    if message.sender_kind == 'user':
        population['users'].add(message.sender_id)
    elif message.sender_kind == 'channel':
        population['channels'].add(message.sender_id)
    else:
        population['unknown'] += 1


def _counts(population):
    return dict(
        message_count=population['messages'],
        known_user_count=len(population['users']),
        channel_sender_count=len(population['channels']),
        unknown_author_messages=population['unknown'],
    )


def _distribution(values, total):
    return dict(
        known_count=len(values), missing_count=total-len(values),
        sum=sum(values) if values else None,
        mean=sum(values)/len(values) if values else None,
        median=median(values) if values else None,
        min=min(values) if values else None, max=max(values) if values else None,
    )


@dataclass(frozen=True)
class GroupActivity:
    """A versioned observation, never an atomic snapshot or durable read cursor."""

    account_id: int
    target: Union[str, int]
    group: GroupMetadata
    start_date: datetime
    end_date: datetime
    collection_started_at: datetime
    collection_finished_at: datetime
    max_messages: int
    scanned_messages: int
    unavailable_messages: int
    pages: int
    stop_reason: str
    coverage_complete: bool
    oldest_observed_message_date: Optional[datetime]
    newest_observed_message_date: Optional[datetime]
    messages: Tuple[ActivityMessage, ...] = field(repr=False)
    schema_version: int = field(default=1, init=False)

    @property
    def statistics(self):
        """Fresh descriptive data; no mutable derived state is stored in the value."""
        total, by_day = _population(), {}
        counters = {name: [] for name in ('views', 'reactions', 'forwards', 'replies')}
        services, latest = 0, None
        for message in self.messages:
            if message.kind == 'service':
                services += 1
                continue
            _add(total, message)
            bucket = by_day.setdefault(message.date.date(), _population())
            _add(bucket, message)
            latest = message.date if latest is None else max(latest, message.date)
            for name, values in counters.items():
                value = getattr(message, name)
                if value is not None:
                    values.append(value)
        daily = []
        day = self.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        while day < self.end_date:
            next_day = day + timedelta(days=1)
            start, end = max(day, self.start_date), min(next_day, self.end_date)
            row = _counts(by_day.get(day.date(), _population()))
            row.update(date=day.date().isoformat(), start_date=_iso(start),
                       end_date=_iso(end), window_seconds=(end-start).total_seconds())
            daily.append(row)
            day = next_day
        result = _counts(total)
        seconds = (self.end_date-self.start_date).total_seconds()
        result.update(
            service_message_count=services, latest_observed_message_date=_iso(latest),
            daily=daily, window_seconds=seconds,
            messages_per_24h=total['messages']*86400/seconds if self.coverage_complete else None,
            counters={name: _distribution(values, total['messages'])
                      for name, values in counters.items()},
        )
        return result

    def to_dict(self):
        return dict(
            schema_version=self.schema_version, account_id=self.account_id,
            target=self.target, group=self.group.to_dict(),
            start_date=_iso(self.start_date), end_date=_iso(self.end_date),
            collection_started_at=_iso(self.collection_started_at),
            collection_finished_at=_iso(self.collection_finished_at),
            max_messages=self.max_messages, scanned_messages=self.scanned_messages,
            unavailable_messages=self.unavailable_messages, pages=self.pages,
            stop_reason=self.stop_reason, coverage_complete=self.coverage_complete,
            oldest_observed_message_date=_iso(self.oldest_observed_message_date),
            newest_observed_message_date=_iso(self.newest_observed_message_date),
            messages=[message.to_dict() for message in self.messages],
            statistics=self.statistics,
        )


def _measurement_parameters(start_date, end_date, max_messages, now):
    window = _HistoryWindow(start_date, end_date)
    if window.end_date > now:
        raise ValueError('end_date must not be in the future')
    if not _integer(max_messages, 1, _MAX_INT):
        raise ValueError('max_messages must be an integer between 1 and 2147483647')
    return window


def _count(value):
    if value is not None and not _integer(value, 0, _MAX_INT):
        raise GroupResponseError('Invalid activity counter')
    return value


def _message(message, date, observed_at):
    sender = message.from_id
    if sender is not None and not isinstance(sender, (types.PeerUser, types.PeerChannel,
                                                      types.PeerChat)):
        raise GroupResponseError('Invalid activity sender')
    if isinstance(sender, types.PeerUser):
        sender_kind, sender_id = 'user', sender.user_id
    elif isinstance(sender, types.PeerChannel):
        sender_kind, sender_id = 'channel', sender.channel_id
    else:
        sender_kind, sender_id = 'unknown', None
    source_id = sender.chat_id if isinstance(sender, types.PeerChat) else sender_id
    if sender is not None and not _integer(source_id, 1):
        raise GroupResponseError('Invalid activity sender ID')
    if isinstance(message, types.MessageService):
        return ActivityMessage(message.id, 'service', date, observed_at, sender_kind,
                               sender_id, None, None, None, None, None, None)
    grouped_id = message.grouped_id
    if grouped_id is not None and not _integer(grouped_id, -2**63, 2**63-1):
        raise GroupResponseError('Invalid activity album ID')
    reactions = None
    if message.reactions is not None:
        reaction_data = message.reactions
        if (not isinstance(reaction_data, types.MessageReactions)
                or not isinstance(reaction_data.results, (list, tuple))):
            raise GroupResponseError('Invalid activity reactions')
        reactions = 0
        for reaction in reaction_data.results:
            if not isinstance(reaction, types.ReactionCount) or reaction.count is None:
                raise GroupResponseError('Invalid activity reaction count')
            reactions += _count(reaction.count)
    replies, comments = None, None
    if message.replies is not None:
        if not isinstance(message.replies, types.MessageReplies) or message.replies.replies is None:
            raise GroupResponseError('Invalid activity replies')
        replies = _count(message.replies.replies)
        comments = bool(message.replies.comments)
    return ActivityMessage(message.id, 'message', date, observed_at, sender_kind, sender_id,
                           grouped_id, _count(message.views), reactions,
                           _count(message.forwards), replies, comments)


def _page(reply, peer_id, limit, last_id, last_date, window, observed_at):
    return history_page(reply, peer_id, limit, last_id, last_date, window, observed_at,
                        _message, label='Activity')


async def _measure_group_activity(operation, target, window, max_messages, started_at, beat=None):
    lookup, peer = await _resolve(operation, target)
    if lookup.group.kind not in ('group', 'megagroup', 'channel') or not isinstance(
            peer, (types.InputPeerChat, types.InputPeerChannel)):
        raise GroupReferenceError('Activity measurement requires a supported group with a usable peer')
    messages, scanned, unavailable, pages = [], 0, 0, 0
    oldest = newest = last_id = last_date = None

    def result(reason, complete=False):
        return GroupActivity(
            lookup.account_id, lookup.target, lookup.group, window.start_date, window.end_date,
            started_at, datetime.now(timezone.utc), max_messages, scanned, unavailable, pages,
            reason, complete, oldest, newest, tuple(messages),
        )

    # offset_date is exclusive and serialized as whole seconds. Round upward
    # before local filtering so an end inside a second cannot omit that second.
    upper = window.end_date.replace(microsecond=0)
    if window.end_date.microsecond:
        upper += timedelta(seconds=1)
    try:
        while scanned < max_messages:
            limit = min(100, max_messages-scanned)
            reply = await operation.client(functions.messages.GetHistoryRequest(
                peer, last_id or 0, upper if last_id is None else None, 0, limit, 0, 0, 0))
            accepted, dates, missing, count, next_id, next_date, reason = _page(
                reply, lookup.group.peer_id, limit, last_id, last_date, window,
                datetime.now(timezone.utc))
            messages.extend(accepted)
            scanned += count
            unavailable += missing
            pages += 1
            last_id, last_date = next_id, next_date
            if dates:
                oldest = min(dates) if oldest is None else min(oldest, min(dates))
                newest = max(dates) if newest is None else max(newest, max(dates))
            if beat is not None:
                beat('activity page done')
            if reason is not None:
                return result(reason, unavailable == 0)
        return result('message_limit')
    except (Exception, asyncio.CancelledError) as error:
        try:
            error.partial_result = result('cancelled' if isinstance(error, asyncio.CancelledError)
                                          else 'error')
        except BaseException:
            pass  # Observational metadata must never replace the original failure.
        raise
