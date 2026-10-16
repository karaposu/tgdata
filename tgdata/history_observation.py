"""Private structural history-page validation; projections remain caller-owned."""

from datetime import datetime, timezone

from telethon.tl import types

from .group_operations import GroupResponseError, _identity, _integer


def _date(value, label):
    try:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise ValueError
        return value.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        raise GroupResponseError('Invalid {} message date'.format(label.lower())) from None


def history_page(reply, peer_id, limit, last_id, last_date, window, observed_at,
                 project, *, label='Activity'):
    """Validate and project the whole page before returning any accepted facts."""
    if not isinstance(reply, (types.messages.Messages, types.messages.MessagesSlice,
                              types.messages.ChannelMessages)):
        raise GroupResponseError('Unexpected {} history response'.format(label.lower()))
    rows = reply.messages
    if not isinstance(rows, (list, tuple)) or len(rows) > limit:
        raise GroupResponseError('Invalid {} history vector'.format(label.lower()))
    messages, dates, unavailable = [], [], 0
    for row in rows:
        if not isinstance(row, (types.Message, types.MessageService, types.MessageEmpty)):
            raise GroupResponseError('Invalid {} history message'.format(label.lower()))
        if not _integer(row.id, 1, 2**31-1) or (last_id is not None and row.id >= last_id):
            raise GroupResponseError('{} history IDs do not progress'.format(label))
        last_id = row.id
        peer = row.peer_id
        if not (peer is None and isinstance(row, types.MessageEmpty)):
            if (not isinstance(peer, (types.PeerChat, types.PeerChannel))
                    or _identity(peer)[2] != peer_id):
                raise GroupResponseError('{} message belongs to another peer'.format(label))
        if isinstance(row, types.MessageEmpty):
            unavailable += 1
            continue
        date = _date(row.date, label)
        if last_date is not None and date > last_date:
            raise GroupResponseError('{} history dates do not progress'.format(label))
        dates.append(date)
        last_date = date
        observation = project(row, date, observed_at)
        if window.contains(date):
            messages.append(observation)
    boundary = any(date < window.start_date for date in dates)
    ended = not rows or isinstance(reply, types.messages.Messages)
    reason = 'window_start' if boundary else 'history_end' if ended else None
    return messages, dates, unavailable, len(rows), last_id, last_date, reason
