"""
Smoke test for the WebSocket transport (issue #67): `transport = websocket`
reaches Telegram's WebSocket door by hostname, never by IP.

Everything runs OFFLINE: loopback sockets only, never Telegram, never an
account. A local TLS WebSocket server ("the door") and a local proxy that
records every destination it is asked for (HTTP CONNECT and SOCKS5) stand in
for the network; Telethon 1.45.0's real connection, sender and client code
run against them. TLS items need the `openssl` command — a throwaway test
certificate authority is generated in a temp folder, nothing is committed —
and are SKIPPED without it.

The opener (tgdata.ws_stream)                                     (loopback)
  1. the handshake: GET /apiws, binary, no Origin; 101 + accept required;
     an IP host refused; an untrusted certificate refused; a silent door times out
  2. framing: fragments and length boundaries, ping -> pong, close / EOF,
     protocol violations
The connection class (tgdata.websocket_transport)                 (loopback)
  3. named at construction (no IP held), the DC map, unmapped DCs refused,
     Telethon's own sender delivers its first message through the door
No IP on any path (built by tgdata's real client factory)         (loopback)
  4. main connect over SOCKS5 and HTTP CONNECT; Telethon's own reconnect
  5. a connection to another DC (an exported sender)
  6. owned operations, LoginFlow, AccountPool sources, a mixed tcp + websocket
     pool, and the direct (no proxy) case
Classification and the rest of the contract
  7. refused upgrade -> retried -> 'transport'; certificate -> stops at once ->
     'unknown'; config errors; TgData's wrappers; polling and the worker
  8. no health verdicts; a mid-session close is a warning, not a traceback
  9. the default path is byte-identical to before #67                (no network)
 10. the login binding and observability                             (no network)
 11. CANARY — RUN AFTER ANY TELETHON UPGRADE: the Telethon internals the
     transport relies on
"""
# To run: python -m tgdata.smoke_tests.test_50_websocket_transport

import ast
import asyncio
import base64
import contextlib
import hashlib
import inspect
import json
import logging
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import types as pytypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from telethon import types
from telethon.crypto import AuthKey, AESModeCTR
from telethon.network import MTProtoSender
from telethon.network.connection.connection import Connection
from telethon.network.connection.tcpobfuscated import ConnectionTcpObfuscated
import telethon.client.telegrambaseclient as telethon_base

from tgdata import connection_engine as ce
from tgdata import login as login_module
from tgdata import health, ws_stream, websocket_transport as wt, worker_protocol
from tgdata import (AccountPool, PoolAccount, PoolGroup, PoolPolicy, ReadBudget,
                    SQLiteAccountPoolStore, ProxyConfigError, TransportConfigError)
from tgdata.connection_engine import ConnectionEngine
from tgdata.login import LoginFlow, LoginError
from tgdata.tgdata import _polling_cannot_recover
from tgdata.websocket_transport import ConnectionWebSocket

TMP = tempfile.mkdtemp(prefix="tgdata_ws_test_")

API_HASH = "0123456789abcdef0123456789abcdef"
IDENTITY_LINES = "device_model = BaselineModel\nlang_code = en\n"
PROXY_LINE = "proxy = socks5://u:p@127.0.0.1:1080\n"

# Today's default path, captured by capture_default_path() at a199c0c — before
# any #67 code change — and pasted here. Step 9 re-captures and compares.
BASELINE = json.loads(r'''
{
 "direct": {
  "binding": "1fb3c4e29b47a61fef00462b2d13c9f211068539ba37ecbcd8ff8199183b97b9",
  "clients": [
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "device_model": "BaselineModel",
     "lang_code": "en",
     "proxy": null,
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": null,
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "base_logger": "<logger tgdata.login.sdk>",
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": null,
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   }
  ],
  "route_lines": [
   "Telegram connections are direct (no proxy configured)",
   "Device identity pinned: device_model='BaselineModel', lang_code='en', system_lang_code='en'"
  ]
 },
 "proxy": {
  "binding": "42d13bbc6c9021ddf4eca7231b2ebfb65c1e3fe617f064bd6ded1f5ad2ae5202",
  "clients": [
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "device_model": "BaselineModel",
     "lang_code": "en",
     "proxy": {
      "addr": "127.0.0.1",
      "password": "p",
      "port": 1080,
      "proxy_type": "socks5",
      "rdns": true,
      "username": "u"
     },
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": {
      "addr": "127.0.0.1",
      "password": "p",
      "port": 1080,
      "proxy_type": "socks5",
      "rdns": true,
      "username": "u"
     },
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "base_logger": "<logger tgdata.login.sdk>",
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": {
      "addr": "127.0.0.1",
      "password": "p",
      "port": 1080,
      "proxy_type": "socks5",
      "rdns": true,
      "username": "u"
     },
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   }
  ],
  "route_lines": [
   "Telegram connections go via proxy socks5://u:***@127.0.0.1:1080",
   "Device identity pinned: device_model='BaselineModel', lang_code='en', system_lang_code='en'"
  ]
 }
}
''')


def write_ini(name: str, body: str, session: str = 'baseline') -> str:
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write("[Telegram]\napi_id = 12345\n"
                f"api_hash = {API_HASH}\n"
                f"session_file = {os.path.join(TMP, session)}\n" + body)
    return path


def _plain(value):
    """Constructor arguments as comparable JSON values (loggers by name)."""
    if isinstance(value, logging.Logger):
        return f"<logger {value.name}>"
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return f"<{type(value).__name__}>"


def capture_default_path():
    """What tgdata builds for a fixed TCP account today: TelegramClient's
    arguments (minus the session object) for the ordinary client, an owned
    account operation's client and LoginFlow's client; the route log lines;
    and the login binding hash — with and without a proxy. Construction
    only: nothing connects."""
    records = []

    class Recorder(ce.TelegramClient):
        def __init__(self, *args, **kwargs):
            records.append({'args': _plain(list(args[1:])), 'kwargs': _plain(kwargs)})
            super().__init__(*args, **kwargs)

    class LoginRecorder(login_module._LoginClient):
        def __init__(self, *args, **kwargs):
            records.append({'args': _plain(list(args[1:])), 'kwargs': _plain(kwargs)})
            super().__init__(*args, **kwargs)

    strict = dict(flood_sleep_threshold=0, request_retries=0, connection_retries=0,
                  retry_delay=0, auto_reconnect=False, raise_last_call_error=True,
                  receive_updates=False)
    out = {}
    log = logging.getLogger("tgdata.connection_engine")
    for name, body in (("proxy", PROXY_LINE + IDENTITY_LINES), ("direct", IDENTITY_LINES)):
        ini = write_ini(f"baseline_{name}.ini", body)
        lines = []
        handler = logging.Handler(logging.INFO)
        handler.emit = lambda record: lines.append(record.getMessage())
        old_level = log.level
        log.setLevel(logging.INFO)
        log.addHandler(handler)
        original, original_login = ce.TelegramClient, login_module._LoginClient
        ce.TelegramClient, login_module._LoginClient = Recorder, LoginRecorder
        records.clear()
        try:
            engine = ConnectionEngine(ini)
            engine._new_client()                     # ordinary client (logs the route once)
            engine._new_client(**strict)             # an owned account operation's client
            flow = LoginFlow(ini)                    # constructor only: builds its client, no socket
            out[name] = {'clients': list(records), 'route_lines': list(lines),
                         'binding': flow._binding}
        finally:
            ce.TelegramClient, login_module._LoginClient = original, original_login
            log.removeHandler(handler)
            log.setLevel(old_level)
    return out


STRICT = dict(flood_sleep_threshold=0, request_retries=0, connection_retries=0, retry_delay=0,
              auto_reconnect=False, raise_last_call_error=True, receive_updates=False)


# ---------------------------------------------------------------- harness --

def make_pki():
    """A throwaway test CA and a *.web.telegram.org leaf signed by it, made with
    the openssl command in a temp folder. None when openssl is unavailable."""
    if shutil.which("openssl") is None:
        return None
    d = os.path.join(TMP, "pki")
    os.makedirs(d, exist_ok=True)
    run = lambda *a: subprocess.run(["openssl", *a], cwd=d, capture_output=True, check=True)
    try:
        run("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "ca.key", "-out", "ca.pem",
            "-days", "2", "-subj", "/CN=tgdata test CA")
        run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "leaf.key", "-out", "leaf.csr",
            "-subj", "/CN=*.web.telegram.org")
        with open(os.path.join(d, "ext.cnf"), "w") as f:
            f.write("subjectAltName=DNS:*.web.telegram.org\n")
        run("x509", "-req", "-in", "leaf.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial",
            "-out", "leaf.pem", "-days", "2", "-extfile", "ext.cnf")
    except (subprocess.CalledProcessError, OSError):
        return None
    server = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server.load_cert_chain(os.path.join(d, "leaf.pem"), os.path.join(d, "leaf.key"))
    trust = ssl.create_default_context(cafile=os.path.join(d, "ca.pem"))
    return pytypes.SimpleNamespace(server=server, trust=trust)


def server_frame(opcode, payload=b"", fin=True, masked=False, rsv=0):
    head = bytearray([(0x80 if fin else 0) | rsv | opcode])
    n = len(payload)
    mask_bit = 0x80 if masked else 0
    if n < 126:
        head.append(mask_bit | n)
    elif n < 65536:
        head.append(mask_bit | 126)
        head += n.to_bytes(2, "big")
    else:
        head.append(mask_bit | 127)
        head += n.to_bytes(8, "big")
    if masked:
        key = os.urandom(4)
        return bytes(head) + key + ws_stream._xor(payload, key)
    return bytes(head) + payload


async def read_client_frame(reader):
    b1, b2 = await reader.readexactly(2)
    n = b2 & 0x7F
    if n == 126:
        n = int.from_bytes(await reader.readexactly(2), "big")
    elif n == 127:
        n = int.from_bytes(await reader.readexactly(8), "big")
    key = await reader.readexactly(4) if b2 & 0x80 else b""
    payload = await reader.readexactly(n)
    return b1 & 0x0F, bool(b2 & 0x80), ws_stream._xor(payload, key) if key else payload


class FakeDoor:
    """A local TLS WebSocket server playing Telegram's door.

    Per connection, `modes` (a queue) or `default_mode` decides what happens
    after the upgrade request: 'close_after_first' (record Telethon's first
    MTProto message, then send a close frame — key exchange fails at once),
    'silent', 'drop' (drop the TCP stream right after the 101),
    'close_now' (a close frame right after the 101), 'status_403',
    'bad_accept', 'no_answer', or 'script' (run self.script(reader, writer))."""

    def __init__(self, pki):
        self.pki, self.modes, self.default_mode, self.script = pki, [], "close_after_first", None
        self.upgrades, self.constructors, self.frames = [], [], []

    async def start(self):
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0, ssl=self.pki.server)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def close(self):
        self.server.close()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(self.server.wait_closed(), 2)

    async def _handle(self, reader, writer):
        mode = self.modes.pop(0) if self.modes else self.default_mode
        try:
            head = (await reader.readuntil(b"\r\n\r\n")).decode("latin-1")
            self.upgrades.append(head)
            if mode == "no_answer":
                await asyncio.sleep(30)
                return
            if mode == "status_403":
                writer.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                await writer.drain()
                return
            key = next(l.split(":", 1)[1].strip() for l in head.split("\r\n")
                       if l.lower().startswith("sec-websocket-key"))
            accept = base64.b64encode(hashlib.sha1((key + ws_stream.WS_GUID).encode()).digest()).decode()
            if mode == "bad_accept":
                accept = base64.b64encode(b"x" * 20).decode()
            writer.write(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                         f"Sec-WebSocket-Accept: {accept}\r\nSec-WebSocket-Protocol: binary\r\n\r\n".encode())
            await writer.drain()
            if mode == "script":
                await self.script(reader, writer)
            elif mode == "drop":
                await asyncio.sleep(0.3)
            elif mode == "close_now":
                writer.write(server_frame(0x8, (1000).to_bytes(2, "big")))
                await writer.drain()
                await asyncio.sleep(0.5)
            elif mode == "silent":
                await asyncio.sleep(30)
            else:                                            # close_after_first
                stream = b""
                while len(stream) < 64 + 1 + 40:
                    opcode, masked, payload = await read_client_frame(reader)
                    self.frames.append((opcode, masked))
                    stream += payload
                plain = AESModeCTR(stream[8:40], stream[40:56]).encrypt(stream)
                body = plain[65:65 + plain[64] * 4]
                self.constructors.append(body[20:24][::-1].hex())
                writer.write(server_frame(0x8, (1000).to_bytes(2, "big")))
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError, ssl.SSLError, asyncio.CancelledError):
            pass
        finally:
            with contextlib.suppress(Exception):
                writer.close()


class RecordingProxy:
    """A local proxy that speaks HTTP CONNECT and SOCKS5 (no-auth or user/pass),
    records every (kind, host, port) it is asked for, and forwards every tunnel
    to `upstream` — so a hostname target reaches a local server."""

    def __init__(self, upstream_port):
        self.upstream_port, self.destinations = upstream_port, []

    async def start(self):
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def close(self):
        self.server.close()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(self.server.wait_closed(), 2)

    def hosts(self):
        return [h for _, h, _ in self.destinations]

    @staticmethod
    async def _pipe(a, b):
        try:
            while True:
                data = await a.read(65536)
                if not data:
                    break
                b.write(data)
                await b.drain()
        except Exception:  # noqa: BLE001 — a test relay
            pass
        finally:
            with contextlib.suppress(Exception):
                b.close()

    async def _handle(self, reader, writer):
        try:
            first = await reader.readexactly(1)
            if first == b"\x05":
                n = (await reader.readexactly(1))[0]
                methods = await reader.readexactly(n)
                if 2 in methods:
                    writer.write(b"\x05\x02")
                    await writer.drain()
                    await reader.readexactly(1)
                    await reader.readexactly((await reader.readexactly(1))[0])
                    await reader.readexactly((await reader.readexactly(1))[0])
                    writer.write(b"\x01\x00")
                else:
                    writer.write(b"\x05\x00")
                await writer.drain()
                _, _, _, atyp = await reader.readexactly(4)
                if atyp == 3:
                    host = (await reader.readexactly((await reader.readexactly(1))[0])).decode()
                elif atyp == 1:
                    host = socket.inet_ntoa(await reader.readexactly(4))
                else:
                    host = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
                port = int.from_bytes(await reader.readexactly(2), "big")
                self.destinations.append(("socks5", host, port))
                ok = b"\x05\x00\x00\x01" + b"\x00" * 6
            else:
                head = (first + await reader.readuntil(b"\r\n\r\n")).decode("latin-1")
                target = head.split("\r\n")[0].split(" ")[1]
                host, _, port = target.rpartition(":")
                self.destinations.append(("http", host.strip("[]"), int(port)))
                ok = b"HTTP/1.1 200 Connection established\r\n\r\n"
            up_reader, up_writer = await asyncio.open_connection("127.0.0.1", self.upstream_port)
            writer.write(ok)
            await writer.drain()
            await asyncio.gather(self._pipe(reader, up_writer), self._pipe(up_reader, writer))
        except Exception:  # noqa: BLE001 — a test relay
            with contextlib.suppress(Exception):
                writer.close()


async def bounded(coro, seconds=6):
    """Run one connect-type call to its end; return the exception it ended with."""
    try:
        await asyncio.wait_for(coro, seconds)
        return None
    except BaseException as e:  # noqa: BLE001 — the test inspects what happened
        if isinstance(e, KeyboardInterrupt):
            raise
        return e


@contextlib.contextmanager
def restoring(client=None):
    """Undo the process-wide state a test sets: the client class's cached
    Telegram config (Telethon keeps it on the class, shared by every client
    tgdata builds) and the WebSocket transport's test trust store."""
    trust = ConnectionWebSocket._ssl_context
    try:
        yield
    finally:
        ConnectionWebSocket._ssl_context = trust
        if client is not None:
            for name in ("_config", "_cdn_config"):
                if name in type(client).__dict__:
                    delattr(type(client), name)


class Loggers(dict):
    def __missing__(self, key):
        return logging.getLogger(key)


def collect(sender):
    """A bare MTProtoSender stores the error that ended it on its
    `_disconnected` future, which a TelegramClient awaits; retrieve it here so
    asyncio does not report it as never retrieved."""
    future = getattr(sender, "_disconnected", None)
    if future is not None and future.done() and not future.cancelled():
        future.exception()


def ws_ini(name, proxy_url, extra="", session="baseline"):
    return write_ini(name, f"transport = websocket\nproxy = {proxy_url}\n" + extra, session)


def is_ip(host):
    try:
        import ipaddress
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


class Checks:
    def __init__(self):
        self.passed = self.failed = 0

    def __call__(self, condition, message):
        if condition:
            self.passed += 1
            print(f"✓ {message}")
        else:
            self.failed += 1
            print(f"✗ {message}")
        return condition


# ------------------------------------------------------------------ items --

async def item1_handshake(c, pki):
    print("\nTEST 1: the opener's handshake...")
    door = await FakeDoor(pki).start()
    try:
        def tunnel():
            s = socket.create_connection(("127.0.0.1", door.port))
            s.setblocking(False)
            return s
        r, w = await ws_stream.open_websocket("venus.web.telegram.org", sock=tunnel(), timeout=5,
                                              ssl_context=pki.trust)
        head = door.upgrades[-1]
        c("GET /apiws HTTP/1.1" in head and "Host: venus.web.telegram.org" in head
          and "Sec-WebSocket-Protocol: binary" in head and "Sec-WebSocket-Version: 13" in head
          and "Upgrade: websocket" in head and "Origin" not in head,
          "request: GET /apiws, Host = the name, binary, version 13, no Origin")
        c(isinstance(r, ws_stream.WsReader) and isinstance(w, ws_stream.WsWriter), "101 + correct accept: a reader/writer pair")
        w.close()
        for mode, what in (("bad_accept", "a wrong accept key"), ("status_403", "a 403")):
            door.modes.append(mode)
            e = await bounded(ws_stream.open_websocket("venus.web.telegram.org", sock=tunnel(), timeout=5,
                                                       ssl_context=pki.trust))
            c(type(e) is ConnectionError, f"{what} -> ConnectionError: {e}")
        before = len(door.upgrades)
        e = await bounded(ws_stream.open_websocket("149.154.167.50", timeout=5, ssl_context=pki.trust))
        c(type(e) is ValueError and len(door.upgrades) == before, f"an IP host -> ValueError before any socket: {e}")
        e = await bounded(ws_stream.open_websocket("venus.web.telegram.org", sock=tunnel(), timeout=5))
        c(isinstance(e, ssl.SSLCertVerificationError), f"the system trust store refuses the test certificate: {type(e).__name__}")
        door.modes.append("no_answer")
        e = await bounded(ws_stream.open_websocket("venus.web.telegram.org", sock=tunnel(), timeout=1,
                                                   ssl_context=pki.trust), seconds=5)
        c(isinstance(e, asyncio.TimeoutError), f"a door that never answers -> timeout within `timeout`: {type(e).__name__}")
    finally:
        await door.close()


async def item2_framing(c, pki):
    print("\nTEST 2: the opener's framing...")
    door = await FakeDoor(pki).start()
    door.default_mode = "script"

    async def opened(script):
        door.script = script
        s = socket.create_connection(("127.0.0.1", door.port))
        s.setblocking(False)
        return await ws_stream.open_websocket("venus.web.telegram.org", sock=s, timeout=5, ssl_context=pki.trust)

    try:
        sizes = [1, 4, 63, 64, 125, 126, 65535, 65536]
        payloads = [os.urandom(n) for n in sizes]

        async def fragmented(reader, writer):
            for p in payloads:
                half = len(p) // 2
                writer.write(server_frame(0x2, p[:half], fin=False) + server_frame(0x0, p[half:]))
            await writer.drain()
            await asyncio.sleep(1)
        r, w = await opened(fragmented)
        got = [await r.readexactly(n) for n in sizes]
        c(got == payloads, f"fragmented + continuation frames round-trip at {sizes}")
        w.close()

        pong = {}
        async def pinging(reader, writer):
            writer.write(server_frame(0x9, b"hi") + server_frame(0x2, b"x"))
            await writer.drain()
            pong["frame"] = await read_client_frame(reader)
            await asyncio.sleep(0.5)
        r, w = await opened(pinging)
        c(await r.readexactly(1) == b"x", "data after a ping is delivered")
        await asyncio.sleep(0.2)
        c(pong.get("frame") == (0xA, True, b"hi"), f"a ping is answered with a masked pong: {pong.get('frame')}")
        w.close()

        closing = {}
        async def close_frame(reader, writer):
            writer.write(server_frame(0x2, b"ab") + server_frame(0x8, (1000).to_bytes(2, "big")))
            await writer.drain()
            closing["reply"] = await read_client_frame(reader)
        r, w = await opened(close_frame)
        data = await r.readexactly(2)
        e = await bounded(r.readexactly(1))
        await asyncio.sleep(0.2)
        c(data == b"ab" and isinstance(e, asyncio.IncompleteReadError) and closing.get("reply", (0,))[0] == 0x8,
          "a close frame ends the stream (IncompleteReadError) and is answered with a close")
        w.close()

        async def eof(reader, writer):
            writer.close()
        r, w = await opened(eof)
        c(isinstance(await bounded(r.readexactly(1)), asyncio.IncompleteReadError), "end of stream -> IncompleteReadError")
        w.close()

        for name, frame in (("a text frame", server_frame(0x1, b"t")),
                            ("a masked server frame", server_frame(0x2, b"m", masked=True)),
                            ("an oversized control frame", server_frame(0x9, b"p" * 126)),
                            ("a reserved bit", server_frame(0x2, b"r", rsv=0x40))):
            async def bad(reader, writer, frame=frame):
                writer.write(frame)
                await writer.drain()
                await asyncio.sleep(0.5)
            r, w = await opened(bad)
            e = await bounded(r.readexactly(1))
            c(type(e) is ConnectionError, f"{name} -> ConnectionError: {e}")
            w.close()

        sent = {}
        async def receiving(reader, writer):
            sent["frame"] = await read_client_frame(reader)
        r, w = await opened(receiving)
        w.write(b"data")
        await w.drain()
        await asyncio.sleep(0.3)
        c(sent.get("frame") == (0x2, True, b"data"), "each write is one masked binary frame")
        w.close()
    finally:
        await door.close()


async def item3_class(c, pki):
    print("\nTEST 3: the connection class...")
    conn = ConnectionWebSocket("149.154.167.50", 443, 2, loggers=Loggers())
    c(conn._ip == "venus.web.telegram.org" and conn._port == 443
      and not any("149.154" in str(v) for v in vars(conn).values()),
      f"named at construction; no IP anywhere in the object: {conn}")
    c([wt.host_for(dc) for dc in range(1, 6)] == [f"{n}.web.telegram.org" for n in
                                                   ("pluto", "venus", "aurora", "vesta", "flora")],
      "DC 1–5 map to pluto, venus, aurora, vesta, flora")
    for dc in (203, 0):
        try:
            ConnectionWebSocket("1.2.3.4", 443, dc, loggers=Loggers())
            c(False, f"DC {dc} accepted")
        except TransportConfigError as e:
            c(True, f"DC {dc} -> TransportConfigError: {e}")
    c(str(conn).endswith("/WebSocket"), f"Telethon's log form names the host and the transport: {conn}")
    door = await FakeDoor(pki).start()
    proxy = await RecordingProxy(door.port).start()
    try:
        with restoring():
            ConnectionWebSocket._ssl_context = pki.trust
            sender = MTProtoSender(None, loggers=Loggers(), retries=0, delay=0, auto_reconnect=False, connect_timeout=5)
            p = {'proxy_type': 'http', 'addr': '127.0.0.1', 'port': proxy.port, 'rdns': True}
            await bounded(sender.connect(ConnectionWebSocket("149.154.167.50", 443, 2, loggers=Loggers(), proxy=p)))
            with contextlib.suppress(Exception):
                await sender.disconnect()
        c(door.constructors[-1:] == ["be7e8ef1"] and all(op == 2 and m for op, m in door.frames),
          "Telethon's real sender: its first message (req_pq_multi) arrives in masked binary frames")
        c(proxy.destinations == [("http", "venus.web.telegram.org", 443)], f"the proxy was asked only for the name: {proxy.destinations}")
    finally:
        await proxy.close()
        await door.close()


async def item4_main_and_reconnect(c, pki):
    print("\nTEST 4: main connect and reconnect, through the real client factory...")
    door = await FakeDoor(pki).start()
    proxy = await RecordingProxy(door.port).start()
    try:
        for scheme in ("socks5://u:p@", "http://"):
            engine = ConnectionEngine(ws_ini(f"main_{scheme[:4]}.ini", f"{scheme}127.0.0.1:{proxy.port}"))
            client = engine._new_client(connection_retries=0, retry_delay=0)
            before = len(proxy.destinations)
            with restoring(client):
                ConnectionWebSocket._ssl_context = pki.trust
                await bounded(client.connect())
                await bounded(client.disconnect())
            got = proxy.destinations[before:]
            c(got and all(h == "venus.web.telegram.org" and port == 443 for _, h, port in got),
              f"{scheme.split(':')[0]}: client.connect() reached only DC 2's name: {got}")
        before = len(proxy.destinations)
        door.modes += ["drop", "silent"]
        p = {'proxy_type': 'socks5', 'addr': '127.0.0.1', 'port': proxy.port, 'rdns': True}
        conn = ConnectionWebSocket("149.154.167.91", 443, 4, loggers=Loggers(), proxy=p)
        sender = MTProtoSender(AuthKey(os.urandom(256)), loggers=Loggers(), retries=1, delay=0,
                               auto_reconnect=True, connect_timeout=5)
        with restoring():
            ConnectionWebSocket._ssl_context = pki.trust
            await bounded(sender.connect(conn))
            for _ in range(40):
                if len(proxy.destinations) - before >= 2:
                    break
                await asyncio.sleep(0.1)
            same_object = sender._connection is conn       # disconnect() clears it, so check first
            await bounded(sender.disconnect())
        got = proxy.hosts()[before:]
        c(len(got) >= 2 and set(got) == {"vesta.web.telegram.org"} and same_object,
          f"a dropped connection: Telethon's own reconnect reuses the object and dials the name again: {got}")
    finally:
        await proxy.close()
        await door.close()


async def item5_exported_sender(c, pki):
    print("\nTEST 5: a connection to another DC (an exported sender)...")
    door = await FakeDoor(pki).start()
    proxy = await RecordingProxy(door.port).start()
    try:
        engine = ConnectionEngine(ws_ini("exported.ini", f"socks5://127.0.0.1:{proxy.port}"))
        client = engine._new_client(connection_retries=0, retry_delay=0)
        with restoring(client):
            ConnectionWebSocket._ssl_context = pki.trust
            type(client)._config = pytypes.SimpleNamespace(dc_options=[
                types.DcOption(id=4, ip_address="149.154.167.91", port=443)])
            before = len(proxy.destinations)
            await bounded(client._create_exported_sender(4))
            got = proxy.hosts()[before:]
        c(got == ["vesta.web.telegram.org"] and not any(is_ip(h) for h in got),
          f"Telethon's exported sender for DC 4 reached vesta by name, given only an IP: {got}")
        c("_config" not in type(client).__dict__, "the shared class-level config cache was restored")
        await bounded(client.disconnect())
    finally:
        await proxy.close()
        await door.close()


async def item6_strict_pool_direct(c, pki):
    print("\nTEST 6: owned operations, LoginFlow, pool sources, a mixed pool, the direct case...")
    door = await FakeDoor(pki).start()
    proxy = await RecordingProxy(door.port).start()
    try:
        url = f"socks5://127.0.0.1:{proxy.port}"
        with restoring():
            ConnectionWebSocket._ssl_context = pki.trust
            engine = ConnectionEngine(ws_ini("owned.ini", url))
            before = len(proxy.destinations)

            async def owned():
                async with engine._account_operation(1):
                    pass
            await bounded(owned())
            got = proxy.hosts()[before:]
            c(got == ["venus.web.telegram.org"], f"an owned account operation (strict options) went by name: {got}")

            flow = LoginFlow(ws_ini("login.ini", url))
            client = flow._make_client()
            before = len(proxy.destinations)
            await bounded(client.connect())
            await bounded(client.disconnect())
            got = proxy.hosts()[before:]
            c(client._connection is ConnectionWebSocket and got == ["venus.web.telegram.org"],
              f"LoginFlow's client carries the transport and went by name: {got}")

            budget = ReadBudget(os.path.join(TMP, "budget.sqlite3"))
            for aid in (101, 102):
                budget.configure(aid, 1000)
            tcp_ini = write_ini("pool_tcp.ini", f"proxy = {url}\n", session="pool_tcp")
            ws_pool_ini = ws_ini("pool_ws.ini", url, session="pool_ws")
            pool = AccountPool([PoolAccount(101, tcp_ini, label="tcp"), PoolAccount(102, ws_pool_ini, label="ws")],
                               [PoolGroup(-1000000000001)], read_budget=budget,
                               state_store=SQLiteAccountPoolStore(os.path.join(TMP, "pool.sqlite3")))
            tcp_client = ws_client = None
            try:
                await pool.initialize()
                for source in pool._sources.values():
                    source.preflight()                       # builds each source's client, never connects
                tcp_client = pool._sources[101]._primary_client
                ws_client = pool._sources[102]._primary_client
                c(tcp_client._connection is not ConnectionWebSocket and ws_client._connection is ConnectionWebSocket,
                  f"one pool, two transports: {tcp_client._connection.__name__} and {ws_client._connection.__name__}")
                c(tcp_client._connection_retries == 0 and ws_client._auto_reconnect is False,
                  "pool sources keep their strict options under either transport")
                before = len(proxy.destinations)
                await bounded(ws_client.connect())
                ws_got = proxy.hosts()[before:]
                before = len(proxy.destinations)
                await bounded(tcp_client.connect(), seconds=4)
                tcp_got = proxy.hosts()[before:]
                c(ws_got == ["venus.web.telegram.org"], f"the websocket source went by name: {ws_got}")
                c(len(tcp_got) == 1 and is_ip(tcp_got[0]), f"the tcp source still dials the DC's IP, as before #67: {tcp_got}")
            finally:
                for cl in (tcp_client, ws_client):
                    if cl is not None:
                        await bounded(cl.disconnect())
                await bounded(pool.close())

        calls = []
        async def spy(host, **kw):
            calls.append((host, kw.get("sock")))
            raise ConnectionError("spy: no network in this test")
        original = wt.open_websocket
        wt.open_websocket = spy
        try:
            direct = ConnectionWebSocket("149.154.167.50", 443, 2, loggers=Loggers(), proxy=None)
            await bounded(direct.connect(timeout=2))
        finally:
            wt.open_websocket = original
        c(calls == [("venus.web.telegram.org", None)], f"no proxy: the opener gets the name and no socket: {calls}")
    finally:
        await proxy.close()
        await door.close()


async def item7_classification(c, pki):
    print("\nTEST 7: classification...")
    stub_pool = pytypes.SimpleNamespace(policy=PoolPolicy())
    door = await FakeDoor(pki).start()
    proxy = await RecordingProxy(door.port).start()
    p = {'proxy_type': 'http', 'addr': '127.0.0.1', 'port': proxy.port, 'rdns': True}
    try:
        with restoring():
            ConnectionWebSocket._ssl_context = pki.trust
            door.default_mode = "status_403"
            before = len(door.upgrades)
            sender = MTProtoSender(None, loggers=Loggers(), retries=2, delay=0, auto_reconnect=False, connect_timeout=5)
            refused = await bounded(sender.connect(ConnectionWebSocket("x", 443, 2, loggers=Loggers(), proxy=p)), 15)
            c(isinstance(refused, ConnectionError) and len(door.upgrades) - before == 3,
              f"a refused upgrade is retried: {len(door.upgrades) - before} attempts, then {type(refused).__name__}")
            outcome = AccountPool._failure(stub_pool, refused, None)
            c(outcome[:2] == ('transport', True), f"…and the pool retries it as {outcome}")
            door.default_mode = "close_after_first"
        before = len(proxy.destinations)
        sender = MTProtoSender(None, loggers=Loggers(), retries=2, delay=0, auto_reconnect=False, connect_timeout=5)
        cert = await bounded(sender.connect(ConnectionWebSocket("x", 443, 1, loggers=Loggers(), proxy=p)), 15)
        c(isinstance(cert, TransportConfigError) and len(proxy.destinations) - before == 1,
          f"an unverifiable certificate stops after 1 attempt as {type(cert).__name__}")
        c(AccountPool._failure(stub_pool, cert, None) == ('unknown', False, None), "…and the pool stops the account ('unknown')")
        try:
            ConnectionEngine(write_ini("bad.ini", "transport = quic\n"))._load_config()
            c(False, "transport = quic accepted")
        except TransportConfigError as e:
            c(True, f"an unknown value stops at config time: {e}")

        engine = ConnectionEngine(write_ini("wrap.ini", ""))

        def stub(error):
            async def connect():
                raise error
            return pytypes.SimpleNamespace(is_connected=lambda: False, connect=connect,
                                           session=pytypes.SimpleNamespace(auth_key=object()))
        logging.getLogger("tgdata.connection_engine").disabled = True
        try:
            for name, call in (("_ensure_connected", engine._ensure_connected), ("_authenticate", engine._authenticate)):
                e = await bounded(call(stub(TransportConfigError("WebSocket transport: test"))))
                c(type(e) is TransportConfigError, f"{name} keeps a TransportConfigError's type")
                e = await bounded(call(stub(OSError("down"))))
                c(type(e) is ConnectionError and "Failed to" in str(e), f"{name} still wraps other errors: {e}")
        finally:
            logging.getLogger("tgdata.connection_engine").disabled = False
        e = TransportConfigError("WebSocket transport: test")
        c(isinstance(e, ProxyConfigError) and _polling_cannot_recover(e), "polling treats it as unrecoverable")
        c(worker_protocol.describe_error(e)['category'] == 'configuration_error',
          "the worker reports it as configuration_error")
    finally:
        await proxy.close()
        await door.close()


async def item8_health_and_quiet_close(c, pki):
    print("\nTEST 8: no health verdicts; a mid-session close is quiet...")
    errors = [TransportConfigError("x"), ConnectionError("WebSocket transport: upgrade refused"),
              asyncio.IncompleteReadError(b"", 1), ValueError("WebSocket transport: refusing an IP")]
    c(all(health.classify(e, include_reported=True) is None for e in errors),
      "health.classify() finds no verdict in any transport error")
    door = await FakeDoor(pki).start()
    proxy = await RecordingProxy(door.port).start()
    records = []
    handler = logging.Handler(logging.DEBUG)
    handler.emit = records.append
    tl = logging.getLogger("telethon")
    old = tl.level
    tl.setLevel(logging.DEBUG)
    tl.addHandler(handler)
    try:
        with restoring():
            ConnectionWebSocket._ssl_context = pki.trust
            door.modes.append("close_now")
            p = {'proxy_type': 'http', 'addr': '127.0.0.1', 'port': proxy.port, 'rdns': True}
            sender = MTProtoSender(AuthKey(os.urandom(256)), loggers=Loggers(), retries=0, delay=0,
                                   auto_reconnect=False, connect_timeout=5)
            await bounded(sender.connect(ConnectionWebSocket("x", 443, 2, loggers=Loggers(), proxy=p)))
            await asyncio.sleep(1)
            await bounded(sender.disconnect())
            collect(sender)
    finally:
        tl.removeHandler(handler)
        tl.setLevel(old)
        await proxy.close()
        await door.close()
    texts = [r.getMessage() for r in records]
    c(any("Server closed the connection" in t for t in texts if t) and
      not any("Unexpected exception" in t for t in texts),
      "the door's close: Telethon logs 'Server closed the connection', no unexpected-exception traceback")


async def item9_default_path(c):
    print("\nTEST 9: the default path is byte-identical to before #67...")
    now = capture_default_path()
    for name in ("proxy", "direct"):
        c(now[name]['clients'] == BASELINE[name]['clients'],
          f"{name}: TelegramClient arguments unchanged for the ordinary, owned and login clients")
        c(now[name]['route_lines'] == BASELINE[name]['route_lines'], f"{name}: route log lines unchanged")
        c(now[name]['binding'] == BASELINE[name]['binding'], f"{name}: login binding hash unchanged")
    code = ("import sys; from tgdata.connection_engine import ConnectionEngine as E; "
            f"E({write_ini('tcp_only.ini', '')!r})._new_client(); "
            "print('tgdata.websocket_transport' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    c(out.stdout.strip() == "False", f"a TCP account never imports the transport module ({out.stdout.strip() or out.stderr[-200:]})")


async def item10_binding_and_observability(c):
    print("\nTEST 10: the login binding and observability...")
    ws = ws_ini("bind_ws.ini", "socks5://u:p@127.0.0.1:1080", IDENTITY_LINES)
    flow = LoginFlow(ws)
    c(flow._binding != BASELINE['proxy']['binding'], "a websocket account's binding differs from the same TCP account's")
    try:
        LoginFlow(write_ini("bind_tcp.ini", PROXY_LINE + IDENTITY_LINES), state=flow.export_state())
        c(False, "a websocket checkpoint restored under tcp")
    except LoginError as e:
        c(str(e).endswith("invalid_state"), f"restoring it under tcp is refused: {e}")
    lines = []
    handler = logging.Handler(logging.INFO)
    handler.emit = lambda r: lines.append(r.getMessage())
    log = logging.getLogger("tgdata.connection_engine")
    old = log.level
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    try:
        ws_engine = ConnectionEngine(ws)
        ws_engine._new_client()
    finally:
        log.removeHandler(handler)
        log.setLevel(old)
    c(any("over Telegram's WebSocket transport by hostname" in l for l in lines), f"the route line names it: {lines[0]}")
    tcp_engine = ConnectionEngine(write_ini("obs_tcp.ini", ""))
    tcp_engine._load_config()
    statuses = (await ws_engine.health_check())['transport'], (await tcp_engine.health_check())['transport']
    c(statuses == ('websocket', 'tcp'), f"health_check() reports the transport: {statuses}")


async def item11_canary(c):
    print("\nTEST 11: CANARY — run after any Telethon upgrade: the internals the transport relies on...")
    params = inspect.signature(Connection.__init__).parameters
    c(list(params) == ['self', 'ip', 'port', 'dc_id', 'loggers', 'proxy', 'local_addr'],
      f"Connection.__init__(ip, port, dc_id, *, loggers, proxy, local_addr): {list(params)}")
    c(Connection("name.example", 1, 2, loggers=Loggers())._ip == "name.example", "…and stores its first argument as _ip")

    seen = {}
    class Recorder(ConnectionTcpObfuscated):
        async def _connect(self, timeout=None, ssl=None):
            seen.update(timeout=timeout, ssl=ssl)
            raise OSError("recorder")
    await bounded(Recorder("h", 1, 2, loggers=Loggers()).connect(timeout=3))
    c(seen == {'timeout': 3, 'ssl': None}, f"Connection.connect() calls _connect(timeout=…, ssl=…): {seen}")

    target = socket.socket()
    target.bind(("127.0.0.1", 0))
    target.listen()
    proxy = await RecordingProxy(target.getsockname()[1]).start()
    try:
        conn = ConnectionTcpObfuscated("name.example", 443, 2, loggers=Loggers(),
                                       proxy={'proxy_type': 'http', 'addr': '127.0.0.1', 'port': proxy.port, 'rdns': True})
        sock = await asyncio.wait_for(conn._proxy_connect(timeout=3), 5)
        sock.close()
        c(proxy.destinations == [("http", "name.example", 443)], f"_proxy_connect dials self._ip by name: {proxy.destinations}")
    finally:
        await proxy.close()
        target.close()
    closed = socket.socket()
    closed.bind(("127.0.0.1", 0))
    port = closed.getsockname()[1]
    closed.close()
    conn = ConnectionTcpObfuscated("name.example", 443, 2, loggers=Loggers(),
                                   proxy={'proxy_type': 'http', 'addr': '127.0.0.1', 'port': port, 'rdns': True})
    e = await bounded(conn._proxy_connect(timeout=3))
    c(isinstance(e, ConnectionError), f"…and a dead proxy raises a ConnectionError (retryable): {type(e).__name__}")

    class FakeWriter:
        def __init__(self):
            self.data = b""
        def write(self, b):
            self.data += b
    conn = ConnectionTcpObfuscated("h", 1, 2, loggers=Loggers())
    conn._reader, conn._writer = object(), FakeWriter()
    conn._codec = conn.packet_codec(conn)
    conn._init_conn()
    c(conn._obfuscation._writer is conn._writer and len(conn._writer.data) == 64,
      "ObfuscatedConnection._init_conn() captures _reader/_writer and writes the 64-byte header")

    for raised, expected in ((OSError, 3), (ValueError, 1)):
        calls = []
        class Failing(ConnectionTcpObfuscated):
            async def _connect(self, timeout=None, ssl=None, raised=raised):
                calls.append(1)
                raise raised("canary")
        sender = MTProtoSender(None, loggers=Loggers(), retries=2, delay=0, auto_reconnect=False)
        await bounded(sender.connect(Failing("h", 1, 2, loggers=Loggers())))
        c(len(calls) == expected, f"_try_connect: {raised.__name__} -> {len(calls)} attempt(s) (expected {expected})")

    base = inspect.getsource(telethon_base)
    c(base.count("self._connection(") == 4, "telegrambaseclient builds connections in exactly four places")
    client_dir = os.path.dirname(telethon_base.__file__)
    cdn = [f for f in os.listdir(client_dir) if f.endswith(".py")
           and "cdn_supported" in open(os.path.join(client_dir, f)).read()]
    c(cdn == [], f"no client code requests CDN downloads (cdn_supported): {cdn}")

    tree = ast.parse(open(ws_stream.__file__).read())
    modules = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | \
              {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    c(all(m in sys.stdlib_module_names for m in modules), f"ws_stream imports only the standard library: {sorted(modules)}")


async def main():
    print("TgData WebSocket transport smoke test (issue #67) — offline\n")
    logging.getLogger("telethon").setLevel(logging.CRITICAL)
    c = Checks()
    pki = make_pki()
    tls_items = (item1_handshake, item2_framing, item3_class, item4_main_and_reconnect,
                 item5_exported_sender, item6_strict_pool_direct, item7_classification,
                 item8_health_and_quiet_close)
    skipped = 0
    for item in tls_items:
        if pki is None:
            skipped += 1
            print(f"\n– {item.__name__}: SKIPPED (openssl not found)")
            continue
        try:
            await item(c, pki)
        except Exception as e:  # noqa: BLE001 — report and continue
            c(False, f"{item.__name__} raised {type(e).__name__}: {e}")
    for item in (item9_default_path, item10_binding_and_observability, item11_canary):
        try:
            await item(c)
        except Exception as e:  # noqa: BLE001
            c(False, f"{item.__name__} raised {type(e).__name__}: {e}")
    print(f"\n{c.passed}/{c.passed + c.failed} checks passed" + (f"; {skipped} items SKIPPED" if skipped else ""))
    return c.failed == 0


if __name__ == "__main__":
    try:
        if "--print-baseline" in sys.argv:
            print(json.dumps(capture_default_path(), indent=1, sort_keys=True))
        else:
            ok = asyncio.run(main())
            sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
