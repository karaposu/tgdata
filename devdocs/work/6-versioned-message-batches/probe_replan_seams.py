"""Observe the SDK/file-object seam needed by the #6 rejection re-plan.

This is a protocol probe, not the production publisher. SDK replies and local
I/O faults are supplied; SDK output handling and Python exception semantics run.
"""

import asyncio
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import telethon
from telethon import errors
from tgdata import health
from tgdata.smoke_tests import test_19_message_batches as t


class FileProbe:
    def __init__(self, stream, fail=None):
        self.stream, self.fail = stream, fail
        self.calls = []

    def __getattr__(self, name):
        value = getattr(self.stream, name)
        if not callable(value):
            return value

        def call(*args, **kwargs):
            self.calls.append(name)
            try:
                if self.fail and name == self.fail[0]:
                    raise self.fail[1]
                return value(*args, **kwargs)
            except Exception as error:
                raise error from None
        return call


async def main():
    print('Re-plan seam probes — Telethon {}'.format(telethon.__version__))
    with tempfile.TemporaryDirectory(prefix='tgdata6_replan_seams_') as tmp, \
            patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
            patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        t.f.TMP = Path(tmp)
        try:
            for name, message in [('document', t.document()), ('photo', t.photo())]:
                _, client, sender = t.instance()
                sender.files[t.ASSET_ID] = t.PAYLOAD
                with tempfile.TemporaryFile(mode='w+b') as raw:
                    supplied = FileProbe(raw)
                    returned = await client.download_media(message, file=supplied)
                    raw.seek(0)
                    assert returned is supplied and raw.read() == t.PAYLOAD
                    assert 'write' in supplied.calls and not raw.closed
                    print('PASS {}: SDK returns supplied proxy, exact bytes, owner retains close'.format(name))

            for operation in ('write', 'flush'):
                _, client, sender = t.instance()
                sender.files[t.ASSET_ID] = t.PAYLOAD
                fault = OSError('synthetic local I/O fault')
                with tempfile.TemporaryFile(mode='w+b') as raw:
                    supplied = FileProbe(raw, (operation, fault))
                    try:
                        raise errors.ChannelPrivateError(request=None)
                    except errors.ChannelPrivateError:
                        caught = await t.f.expect(OSError, client.download_media(t.document(), file=supplied))
                    assert caught is fault and health.classify(caught) is None
                    assert caught.__suppress_context__ and caught.__cause__ is None
                    print('PASS SDK {} fault: original OSError retained, incidental RPC not classified'.format(operation))

            _, client, sender = t.instance()
            reason = errors.ChannelPrivateError(request=None)
            original = ConnectionError('synthetic SDK transport wrapper')
            original.__cause__ = reason
            sender.file_script = [original]
            with tempfile.TemporaryFile(mode='w+b') as raw:
                caught = await t.f.expect(ConnectionError, client.download_media(t.document(), file=FileProbe(raw)))
            assert caught is original and caught.__cause__ is reason
            assert health.classify(caught).verdict == 'no access'
            print('PASS SDK failure: file proxy leaves transport exception identity and explicit RPC cause intact')

            for primary in (errors.ChannelPrivateError(request=None), asyncio.CancelledError('synthetic cancellation')):
                observed = []

                def unwind():
                    try:
                        raise primary
                    finally:
                        try:
                            raise PermissionError('synthetic secondary cleanup failure')
                        except Exception as secondary:
                            observed.append(type(secondary).__name__)

                try:
                    unwind()
                except BaseException as caught:
                    assert caught is primary and observed == ['PermissionError']
                print('PASS unwind: primary {} survives caught secondary cleanup error'.format(type(primary).__name__))
        finally:
            for client in t.f.CLIENTS:
                await client.disconnect()
            t.f.CLIENTS.clear()
    print('All 7 seam observations passed; no production publisher change or live-server claim')


if __name__ == '__main__':
    asyncio.run(main())
