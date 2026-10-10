"""Ground-truth inputs for revision3; no production code is changed or replaced.

Uses the prior review's real SDK result-handler adapter for synthetic RPC replies.
The exception examples observe Python's actual cause/context object relationships.
This is planning evidence, not validation of an unbuilt implementation.
"""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import telethon
from telethon import errors
from telethon.errors.rpcbaseerrors import _NESTS_QUERY
from telethon.tl import functions, types
from tgdata import AuthRequiredError, health
from tgdata.smoke_tests import test_32_account_operation as fx
from tgdata.smoke_tests import test_33_owned_health as stage2
import pr_probes


def describe(request):
    wrappers = []
    while isinstance(request, _NESTS_QUERY):
        wrappers.append(type(request).__name__)
        request = request.query
    cls = type(request)
    return dict(wrappers=wrappers, module=cls.__module__, name=cls.__name__,
                constructor=hex(cls.CONSTRUCTOR_ID))


async def sdk_shapes():
    requests = [
        ('history', fx.history()),
        ('nested_takeout', functions.InvokeWithTakeoutRequest(123, fx.history())),
        ('messages_ids', functions.messages.GetMessagesRequest([])),
        ('channels_ids', functions.channels.GetMessagesRequest(types.InputChannel(7, 7), [])),
    ]
    rows = []
    for label, request in requests:
        tg, f = stage2.setup(cached=111)
        sent = describe(request)
        try:
            async with tg._account_health_operation(222, 'read', 7) as (op, observation):
                f.wire.review_errors = {sent['name']: [(420, 'FLOOD_WAIT_120')]}
                await op.client(request)
        except errors.FloodWaitError as error:
            received = describe(error.request)
        else:
            raise AssertionError('Expected real SDK error')
        assert sent['constructor'] == received['constructor']
        assert received['wrappers'][0] == 'InvokeWithoutUpdatesRequest'
        rows.append(dict(case=label, caller=sent, error=received))
    assert rows[2]['caller']['name'] == rows[3]['caller']['name']
    assert rows[2]['caller']['module'] != rows[3]['caller']['module']
    assert rows[2]['caller']['constructor'] != rows[3]['caller']['constructor']
    return rows


def chain_shapes():
    original = errors.rpc_message_to_error(types.RpcError(401, 'AUTH_KEY_UNREGISTERED'),
                                           functions.updates.GetStateRequest())
    try:
        try:
            raise original
        except errors.RPCError as cause:
            raise AuthRequiredError('synthetic unverified session', reason='AUTH_KEY_UNREGISTERED') from cause
    except AuthRequiredError as error:
        isolated = error
    assert isolated.__cause__ is original

    try:
        raise isolated
    except AuthRequiredError:
        try:
            raise RuntimeError('implicit wrapper')
        except RuntimeError as error:
            implicit_wrapper = error
        try:
            raise errors.ChannelPrivateError(fx.history())
        except errors.RPCError as error:
            fresh_rpc = error
        try:
            raise RuntimeError('explicit wrapper') from isolated
        except RuntimeError as error:
            explicit_wrapper = error
    assert fresh_rpc.__context__ is isolated and fresh_rpc is not original
    assert implicit_wrapper.__context__ is isolated
    assert explicit_wrapper.__cause__ is isolated

    prior = errors.ChannelPrivateError(fx.history())
    try:
        raise prior
    except errors.RPCError:
        try:
            raise ValueError('local setup failure inside an existing handler')
        except ValueError as error:
            local_failure = error
    assert local_failure.__context__ is prior and local_failure.__cause__ is None
    return dict(
        isolated_chain=[type(e).__name__ for e in health._chain(isolated)],
        implicit_wrapper=[type(e).__name__ for e in health._chain(implicit_wrapper)],
        explicit_wrapper=[type(e).__name__ for e in health._chain(explicit_wrapper)],
        fresh_rpc=[type(e).__name__ for e in health._chain(fresh_rpc)],
        original_cause_can_be_rethrown_by_identity=isolated.__cause__ is original,
        prior_implicit_context=[type(e).__name__ for e in health._chain(local_failure)],
        prior_rpc_is_not_explicit_cause=local_failure.__cause__ is None)


async def child_task_failure():
    tg, f = stage2.setup(accounts=[111, 222], cached=111)
    legacy = f.engine._new_client()
    f.engine._primary_client = legacy
    await legacy.connect()
    original_factory = f.engine._new_client

    def new_client(*args, **kwargs):
        client = original_factory(*args, **kwargs)
        client._sender.review_errors = {'GetStateRequest': [(401, 'AUTH_KEY_UNREGISTERED')]}
        return client

    async def child():
        async with tg._account_health_operation(222, 'read', 7):
            raise AssertionError('Unverified client must not yield')

    with patch.object(f.engine, '_new_client', new_client):
        try:
            async with tg._health.call('legacy_parent', 7):
                await asyncio.create_task(child())
        except AuthRequiredError as error:
            # Actual SDK / tgdata exception instances retain private attributes
            # without changing identity, text, cause or cancellation semantics.
            before = (str(error), error.__cause__)
            error._planning_probe_neutral = True
            assert (str(error), error.__cause__) == before
        else:
            raise AssertionError('Expected authentication refusal')
    snapshot = tg._health.snapshot()
    assert tg.get_account_health(222) is None
    assert snapshot['account']['user_id'] == 111 and snapshot['verdict'] == 'logged out'
    return dict(unverified_owned_snapshot=None, legacy_owner=snapshot['account']['user_id'],
                legacy_verdict=snapshot['verdict'], legacy_events=snapshot['events'],
                exception_can_carry_neutral_attribution=True)


async def main():
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata_stage2_replan_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(fx.Wire, 'send', pr_probes.wire_send):
        fx.TMP = Path(tmp)
        try:
            print(json.dumps(dict(sdk=telethon.__version__, request_shapes=await sdk_shapes())), flush=True)
            print(json.dumps(dict(exception_shapes=chain_shapes())), flush=True)
            print(json.dumps(dict(child_task=await child_task_failure())), flush=True)
        finally:
            await asyncio.gather(*pr_probes.WIRE_TASKS)
            for client in fx.CLIENTS:
                await client.disconnect()
            for tg in stage2.FACADES:
                await tg.close()
            fx.CLIENTS.clear()
            stage2.FACADES.clear()
            pr_probes.WIRE_TASKS.clear()


if __name__ == '__main__':
    asyncio.run(main())
