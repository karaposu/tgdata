"""Join admission for the private, verified public-operation context only.

Ordinary clients have no active marker and keep their existing SDK behavior.
This is not a guard for arbitrary raw-client or lower transport operations.
"""

import asyncio
import inspect

from telethon import utils
from telethon.tl import functions, types
from telethon.tl.tlobject import TLRequest

from .join_budget import JoinBudget, JoinBudgetStatus, JoinBudgetError, JoinBudgetConfigError


class UnsupportedJoinRequest(JoinBudgetError):
    """A request cannot use the bounded owned-operation join admission contract."""


_JOINS = (functions.channels.JoinChannelRequest, functions.messages.ImportChatInviteRequest)
_JOIN_RESULT = types.messages.ChatInviteJoinResultOk.SUBCLASS_OF_ID


def _join_request(request, depth=0):
    if depth > 8:
        raise UnsupportedJoinRequest('Join request envelopes exceed the supported depth')
    if utils.is_list_like(request):
        raise UnsupportedJoinRequest('Batched requests are not supported in the joining operation')
    if isinstance(request, _JOINS):
        return request
    if isinstance(request, functions.InvokeWithoutUpdatesRequest):
        return _join_request(request.query, depth + 1)
    query = getattr(request, 'query', None)
    if isinstance(query, TLRequest) and _join_request(query, depth + 1) is not None:
        raise UnsupportedJoinRequest('Unsupported wrapper around a join request')
    if getattr(request, 'SUBCLASS_OF_ID', None) == _JOIN_RESULT:
        raise UnsupportedJoinRequest('Unsupported join request family')
    return None


def _join_error_matches(error, request):
    try:
        return isinstance(request, _JOINS) and _join_request(getattr(error, 'request', None)) is request
    except asyncio.CancelledError:
        raise
    except Exception:
        # An unreadable origin is not proof of a successful/pending mutation.
        return False


def _incomplete(value, message):
    # Invalid asynchronous providers must never be awaited into permission.
    # Closing a native coroutine is only hygiene, secondary to the local refusal.
    if inspect.iscoroutine(value):
        try:
            value.close()
        except BaseException:
            pass
    raise JoinBudgetConfigError(message) from None


def _join_policy(budget, account_id):
    if not isinstance(budget, JoinBudget):
        raise JoinBudgetConfigError('join_group requires a configured JoinBudget instance')
    result = budget.status(account_id)
    if not isinstance(result, JoinBudgetStatus) or result.account_id != account_id:
        _incomplete(result, 'Join policy must synchronously describe the verified account')
    # Even remaining>0 is only a snapshot, never a reservation for the later send.
    return result


class _JoinSender:
    def __init__(self, sender, client, operation, budget, request):
        self._sender, self._client, self._operation = sender, client, operation
        self._budget, self._request = budget, request

    def __getattr__(self, name):
        return getattr(self._sender, name)

    def send(self, request, ordered=False):
        async def admitted():
            if _join_request(request) is not self._request:
                raise UnsupportedJoinRequest('The admitted join request changed')
            account_id = await self._operation.verify_account()
            if self._operation.client is not self._client or _join_request(request) is not self._request:
                raise UnsupportedJoinRequest('The joining operation or request changed')
            result = self._budget._claim(account_id)
            if result is not None:
                _incomplete(result, 'Join claim must complete synchronously before sending')
            # No await between completed durable admission and actual SDK enqueue.
            pending = self._sender.send(request, ordered=ordered)
            return await pending
        return admitted()


class JoinClientMixin:
    async def _call(self, sender, request, ordered=False, flood_sleep_threshold=None):
        budget = getattr(self, '_tgdata_join_budget', None)
        if budget is not None:
            leaf = _join_request(request)
            if leaf is not None:
                operation = getattr(self, '_tgdata_account_operation', None)
                if operation is None or operation.client is not self:
                    raise UnsupportedJoinRequest('Join admission requires this client\'s verified operation')
                sender = _JoinSender(sender, self, operation, budget, leaf)
        return await super()._call(sender, request, ordered=ordered,
                                   flood_sleep_threshold=flood_sleep_threshold)
