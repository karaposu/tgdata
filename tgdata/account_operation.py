"""Private ownership and lifetime contract for short-lived account operations.

Not a public raw-client API: internal callers keep all work in the opening
task and context, and never log in, replace credentials or detach client work.
"""

import asyncio
import logging

from telethon import errors
from telethon.tl import functions, types


logger = logging.getLogger(__name__)


def _expected_account_id(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError('expected_account_id must be a positive integer')
    return value


class AccountIdentityError(RuntimeError):
    """The authenticated identity could not verify the expected account."""

    def __init__(self, expected_account_id, actual_account_id=None):
        self.expected_account_id = expected_account_id
        self.actual_account_id = actual_account_id
        if actual_account_id is None:
            message = 'Could not verify the authenticated Telegram account'
        else:
            message = ('Expected Telegram account {}, authenticated as {}'
                       .format(expected_account_id, actual_account_id))
        super().__init__(message)
        self.__suppress_context__ = True


class _AccountOperation:
    __slots__ = ('_client', '_account_id', '_task', '_active', '_auth_required')

    def __init__(self, client, account_id, auth_required):
        self._client = client
        self._account_id = _expected_account_id(account_id)
        self._task = asyncio.current_task()
        self._active = True
        self._auth_required = auth_required

    @property
    def account_id(self):
        return self._account_id

    @property
    def client(self):
        self._check_active()
        return self._client

    def _check_active(self):
        if not self._active:
            raise RuntimeError('Account operation is closed')
        if asyncio.current_task() is not self._task:
            raise RuntimeError('Account operation belongs to its opening task')

    def _close(self):
        self._active = False

    def _identity_error(self, actual=None):
        self._close()
        return AccountIdentityError(self._account_id, actual)

    async def verify_account(self):
        """Prove the same owner again, before a later admission/claim.

        A direct self RPC preserves auth errors which get_me() hides, and
        does not treat Telethon's possibly stale _self_id as authority.
        Identity/auth loss permanently invalidates this handle.
        """
        self._check_active()
        try:
            users = await self._client(
                functions.users.GetUsersRequest([types.InputUserSelf()]))
        except (errors.UnauthorizedError, errors.AuthKeyError) as exc:
            self._close()
            raise self._auth_required(exc) from exc
        self._check_active()
        if users is None or users == [] or users == ():
            self._close()
            raise self._auth_required(None) from None
        if not isinstance(users, (list, tuple)) or len(users) != 1:
            raise self._identity_error() from None
        user = users[0]
        if user is None or isinstance(user, types.UserEmpty):
            self._close()
            raise self._auth_required(None) from None
        if not isinstance(user, types.User):
            raise self._identity_error() from None
        actual = user.id
        if isinstance(actual, bool) or not isinstance(actual, int) or actual <= 0:
            raise self._identity_error() from None
        if actual != self._account_id:
            raise self._identity_error(actual) from None
        return self._account_id


async def _disconnect_owned(client):
    """Settle one SDK disconnect attempt, then deliver caller cancellation.

    Telethon shields its own disconnect task. Shielding a retained outer
    task too prevents cancelling its returned Future and losing the ability
    to await completion. There is deliberately no shutdown timeout promise.
    """
    async def close():
        try:
            await client.disconnect()
        except (Exception, asyncio.CancelledError) as exc:
            # An internal disconnect cancellation is a cleanup failure, not
            # evidence that our caller was cancelled. Retain no error text.
            return type(exc).__name__

    completion = asyncio.ensure_future(close())
    cancelled = None
    while not completion.done():
        try:
            await asyncio.shield(completion)
        except asyncio.CancelledError as exc:
            cancelled = exc
    failure = completion.result()
    if failure is not None:
        try:
            logger.error('Account operation cleanup failed (%s)', failure)
        except (Exception, asyncio.CancelledError):
            pass  # Diagnostics must not replace the work's result/failure.
    if cancelled is not None:
        raise cancelled
