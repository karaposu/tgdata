"""Revision3 critic probes: real SDK/asyncio composition; no production edits."""
import argparse
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import telethon
from telethon.tl import functions, types
from tgdata import AuthRequiredError, health
from tgdata.connection_engine import _AnswerEvidence
from tgdata.smoke_tests import test_32_account_operation as fx
from tgdata.smoke_tests import test_33_owned_health as stage2
import pr_probes


async def mutable_batch():
    tg, f = stage2.setup(cached=111)
    requests = [functions.updates.GetStateRequest()]
    held = asyncio.get_running_loop().create_future()
    original_call = _AnswerEvidence.__call__
    at_entry = []

    async def inspect_entry(client, request, **kwargs):
        if request is requests:
            at_entry.extend(type(item).__name__ for item in request)
        return await original_call(client, request, **kwargs)

    async def worker():
        async with tg._account_health_operation(222, 'read', 7) as (op, observation):
            f.wire.script['GetStateRequest'] = [held]
            await op.client(requests)
            return dict(entry=at_entry, wire=f.wire.calls[-1],
                        recorded_success=sorted(observation.requests))

    with patch.object(_AnswerEvidence, '__call__', inspect_entry):
        task = asyncio.create_task(worker())
        while not f.clients or f.wire.calls.count('GetStateRequest') < 2:
            await asyncio.sleep(0)
        requests[:] = [fx.history()]
        held.set_result(types.updates.State(1, 1, fx.DATE, 1, 0))
        result = await task
    assert result == dict(entry=['GetStateRequest'], wire='GetStateRequest',
                          recorded_success=['GetHistoryRequest'])
    return result


async def marker_roundtrip():
    tg, f = stage2.setup(cached=111)
    original_factory = f.engine._new_client
    originals = []

    def factory(*args, **kwargs):
        client = original_factory(*args, **kwargs)
        client._sender.review_errors = {'GetStateRequest': [(401, 'AUTH_KEY_UNREGISTERED')]}
        return client

    async def child():
        try:
            async with tg._account_health_operation(222, 'read', 7):
                raise AssertionError('Must refuse before proof')
        except AuthRequiredError as error:
            originals.append(error)
            original = (str(error), error.__cause__, str(error.__cause__))
            error._r3_probe_neutral = True
            error.__cause__._r3_probe_neutral = True
            assert original == (str(error), error.__cause__, str(error.__cause__))
            raise

    with patch.object(f.engine, '_new_client', factory):
        try:
            await asyncio.create_task(child())
        except AuthRequiredError as error:
            assert error is originals[0] and error._r3_probe_neutral
            assert error.__cause__._r3_probe_neutral
            verdict = health.classify(error, include_reported=True).verdict
            assert verdict == 'logged out' and f.wire.closed
            try:
                raise RuntimeError('forwarded') from error
            except RuntimeError as wrapper:
                assert wrapper.__cause__ is originals[0]
                assert wrapper.__cause__._r3_probe_neutral
                assert health.classify(wrapper, include_reported=True).verdict == verdict
        else:
            raise AssertionError('Expected refusal')
    return dict(same_error=True, root_and_cause_metadata_survive=True,
                explicit_wrapper_retains_marker=True, diagnostic_verdict=verdict,
                source_closed_before_delivery=True)


async def main(mode):
    assert telethon.__version__ == '1.45.0'
    with tempfile.TemporaryDirectory(prefix='tgdata_r3_critic_') as tmp, \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')), \
         patch.object(fx.Wire, 'send', pr_probes.wire_send):
        fx.TMP = Path(tmp)
        try:
            fn = mutable_batch if mode == 'finding' else marker_roundtrip
            print(json.dumps(dict(probe=fn.__name__, observed=await fn())), flush=True)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('finding', 'premise'))
    asyncio.run(main(parser.parse_args().mode))
