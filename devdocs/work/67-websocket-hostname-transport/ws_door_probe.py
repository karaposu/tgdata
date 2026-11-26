#!/usr/bin/env python3
"""
Probe: can Telethon reach Telegram through its WebSocket door
(wss://<name>.web.telegram.org/apiws) via a proxy, by hostname only?

No account, no login, no session file, no api_id. For each target it:
  1. opens a tunnel to <name>:443 through the proxy BY NAME
     (HTTP CONNECT <name>:443, or SOCKS5 with remote DNS) and records the
     proxy's exit-IP header (Bright Data: x-brd-ip) when it sends one;
  2. does TLS with SNI = <name>, certificate verified;
  3. does the WebSocket handshake: GET /apiws, Sec-WebSocket-Protocol: binary;
  4. runs Telethon 1.45.0's own obfuscated2 transport and MTProto handshake
     over it, on an empty in-memory key: creating an auth key proves the
     whole path works both ways. Nothing is logged in; the key is thrown away;
  5. sends one MTProto ping, and optionally another after --hold seconds idle
     (does the proxy cut quiet tunnels?).

If step 4 fails after step 3 succeeded, it retries once with the DC number
written into the obfuscated header (bytes 60-61), which some relays route by.

It never connects to an IP address and never resolves a Telegram name
locally: targets that look like IPs are refused, and without a proxy it
refuses to run unless --direct is given.

Usage (the proxy URL from the environment keeps it out of shell history):
    export TG_WS_PROXY='http://USER:PASS@brd.superproxy.io:33335'
    python ws_door_probe.py                    # DC1-5, kws* and planet names, with -1 variants
    python ws_door_probe.py --dc 4 --hold 600  # one DC, then 10 idle minutes
    python ws_door_probe.py --codec intermediate

Needs: telethon 1.45.0; python-socks only for a socks5:// proxy.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import ipaddress
import logging
import os
import socket
import ssl
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import unquote, urlsplit

from telethon.crypto import AESModeCTR
from telethon.network import MTProtoSender
from telethon.network.connection.tcpabridged import AbridgedPacketCodec
from telethon.network.connection.tcpintermediate import IntermediatePacketCodec
from telethon.network.connection.tcpobfuscated import ConnectionTcpObfuscated, ObfuscatedIO
from telethon.tl.functions import PingRequest

DOMAIN = "web.telegram.org"
PLANETS = {1: "pluto", 2: "venus", 3: "aurora", 4: "vesta", 5: "flora"}   # GramJS's names; DC mapping unverified
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


# ── the proxy ────────────────────────────────────────────────────────────────

@dataclass
class ProxySpec:
    scheme: str                 # 'http' or 'socks5'
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    url: str

    @property
    def shown(self) -> str:
        auth = f"{self.username}:***@" if self.password is not None else (f"{self.username}@" if self.username else "")
        return f"{self.scheme}://{auth}{self.host}:{self.port}"


def parse_proxy(url: str) -> ProxySpec:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    if scheme in ("socks5h",):
        scheme = "socks5"
    if scheme not in ("http", "socks5"):
        raise SystemExit(f"proxy scheme {parts.scheme!r} not supported here — use http:// or socks5://")
    if not parts.hostname or not parts.port:
        raise SystemExit("proxy must name a host and a port")
    return ProxySpec(scheme, parts.hostname, parts.port,
                     unquote(parts.username) if parts.username else None,
                     unquote(parts.password) if parts.password is not None else None, url.strip())


# ── one target's results ─────────────────────────────────────────────────────

@dataclass
class Report:
    host: str
    dc: int
    header_dc: Optional[int] = None
    steps: Dict[str, str] = field(default_factory=dict)
    exit_ip: Optional[str] = None
    auth_key: bool = False
    pong: bool = False
    pong_after_hold: Optional[bool] = None
    ws_close: Optional[str] = None
    error: Optional[str] = None
    seconds: float = 0.0


# ── WebSocket framing over an asyncio stream ─────────────────────────────────

def _xor(data: bytes, mask: bytes) -> bytes:
    if not data:
        return b""
    rep = (mask * (len(data) // 4 + 1))[:len(data)]
    return (int.from_bytes(data, "big") ^ int.from_bytes(rep, "big")).to_bytes(len(data), "big")


def client_frame(opcode: int, payload: bytes) -> bytes:
    """One FIN frame from a client: clients must mask."""
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


class WsReader:
    """readexactly() over binary frames: the frames carry one byte stream."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, report: Report):
        self._r, self._w, self._report = reader, writer, report
        self._buf = bytearray()

    async def readexactly(self, n: int) -> bytes:
        while len(self._buf) < n:
            if not await self._next_frame():
                partial = bytes(self._buf)
                self._buf.clear()
                raise asyncio.IncompleteReadError(partial, n)
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    async def _next_frame(self) -> bool:
        try:
            b1, b2 = await self._r.readexactly(2)
            opcode, n = b1 & 0x0F, b2 & 0x7F
            if n == 126:
                n = int.from_bytes(await self._r.readexactly(2), "big")
            elif n == 127:
                n = int.from_bytes(await self._r.readexactly(8), "big")
            mask = await self._r.readexactly(4) if b2 & 0x80 else None
            payload = await self._r.readexactly(n) if n else b""
        except (asyncio.IncompleteReadError, ConnectionError):
            self._report.ws_close = self._report.ws_close or "stream ended"
            return False
        if mask:
            payload = _xor(payload, mask)
        if opcode in (0x0, 0x2):                    # continuation, binary
            self._buf += payload
            return True
        if opcode == 0x9:                           # ping -> pong
            self._w.write(client_frame(0xA, payload))
            return True
        if opcode == 0xA:                           # pong
            return True
        if opcode == 0x8:                           # close
            code = int.from_bytes(payload[:2], "big") if len(payload) >= 2 else None
            reason = payload[2:].decode("utf-8", "replace")
            self._report.ws_close = f"server closed the WebSocket (code {code}{', ' + reason if reason else ''})"
            return False
        self._report.ws_close = f"unexpected frame opcode {opcode}"
        return False


class WsWriter:
    """write() sends one binary frame; the rest is the stream writer's."""

    def __init__(self, writer: asyncio.StreamWriter):
        self._w = writer

    def write(self, data) -> None:
        if data:
            self._w.write(client_frame(0x2, bytes(data)))

    async def drain(self) -> None:
        await self._w.drain()

    def close(self) -> None:
        try:
            self._w.write(client_frame(0x8, (1000).to_bytes(2, "big")))
        except Exception:  # noqa: BLE001
            pass
        self._w.close()

    async def wait_closed(self) -> None:
        await self._w.wait_closed()


# ── tunnel, TLS, handshake ───────────────────────────────────────────────────

async def _recv_headers(loop, sock: socket.socket, limit: int = 65536) -> bytes:
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = await loop.sock_recv(sock, 4096)
        if not chunk:
            raise ConnectionError("proxy closed the connection during CONNECT")
        data += chunk
        if len(data) > limit:
            raise ConnectionError("proxy sent oversized CONNECT response")
    return data


async def open_tunnel(proxy: Optional[ProxySpec], host: str, port: int, report: Report) -> socket.socket:
    """A socket whose far end is <host>:<port>, reached BY NAME."""
    loop = asyncio.get_running_loop()
    if proxy is None:                                       # --direct: the OS resolves the name
        family, kind, proto, _, addr = (await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM))[0]
        sock = socket.socket(family, kind, proto)
        sock.setblocking(False)
        await loop.sock_connect(sock, addr)
        report.steps["tunnel"] = "direct (no proxy)"
        return sock
    if proxy.scheme == "socks5":
        try:
            from python_socks.async_.asyncio import Proxy
        except ImportError:
            raise SystemExit("socks5:// needs python-socks: pip install 'python-socks[asyncio]'")
        sock = await Proxy.from_url(proxy.url, rdns=True).connect(dest_host=host, dest_port=port)
        report.steps["tunnel"] = "SOCKS5 by name (remote DNS)"
        return sock
    # HTTP CONNECT, by hand, to see the proxy's response headers
    family, kind, proto, _, addr = (await loop.getaddrinfo(proxy.host, proxy.port, type=socket.SOCK_STREAM))[0]
    sock = socket.socket(family, kind, proto)
    sock.setblocking(False)
    try:
        await loop.sock_connect(sock, addr)
        request = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n"
        if proxy.username is not None:
            token = base64.b64encode(f"{proxy.username}:{proxy.password or ''}".encode()).decode()
            request += f"Proxy-Authorization: Basic {token}\r\n"
        await loop.sock_sendall(sock, (request + "\r\n").encode())
        head = (await _recv_headers(loop, sock)).decode("latin-1")
        lines = head.split("\r\n")
        status = lines[0]
        headers = {k.strip().lower(): v.strip() for k, v in (l.split(":", 1) for l in lines[1:] if ":" in l)}
        report.exit_ip = headers.get("x-brd-ip") or headers.get("x-luminati-ip")
        brd = {k: v for k, v in headers.items() if k.startswith(("x-brd", "x-luminati"))}
        report.steps["tunnel"] = f"{status}" + (f" {brd}" if brd else "")
        if " 200" not in status:
            raise ConnectionError(f"proxy refused CONNECT: {status}")
        return sock
    except BaseException:
        sock.close()
        raise


async def open_websocket(sock: socket.socket, host: str, report: Report, origin: bool):
    ctx = ssl.create_default_context()                      # verifies the certificate and the name
    reader, writer = await asyncio.open_connection(sock=sock, ssl=ctx, server_hostname=host,
                                                   ssl_handshake_timeout=15)
    cert = writer.get_extra_info("peercert") or {}
    subject = dict(x[0] for x in cert.get("subject", ()))
    tls = writer.get_extra_info("ssl_object")
    report.steps["tls"] = f"ok — {tls.version() if tls else '?'}, certificate CN={subject.get('commonName', '?')}"

    key = base64.b64encode(os.urandom(16)).decode()
    lines = [f"GET /apiws HTTP/1.1", f"Host: {host}", "Upgrade: websocket", "Connection: Upgrade",
             f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13", "Sec-WebSocket-Protocol: binary"]
    if origin:
        lines.append("Origin: https://web.telegram.org")
    writer.write(("\r\n".join(lines) + "\r\n\r\n").encode())
    await writer.drain()
    head = (await reader.readuntil(b"\r\n\r\n")).decode("latin-1")
    status = head.split("\r\n", 1)[0]
    headers = {k.strip().lower(): v.strip()
               for k, v in (l.split(":", 1) for l in head.split("\r\n")[1:] if ":" in l)}
    expected = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
    ok = " 101" in status and headers.get("sec-websocket-accept") == expected
    report.steps["websocket"] = (f"{status}; protocol={headers.get('sec-websocket-protocol', '-')}"
                                 + ("" if ok else " — handshake NOT accepted"))
    if not ok:
        writer.close()
        raise ConnectionError(f"WebSocket handshake refused: {status}")
    return reader, writer


# ── Telethon's obfuscated transport, carried over the WebSocket ──────────────

def init_header(packet_codec, header_dc: Optional[int]):
    """Telethon's ObfuscatedIO.init_header, plus an optional DC number in
    bytes 60-61 (Telethon leaves them random)."""
    keywords = (b"PVrG", b"GET ", b"POST", b"\xee\xee\xee\xee")
    while True:
        random = os.urandom(64)
        if random[0] != 0xEF and random[:4] not in keywords and random[4:8] != b"\0\0\0\0":
            break
    random = bytearray(random)
    random_reversed = random[55:7:-1]
    encryptor = AESModeCTR(bytes(random[8:40]), bytes(random[40:56]))
    decryptor = AESModeCTR(bytes(random_reversed[:32]), bytes(random_reversed[32:48]))
    random[56:60] = packet_codec.obfuscate_tag
    if header_dc is not None:
        random[60:62] = header_dc.to_bytes(2, "little", signed=True)
    random[56:64] = encryptor.encrypt(bytes(random))[56:64]
    return random, encryptor, decryptor


class ProbeObfuscatedIO(ObfuscatedIO):
    def __init__(self, connection):
        self._reader = connection._reader
        self._writer = connection._writer
        self.header, self._encrypt, self._decrypt = init_header(connection.packet_codec, connection.header_dc)


class WsConnection(ConnectionTcpObfuscated):
    """Telethon's ConnectionTcpObfuscated, but its byte stream runs inside a
    WebSocket to <host>, reached by name. The IP argument is never used."""
    obfuscated_io = ProbeObfuscatedIO
    probe_proxy: Optional[ProxySpec] = None
    report: Report = None
    origin = True
    header_dc: Optional[int] = None

    async def _connect(self, timeout=None, ssl=None):
        host, report = self._ip, self.report             # _ip holds the hostname here
        sock = await asyncio.wait_for(open_tunnel(self.probe_proxy, host, 443, report), timeout)
        reader, writer = await asyncio.wait_for(open_websocket(sock, host, report, self.origin), timeout)
        self._reader = WsReader(reader, writer, report)
        self._writer = WsWriter(writer)
        self._codec = self.packet_codec(self)
        self._init_conn()
        await self._writer.drain()


class WsAbridged(WsConnection):
    packet_codec = AbridgedPacketCodec


class WsIntermediate(WsConnection):
    packet_codec = IntermediatePacketCodec


class _Loggers(dict):
    def __missing__(self, key):
        return logging.getLogger(key)


LOGGERS = _Loggers()


# ── running a target ─────────────────────────────────────────────────────────

async def run_once(host: str, dc: int, header_dc: Optional[int], args, proxy) -> Report:
    report = Report(host=host, dc=dc, header_dc=header_dc)
    conn_cls = WsIntermediate if args.codec == "intermediate" else WsAbridged
    conn = conn_cls(host, 443, dc, loggers=LOGGERS)
    conn.probe_proxy, conn.report, conn.origin, conn.header_dc = proxy, report, not args.no_origin, header_dc
    sender = MTProtoSender(None, loggers=LOGGERS, retries=0, delay=0, auto_reconnect=False,
                           connect_timeout=args.timeout)
    start = time.monotonic()
    try:
        await asyncio.wait_for(sender.connect(conn), args.timeout * 3)
        report.auth_key = bool(sender.auth_key and sender.auth_key.key)
        ping_id = int.from_bytes(os.urandom(8), "big", signed=True)
        pong = await asyncio.wait_for(sender.send(PingRequest(ping_id=ping_id)), args.timeout)
        report.pong = getattr(pong, "ping_id", None) == ping_id
        if args.hold:
            await asyncio.sleep(args.hold)
            ping_id = int.from_bytes(os.urandom(8), "big", signed=True)
            try:
                pong = await asyncio.wait_for(sender.send(PingRequest(ping_id=ping_id)), args.timeout)
                report.pong_after_hold = getattr(pong, "ping_id", None) == ping_id
            except Exception:  # noqa: BLE001
                report.pong_after_hold = False
    except Exception as e:  # noqa: BLE001
        report.error = f"{type(e).__name__}: {e}"
    finally:
        report.seconds = time.monotonic() - start
        for closer in (sender.disconnect, conn.disconnect):
            try:
                await asyncio.wait_for(closer(), 10)
            except Exception:  # noqa: BLE001
                pass
    return report


def targets(args) -> List[tuple]:
    out = []
    for dc in args.dc:
        names = []
        if args.family in ("kws", "both"):
            names.append(f"kws{dc}")
        if args.family in ("planet", "both"):
            names.append(PLANETS[dc])
        for name in names:
            out.append((f"{name}.{DOMAIN}", dc, False))
            if not args.no_media:
                out.append((f"{name}-1.{DOMAIN}", dc, True))
    for host in args.host or []:
        out.append((host, args.dc[0], False))
    for host, _, _ in out:
        try:
            ipaddress.ip_address(host)
            raise SystemExit(f"refusing {host!r}: an IP address — this probe connects by name only")
        except ValueError:
            pass
    return out


def show(r: Report) -> None:
    hdr = "" if r.header_dc is None else f" [DC {r.header_dc} in the obfuscated header]"
    print(f"\n{r.host}  (DC {r.dc}){hdr}  {r.seconds:.1f}s")
    for step in ("tunnel", "tls", "websocket"):
        if step in r.steps:
            print(f"   {step:<10} {r.steps[step]}")
    if r.exit_ip:
        print(f"   {'exit IP':<10} {r.exit_ip}")
    if "websocket" in r.steps and " 101" in r.steps["websocket"]:
        print(f"   {'mtproto':<10} {'auth key created' if r.auth_key else 'NO auth key'}"
              f"{'; ping answered' if r.pong else ''}")
        if r.pong_after_hold is not None:
            print(f"   {'hold':<10} ping after the idle hold: {'answered' if r.pong_after_hold else 'NOT answered'}")
    if r.ws_close and not r.auth_key:
        print(f"   {'closed':<10} {r.ws_close}")
    if r.error and not r.pong:
        print(f"   {'error':<10} {r.error}")


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proxy", default=os.environ.get("TG_WS_PROXY"),
                    help="http://user:pass@host:port or socks5://… (default: $TG_WS_PROXY)")
    ap.add_argument("--direct", action="store_true", help="no proxy: connect from this machine's own IP")
    ap.add_argument("--dc", type=int, action="append", choices=range(1, 6), help="DC number(s); default 1-5")
    ap.add_argument("--family", choices=("kws", "planet", "both"), default="both")
    ap.add_argument("--no-media", action="store_true", help="skip the -1 names")
    ap.add_argument("--host", action="append", help="an extra hostname to try (never an IP)")
    ap.add_argument("--codec", choices=("abridged", "intermediate"), default="abridged")
    ap.add_argument("--no-origin", action="store_true", help="omit the Origin header")
    ap.add_argument("--hold", type=float, default=0, help="idle seconds before a second ping")
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--verbose", action="store_true", help="show Telethon's own log lines")
    args = ap.parse_args()
    args.dc = args.dc or [1, 2, 3, 4, 5]

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.CRITICAL,
                        format="   log %(name)s %(levelname)s: %(message)s")
    if args.direct:
        proxy = None
        print("NO PROXY: connecting from this machine's own IP address.")
    elif not args.proxy:
        print("No proxy given (--proxy or $TG_WS_PROXY). Refusing to connect directly; pass --direct to do that.")
        return 2
    else:
        proxy = parse_proxy(args.proxy)
        print(f"Proxy: {proxy.shown}")
    print(f"Codec: {args.codec}; Origin header: {'no' if args.no_origin else 'yes'}; "
          f"hold: {args.hold:g}s. No account, no session, no api_id.")

    reports = []
    for host, dc, media in targets(args):
        r = await run_once(host, dc, None, args, proxy)
        ws_ok = " 101" in r.steps.get("websocket", "")
        if ws_ok and not r.auth_key:                  # the door answered but MTProto did not: try the DC in the header
            show(r)
            reports.append(r)
            r = await run_once(host, dc, -dc if media else dc, args, proxy)
        show(r)
        reports.append(r)
        await asyncio.sleep(0.5)

    print("\nSummary")
    for dc in args.dc:
        good = [r for r in reports if r.dc == dc and r.auth_key]
        print(f"   DC {dc}: " + (", ".join(sorted({r.host.split('.')[0] + ('' if r.header_dc is None else '*')
                                                  for r in good})) if good else "no working name"))
    ips = sorted({r.exit_ip for r in reports if r.exit_ip})
    if ips:
        print(f"   exit IPs the proxy reported: {', '.join(ips)}")
    if any(r.header_dc is not None and r.auth_key for r in reports):
        print("   * = worked only with the DC number in the obfuscated header")
    return 0 if any(r.auth_key for r in reports) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
