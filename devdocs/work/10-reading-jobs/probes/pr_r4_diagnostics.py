"""Fresh SDK/Worker probes at later proof, source and projection boundaries."""
import asyncio
import io
import json
import logging
from pathlib import Path
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tgdata import MessageBatch, health, worker
from tgdata.connection_engine import ConnectionEngine
from tgdata import worker_protocol as protocol
from tgdata.smoke_tests import test_37_worker as core


async def source_case(stage, operation, code, text):
    async with core.Setup() as s:
        item = s.items[111]
        item.room.left = True
        error = core.sdk_error(code, text)
        error.request = None  # Actual transport binds the decoded error to the sent request.
        if stage == 'state':
            item.responses['GetStateRequest'] = error
        elif stage == 'admission':
            item.scripts['GetUsersRequest'] = [[core.f.user(111)], error]
        elif stage == 'resolution':
            item.scripts['ResolveUsernameRequest'] = [error]
        elif stage == 'history':
            item.scripts['GetHistoryRequest'] = [error]
        elif stage == 'partial':
            item.scripts['GetHistoryRequest'] = [
                core.b.f.response([core.b.f.message(n) for n in reversed(range(101, 201))]), error]
        else:
            raise AssertionError(stage)
        kwargs = dict(group_id='@room', after_id='100', limit=200) if stage == 'partial' else {}
        value, events = await s.call(operation, **kwargs)
        assert not value['ok'] and not value['worker_stopping']
        assert core.SECRET not in json.dumps([value, events])
        wrapped = stage in ('state', 'admission') and isinstance(error, (core.errors.UnauthorizedError, core.errors.AuthKeyError))
        expected = 'authentication_required' if wrapped else 'telegram_error'
        assert value['error']['category'] == expected
        if wrapped:
            assert value['error']['type'] == 'AuthRequiredError'
            assert value['error'].get('reason') == (text if text != core.SECRET else None)
            assert value['error']['banned'] is (text == 'USER_DEACTIVATED_BAN')
        else:
            assert value['error']['type'] == type(error).__name__
            assert value['error']['code'] == error.code
            assert value['error'].get('name') == health._TELEGRAM_NAMES.get(type(error))
        sender = item.clients[-1]._sender
        assert sender.closed and sender.close_calls == 1
        assert all(e['account_id'] == e['event']['account']['user_id'] == '111' and
                   e['request_id'] == value['request_id'] for e in events)
        assert all(e['event']['error'] is None for e in events) if text == core.SECRET else True
        charge = 200 if stage == 'partial' else (1 if operation == 'check_group_access' else 2) if stage == 'history' else 0
        assert s.budget.status(111).used == charge and s.join.status(111).used == 0
        if stage not in ('history', 'partial'):
            assert 'GetHistoryRequest' not in sender.calls
        assert not any(name in sender.calls for name in ('JoinChannelRequest', 'ImportChatInviteRequest',
                                                        'SendCodeRequest', 'SignInRequest'))
        if stage == 'partial':
            batch = MessageBatch(value['partial_result'])
            assert len(batch.messages) == 100 and batch.batch_id == error.partial_result.batch_id
        # A successful job on B cannot inherit or clear A's observation.
        before = s.worker._apps[111].get_account_health(111)
        successor, later = await s.call(account=222)
        assert successor['ok'] and successor['account_id'] == '222' and not later
        after = s.worker._apps[111].get_account_health(111)
        assert before == after and s.budget.status(222).used == 2
        return dict(stage=stage, operation=operation, sdk_type=type(error).__name__,
                    category=expected, known=text != core.SECRET, health=len(events),
                    charge=charge, raw_text=False, native_cleanup=True, isolated_successor=True)


def protocol_controls():
    refused = 0
    for raw in (b'{"version":1,"request_id":1e309}\n', b'['*2000 + b']'*2000 + b'\n',
                b'{"version":1,"request_id":' + b'1'*5000 + b'}\n'):
        decoder = protocol.RequestDecoder()
        try:
            decoder.decode(raw)
        except protocol.WorkerError:
            assert decoder.last_id == 0
            refused += 1
        else:
            raise AssertionError('Malformed request accepted')
    value = dict(kind='control', text='a\u00e9\U0001f600' * 200)
    encoded = protocol.encode_frame(value)
    assert protocol.encode_frame(value, maximum=len(encoded)) == encoded
    try:
        protocol.encode_frame(value, maximum=len(encoded)-1)
    except protocol.WorkerError as error:
        assert error.code == 'delivery_failed'
    else:
        raise AssertionError('Oversize frame accepted')
    class ShortWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:3])
    stream = ShortWriter()
    worker._write_all(stream, encoded)
    assert stream.getvalue() == encoded
    original = ConnectionEngine._auth_required('private', core.sdk_error(401, core.SECRET), False)
    assert original.reason == core.SECRET and 'reason' not in protocol.describe_error(original)
    return dict(malformed=refused, exact_frame_limit=True, short_writes_exact=True, library_reason_preserved=True)


async def main():
    count = 0
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        for stage, operations in (
                ('state', protocol.OPERATIONS),
                ('admission', ('read_batch', 'check_group_access', 'join_group')),
                ('resolution', protocol.OPERATIONS),
                ('history', ('read_batch', 'check_group_access')),
                ('partial', ('read_batch',))):
            for operation in operations:
                for code in (401, 406, 403):
                    result = await source_case(stage, operation, code, core.SECRET)
                    print(json.dumps(result), flush=True)
                    count += 1
        for operation in ('read_batch', 'check_group_access', 'join_group'):
            for text in ('SESSION_REVOKED', 'USER_DEACTIVATED_BAN'):
                result = await source_case('admission', operation, 401, text)
                print(json.dumps(result), flush=True)
                count += 1
        print(json.dumps(protocol_controls()), flush=True)
    print('PASS fresh diagnostic histories:', count, '+ protocol control group', flush=True)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    asyncio.run(main())
