"""Real SDK/asyncio composition probe; synthetic transport only, sockets forbidden."""
import asyncio
import contextvars
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import telethon
from telethon import errors
from tgdata import health
from tgdata.account_operation import AccountIdentityError
from tgdata.connection_engine import _AnswerEvidence
from tgdata.smoke_tests import test_32_account_operation as fixture


async def main():
    assert telethon.__version__ == '1.45.0'
    observed = []
    original = _AnswerEvidence.__call__
    send = fixture.Wire.send

    async def inspect_source(client, request, **kwargs):
        try:
            result = await original(client, request, **kwargs)
        except (errors.RPCError, errors.MultiError) as exc:
            observed.append((client, request, exc))
            raise
        else:
            observed.append((client, request, None))
            return result

    def send_list(wire, request, **kwargs):
        if isinstance(request, (list, tuple)):
            return [send(wire, item, **kwargs) for item in request]
        return send(wire, request, **kwargs)

    with tempfile.TemporaryDirectory() as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(_AnswerEvidence, '__call__', inspect_source), \
         patch.object(fixture.Wire, 'send', send_list):
        fixture.TMP = Path(tmp)
        f = fixture.Fixture(cached=111, budget=True)
        async with f.engine._account_operation(222) as op:
            observed.clear()
            denied = errors.ChannelPrivateError(fixture.history())
            f.wire.script['GetHistoryRequest'] = [denied]
            caught = await fixture.expect(type(denied), op.client(fixture.history()))
            assert caught is denied
            assert any(c is op.client and e is denied for c, r, e in observed)
            assert any(type(r).__name__ == 'GetUsersRequest' and e is None
                       for c, r, e in observed)
            assert f.budget.status(222).remaining == 19
            f.wire.account = 333
            await fixture.expect(AccountIdentityError, op.verify_account())
            fixture.refuses(RuntimeError, lambda: op.client)

        f2 = fixture.Fixture(cached=111)
        async with f2.engine._account_operation(222) as op:
            denied = errors.ChannelPrivateError(fixture.history())
            f2.wire.script['GetHistoryRequest'] = [denied]
            error = await fixture.expect(errors.MultiError,
                op.client([fixture.history(), fixture.history()]))
            assert error.exceptions == [denied, None]
            assert any(c is op.client and e is error for c, r, e in observed)

        # Observe the exact Python task/context and real SDK cleanup ordering.
        ambient = contextvars.ContextVar('probe_ambient', default=None)
        ambient.set('outer')
        token = ambient.set(None)
        callback_done = asyncio.Event()
        close_release = asyncio.Event()
        f3 = fixture.Fixture(cached=111)
        primary = ValueError('primary')
        notifications = []

        async def notify():
            assert f3.wire.closed and ambient.get() is None
            try:
                raise asyncio.CancelledError()
            except asyncio.CancelledError:
                callback_done.set()

        async def operation():
            try:
                async with f3.engine._account_operation(222):
                    f3.wire.close_release = close_release
                    raise primary
            finally:
                notifications.append(asyncio.create_task(notify()))

        work = asyncio.create_task(operation())
        while not f3.clients:
            await asyncio.sleep(0)
        await asyncio.wait_for(f3.wire.close_entered.wait(), 2)
        assert not notifications and not work.done()
        close_release.set()
        assert await fixture.expect(ValueError, work) is primary
        await asyncio.wait_for(callback_done.wait(), 2)
        await asyncio.gather(*notifications)
        ambient.reset(token)
        assert ambient.get() == 'outer'
        for client in fixture.CLIENTS:
            await client.disconnect()
        fixture.CLIENTS.clear()
    print(json.dumps(dict(sdk=telethon.__version__, source_identity=True,
        budget_reentry=True, caught_invalidation=True, real_multi_error=True,
        closed_before_callback=True, primary_preserved=True, contexts_reset=True)))


if __name__ == '__main__':
    asyncio.run(main())
