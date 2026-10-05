"""Optional join admission at Telethon 1.45.0's actual retry/send boundary."""

from telethon import utils
from telethon.tl import functions, types
from telethon.tl.tlobject import TLRequest

from . import health
from .budget_client import _WRAPPERS
from .join_budget import JoinBudgetError, UnsupportedJoinRequest, _integer

_JOINS = (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest)
_JOIN_RESULT = types.messages.ChatInviteJoinResultOk.SUBCLASS_OF_ID


def _is_join(request, depth=0):
    if depth > 8:
        raise UnsupportedJoinRequest('Nested request wrappers cannot be admitted safely')
    if utils.is_list_like(request):
        return any(_is_join(item, depth + 1) for item in request)
    if isinstance(request, _JOINS):
        return True
    if isinstance(request, _WRAPPERS):
        return _is_join(request.query, depth + 1)
    query = getattr(request, 'query', None)
    if isinstance(query, TLRequest) and _is_join(query, depth + 1):
        raise UnsupportedJoinRequest('Unsupported wrapper around a join request')
    if getattr(request, 'SUBCLASS_OF_ID', None) == _JOIN_RESULT:
        raise UnsupportedJoinRequest('Unsupported join request family')
    return False


class _JoinSender:
    def __init__(self, sender, client, budget):
        self._sender, self._client, self._budget = sender, client, budget

    def __getattr__(self, name):
        return getattr(self._sender, name)

    def send(self, request, ordered=False):
        async def admitted():
            account_id = await self._client._join_budget_account()
            self._budget._claim(account_id)
            # The claim is committed before enqueue; no await can intervene.
            pending = self._sender.send(request, ordered=ordered)
            return await pending
        # Failed/cancelled replies and SDK retries never refund an attempt.
        return admitted()


class JoinClientMixin:
    async def _join_budget_account(self):
        me = await self.get_me(input_peer=False)
        if me is None:
            await self(functions.updates.GetStateRequest())
            raise JoinBudgetError('Telegram did not provide an authenticated account identity')
        account_id = _integer(me.id, 'authenticated account_id', 1)
        health.note_account(account_id)
        return account_id

    async def _call(self, sender, request, ordered=False, flood_sleep_threshold=None):
        budget = getattr(self, '_tgdata_join_budget', None)
        if budget is not None:
            if utils.is_list_like(request):
                request = list(request)
                if any(_is_join(item) for item in request):
                    raise UnsupportedJoinRequest('Batched joins are not supported with a join budget')
            elif _is_join(request):
                sender = _JoinSender(sender, self, budget)
        return await super()._call(sender, request, ordered=ordered,
                                   flood_sleep_threshold=flood_sleep_threshold)
