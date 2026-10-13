"""Observe installed SDK/credential boundaries; synthetic wire only, no sockets."""
import asyncio
from datetime import datetime, timezone, timedelta
import inspect
import json
import logging
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from telethon import errors, functions, types
from telethon.crypto import AuthKey
from telethon.sessions import StringSession
from tgdata.connection_engine import ConnectionEngine
from tgdata.session_store import StoredSession

KEY = bytes(range(256))
OTHER = bytes(reversed(range(256)))
DATE = datetime(2026, 10, 13, tzinfo=timezone.utc)
PHONE = '+10000000000'


class Store(dict):
    def load(self, name): return self.get(name)
    def save(self, name, data): self[name] = data


def config_response():
    options = {}
    for name, parameter in inspect.signature(types.Config).parameters.items():
        if parameter.default is not inspect.Parameter.empty: continue
        options[name] = '' if parameter.annotation is str else 0
    options.update(date=DATE, expires=DATE+timedelta(days=1), test_mode=False, this_dc=2,
                   dc_options=[types.DcOption(2,'149.154.167.51',443),
                               types.DcOption(3,'149.154.175.100',443)])
    return types.Config(**options)


def self_user():
    return types.User(id=4242,is_self=True,access_hash=9988,first_name='Synthetic',phone=PHONE[1:])


class Wire:
    def __init__(self, handler):
        self.handler=handler;self.calls=[];self.connections=[];self.auth_key=AuthKey(KEY)
        self.up=True;self._disconnected=asyncio.get_running_loop().create_future()
    def is_connected(self): return self.up
    @property
    def disconnected(self): return self._disconnected
    async def connect(self, connection):
        self.connections.append(connection)
        self.up=True;self._disconnected=asyncio.get_running_loop().create_future()
        if not self.auth_key.key: self.auth_key=AuthKey(OTHER)
        return True
    async def disconnect(self):
        self.up=False
        if not self._disconnected.done(): self._disconnected.set_result(None)
    def send(self, request, ordered=False):
        bytes(request)
        while hasattr(request,'query'): request=request.query
        self.calls.append(type(request).__name__)
        result=self.handler(request)
        future=asyncio.get_running_loop().create_future()
        if isinstance(result,BaseException): future.set_exception(result)
        else: future.set_result(result)
        return future


def client(path, handler):
    file=path/'synthetic.ini'
    file.write_text('[Telegram]\napi_id=12345\napi_hash=0123456789abcdef0123456789abcdef\n'
                    'session_file=must-not-open\nproxy=socks5://test:secret@127.0.0.1:9\n'
                    'device_model=Login Probe\n')
    store=Store();session=StoredSession(store,'synthetic')
    session.set_dc(2,'149.154.167.51',443);session.auth_key=AuthKey(KEY)
    c=ConnectionEngine(str(file),interactive_login=False)._new_client(session_file=session,
        request_retries=0,connection_retries=0,retry_delay=0,auto_reconnect=False,
        receive_updates=False,flood_sleep_threshold=0,raise_last_call_error=True)
    c._sender=Wire(handler)
    return c,store


async def main(path):
    results=[]
    def sent(request):
        assert isinstance(request,(functions.auth.SendCodeRequest,functions.auth.ResendCodeRequest))
        return types.auth.SentCode(types.auth.SentCodeTypeApp(5),'synthetic-hash',timeout=30)
    c,store=client(path,sent)
    try:
        await c.send_code_request(PHONE);await c.send_code_request(PHONE)
        assert c._sender.calls==['SendCodeRequest','ResendCodeRequest']
        results.append(dict(case='convenience_repeated_start',requests=c._sender.calls[:],implicit_resend=True))
        portable=StringSession.save(c.session)
        restored=StringSession(portable)
        assert restored.auth_key.key==KEY
        other=type(c)(restored,12345,'0123456789abcdef0123456789abcdef')
        try:
            assert not other._phone_code_hash
            assert c._phone_code_hash and c.session.dump().startswith('1:')
            results.append(dict(case='credential_is_not_challenge',key_retained=True,challenge_map_lost=True,
                                stored_format_differs=not portable.startswith('1:')))
        finally: await other.disconnect()
    finally: await c.disconnect()

    def post_auth(request):
        if isinstance(request,functions.users.GetUsersRequest): return errors.AuthKeyUnregisteredError(request)
        if isinstance(request,functions.auth.SignInRequest): return types.auth.Authorization(self_user())
        if isinstance(request,functions.updates.GetStateRequest): return types.updates.State(1,1,DATE,1,0)
        if isinstance(request,functions.updates.GetDifferenceRequest): return OSError('synthetic post-auth failure')
        raise AssertionError(type(request).__name__)
    c,store=client(path,post_auth)
    try:
        try: await c.sign_in(PHONE,'12345',phone_code_hash='synthetic-hash')
        except OSError: pass
        else: raise AssertionError('post-auth failure did not escape')
        assert c._authorized and c._self_id==4242
        assert c._sender.calls==['GetUsersRequest','SignInRequest','GetStateRequest','GetDifferenceRequest']
        await c.disconnect()
        restored=StoredSession(store,'synthetic')
        assert restored.auth_key.key==KEY and restored.get_input_entity(0).access_hash==4242
        results.append(dict(case='post_auth_failure',method_raised=True,SDK_authorized=True,
                            credential_and_self_row_retained=True,requests=c._sender.calls[:]))
    finally: await c.disconnect()

    def migrate(request):
        if isinstance(request,functions.auth.SendCodeRequest): return errors.PhoneMigrateError(request,capture=3)
        if isinstance(request,(functions.users.GetUsersRequest,functions.updates.GetStateRequest)):
            return errors.AuthKeyUnregisteredError(request)
        if isinstance(request,functions.help.GetConfigRequest): return config_response()
        raise AssertionError(type(request).__name__)
    c,store=client(path,migrate)
    try:
        with patch.object(type(c),'_config',None):
            try: await c(functions.auth.SendCodeRequest(PHONE,12345,'0123456789abcdef0123456789abcdef',types.CodeSettings()))
            except errors.PhoneMigrateError: pass
            else: raise AssertionError('zero-retry migration did not raise')
        assert c.session.dc_id==3 and c.session.auth_key.key==OTHER
        assert c._sender.calls.count('SendCodeRequest')==1 and len(c._sender.connections)==1
        assert c._sender.connections[0]._proxy==c._proxy
        results.append(dict(case='zero_retry_migration',method_raised=True,dc_changed=True,key_changed=True,
                            auth_requests=1,proxy_retained=True,requests=c._sender.calls[:]))
    finally: await c.disconnect()

    class FailedStore(Store):
        def save(self,name,data): raise OSError('synthetic credential-save failure')
    store=FailedStore();s=StoredSession(store,'synthetic');s.auth_key=AuthKey(KEY)
    s.save()
    assert not store and s.dump().startswith('1:')
    results.append(dict(case='save_is_not_publication_receipt',save_raised=False,stored=False,dump_available=True))
    assert not list(path.glob('*.session'))
    print(json.dumps(dict(result='PASS',groups=len(results),observations=results,scope='actual SDK/serializer with synthetic wire; no server qualification'),indent=2))


if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    with tempfile.TemporaryDirectory(prefix='tgdata8-sdk-probe-') as folder, \
         patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        asyncio.run(asyncio.wait_for(main(Path(folder)),10))
