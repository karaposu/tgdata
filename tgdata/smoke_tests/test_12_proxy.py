"""
Smoke test for proxy support — the "one door to Telegram".

  1. proxy URL parsing and masking                      (no network)
  2. config: no proxy = direct, require_proxy refusal,   (no network)
     inline comments, password kept out of repr
  3. every client is built with the proxy                (no network)
  4. a dead proxy FAILS — no fallback to a direct line   (loopback only)
  5. a proxy that refuses the tunnel FAILS, and the      (loopback only)
     attempt really went to the proxy
  6. a working proxy carries the whole connection:       (loopback relay + Telegram)
     a local SOCKS5 relay with a user name and password
     forwards a FRESH, anonymous session to Telegram and
     back — no account is logged in or touched
  7. a real proxy from the config, if it has one         (the account — pending)

Items 4–6 need python-socks:  pip install 'tgdata[proxy]'
Item 6 reads only api_id / api_hash from the config; it uses a throwaway
session in a temp folder, so the account's own session is never opened.
"""
# To run: python -m tgdata.smoke_tests.test_12_proxy [config.ini]

import asyncio
import configparser
import os
import shutil
import socket
import sys
import tempfile
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import TgData, ProxyConfigError, AuthRequiredError
from tgdata.connection_engine import ConnectionEngine, parse_proxy_url, _proxy_library_available

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "config.ini"
TMP = tempfile.mkdtemp(prefix="tgdata_proxy_test_")


def write_ini(name: str, body: str) -> str:
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write("[Telegram]\napi_id = 12345\napi_hash = 0123456789abcdef0123456789abcdef\n"
                f"session_file = {os.path.join(TMP, 'throwaway')}\n" + body)
    return path


def real_api_ini(name: str, proxy_line: str) -> str:
    """api_id / api_hash from the real config, a THROWAWAY session, the given proxy."""
    cp = configparser.ConfigParser()
    cp.read(CONFIG)
    sec = next(s for s in cp.sections() if s.lower() == 'telegram')
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write(f"[Telegram]\napi_id = {cp[sec]['api_id'].strip()}\napi_hash = {cp[sec]['api_hash'].strip()}\n"
                f"session_file = {os.path.join(TMP, 'fresh_' + name)}\n{proxy_line}\n")
    return path


def closed_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Socks5Relay:
    """A minimal local SOCKS5 server (RFC 1928 CONNECT + RFC 1929 user/pass)
    that records every tunnel it is asked for. forward=False refuses them."""

    def __init__(self, username=None, password=None, forward=True):
        self.username, self.password, self.forward = username, password, forward
        self.destinations, self.auth_results = [], []

    async def start(self):
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def close(self):
        self.server.close()
        await self.server.wait_closed()

    @staticmethod
    async def _pipe(reader, writer):
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def _handle(self, reader, writer):
        try:
            _, n = await reader.readexactly(2)
            methods = await reader.readexactly(n)
            if self.username is not None:
                if 2 not in methods:
                    writer.write(b"\x05\xff")
                    return
                writer.write(b"\x05\x02")
                await writer.drain()
                _, ulen = await reader.readexactly(2)
                user = (await reader.readexactly(ulen)).decode()
                plen = (await reader.readexactly(1))[0]
                pwd = (await reader.readexactly(plen)).decode()
                ok = (user, pwd) == (self.username, self.password)
                self.auth_results.append(ok)
                writer.write(b"\x01\x00" if ok else b"\x01\x01")
                await writer.drain()
                if not ok:
                    return
            else:
                writer.write(b"\x05\x00")
                await writer.drain()
            _, _, _, atyp = await reader.readexactly(4)
            if atyp == 1:
                host = socket.inet_ntoa(await reader.readexactly(4))
            elif atyp == 3:
                host = (await reader.readexactly((await reader.readexactly(1))[0])).decode()
            else:
                host = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
            port = int.from_bytes(await reader.readexactly(2), "big")
            self.destinations.append((host, port))
            if not self.forward:
                writer.write(b"\x05\x05\x00\x01" + b"\x00" * 6)   # connection refused
                await writer.drain()
                return
            up_reader, up_writer = await asyncio.wait_for(asyncio.open_connection(host, port), 15)
            writer.write(b"\x05\x00\x00\x01" + b"\x00" * 6)
            await writer.drain()
            await asyncio.gather(self._pipe(reader, up_writer), self._pipe(up_reader, writer))
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass


# ------------------------------------------------------------ no network --

async def test_parse():
    print("TEST 1: proxy URL parsing and masking...")
    try:
        p, shown = parse_proxy_url("socks5://alice:s3cr%40t@10.0.0.5:1080")
        assert p == {'proxy_type': 'socks5', 'addr': '10.0.0.5', 'port': 1080, 'rdns': True,
                     'username': 'alice', 'password': 's3cr@t'}, p
        assert shown == "socks5://alice:***@10.0.0.5:1080" and "s3cr" not in shown, shown
        assert parse_proxy_url("http://proxy.example:8080") == (
            {'proxy_type': 'http', 'addr': 'proxy.example', 'port': 8080, 'rdns': True},
            "http://proxy.example:8080")
        assert parse_proxy_url("socks5h://h:1")[0]['proxy_type'] == 'socks5'
        assert parse_proxy_url("socks4://u@[::1]:9050")[1] == "socks4://u@[::1]:9050"
        for bad in ("1.2.3.4:1080", "ftp://h:1", "https://h:443", "socks5://h", "socks5://h:abc",
                    "tg://proxy?server=x&port=443&secret=y", "https://t.me/proxy?server=x"):
            try:
                parse_proxy_url(bad)
                raise AssertionError(f"accepted {bad!r}")
            except ProxyConfigError:
                pass
        print("✓ socks5 / socks4 / http parsed; password decoded and masked; 7 bad forms refused")
        return True
    except Exception as e:
        print(f"✗ Parsing test failed: {e}")
        return False


async def test_config():
    print("\nTEST 2: config loading...")
    try:
        cfg = ConnectionEngine(write_ini("direct.ini", ""))._load_config()
        assert cfg.proxy is None and cfg.proxy_display is None and cfg.require_proxy is False
        print("✓ No proxy key: direct, exactly as before")

        cfg = ConnectionEngine(write_ini("none.ini", "proxy = none\n"))._load_config()
        assert cfg.proxy is None
        print("✓ proxy = none: direct")

        try:
            ConnectionEngine(write_ini("req.ini", "require_proxy = true\n"))._load_config()
            raise AssertionError("require_proxy without a proxy was accepted")
        except ProxyConfigError as e:
            assert "refusing" in str(e)
        print("✓ require_proxy = true with no proxy: refused before any connection")

        try:
            ConnectionEngine(write_ini("badreq.ini", "require_proxy = maybe\n"))._load_config()
            raise AssertionError("require_proxy = maybe was accepted")
        except ProxyConfigError:
            pass
        print("✓ require_proxy = maybe: refused")

        if _proxy_library_available():
            cfg = ConnectionEngine(write_ini("proxy.ini",
                "proxy = 'socks5://bob:Zx9_SECRET@127.0.0.1:1080'  ; the account's proxy\n"
                "require_proxy = yes\n"))._load_config()
            assert cfg.proxy['addr'] == '127.0.0.1' and cfg.proxy['password'] == 'Zx9_SECRET' and cfg.require_proxy
            assert cfg.proxy_display == "socks5://bob:***@127.0.0.1:1080"
            assert "Zx9_SECRET" not in repr(cfg) and "Zx9_SECRET" not in str(cfg), repr(cfg)
            print("✓ Quoted proxy with an inline comment parsed; password absent from repr")
        else:
            try:
                ConnectionEngine(write_ini("nolib.ini", "proxy = socks5://127.0.0.1:1080\n"))._load_config()
                raise AssertionError("a proxy was accepted without a proxy library")
            except ProxyConfigError as e:
                assert "tgdata[proxy]" in str(e)
            print("✓ Proxy configured but python-socks missing: refused with the install hint")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_factory():
    print("\nTEST 3: every client is built with the proxy...")
    if not _proxy_library_available():
        print("! skipped — python-socks not installed")
        return True
    try:
        eng = ConnectionEngine(write_ini("factory.ini", "proxy = socks5://u:p@127.0.0.1:1080\n"), pool_size=3)
        main = eng._new_client()
        pooled = eng._new_client(eng._load_config().session_file + "_1")
        for c in (main, pooled):
            assert c._proxy == {'proxy_type': 'socks5', 'addr': '127.0.0.1', 'port': 1080,
                                'rdns': True, 'username': 'u', 'password': 'p'}, c._proxy
        direct = ConnectionEngine(write_ini("factory_direct.ini", ""))._new_client()
        assert direct._proxy is None
        health = await eng.health_check()
        assert health['proxy'] == "socks5://u:***@127.0.0.1:1080", health['proxy']
        print("✓ Main and pool clients carry the proxy; a direct config carries none; health shows it masked")
        return True
    except Exception as e:
        print(f"✗ Factory test failed: {e}")
        return False


# --------------------------------------------------------------- loopback --

async def test_dead_proxy():
    print("\nTEST 4: a dead proxy fails — no fallback to a direct connection...")
    if not _proxy_library_available():
        print("! skipped — python-socks not installed")
        return True
    try:
        eng = ConnectionEngine(write_ini("dead.ini", f"proxy = socks5://127.0.0.1:{closed_port()}\n"))
        start = time.time()
        try:
            async with eng.ephemeral_client():
                raise AssertionError("connected although the proxy is down — a direct fallback happened")
        except ConnectionError as e:
            print(f"✓ Connection refused through the dead proxy after {time.time() - start:.0f}s: {e}")
        return True
    except Exception as e:
        print(f"✗ Dead-proxy test failed: {type(e).__name__}: {e}")
        return False


async def test_refusing_proxy():
    print("\nTEST 5: a proxy that refuses the tunnel fails, and the attempt went to the proxy...")
    if not _proxy_library_available():
        print("! skipped — python-socks not installed")
        return True
    relay = await Socks5Relay(forward=False).start()
    try:
        eng = ConnectionEngine(write_ini("refuse.ini", f"proxy = socks5://127.0.0.1:{relay.port}\n"))
        try:
            async with eng.ephemeral_client():
                raise AssertionError("connected although the proxy refused — a direct fallback happened")
        except ConnectionError:
            pass
        assert relay.destinations, "the proxy was never asked for a tunnel"
        host, port = relay.destinations[0]
        print(f"✓ The proxy was asked for {host}:{port} ({len(relay.destinations)} attempts), "
              f"refused, and the client stopped there")
        return True
    except Exception as e:
        print(f"✗ Refusing-proxy test failed: {type(e).__name__}: {e}")
        return False
    finally:
        await relay.close()


async def test_working_relay():
    print("\nTEST 6: a working proxy carries the whole connection (throwaway session, no login)...")
    if not _proxy_library_available():
        print("! skipped — python-socks not installed")
        return True
    if not os.path.exists(CONFIG):
        print(f"! skipped — {CONFIG} not found (only its api_id / api_hash are read)")
        return True
    relay = await Socks5Relay(username="relay_user", password="p@ss:word").start()
    try:
        ini = real_api_ini("relay.ini", f"proxy = socks5://relay_user:p%40ss%3Aword@127.0.0.1:{relay.port}")
        eng = ConnectionEngine(ini)
        try:
            async with eng.ephemeral_client():
                raise AssertionError("a throwaway session claims to be authorized")
        except AuthRequiredError:
            pass                               # connected, asked Telegram, got "not logged in" back
        assert relay.auth_results and all(relay.auth_results), relay.auth_results
        assert relay.destinations and all(p == 443 or p == 80 for _, p in relay.destinations), relay.destinations
        print(f"✓ Round trip to Telegram through the relay: credentials accepted, tunnels to "
              f"{sorted(set(relay.destinations))}, answer 'not authorized' (a throwaway session)")
        return True
    except Exception as e:
        print(f"✗ Relay test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await relay.close()


async def test_real_proxy():
    print("\nTEST 7: a real proxy from the config...")
    if not os.path.exists(CONFIG):
        print(f"! skipped — {CONFIG} not found")
        return True
    try:
        eng = ConnectionEngine(CONFIG)
        cfg = eng._load_config()
        if not cfg.proxy:
            print("! skipped — this config has no `proxy` key (real-proxy test pending)")
            return True
        async with eng.ephemeral_client() as client:
            me = await client.get_me()
        print(f"✓ Logged-in account reached through {cfg.proxy_display}: id={me.id}")
        return True
    except Exception as e:
        print(f"✗ Real-proxy test failed: {type(e).__name__}: {e}")
        return False


async def main():
    print("Proxy Support Tests")
    print("=" * 60)
    print(f"config (items 6–7): {CONFIG}")
    print(f"proxy library installed: {_proxy_library_available()}\n")
    tests = [test_parse, test_config, test_factory, test_dead_proxy,
             test_refusing_proxy, test_working_relay, test_real_proxy]
    results = []
    try:
        for test in tests:
            results.append(await asyncio.wait_for(test(), timeout=90))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("\nSummary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
