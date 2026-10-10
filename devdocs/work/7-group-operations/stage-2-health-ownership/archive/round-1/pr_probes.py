"""PR22 probes against unmodified product3d59455; all network sockets forbidden.

Synthetic decoded RPC replies go through Telethon's actual sender result handler.
This observes the request object the SDK really sends, not a test-supplied error's
convenient unwrapped request. Assertions below characterize reviewed behavior,
including defects; exit0 is not a passing acceptance suite.
"""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import telethon
from telethon import errors
from telethon.network.mtprotosender import MTProtoSender
from telethon.tl import functions, types
from tgdata.account_operation import AccountIdentityError
from tgdata.smoke_tests import test_32_account_operation as fx
from tgdata.smoke_tests import test_33_owned_health as stage2

WIRE_TASKS = []
ORIGINAL_SEND = fx.Wire.send


def wire_send(wire, request, ordered=False):
    if isinstance(request, (list, tuple)):
        return [wire_send(wire, item, ordered=ordered) for item in request]
    inner = request
    while hasattr(inner, 'query'):
        inner = inner.query
    name = type(inner).__name__
    pending = getattr(wire, 'review_errors', {}).get(name)
    if not pending:
        return ORIGINAL_SEND(wire, request, ordered=ordered)
    code, message = pending.pop(0)
    wire.calls.append(name)
    sender = MTProtoSender(wire.auth_key, loggers=wire.client._log)
    sender._user_connected = True
    sender._send_queue = []  # Observe actual RequestState without a live send loop.
    future = sender.send(request, ordered=ordered)
    state = sender._send_queue.pop()
    state.msg_id = 123
    sender._pending_state[state.msg_id] = state
    reply = SimpleNamespace(obj=SimpleNamespace(req_msg_id=state.msg_id,
        error=types.RpcError(code, message), body=None))
    task = asyncio.create_task(sender._handle_rpc_result(reply))
    WIRE_TASKS.append(task)
    return future


async def rpc_failure(tg, f, request, message, code=420, method='read'):
    try:
        async with tg._account_health_operation(222, method, 7) as (op, observation):
            f.wire.review_errors = {type(request).__name__: [(code, message)]}
            await op.client(request)
    except errors.RPCError as exc:
        return exc
    raise AssertionError('Expected actual SDK RPC error')


async def wrapped_wait_keys():
    tg, f = stage2.setup(cached=111)
    error = await rpc_failure(tg, f, fx.history(), 'FLOOD_WAIT_120')
    before = tg.get_account_health(222)
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.client(fx.history())
        success_names = sorted(observation.requests)
    after_success = tg.get_account_health(222)
    await rpc_failure(tg, f, functions.updates.GetStateRequest(), 'FLOOD_WAIT_15')
    after_other_wait = tg.get_account_health(222)
    assert type(error.request).__name__ == 'InvokeWithoutUpdatesRequest'
    assert success_names == ['GetHistoryRequest']
    assert list(after_success['waiting']) == ['InvokeWithoutUpdatesRequest']
    assert after_other_wait['waiting']['InvokeWithoutUpdatesRequest']['seconds'] == 15
    return dict(error_request=type(error.request).__name__,
        inner_request=type(error.request.query).__name__, success_names=success_names,
        initial_wait_keys=list(before['waiting']),
        wait_keys_after_matching_success=list(after_success['waiting']),
        wait_seconds_after_other_request=after_other_wait['waiting']['InvokeWithoutUpdatesRequest']['seconds'])


async def repeated_proof_recovers_restriction():
    tg, f = stage2.setup(cached=111)
    await rpc_failure(tg, f, fx.history(), 'PEER_FLOOD', errors.PeerFloodError.code)
    before = tg.get_account_health(222)['verdict']
    async with tg._account_health_operation(222, 'read', 7) as (op, observation):
        await op.verify_account()
        evidence = sorted(observation.requests)
    after = tg.get_account_health(222)
    assert before == 'restricted' and after['verdict'] == 'ok'
    assert 'GetHistoryRequest' not in f.wire.calls
    return dict(before=before, after=after['verdict'], post_proof_evidence=evidence,
                refused_request_retried=False, events=after['events'])


async def independent_legacy_error_is_excluded():
    tg, f = stage2.setup(accounts=[111, 222], cached=111)
    legacy = f.engine._new_client()
    f.engine._primary_client = legacy
    await legacy.connect()
    actual = isolated = None
    try:
        async with tg._health.call('legacy_outer', 7):
            try:
                async with tg._account_health_operation(111, 'read', 7):
                    raise AssertionError('The second client authenticates as222')
            except AccountIdentityError as exc:
                isolated = exc
                legacy._sender.review_errors = {'GetHistoryRequest': [(400, 'CHANNEL_PRIVATE')]}
                await legacy(fx.history())
    except errors.ChannelPrivateError as exc:
        actual = exc
    snap = tg._health.snapshot()
    assert actual is not None and actual.__context__ is isolated
    assert snap['account']['user_id'] == 111 and not snap['no_access'] and snap['events'] == 0
    return dict(new_rpc=type(actual).__name__, implicit_context=type(actual.__context__).__name__,
                account=snap['account']['user_id'], events=snap['events'], no_access=snap['no_access'])


async def notifications_after_different_cleanup_durations():
    events = []
    tg, f = stage2.setup(events.append, cached=111)
    release = asyncio.Event()
    async def first():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.close_release = release
            f.wire.review_errors = {'GetHistoryRequest': [(401, 'USER_DEACTIVATED_BAN')]}
            await op.client(fx.history())
    task = asyncio.create_task(first())
    while not f.clients:
        await asyncio.sleep(0)
    first_wire = f.clients[0]._sender
    await first_wire.close_entered.wait()
    async with tg._account_health_operation(222, 'read', 7):
        pass
    await stage2.deliveries(tg)
    release.set()
    await fx.expect(errors.UserDeactivatedBanError, task)
    await stage2.deliveries(tg)
    order = [e['verdict'] for e in events]
    assert order == ['ok', 'banned'] and tg.get_account_health(222)['verdict'] == 'ok'
    assert events[0]['time'] > events[1]['time']
    return dict(callback_order=order, snapshot=tg.get_account_health(222)['verdict'],
                event_times_retain_observation_order=True)


async def concurrent_callbacks_can_close():
    entered = []
    completed = []
    both = asyncio.Event()
    async def callback(event):
        entered.append(event['group'])
        if len(entered) == 2:
            both.set()
        await both.wait()
        await tg.close()
        completed.append(event['group'])
    tg, f = stage2.setup(callback, cached=111)
    await stage2.fail(tg, f, group=7)
    await stage2.fail(tg, f, group=8)
    await asyncio.wait_for(stage2.deliveries(tg), 2)
    assert len(entered) == 2 and completed and not tg._account_health[222]._tasks
    return dict(entered=len(entered), close_completed=len(completed), pending_tasks=0)


async def main():
    assert telethon.__version__ == '1.45.0'
    probes = [wrapped_wait_keys, repeated_proof_recovers_restriction,
              independent_legacy_error_is_excluded,
              notifications_after_different_cleanup_durations,
              concurrent_callbacks_can_close]
    with tempfile.TemporaryDirectory(prefix='tgdata_pr22_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(fx.Wire, 'send', wire_send):
        fx.TMP = Path(tmp)
        for probe in probes:
            try:
                result = await asyncio.wait_for(probe(), 10)
                print(json.dumps(dict(probe=probe.__name__, observed=result)), flush=True)
            finally:
                await asyncio.gather(*WIRE_TASKS)
                WIRE_TASKS.clear()
                for client in fx.CLIENTS:
                    if client._sender.close_release is not None:
                        client._sender.close_release.set()
                    client._sender.close_error = None
                    await client.disconnect()
                fx.CLIENTS.clear()
                for tg in stage2.FACADES:
                    await tg.close()
                stage2.FACADES.clear()


if __name__ == '__main__':
    asyncio.run(main())
