"""Required prebuild cancellation experiment on actual SDK/ledger/owned cleanup."""
import asyncio
import json
from pathlib import Path
import socket
import struct
import tempfile
from unittest.mock import patch

import contract_probe as cp


class UserVector:
    def __bytes__(self):
        return struct.pack('<Ii', 0x1cb5c415, 1) + bytes(cp.fx.user(222))


async def cancellation(phase):
    tg, fixture, budget = cp.setup()
    entered, release = asyncio.Event(), asyncio.Event()

    async def work():
        async with tg._account_health_operation(222, 'join_probe', 'synthetic') as (op, _):
            op.client._stage5_probe_budget = budget
            if phase == 'before':
                fixture.wire.script['GetUsersRequest'] = [cp.g.Reply(
                    UserVector(), entered=entered, release=release)]
            else:
                reply = cp.ok_reply()
                reply.entered, reply.release = entered, release
                fixture.wire.script['JoinChannelRequest'] = [reply]
            return await op.client(cp.functions.channels.JoinChannelRequest(cp.types.InputChannel(9, 19)))

    task = asyncio.create_task(work())
    try:
        await asyncio.wait_for(entered.wait(), 10)
        expected = 0 if phase == 'before' else 1
        assert budget.status(222).used == expected
        assert fixture.wire.calls.count('JoinChannelRequest') == expected
        task.cancel()
        try:
            await asyncio.wait_for(task, 10)
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('Caller cancellation was not preserved')
        assert fixture.wire.closed and fixture.wire.close_calls == 1
        assert budget.status(222).used == expected
        return dict(phase=phase, join_sends=expected, persisted_charge=expected,
                    caller='CancelledError', disconnect_settled=True, disconnect_attempts=1)
    finally:
        release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await asyncio.gather(*cp.h.RPC_TASKS, return_exceptions=True)


async def main():
    assert cp.telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata-stage5-prebuild-') as temp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(cp.telethon.TelegramClient, 'start', side_effect=AssertionError('login forbidden')), \
         patch.object(cp.telethon.TelegramClient, 'send_code_request', side_effect=AssertionError('code forbidden')), \
         patch.object(cp.fx.Wire, 'send', cp.wire_send), \
         patch.object(cp.connection, '_client_class', lambda base: type(
             'ProbeClient', (cp.ProbeMixin, cp.ORIGINAL_CLASS(base)), {})):
        cp.fx.TMP = Path(temp)
        try:
            for phase in ('before', 'after'):
                print(json.dumps(dict(result='PASS', observation=await cancellation(phase))), flush=True)
        finally:
            for client in cp.fx.CLIENTS:
                await client.disconnect()
            for tg in cp.h.FACADES:
                await tg.close()
            await asyncio.gather(*cp.h.RPC_TASKS, return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
