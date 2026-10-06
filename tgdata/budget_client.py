"""Opt-in quota guards at Telethon's actual send and page-building seams."""

from telethon import utils
from telethon.client.messages import _IDsIter, _MessagesIter
from telethon.tl import functions, types
from telethon.tl.tlobject import TLRequest

from . import health
from .read_budget import (
    ReadBudgetError, ReadBudgetExceeded, UnsupportedBudgetRequest, _integer,
)


def _classes(module, names):
    return tuple(cls for name in names for cls in [getattr(module, name, None)] if cls is not None)


_LIMIT_READS = _classes(functions.messages, (
    'GetHistoryRequest', 'SearchRequest', 'SearchGlobalRequest', 'GetRepliesRequest',
))
_ID_READS = (_classes(functions.messages, ('GetMessagesRequest', 'GetScheduledMessagesRequest'))
             + _classes(functions.channels, ('GetMessagesRequest',)))
_WRAPPERS = _classes(functions, (
    'InvokeAfterMsgRequest', 'InvokeAfterMsgsRequest', 'InvokeWithLayerRequest',
    'InvokeWithoutUpdatesRequest', 'InvokeWithMessagesRangeRequest', 'InvokeWithTakeoutRequest',
    'InvokeWithBusinessConnectionRequest', 'InitConnectionRequest',
))
_MESSAGES_RESULT = types.messages.Messages.SUBCLASS_OF_ID
_MESSAGE_RESULTS = {_MESSAGES_RESULT, types.messages.DiscussionMessage.SUBCLASS_OF_ID}


def _request_cost(request, depth=0):
    if depth > 8:
        raise UnsupportedBudgetRequest('Nested request wrappers cannot be bounded safely')
    if isinstance(request, _WRAPPERS):
        return _request_cost(request.query, depth + 1)
    query = getattr(request, 'query', None)
    if isinstance(query, TLRequest) and _request_cost(query, depth + 1):
        raise UnsupportedBudgetRequest(f'{type(request).__name__} is not a supported message-read wrapper')
    if isinstance(request, _LIMIT_READS):
        amount = request.limit
    elif isinstance(request, _ID_READS):
        try:
            amount = len(request.id)
        except TypeError:
            raise UnsupportedBudgetRequest('Message ID reads require a finite ID vector') from None
    elif getattr(request, 'SUBCLASS_OF_ID', None) in _MESSAGE_RESULTS:
        raise UnsupportedBudgetRequest(f'{type(request).__name__} has no supported message-read bound')
    else:
        return 0  # Metadata, file bytes, and passive-update recovery are outside this allowance.
    try:
        return _integer(amount, 'message request bound', 1)
    except ReadBudgetError:
        raise UnsupportedBudgetRequest(f'{type(request).__name__} requires a positive message-read bound') from None


def _returned_count(result):
    if isinstance(result, types.messages.MessagesNotModified):
        return 0
    messages = getattr(result, 'messages', None)
    if getattr(result, 'SUBCLASS_OF_ID', None) == _MESSAGES_RESULT and isinstance(messages, (list, tuple)):
        return len(messages)
    raise ReadBudgetError('Unexpected response shape for a budgeted message read')


class _BudgetSender:
    def __init__(self, sender, client, budget):
        self._sender, self._client, self._budget = sender, client, budget

    def __getattr__(self, name):
        return getattr(self._sender, name)

    def send(self, request, ordered=False):
        async def admitted():
            # Called inside Telethon's retry loop, after request resolution and
            # cached waits. A retry is a new attempt, not free extra traffic.
            account_id = await self._client._read_budget_account()
            amount = _request_cost(request)
            reservation = self._budget._reserve(account_id, amount)
            # No await between the committed claim and enqueueing this request.
            pending = self._sender.send(request, ordered=ordered)
            result = await pending
            actual = _returned_count(result)
            self._budget._settle(reservation, actual)
            if actual > reservation.amount:
                raise ReadBudgetError('Telegram returned more messages than the reserved request bound')
            return result

        # Errors/cancellation deliberately leave the full reservation charged.
        return admitted()


class BudgetClientMixin:
    async def _read_budget_account(self):
        # Never use _self_id as billing authority: restored cache rows may be
        # stale, and get_me itself leaves a nonempty cached id untouched.
        me = await self.get_me(input_peer=False)
        if me is None:
            # get_me hides UnauthorizedError. Ask again through a call that
            # preserves Telegram's real logout/ban reason for health reporting.
            await self(functions.updates.GetStateRequest())
            raise ReadBudgetError('Telegram did not provide an authenticated account identity')
        account_id = _integer(me.id, 'authenticated account_id', 1)
        health.note_account(account_id)
        return account_id

    async def _call(self, sender, request, ordered=False, flood_sleep_threshold=None):
        budget = getattr(self, '_tgdata_read_budget', None)
        if budget is not None:
            if utils.is_list_like(request):
                request = list(request)
                if any(_request_cost(item) for item in request):
                    raise UnsupportedBudgetRequest('Batched message reads are not supported with a read budget')
            elif _request_cost(request):
                sender = _BudgetSender(sender, self, budget)
        return await super()._call(sender, request, ordered=ordered,
                                   flood_sleep_threshold=flood_sleep_threshold)

    def iter_messages(self, *args, **kwargs):
        iterator = super().iter_messages(*args, **kwargs)
        budget = getattr(self, '_tgdata_read_budget', None)
        if budget is None:
            return iterator
        load = iterator._load_next_chunk
        if isinstance(iterator, _MessagesIter):
            async def bounded_page():
                account_id = await self._read_budget_account()
                status = budget.status(account_id)
                if status.remaining == 0:
                    raise ReadBudgetExceeded(status, 1, status.next_available_at)
                old_left = iterator.left
                has_offset = hasattr(iterator.request, 'add_offset')
                old_offset = getattr(iterator.request, 'add_offset', None)
                iterator.left = min(old_left, status.remaining)
                try:
                    return await load()
                finally:
                    iterator.left = old_left
                    # The SDK assumes a shortened reverse page is the final
                    # page. Restore its baseline before a later larger page.
                    if has_offset:
                        iterator.request.add_offset = old_offset
            iterator._load_next_chunk = bounded_page
        elif isinstance(iterator, _IDsIter):
            async def bounded_ids():
                old_offset = iterator._offset
                try:
                    return await load()
                except ReadBudgetError:
                    # _IDsIter advances before send. A refused chunk must not
                    # disappear if its caller resumes after capacity returns.
                    iterator._offset = old_offset
                    raise
            iterator._load_next_chunk = bounded_ids
        return iterator
