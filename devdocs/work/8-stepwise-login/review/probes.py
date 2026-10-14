"""Fresh PR28 histories. Production/test sources remain unchanged; no sockets."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import socket
import sys
import time
import traceback
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from telethon import errors, functions, types
from telethon.sessions import MemorySession
from tgdata import LoginFlow, LoginError, health
from tgdata.account_operation import _disconnect_owned
from tgdata.connection_engine import ConnectionEngine
from tgdata.session_store import StoredSession
from tgdata.smoke_tests.test_41_stepwise_login import (
    fixture, Wire, PHONE, CODE, PASSWORD, KEY, HASH, expect)


async def cancelled(task):
    try:
        await task
    except asyncio.CancelledError:
        return
    raise AssertionError('Caller stop was lost')


async def delivery_variants():
    for cls in (types.auth.SentCodeTypeSms, types.auth.SentCodeTypeCall):
        with fixture() as (config, service):
            def reply(w, r):
                if isinstance(r, functions.auth.SendCodeRequest):
                    service.answer(w, r)
                    return types.auth.SentCode(cls(5), HASH, timeout=1)
                return NotImplemented
            service.hook = reply
            flow = LoginFlow(config)
            status = await flow.start(PHONE)
            assert status.step == 'code' and status.delivery in ('sms', 'call')
            flow = LoginFlow(config, state=flow.export_state())
            assert (await flow.submit_code(CODE)).step == 'complete'
    return 'SMS and voice challenge restore to final authorization'


async def signin_signup_refusal():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        service.hook = lambda w, r: types.auth.AuthorizationSignUpRequired() if isinstance(r, functions.auth.SignInRequest) else NotImplemented
        status = await flow.submit_code(CODE)
        assert status.step == 'unsupported' and status.action_required == 'signup'
        await expect('wrong_step', flow.submit_password(PASSWORD))
        assert service.calls.count('SendCodeRequest') == 1
        assert not any(n in service.calls for n in ('SignUpRequest','CheckPasswordRequest'))
    return 'SignIn signup response performs no signup or password mutation'


async def wait_code_and_password():
    observations = []
    for step in ('code','password'):
        with fixture(step == 'password') as (config, service):
            flow = LoginFlow(config)
            await flow.start(PHONE)
            if step == 'password':
                await flow.submit_code(CODE)
            request_type = functions.auth.SignInRequest if step == 'code' else functions.auth.CheckPasswordRequest
            service.hook = lambda w, r: errors.FloodWaitError(r, capture=60) if isinstance(r, request_type) else NotImplemented
            method = flow.submit_code if step == 'code' else flow.submit_password
            value = CODE if step == 'code' else PASSWORD
            await expect('wait', method(value))
            flow = LoginFlow(config, state=flow.export_state())
            assert flow.status.step == step and flow.status.retry_after > 0
            count = len(service.calls)
            method = flow.submit_code if step == 'code' else flow.submit_password
            await expect('wait', method(value))
            assert len(service.calls) == count
            service.hook = None
            with patch('tgdata.login.time.time', return_value=time.time()+70):
                assert (await method(value)).step == 'complete'
            observations.append(step)
    return {'preserved_phase_and_wait': observations, 'early_retry_traffic': 0}


async def wait_on_uncertain_check():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        service.hook = lambda w, r: OSError('synthetic loss') if isinstance(r, functions.auth.SignInRequest) else NotImplemented
        await expect('transport_error', flow.submit_code(CODE))
        service.hook = lambda w, r: errors.FloodWaitError(r, capture=60) if isinstance(r, functions.users.GetUsersRequest) else NotImplemented
        await expect('wait', flow.check_authorization())
        assert flow.status.step == 'uncertain'
        flow = LoginFlow(config, state=flow.export_state())
        service.hook = None
        with patch('tgdata.login.time.time', return_value=time.time()+70):
            assert (await flow.check_authorization()).step == 'code'
        assert service.calls.count('SendCodeRequest') == 1
    return 'Read-only check wait preserves uncertainty and restartable deadline'


async def bounded_double_redirect():
    with fixture() as (config, service):
        service.hook = lambda w, r: errors.PhoneMigrateError(r, capture=3 if w.client.session.dc_id != 3 else 2) if isinstance(r, functions.auth.SendCodeRequest) else NotImplemented
        flow = LoginFlow(config)
        with patch.object(type(service.clients[0]), '_config', None):
            await expect('restart_required', flow.start(PHONE))
        assert flow.status.step == 'restart_required'
        assert service.calls.count('SendCodeRequest') == 2
        assert all(c._proxy == w.client._proxy for w in service.wires for c in w.connections)
    return {'SendCode_requests': 2, 'step': 'restart_required', 'proxy_preserved': True}


async def queued_stop_reaches_public_boundary():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        entered = False
        async def caller():
            nonlocal entered
            entered = True
            asyncio.current_task().cancel()
            await flow.start(PHONE)
        task = asyncio.create_task(caller())
        await cancelled(task)
        assert entered and not service.calls and flow.status.step == 'phone'
        assert not flow._busy and flow.export_state()
    return {'caller_entered_API': True, 'source_requests': 0, 'busy_after': False}


async def late_response_after_stop():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        entered, stopping, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        async def delayed(w, r):
            if isinstance(r, functions.auth.SignInRequest):
                entered.set()
                try:
                    await asyncio.Future()
                except asyncio.CancelledError:
                    stopping.set()
                    await release.wait()
                    return service.answer(w, r)
            return NotImplemented
        service.hook = delayed
        task = asyncio.create_task(flow.submit_code(CODE))
        await entered.wait()
        task.cancel()
        await stopping.wait()
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        await cancelled(task)
        assert flow.status.step == 'complete' and flow.session_data
        assert service.calls.count('SignInRequest') == 1
        assert all(not w.up for w in service.wires)
    return {'caller_cancelled': True, 'late_authorization_retained': True, 'signins': 1}


async def component_self_cancel():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        async def self_stop(w, r):
            if isinstance(r, functions.auth.SendCodeRequest):
                asyncio.current_task().cancel()
                await asyncio.sleep(0)
            return NotImplemented
        service.hook = self_stop
        task = asyncio.create_task(flow.start(PHONE))
        await expect('interrupted', task)
        assert not task.cancelled() and flow.status.step == 'uncertain'
    return {'public_task_cancelled': False, 'kind': 'interrupted'}


async def paired_code_and_flush_failure():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        def fail_flush():
            raise OSError('synthetic private flush failure')
        with patch.object(flow._session, 'close', fail_flush):
            await expect('invalid_code', flow.submit_code('99999'))
        assert flow.status.step == 'code' and flow.status.cleanup_pending
        await expect('cleanup_required', flow.submit_code(CODE))
        assert not (await flow.close()).cleanup_pending
        assert (await flow.submit_code(CODE)).step == 'complete'
    return 'Original invalid-code error survives native flush failure; explicit close permits continuation'


async def close_retry_repeated_stop():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        async def fail(w):
            raise OSError('synthetic close failure')
        service.close_hook = fail
        status = await flow.start(PHONE)
        assert status.step == 'code' and status.cleanup_pending
        entered, release = asyncio.Event(), asyncio.Event()
        async def hold(w):
            entered.set()
            await release.wait()
        service.close_hook = hold
        task = asyncio.create_task(flow.close())
        await entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        await expect('busy', flow.submit_code(CODE))
        release.set()
        await cancelled(task)
        assert not flow.status.cleanup_pending and flow.status.step == 'code'
        assert flow.export_state()
    return 'Repeatedly cancelled close settles once before releasing pending state'


async def component_close_cancel():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        async def stop(w):
            raise asyncio.CancelledError('synthetic component cleanup stop')
        service.close_hook = stop
        status = await flow.start(PHONE)
        assert status.step == 'code' and status.cleanup_pending
        service.close_hook = None
        assert not (await flow.close()).cleanup_pending
        assert flow.export_state()
    return 'Component cleanup stop preserves result and requires explicit cleanup retry'


async def completed_key_revoked():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        await flow.submit_code(CODE)
        flow = LoginFlow(config, state=flow.export_state())
        service.authorized.clear()
        assert (await flow.check_authorization()).step == 'restart_required'
        try:
            flow.session_data
        except LoginError as exc:
            assert exc.kind == 'not_complete'
        else:
            raise AssertionError('Known revoked credential still called complete')
        assert service.calls.count('SendCodeRequest') == 1
    return 'Fresh unauthorized observation invalidates completed status without requesting a code'


async def ordinary_client_consumes_credential():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        await flow.submit_code(CODE)
        store = type('Store', (dict,), {'load': dict.get, 'save': dict.__setitem__})()
        store['reader'] = flow.session_data
        client = ConnectionEngine(config, session_store=store, interactive_login=False)._new_client('reader')
        client._sender = Wire(client, service)
        try:
            await client.connect()
            user = await client.get_me()
            assert user.id == 4242 and await client.is_user_authorized()
        finally:
            await _disconnect_owned(client)
        restored = StoredSession(store, 'reader')
        assert restored.auth_key.key == KEY and restored.get_input_entity(0).access_hash == 4242
        assert service.calls.count('SendCodeRequest') == 1
    return 'Ordinary native client connects and verifies identity from the returned stored session'


async def real_ambient_health():
    with fixture(True) as (config, service):
        events = []
        monitor = health.HealthMonitor(events.append, identity=lambda: ('stale-owner', 111))
        try:
            async with monitor.call('old_reader'):
                raise errors.AuthKeyUnregisteredError(None)
        except errors.AuthKeyUnregisteredError:
            pass
        assert monitor._account == health.LOGGED_OUT
        initial = len(events)
        flow = LoginFlow(config)
        async with monitor.call('application_handler') as call:
            # Actual native RPC answer on the ambient task before nested login.
            client = ConnectionEngine(config)._new_client(session_file=MemorySession())
            client._sender = Wire(client, service)
            try:
                await client.connect()
                await client(functions.help.GetConfigRequest())
            finally:
                await _disconnect_owned(client)
            assert call.answered > monitor._account_tick
            await flow.start(PHONE)
            await flow.submit_code(CODE)
            await flow.submit_password(PASSWORD)
        assert monitor._account == health.LOGGED_OUT and len(events) == initial
    return 'Native auth neither relabels nor recovers stale owner in actual HealthMonitor'


async def application_continues_after_call():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        settled, finish = asyncio.Event(), asyncio.Event()
        async def handler():
            await flow.start(PHONE)
            settled.set()
            await finish.wait()
        task = asyncio.create_task(handler())
        await settled.wait()
        assert not task.done() and flow.export_state()
        assert (await flow.submit_code(CODE)).step == 'complete'
        finish.set()
        await task
    return 'Invocation completion is independent of later application-task lifetime'


async def malformed_phase_matrix():
    with fixture() as (config, service):
        flow = LoginFlow(config)
        await flow.start(PHONE)
        base = json.loads(base64.urlsafe_b64decode(flow.export_state().split(':',2)[2]))
        edits = [dict(version=True), dict(step='complete'), dict(uncertain_action='code'),
                 dict(phone=None), dict(code_hash=''), dict(account_id=0),
                 dict(not_before=float('nan')), dict(identity={})]
        start = len(service.calls)
        for edit in edits:
            data = dict(base, **edit)
            blob = 'tgdata-login:1:' + base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
            try:
                LoginFlow(config, state=blob)
            except LoginError as exc:
                assert exc.kind == 'invalid_state'
                assert exc.__context__ is None and exc.__cause__ is None
            else:
                raise AssertionError('Malformed phase admitted')
        assert len(service.calls) == start
    return {'malformed_inputs_rejected_before_network': len(edits)}


async def main():
    cases = [delivery_variants, signin_signup_refusal, wait_code_and_password,
             wait_on_uncertain_check, bounded_double_redirect, queued_stop_reaches_public_boundary,
             late_response_after_stop, component_self_cancel, paired_code_and_flush_failure,
             close_retry_repeated_stop, component_close_cancel, completed_key_revoked,
             ordinary_client_consumes_credential, real_ambient_health,
             application_continues_after_call, malformed_phase_matrix]
    results = []
    loop = asyncio.get_running_loop()
    leaked = []
    previous = loop.get_exception_handler()
    loop.set_exception_handler(lambda loop, context: leaked.append(context.get('message')))
    try:
        for case in cases:
            try:
                observed = await asyncio.wait_for(case(), 15)
                await asyncio.sleep(0)
                pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
                assert not pending, 'Owned tasks remained after case'
                assert not leaked, 'Unobserved task exception'
                row = dict(case=case.__name__, result='PASS', observation=observed)
            except BaseException as exc:
                row = dict(case=case.__name__, result='FAIL', error_type=type(exc).__name__)
                traceback.print_exc()
            results.append(row)
            print(json.dumps(row), flush=True)
    finally:
        loop.set_exception_handler(previous)
    passed = all(row['result']=='PASS' for row in results)
    manifest = dict(result='PASS' if passed else 'FAIL', groups=len(results), observations=results,
                    product_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                    for name in ('tgdata/login.py','tgdata/connection_engine.py',
                                                 'tgdata/session_store.py','tgdata/account_operation.py')},
                    scope='actual installed SDK and library; controlled wire, no live provider qualification')
    (HERE/'results.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Fresh PR probes: {}/{}'.format(sum(r['result']=='PASS' for r in results),len(results)),flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        raise SystemExit(asyncio.run(main()))
