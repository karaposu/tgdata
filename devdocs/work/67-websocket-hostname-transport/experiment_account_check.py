#!/usr/bin/env python3
"""
Experiment for tgdata #67 (critic.md, REORDER): does Telegram serve THIS
account's existing session over its WebSocket door, by hostname, through the
account's proxy — before any of the feature is built?

It runs a real Telethon 1.45.0 client on a COPY of the account's session file,
with the account's api_id / api_hash / pinned device identity and proxy, using
a connection class that does exactly what the plan's step 3 specifies:
  - the data centre's IP is replaced at construction by
    <planet>.web.telegram.org:443 — the object never holds an IP;
  - the socket comes from Telethon's own proxy code, by name;
  - TLS with SNI and a verified certificate;
  - GET /apiws with Sec-WebSocket-Protocol: binary, and no Origin header;
  - Telethon's own obfuscated transport, carried in binary frames.

Steps:
  1. connect, then updates.GetState;
  2. get_me;
  3. read 5 messages;
  4. download one media file stored on another data centre;
  5. stay idle for --idle seconds (default 330);
  6. read again.
It prints every "Connecting to ..." line Telethon logs — each must be a
hostname — and any Telegram error, by name.

SAFETY — read before running:
  * Nothing else may use this account's session while this runs. Telegram
    revokes a session key used from two addresses at once (AUTH_KEY_DUPLICATED),
    which logs the account out. Stop the account's normal application first,
    then pass --exclusive-confirmed.
  * The session file is copied; the original is never opened for writing.
  * It never logs in and never asks for a login code. A session that is not
    logged in stops the run.
  * Downloads go to memory only; nothing is written to disk except the copy,
    which is deleted at the end.

Usage:
    python experiment_account_check.py --config /path/to/account.ini --exclusive-confirmed
    python experiment_account_check.py --config account.ini --chat some_public_channel --exclusive-confirmed
The config is a tgdata [Telegram] section: api_id, api_hash, session_file, proxy,
and optional device_model / system_version / app_version / lang_code /
system_lang_code.

Needs: telethon==1.45.0 and python-socks[asyncio] — for every proxy kind, http:// included
(Telethon's own proxy code uses it).
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import configparser
import hashlib
import ipaddress
import logging
import os
import re
import shutil
import ssl
import sys
import tempfile
import time
from typing import List, Optional
from urllib.parse import unquote, urlsplit

import telethon
from telethon import TelegramClient, functions
from telethon.errors import AuthKeyDuplicatedError, RPCError
from telethon.network.connection.tcpobfuscated import ConnectionTcpObfuscated

DC_HOSTS = {1: "pluto", 2: "venus", 3: "aurora", 4: "vesta", 5: "flora"}
DOMAIN, PORT, PATH = "web.telegram.org", 443, "/apiws"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
IDENTITY_KEYS = ("device_model", "system_version", "app_version", "lang_code", "system_lang_code")
MAX_FRAME = 16 * 1024 * 1024


# ------------------------------------------------------------ WebSocket stream --

def _xor(data: bytes, mask: bytes) -> bytes:
    if not data:
        return b""
    rep = (mask * (len(data) // 4 + 1))[:len(data)]
    return (int.from_bytes(data, "big") ^ int.from_bytes(rep, "big")).to_bytes(len(data), "big")


def client_frame(opcode: int, payload: bytes) -> bytes:
    head = bytearray([0x80 | opcode])
    n = len(payload)
    if n < 126:
        head.append(0x80 | n)
    elif n < 65536:
        head.append(0x80 | 126)
        head += n.to_bytes(2, "big")
    else:
        head.append(0x80 | 127)
        head += n.to_bytes(8, "big")
    mask = os.urandom(4)
    return bytes(head) + mask + _xor(payload, mask)


class WsWriter:
    def __init__(self, writer: asyncio.StreamWriter):
        self._w = writer

    def write(self, data) -> None:
        self._w.write(client_frame(0x2, bytes(data)))

    async def drain(self) -> None:
        await self._w.drain()

    def close(self) -> None:
        try:
            self._w.write(client_frame(0x8, (1000).to_bytes(2, "big")))
        except Exception:
            pass
        self._w.close()

    async def wait_closed(self) -> None:
        await self._w.wait_closed()


class WsReader:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._r, self._w = reader, writer
        self._buf = bytearray()
        self._closed = False

    async def readexactly(self, n: int) -> bytes:
        while len(self._buf) < n:
            if self._closed:
                raise asyncio.IncompleteReadError(bytes(self._buf), n)
            await self._next_frame()
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    async def _next_frame(self) -> None:
        try:
            b1, b2 = await self._r.readexactly(2)
        except asyncio.IncompleteReadError:
            self._closed = True
            return
        opcode, masked, n = b1 & 0x0F, b2 & 0x80, b2 & 0x7F
        if b1 & 0x70:
            raise ConnectionError("WebSocket transport: reserved bits set by the server")
        if masked:
            raise ConnectionError("WebSocket transport: the server sent a masked frame")
        if n == 126:
            n = int.from_bytes(await self._r.readexactly(2), "big")
        elif n == 127:
            n = int.from_bytes(await self._r.readexactly(8), "big")
        if opcode >= 0x8 and (n > 125 or not b1 & 0x80):
            raise ConnectionError("WebSocket transport: malformed control frame")
        if n > MAX_FRAME:
            raise ConnectionError(f"WebSocket transport: frame of {n} bytes refused")
        payload = await self._r.readexactly(n) if n else b""
        if opcode in (0x0, 0x2):
            self._buf += payload
        elif opcode == 0x9:
            self._w.write(client_frame(0xA, payload))
        elif opcode == 0xA:
            pass
        elif opcode == 0x8:
            try:
                self._w.write(client_frame(0x8, payload[:2]))
            except Exception:
                pass
            self._closed = True
        else:
            raise ConnectionError(f"WebSocket transport: unexpected opcode {opcode:#x}")


async def open_websocket(host: str, *, sock=None, port: int = PORT, timeout: Optional[float] = None,
                         ssl_context: Optional[ssl.SSLContext] = None):
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        raise ValueError(f"WebSocket transport: refusing an IP address as the host ({host})")
    ctx = ssl_context or ssl.create_default_context()

    async def _open():
        if sock is not None:
            reader, writer = await asyncio.open_connection(sock=sock, ssl=ctx, server_hostname=host)
        else:
            reader, writer = await asyncio.open_connection(host, port, ssl=ctx, server_hostname=host)
        try:
            key = base64.b64encode(os.urandom(16)).decode()
            writer.write((f"GET {PATH} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
                          f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                          f"Sec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: binary\r\n\r\n").encode())
            await writer.drain()
            head = (await reader.readuntil(b"\r\n\r\n"))[:16384].decode("latin-1")
            lines = head.split("\r\n")
            headers = {k.strip().lower(): v.strip() for k, v in (l.split(":", 1) for l in lines[1:] if ":" in l)}
            expected = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
            if " 101" not in lines[0] or headers.get("sec-websocket-accept") != expected:
                raise ConnectionError(f"WebSocket transport: upgrade to {host} refused ({lines[0]})")
            if headers.get("sec-websocket-protocol", "binary").lower() != "binary":
                raise ConnectionError(f"WebSocket transport: {host} chose another subprotocol")
            return WsReader(reader, writer), WsWriter(writer)
        except BaseException:
            writer.close()
            raise

    return await asyncio.wait_for(_open(), timeout)


class CertificateRefused(ValueError):
    """Stands in for the planned TransportConfigError: never retried by Telethon."""


class ConnectionWebSocket(ConnectionTcpObfuscated):
    _ssl_context = None   # self-test seam only; None = the system trust store

    def __init__(self, ip, port, dc_id, **kwargs):
        if dc_id not in DC_HOSTS:
            raise ValueError(f"WebSocket transport: no hostname for DC {dc_id}")
        super().__init__(f"{DC_HOSTS[dc_id]}.{DOMAIN}", PORT, dc_id, **kwargs)

    async def _connect(self, timeout=None, ssl=None):
        sock = await self._proxy_connect(timeout=timeout) if self._proxy else None
        try:
            self._reader, self._writer = await open_websocket(
                self._ip, sock=sock, port=self._port, timeout=timeout, ssl_context=self._ssl_context)
        except __import__("ssl").SSLCertVerificationError as e:
            if sock is not None:
                sock.close()
            raise CertificateRefused(f"WebSocket transport: the certificate of {self._ip} did not verify "
                                     f"({e.verify_message})") from e
        except BaseException:
            if sock is not None:
                sock.close()
            raise
        try:
            self._codec = self.packet_codec(self)
            self._init_conn()
            await self._writer.drain()
        except BaseException:
            self._writer.close()
            raise


# -------------------------------------------------------------- the account --

_SCHEMES = {"socks5": "socks5", "socks5h": "socks5", "socks4": "socks4", "socks4a": "socks4", "http": "http"}


def read_config(path: str):
    cp = configparser.ConfigParser(interpolation=None)
    if not cp.read(path):
        raise SystemExit(f"cannot read {path}")
    section = next((s for s in cp.sections() if s.lower() == "telegram"), None)
    if section is None:
        raise SystemExit(f"no [Telegram] section in {path}")
    sec = cp[section]

    def value(key):
        raw = sec.get(key)
        if raw is None:
            return None
        raw = re.split(r"\s[;#]", raw, maxsplit=1)[0].strip().strip("'\"").strip()
        return raw or None

    api_id, api_hash, session = value("api_id"), value("api_hash"), value("session_file") or value("username")
    if not (api_id and api_hash and session):
        raise SystemExit("the config needs api_id, api_hash and session_file")
    proxy_url = (sec.get("proxy") or "").split()
    proxy_url = proxy_url[0].strip("'\"") if proxy_url else ""
    if proxy_url.lower() in ("", "none", "false", "0", "off", "no"):
        raise SystemExit("this experiment runs through the account's proxy; the config has none")
    parts = urlsplit(proxy_url)
    if parts.scheme.lower() not in _SCHEMES or not parts.hostname or parts.port is None:
        raise SystemExit("proxy must be socks5://, socks4:// or http://host:port")
    proxy = {"proxy_type": _SCHEMES[parts.scheme.lower()], "addr": parts.hostname, "port": parts.port, "rdns": True}
    if parts.username:
        proxy["username"] = unquote(parts.username)
    if parts.password is not None:
        proxy["password"] = unquote(parts.password)
    shown = f"{parts.scheme}://{(parts.username + ':***@') if parts.username else ''}{parts.hostname}:{parts.port}"
    identity = {k: value(k) for k in IDENTITY_KEYS if value(k)}
    if identity.get("lang_code") and not identity.get("system_lang_code"):
        identity["system_lang_code"] = identity["lang_code"]
    session_path = os.path.expanduser(session)
    if not session_path.endswith(".session"):
        session_path += ".session"
    return int(api_id), api_hash, session_path, proxy, shown, identity


class ConnectLines(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.lines: List[str] = []

    def emit(self, record):
        message = record.getMessage()
        if message.startswith("Connecting to"):
            self.lines.append(message)


def _error(e: BaseException) -> str:
    if isinstance(e, RPCError):
        return f"{type(e).__name__} (Telegram {getattr(e, 'code', '?')}: {getattr(e, 'message', '')})"
    return f"{type(e).__name__}: {e}"


async def find_other_dc_media(client, entity, home_dc: int, limit: int):
    async for msg in client.iter_messages(entity, limit=limit):
        media = getattr(msg, "document", None) or getattr(msg, "photo", None)
        dc = getattr(media, "dc_id", None)
        if media is not None and dc and dc != home_dc and dc in DC_HOSTS:
            return msg, dc
    return None, None


async def run(args) -> int:
    api_id, api_hash, session_path, proxy, shown, identity = read_config(args.config)
    if not os.path.exists(session_path):
        raise SystemExit(f"session file not found: {session_path}")
    print(f"Telethon {telethon.__version__}; proxy {shown}; identity pinned: {sorted(identity) or 'none'}")
    print(f"Session: a copy of {os.path.basename(session_path)} (the original is not modified)")
    workdir = tempfile.mkdtemp(prefix="tgdata67_")
    copy = os.path.join(workdir, "check.session")
    shutil.copy2(session_path, copy)

    catcher = ConnectLines()
    tl = logging.getLogger("telethon")
    tl.setLevel(logging.INFO)
    tl.addHandler(catcher)
    results, verdict_notes = [], []
    client = TelegramClient(copy, api_id, api_hash, proxy=proxy, connection=ConnectionWebSocket,
                            receive_updates=False, connection_retries=1, retry_delay=1,
                            request_retries=1, flood_sleep_threshold=0, **identity)

    def record(step, ok, detail):
        results.append((step, ok, detail))
        print(f"{'✓' if ok else ('–' if ok is None else '✗')} {step}: {detail}")

    duplicated = disqualified = False
    try:
        try:
            await asyncio.wait_for(client.connect(), args.timeout * 4)
            state = await asyncio.wait_for(client(functions.updates.GetStateRequest()), args.timeout)
            record("1 connect + GetState", True, f"pts={state.pts} on DC {client.session.dc_id}")
        except AuthKeyDuplicatedError as e:
            duplicated = True
            record("1 connect + GetState", False, _error(e))
            raise
        except RPCError as e:
            disqualified = True
            record("1 connect + GetState", False, _error(e))
            raise
        except asyncio.TimeoutError:
            disqualified = True
            record("1 connect + GetState", False, "no answer from Telegram over the door")
            raise

        me = await asyncio.wait_for(client.get_me(), args.timeout)
        if me is None:
            disqualified = True
            record("2 get_me", False, "Telegram returned no account")
            return 1
        record("2 get_me", True, f"account id ends …{str(me.id)[-3:]}")

        if args.chat:
            entity = await client.get_entity(args.chat)
        else:
            entity = None
            async for d in client.iter_dialogs(limit=30):
                if d.is_channel or d.is_group:
                    entity = d.entity
                    break
            if entity is None:
                raise SystemExit("no channel or group among the first 30 dialogs; pass --chat")
        msgs = await asyncio.wait_for(client.get_messages(entity, limit=5), args.timeout * 2)
        record("3 read", True, f"{len(msgs)} messages")

        home = client.session.dc_id
        msg, dc = await find_other_dc_media(client, entity, home, args.search)
        if msg is None and not args.chat:
            async for d in client.iter_dialogs(limit=15):
                if d.is_channel:
                    msg, dc = await find_other_dc_media(client, d.entity, home, args.search)
                    if msg is not None:
                        break
        if msg is None:
            record("4 other-DC download", None,
                   f"SKIPPED — no media stored outside DC {home} found; rerun with --chat <a large public channel>")
        else:
            data = await asyncio.wait_for(client.download_media(msg, file=bytes), args.timeout * 12)
            record("4 other-DC download", True, f"{len(data or b'')} bytes from DC {dc} (home DC {home})")

        print(f"… idle for {args.idle:.0f} s")
        start = time.monotonic()
        while time.monotonic() - start < args.idle:
            await asyncio.sleep(min(60, args.idle - (time.monotonic() - start)))
            print(f"   {time.monotonic() - start:.0f} s")
        msgs = await asyncio.wait_for(client.get_messages(entity, limit=1), args.timeout * 2)
        record("6 read after idle", True, f"{len(msgs)} message")
    except AuthKeyDuplicatedError as e:
        duplicated = True
        if not results or results[-1][1] is not False:
            record("error", False, _error(e))
    except (RPCError, asyncio.TimeoutError, ConnectionError, ValueError) as e:
        if not results or results[-1][1] is not False:
            record("error", False, _error(e))
        if isinstance(e, RPCError) and getattr(e, "code", None) in (401, 403, 406, 420):
            disqualified = True          # an account / authorization refusal, at any step
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
        tl.removeHandler(catcher)
        shutil.rmtree(workdir, ignore_errors=True)

    print("\nConnections Telethon opened:")
    ip_seen = False
    for line in catcher.lines:
        host = line[len("Connecting to "):].split(":")[0]
        try:
            ipaddress.ip_address(host.strip("[]"))
            ip_seen = True
            print(f"   ✗ {line}")
        except ValueError:
            print(f"   ✓ {line}")
    if not catcher.lines:
        print("   (none logged)")

    print("\nResult")
    if duplicated:
        print("   INVALID RUN — another client was using this session (AUTH_KEY_DUPLICATED).")
        print("   The session key may now be revoked; log the account in again before retrying.")
        return 3
    failed = [r for r in results if r[1] is False]
    if ip_seen:
        print("   FAIL — a connection named an IP address.")
        return 1
    if disqualified:
        print("   DISQUALIFYING — Telegram refused the account or its session over the door.")
        print("   Control: restart the account's normal application now — if it works there,")
        print("   the refusal is specific to the WebSocket door.")
        return 1
    if failed:
        print("   INCONCLUSIVE — a step failed for a reason that is not an account refusal:")
        for step, _, detail in failed:
            print(f"     {step}: {detail}")
        print("   Send the full output back; it will be judged against critic.md's results.")
        return 4
    skipped = [r for r in results if r[1] is None]
    print("   PASS" + (" (the other-DC download was not exercised)" if skipped else ""))
    print("   Now restart the account's normal application and confirm it works — that is the control.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="the account's tgdata config (.ini)")
    ap.add_argument("--chat", help="a channel or group to read and search for other-DC media")
    ap.add_argument("--search", type=int, default=300, help="messages to search for other-DC media")
    ap.add_argument("--idle", type=float, default=330)
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--exclusive-confirmed", action="store_true",
                    help="confirm nothing else is using this account's session right now")
    args = ap.parse_args()
    if not args.exclusive_confirmed:
        print("Refusing to run: stop every application using this account's session, then pass "
              "--exclusive-confirmed. (Two simultaneous users of one session get it revoked.)")
        return 2
    logging.basicConfig(level=logging.WARNING, format="   log %(name)s %(levelname)s: %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
