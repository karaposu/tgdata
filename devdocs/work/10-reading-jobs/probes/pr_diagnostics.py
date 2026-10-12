"""Fresh diagnostic/protocol observations through real SDK errors and worker jobs."""
import asyncio
import json
import logging
from pathlib import Path
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from telethon import errors, functions, types
from tgdata.smoke_tests import test_37_worker as f
from tgdata.worker_protocol import RequestDecoder, WorkerError

SENTINEL = 'RAW_AUTH_DIAGNOSTIC_7D93C1'


async def auth_case(code, message):
    async with f.Setup() as setup:
        request = functions.users.GetUsersRequest([types.InputUserSelf()])
        # Real SDK RPC error decoding: only Telegram's wire answer is synthetic.
        encoded = bytes(types.RpcError(error_code=code, error_message=message))
        from telethon.extensions import BinaryReader
        with BinaryReader(encoded) as reader:
            decoded = reader.tgread_object()
        source_error = errors.rpc_message_to_error(decoded, request)
        setup.items[111].scripts['GetUsersRequest'] = [source_error]
        value, events = await setup.call('lookup_group')
        leaked = SENTINEL in json.dumps(value)
        source = setup.items[111].clients[-1]._sender
        result = dict(case='auth_diagnostic', rpc_code=code, sdk_type=type(source_error).__name__,
            error=value['error'], raw_text_forwarded=leaked, health_events=len(events),
            group_requests=any('Resolve' in name or 'History' in name for name in source.calls),
            read_charge=setup.budget.status(111).used, actual_cleanup=source.closed)
        assert not result['group_requests'] and result['read_charge'] == 0 and source.closed
        print(json.dumps(result), flush=True)
        return result


def protocol_controls():
    decoder = RequestDecoder()
    invalid = [True, 0, 9007199254740992, '1', 1.0, None]
    for ident in invalid:
        raw = dict(version=1, request_id=ident, account_id='111', operation='lookup_group', params={'target':'@room'})
        try:
            decoder.decode((json.dumps(raw)+'\n').encode())
        except WorkerError:
            assert decoder.last_id == 0
        else:
            raise AssertionError('Invalid request ID admitted')
    bad = dict(version=1, request_id=17, account_id='111', operation='lookup_group', params={'target':None})
    for expected in ('invalid_parameters', 'stale_request_id'):
        try:
            decoder.decode((json.dumps(bad)+'\n').encode())
        except WorkerError as error:
            assert error.code == expected and error.request_id == 17
        else:
            raise AssertionError('Refused identity reused')
    print(json.dumps(dict(case='protocol_controls', invalid_ids=6,
                         source_free_refusal_consumed=True, duplicate_refused=True)), flush=True)


async def main():
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        for code, message in ((401, SENTINEL), (406, SENTINEL),
                              (403, SENTINEL), (401, 'AUTH_KEY_UNREGISTERED')):
            await auth_case(code, message)
        protocol_controls()


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    asyncio.run(main())
