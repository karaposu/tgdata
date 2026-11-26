"""
The WebSocket transport (`transport = websocket` in an account's config):
every connection reaches Telegram's WebSocket door by hostname,
wss://<planet>.web.telegram.org/apiws, and never by IP address.

ConnectionWebSocket is a Telethon 1.45.0 connection class. Telethon builds one
for every connection it opens — the main one, connections to other data
centres for downloads, their reconnects — and always passes the data centre's
number. The class hands Telethon the DC's HOSTNAME in place of the IP it was
given, at construction, so the object never holds an IP and nothing built from
it can dial one. Telethon's own proxy code then tunnels to that name (remote
DNS is always on in tgdata), tgdata.ws_stream does TLS and the WebSocket
handshake, and Telethon's own obfuscated transport runs inside the frames.

The module is imported only when an account selects the transport, so it can
never affect an account that does not.

Relies on Telethon 1.45.0 internals (Connection.__init__/_connect/_proxy_connect,
ObfuscatedConnection._init_conn); test_50's canary checks them after any
Telethon upgrade.
"""

import ssl as ssl_module

from telethon.network.connection.tcpobfuscated import ConnectionTcpObfuscated

from .connection_engine import TransportConfigError
from .ws_stream import open_websocket

# DC number -> WebSocket host. The same map an independent client uses
# (gotd/td, telegram/dcs/prod.go, commit b4bf604), verified for all five DCs
# by a no-account probe and for an account's own DCs by a live check
# (2026-11-26). The media "-1" names are never used: two of them do not answer.
DC_HOSTS = {1: 'pluto', 2: 'venus', 3: 'aurora', 4: 'vesta', 5: 'flora'}
DOMAIN = 'web.telegram.org'
PORT = 443


def host_for(dc_id) -> str:
    """The WebSocket host for a data centre; any other DC (CDN, test, unknown)
    is a TransportConfigError — never a guess, never an IP."""
    name = DC_HOSTS.get(dc_id)
    if name is None:
        raise TransportConfigError(
            f"WebSocket transport: no WebSocket host is known for data centre {dc_id!r}")
    return f"{name}.{DOMAIN}"


class ConnectionWebSocket(ConnectionTcpObfuscated):
    """Telethon's obfuscated transport, carried over wss://<planet>.web.telegram.org/apiws.

    Telethon logs every connection as "Connecting to <host>:443/WebSocket..." —
    the operator's evidence that each one went by name."""

    # Test seam only: a context trusting a test certificate authority. Production
    # code never sets it; None means the system trust store.
    _ssl_context = None

    def __init__(self, ip, port, dc_id, **kwargs):
        # The IP (and port) Telethon passes are dropped here.
        super().__init__(host_for(dc_id), PORT, dc_id, **kwargs)

    async def _connect(self, timeout=None, ssl=None):
        # `ssl` is Telethon's TLS-to-IP option; tgdata never passes it, and
        # this transport always runs TLS to the hostname.
        sock = await self._proxy_connect(timeout=timeout) if self._proxy else None
        try:
            self._reader, self._writer = await open_websocket(
                self._ip, sock=sock, port=self._port, timeout=timeout, ssl_context=self._ssl_context)
        except ssl_module.SSLCertVerificationError as e:
            _close(sock)
            raise TransportConfigError(
                f"WebSocket transport: the certificate of {self._ip} did not verify "
                f"({e.verify_message}) — a proxy that intercepts TLS, or a missing trust store") from e
        except BaseException:
            _close(sock)
            raise
        try:
            self._codec = self.packet_codec(self)
            self._init_conn()          # ObfuscatedIO captures _reader/_writer here
            await self._writer.drain()
        except BaseException:
            self._writer.close()       # Telethon's disconnect() skips a connect that never completed
            raise


def _close(sock) -> None:
    if sock is not None:
        try:
            sock.close()
        except OSError:
            pass
