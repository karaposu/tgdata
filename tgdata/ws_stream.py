"""
A byte stream over Telegram's WebSocket door: TLS, the /apiws handshake, and
RFC 6455 client framing.

`open_websocket()` turns a hostname — and, when a proxy is used, a socket
already tunnelled to that hostname — into a reader/writer pair with exactly
the methods Telethon's connection layer calls: `readexactly`, `write`,
`drain`, `close`, `wait_closed`. The WebSocket transport
(`tgdata.websocket_transport`) hands that pair to Telethon's own obfuscated
transport, which neither knows nor cares that its bytes travel in WebSocket
frames.

This module imports only the standard library — never Telethon, never the rest
of tgdata — so a Telethon change cannot break it, and a port to another
Telethon only has to rewrite the connection class.

Errors are standard ones, chosen for how Telethon and tgdata treat them:
  - ValueError: an IP address given where a hostname is required. Never retried.
  - ssl.SSLCertVerificationError: the certificate did not verify. Propagated
    unchanged; the connection class turns it into tgdata's TransportConfigError.
  - ConnectionError: the door refused the upgrade, or broke the protocol.
    Retried like any network failure.
  - asyncio.IncompleteReadError: the door closed the stream mid-session. Telethon
    reads it as "the server closed the connection" and reconnects if allowed.
After the handshake, only ConnectionError / IncompleteReadError are raised: the
only kinds Telethon's receive loop handles without an "unexpected exception"
traceback.
"""

import asyncio
import base64
import hashlib
import ipaddress
import os
import ssl
from typing import Optional, Tuple

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"   # RFC 6455 §1.3
PATH = "/apiws"
MAX_HEADER = 16 * 1024          # the upgrade response's status line and headers
MAX_FRAME = 16 * 1024 * 1024    # one data frame; MTProto messages are far smaller


def _xor(data: bytes, mask: bytes) -> bytes:
    if not data:
        return b""
    repeated = (mask * (len(data) // 4 + 1))[:len(data)]
    return (int.from_bytes(data, "big") ^ int.from_bytes(repeated, "big")).to_bytes(len(data), "big")


def client_frame(opcode: int, payload: bytes) -> bytes:
    """One complete (FIN) frame from a client. Clients must mask (RFC 6455 §5.3)."""
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
    """Each write() is one masked binary frame, written in a single call, so a
    frame can never interleave with a pong the reader writes."""

    def __init__(self, writer: asyncio.StreamWriter):
        self._writer = writer

    def write(self, data) -> None:
        self._writer.write(client_frame(0x2, bytes(data)))

    async def drain(self) -> None:
        await self._writer.drain()

    def close(self) -> None:
        try:
            self._writer.write(client_frame(0x8, (1000).to_bytes(2, "big")))
        except Exception:  # noqa: BLE001 — closing must not raise
            pass
        self._writer.close()

    async def wait_closed(self) -> None:
        await self._writer.wait_closed()


class WsReader:
    """readexactly() over the payloads of binary and continuation frames.
    Pings are answered; a close frame or end of stream ends the stream."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, host: str):
        self._reader, self._writer, self._host = reader, writer, host
        self._buffer = bytearray()
        self._closed = False

    async def readexactly(self, n: int) -> bytes:
        while len(self._buffer) < n:
            if self._closed:
                raise asyncio.IncompleteReadError(bytes(self._buffer), n)
            await self._next_frame()
        out = bytes(self._buffer[:n])
        del self._buffer[:n]
        return out

    def _violation(self, what: str) -> ConnectionError:
        return ConnectionError(f"WebSocket transport: {self._host} {what}")

    async def _next_frame(self) -> None:
        try:
            b1, b2 = await self._reader.readexactly(2)
        except asyncio.IncompleteReadError:
            self._closed = True
            return
        opcode, n = b1 & 0x0F, b2 & 0x7F
        if b1 & 0x70:
            raise self._violation("set reserved bits")
        if b2 & 0x80:
            raise self._violation("sent a masked frame")
        if n == 126:
            n = int.from_bytes(await self._reader.readexactly(2), "big")
        elif n == 127:
            n = int.from_bytes(await self._reader.readexactly(8), "big")
        if opcode >= 0x8 and (n > 125 or not b1 & 0x80):
            raise self._violation("sent a malformed control frame")
        if n > MAX_FRAME:
            raise self._violation(f"sent a frame of {n} bytes")
        payload = await self._reader.readexactly(n) if n else b""
        if opcode in (0x0, 0x2):                 # continuation / binary
            self._buffer += payload
        elif opcode == 0x9:                      # ping -> pong, never awaiting drain here
            self._writer.write(client_frame(0xA, payload))
        elif opcode == 0xA:                      # pong
            pass
        elif opcode == 0x8:                      # close: answer once, then end the stream
            try:
                self._writer.write(client_frame(0x8, payload[:2]))
            except Exception:  # noqa: BLE001 — the stream is ending anyway
                pass
            self._closed = True
        else:                                    # text (0x1) or an unknown opcode
            raise self._violation(f"sent opcode {opcode:#x}, not binary")


def _refuse_ip(host: str) -> None:
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return
    raise ValueError(f"WebSocket transport: refusing an IP address as the host ({host}) — "
                     f"the door is reached by name only")


async def open_websocket(host: str, *, sock=None, port: int = 443, timeout: Optional[float] = None,
                         ssl_context: Optional[ssl.SSLContext] = None) -> Tuple[WsReader, WsWriter]:
    """
    Open wss://<host>/apiws and return (reader, writer).

    With `sock` (a socket a proxy already tunnelled to `host`), TLS runs over
    it; without, the operating system resolves `host` and connects directly.
    TLS always verifies the certificate against `host` (SNI), with the system
    trust store unless `ssl_context` is given. No Origin header is sent: the
    door does not require one (observed 2026-11-26), and tgdata presents a
    desktop identity, not a browser page. One `timeout` bounds TLS and the
    handshake together.
    """
    _refuse_ip(host)
    context = ssl_context or ssl.create_default_context()

    async def _open():
        if sock is not None:
            reader, writer = await asyncio.open_connection(sock=sock, ssl=context, server_hostname=host)
        else:
            reader, writer = await asyncio.open_connection(host, port, ssl=context, server_hostname=host)
        try:
            key = base64.b64encode(os.urandom(16)).decode()
            writer.write((f"GET {PATH} HTTP/1.1\r\n"
                          f"Host: {host}\r\n"
                          f"Upgrade: websocket\r\n"
                          f"Connection: Upgrade\r\n"
                          f"Sec-WebSocket-Key: {key}\r\n"
                          f"Sec-WebSocket-Version: 13\r\n"
                          f"Sec-WebSocket-Protocol: binary\r\n\r\n").encode())
            await writer.drain()
            try:
                head = await reader.readuntil(b"\r\n\r\n")
            except (asyncio.LimitOverrunError, asyncio.IncompleteReadError):
                raise ConnectionError(f"WebSocket transport: {host} did not answer the upgrade") from None
            if len(head) > MAX_HEADER:
                raise ConnectionError(f"WebSocket transport: {host} sent an oversized upgrade response")
            lines = head.decode("latin-1").split("\r\n")
            headers = {k.strip().lower(): v.strip()
                       for k, v in (line.split(":", 1) for line in lines[1:] if ":" in line)}
            expected = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
            status = lines[0].split(" ", 2)
            if len(status) < 2 or status[1] != "101" or headers.get("sec-websocket-accept") != expected:
                raise ConnectionError(f"WebSocket transport: upgrade to {host} refused ({lines[0]})")
            if headers.get("sec-websocket-protocol", "binary").lower() != "binary":
                raise ConnectionError(f"WebSocket transport: {host} chose another subprotocol")
            return WsReader(reader, writer, host), WsWriter(writer)
        except BaseException:
            writer.close()
            raise

    return await asyncio.wait_for(_open(), timeout)
