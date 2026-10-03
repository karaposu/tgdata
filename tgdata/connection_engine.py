"""
Connection management engine for Telegram.
Handles connection pooling, rate limiting, retries, health checks, and the
account's proxy: every client is built by one function, _new_client(), which
applies the configured proxy to every connection and never falls back to a
direct one. Every client it builds also honours Telethon's per-request
flood_sleep_threshold, which Telethon itself ignores (_PerCallFloodThreshold).
"""

import asyncio
import configparser
import contextvars
import functools
import importlib.util
import logging
import re
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Tuple, Union
from urllib.parse import urlsplit, unquote
from telethon import TelegramClient, functions
from telethon.client.telegrambaseclient import TelegramBaseClient
from telethon.errors import FloodWaitError, AuthKeyUnregisteredError, UnauthorizedError, AuthKeyError
from telethon.sessions import StringSession

from . import health
from .health import telegram_error_name as _telegram_error_name
from .models import ConnectionConfig, RateLimitInfo

logger = logging.getLogger(__name__)


# ── a per-request flood threshold that actually works ──────────────────────
#
# (owner task, seconds) while a request sent with flood_sleep_threshold=N is
# in flight; None otherwise.
_PER_CALL_FLOOD_THRESHOLD = contextvars.ContextVar('tgdata_per_call_flood_threshold', default=None)


class _PerCallFloodThreshold:
    """Makes ``client(request, flood_sleep_threshold=N)`` do what Telethon
    documents: use N, for this request only, instead of the client-wide value.

    Telethon ignores the value. UserMethods.__call__ accepts it and calls
    _call without it, and _call decides whether to sleep through a flood wait
    by reading ``self.flood_sleep_threshold`` — the client-wide property —
    both before sending (a wait already known for that request type) and
    after a wait error. Checked in Telethon 1.33.1, 1.34.0, 1.40.0, 1.42.0,
    1.44.0 and 1.45.0: identical in all of them. So a per-call 0 still sleeps
    every wait up to the client threshold (60 s by default), silently.

    This mixin overrides that property: while a request sent with its own
    value is in flight, the property returns that value — but only to the
    task that sent it. Telethon starts background tasks inside connect() (the
    updates loop, keepalive), and connect() can run mid-request on a
    data-centre switch; a task created then inherits the context variable,
    and must not inherit the value. A request sent WITHOUT its own value
    clears any value an enclosing request in the same task set (for example
    a name Telethon resolves from inside that request), so a value applies to
    exactly the request it was passed with. The value is also passed on to
    Telethon, so a future Telethon that honours it natively behaves the same.

    tgdata/smoke_tests/test_14_flood_threshold.py checks this against the
    installed Telethon — run it after any Telethon upgrade.
    """

    @property
    def flood_sleep_threshold(self):
        held = _PER_CALL_FLOOD_THRESHOLD.get()
        if held is not None:
            try:
                if asyncio.current_task() is held[0]:
                    return held[1]
            except RuntimeError:            # read outside a running loop: no per-call value
                pass
        return TelegramBaseClient.flood_sleep_threshold.fget(self)

    @flood_sleep_threshold.setter
    def flood_sleep_threshold(self, value):
        TelegramBaseClient.flood_sleep_threshold.fset(self, value)    # keeps Telethon's 24 h cap

    async def __call__(self, request, ordered=False, flood_sleep_threshold=None):
        if flood_sleep_threshold is None:
            if _PER_CALL_FLOOD_THRESHOLD.get() is None:                # the common path
                return await super().__call__(request, ordered=ordered)
            token = _PER_CALL_FLOOD_THRESHOLD.set(None)                # never inherit one
            try:
                return await super().__call__(request, ordered=ordered)
            finally:
                _PER_CALL_FLOOD_THRESHOLD.reset(token)
        token = _PER_CALL_FLOOD_THRESHOLD.set((asyncio.current_task(), flood_sleep_threshold))
        try:
            return await super().__call__(request, ordered=ordered,
                                          flood_sleep_threshold=flood_sleep_threshold)
        finally:
            _PER_CALL_FLOOD_THRESHOLD.reset(token)


@functools.lru_cache(maxsize=None)
def _client_class(base):
    """The client class _new_client() builds: `base` (Telethon's
    TelegramClient, or whatever stands in for it in a test) with
    _PerCallFloodThreshold in front of it. Cached per base."""
    return type(f"Tgdata{base.__name__}", (_PerCallFloodThreshold, base), {})


class ProxyConfigError(ValueError):
    """The proxy settings in the [Telegram] section cannot be used: a
    malformed proxy URL, an unsupported proxy kind, the proxy library not
    installed, or require_proxy set with no proxy configured.

    Raised while reading the config — before any connection is opened — so a
    broken proxy setting can never turn into a direct connection."""


# URL scheme -> Telethon proxy type. 'socks5h' / 'socks4a' are accepted as
# spellings: Telegram's servers are addressed by IP, so remote DNS is moot.
_PROXY_SCHEMES = {'socks5': 'socks5', 'socks5h': 'socks5',
                  'socks4': 'socks4', 'socks4a': 'socks4',
                  'http': 'http'}
_TRUE = {'1', 'true', 'yes', 'on'}
_FALSE = {'', '0', 'false', 'no', 'off', 'none'}

# The device identity Telegram is told on every connection (Telethon's
# InitConnection), in the order a config snippet prints them.
IDENTITY_KEYS = ('device_model', 'system_version', 'app_version', 'lang_code', 'system_lang_code')


def parse_proxy_url(url: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse a proxy URL into Telethon's proxy dict and a masked display form.

    Accepted: socks5://host:port, socks5://user:pass@host:port, socks4://...,
    http://... (an HTTP CONNECT proxy). Special characters in the user name or
    password must be percent-encoded (e.g. '@' as %40). MTProto proxies
    (tg://proxy?..., t.me/proxy?...) are a different protocol and are not
    supported.

    Returns:
        (proxy_dict, display) — display has the password replaced by '***'.

    Raises:
        ProxyConfigError: the URL cannot be used.
    """
    raw = (url or '').strip()
    low = raw.lower()
    if low.startswith('tg://') or 't.me/proxy' in low or 'telegram.me/proxy' in low:
        raise ProxyConfigError(
            "MTProto proxies (tg://proxy / t.me/proxy links) are not supported — "
            "use a SOCKS5, SOCKS4 or HTTP proxy")
    if '://' not in raw:
        raise ProxyConfigError(
            f"proxy {raw!r} has no scheme — write it as socks5://host:port "
            f"(or socks4://, http://)")
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    if scheme not in _PROXY_SCHEMES:
        raise ProxyConfigError(
            f"proxy scheme {scheme!r} is not supported — use socks5://, socks4:// or http://")
    try:
        port = parts.port
    except ValueError:
        raise ProxyConfigError(f"proxy port in {scheme}://… is not a valid number") from None
    host = parts.hostname
    if not host or port is None:
        raise ProxyConfigError(f"proxy must name a host and a port: {scheme}://host:port")
    username = unquote(parts.username) if parts.username else None
    password = unquote(parts.password) if parts.password is not None else None

    proxy = {'proxy_type': _PROXY_SCHEMES[scheme], 'addr': host, 'port': port, 'rdns': True}
    if username is not None:
        proxy['username'] = username
    if password is not None:
        proxy['password'] = password

    shown_host = f"[{host}]" if ':' in host else host
    auth = ''
    if username is not None:
        auth = f"{parts.username}:***@" if password is not None else f"{parts.username}@"
    return proxy, f"{scheme}://{auth}{shown_host}:{port}"


def _proxy_library_available() -> bool:
    """Telethon proxies through python-socks (preferred) or PySocks."""
    return any(importlib.util.find_spec(m) is not None for m in ('python_socks', 'socks'))


class ConnectionPool:
    """Manage multiple connections with rate limiting"""
    
    def __init__(self, max_connections: int = 3):
        self.max_connections = max_connections
        self.connections: List[TelegramClient] = []
        self.current_index = 0
        self.rate_limits: Dict[int, RateLimitInfo] = {}
        
    async def get_connection(self) -> TelegramClient:
        """Get next available connection using round-robin"""
        if not self.connections:
            raise ValueError("No connections in pool")
            
        # Try to find a connection not rate-limited
        attempts = 0
        while attempts < len(self.connections):
            conn = self.connections[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.connections)
            
            rate_info = self.rate_limits.get(id(conn), RateLimitInfo())
            if time.time() < rate_info.flood_wait_until:
                attempts += 1
                continue
                
            return conn
            
        # All connections rate-limited, return the one with shortest wait
        return min(self.connections, 
                  key=lambda c: self.rate_limits.get(id(c), RateLimitInfo()).flood_wait_until)
        
    def mark_rate_limited(self, conn: TelegramClient, wait_seconds: float):
        """Mark a connection as rate-limited"""
        rate_info = self.rate_limits.get(id(conn), RateLimitInfo())
        rate_info.flood_wait_until = time.time() + wait_seconds
        self.rate_limits[id(conn)] = rate_info
        logger.warning(f"Connection {id(conn)} rate-limited for {wait_seconds}s")
    
    def add_connection(self, conn: TelegramClient):
        """Add a connection to the pool"""
        self.connections.append(conn)
        
    async def close_all(self):
        """Close all connections in the pool"""
        for conn in self.connections:
            await conn.disconnect()
        self.connections.clear()


class AuthRequiredError(ConnectionError, RuntimeError):
    """The session is not logged in, and tgdata may not ask Telegram for a
    login code here.

    tgdata never requests a code nobody can type. Telethon's interactive
    login (start()) sends a code to the account owner and then waits on
    stdin; in a background job it fails, and every retry sends another code.
    So the persistent connection, every pool connection and every
    use-and-close client ask Telegram directly whether the session is logged
    in, and raise this instead of prompting — unless a first login is being
    done by hand at a terminal, or the caller passed interactive_login=True.

    .reason — Telegram's own name for the problem: AUTH_KEY_UNREGISTERED or
    SESSION_REVOKED (logged out), USER_DEACTIVATED_BAN (banned), ... The
    Telegram error itself is the exception's __cause__.
    .banned — True when the account is banned or deleted: logging in again
    will not help.
    .first_login — True when the session has never been logged in: a
    configuration step, not something Telegram did to the account, so it is
    not reported as a health event.

    Both a ConnectionError (what the persistent path raised for a failed
    login before) and a RuntimeError (what this class was before), so
    existing handlers of either keep catching it.
    Fix a logout: log in again by hand, TgData(..., interactive_login=True)
    in a terminal."""

    def __init__(self, message: str, reason: Optional[str] = None, banned: bool = False,
                 first_login: bool = False):
        super().__init__(message)
        self.reason = reason
        self.banned = banned
        self.first_login = first_login


# The account itself is gone: logging in again cannot help
_BANNED = {'USER_DEACTIVATED_BAN', 'USER_DEACTIVATED'}


def _human_at_terminal() -> bool:
    """Whether someone could type a login code: stdin is an interactive
    terminal. A pseudo-terminal nobody watches (tmux, screen) passes too —
    which is why a session that was logged in before never prompts on this
    alone; only a first login does."""
    try:
        return bool(sys.stdin) and sys.stdin.isatty()
    except (AttributeError, ValueError, OSError):
        return False


class ConnectionEngine:
    """
    Manages Telegram connections with advanced features.
    """
    
    def __init__(self, 
                 config_path: str = "config.ini",
                 pool_size: int = 1,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 exponential_backoff: bool = True,
                 interactive_login: Optional[bool] = None):
        """
        Initialize connection engine.

        Args:
            config_path: Path to configuration file
            pool_size: Number of connections in pool (1 = no pooling)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            exponential_backoff: Whether to use exponential backoff
            interactive_login: When tgdata may run Telethon's interactive
                login, which asks Telegram to send a code and waits for it on
                stdin. None (default): only a first login on a brand-new
                session, with someone at a terminal. True: also log a logged-out
                session back in — run it by hand. False: never. Otherwise a
                session that is not logged in raises AuthRequiredError, and no
                code is ever requested.
        """
        self.config_path = config_path
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.interactive_login = interactive_login
        
        self._config: Optional[ConnectionConfig] = None
        self._primary_client: Optional[TelegramClient] = None
        self._pool: Optional[ConnectionPool] = None
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = 0
        self._route_logged = False         # "via proxy …" / "direct" is logged once per engine
        
    def _load_config(self) -> ConnectionConfig:
        """Load configuration from file"""
        if self._config:
            return self._config
            
        config = configparser.ConfigParser()
        config.read(self.config_path)
        
        # Handle case-insensitive section names
        telegram_section = None
        for section in config.sections():
            if section.lower() == 'telegram':
                telegram_section = section
                break
        
        if telegram_section is None:
            raise ValueError("No [telegram] or [Telegram] section found in config file")

        def _unquote(value):
            # INI values are raw text: `username = 'name'` yields the QUOTES as
            # part of the value, and a quoted session name becomes a file
            # literally called 'name'.session on disk. Strip surrounding
            # quotes from every string we read.
            return value.strip().strip("'\"") if isinstance(value, str) else value

        section = config[telegram_section]
        raw_session = _unquote(section.get('session_file'))
        raw_username = _unquote(section.get('username'))

        # Session naming precedence: an EXPLICIT session_file always wins — it
        # is the documented home of the credential, and honoring it keeps the
        # session's location independent of the process's working directory.
        # The legacy behavior (username as the session name) applies only when
        # no session_file is configured, so old username-only configs keep
        # finding their existing sessions. 'telegram_session' is the final
        # fallback when neither is set.
        session_name = raw_session or raw_username or 'telegram_session'

        # The account's proxy (optional). No `proxy` key = a direct connection,
        # exactly as before. A configured proxy is used for EVERY connection,
        # and a proxy that cannot be used stops here — never a silent fallback
        # to a direct connection. `require_proxy = true` makes a missing proxy
        # an error too. The first whitespace-separated token is the value, so
        # an inline "; comment" after it is ignored (URLs contain no spaces),
        # and quotes are stripped from that token. Read RAW: ConfigParser
        # would otherwise treat the '%' of a percent-encoded password
        # (p%40ss for p@ss) as interpolation and fail.
        def _first_token(value):
            tokens = value.split() if value else []
            return tokens[0].strip("'\"") if tokens else ''

        raw_proxy = _first_token(section.get('proxy', raw=True))
        raw_require = _first_token(section.get('require_proxy', raw=True)).lower()
        if raw_require not in _TRUE | _FALSE:
            raise ProxyConfigError(
                f"require_proxy = {raw_require!r} in {self.config_path} — use true or false")
        require_proxy = raw_require in _TRUE
        proxy, proxy_display = None, None
        if raw_proxy.lower() not in _FALSE:
            proxy, proxy_display = parse_proxy_url(raw_proxy)
            if not _proxy_library_available():
                raise ProxyConfigError(
                    f"a proxy is configured ({proxy_display}) but no proxy library is "
                    f"installed — pip install 'tgdata[proxy]' (python-socks[asyncio])")
        elif require_proxy:
            raise ProxyConfigError(
                f"require_proxy is set in {self.config_path} but no proxy is configured — "
                f"refusing to connect to Telegram directly")

        # The account's device identity (optional): what every connection tells
        # Telegram it is running on. With no keys, Telethon derives it from the
        # machine (CPU type, OS release) and from its own version, so the same
        # account presents a different device on another machine, after an OS
        # update, and after every Telethon upgrade. Pinned keys make it the
        # same everywhere. Telethon sends it on EVERY connection, not only at
        # login, so pinning applies to an existing session from its next
        # connection — no new login.
        # Values may contain spaces ("PC 64bit"), so the whole value is kept;
        # an inline " ; comment" or " # comment" is dropped and surrounding
        # quotes are stripped. Read RAW, like the proxy keys, so a '%' is never
        # taken for ConfigParser interpolation.
        def _identity_value(key):
            value = section.get(key, raw=True)
            if value is None:
                return None
            value = re.split(r'\s[;#]', value, maxsplit=1)[0].strip().strip("'\"").strip()
            return value or None

        identity = {key: _identity_value(key) for key in IDENTITY_KEYS}
        # Telethon documents system_lang_code as defaulting to lang_code, but its
        # constructor defaults both to 'en' independently; follow the documented
        # intent, so `lang_code = ru` alone does not present an app in Russian
        # on an English system.
        if identity['lang_code'] and not identity['system_lang_code']:
            identity['system_lang_code'] = identity['lang_code']

        self._config = ConnectionConfig(
            api_id=_unquote(section['api_id']),
            api_hash=_unquote(section['api_hash']),
            session_file=session_name,
            phone=_unquote(section.get('phone')),
            username=raw_username,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            exponential_backoff=self.exponential_backoff,
            proxy=proxy,
            proxy_display=proxy_display,
            require_proxy=require_proxy,
            **identity
        )

        return self._config

    @staticmethod
    def _identity_kwargs(config: ConnectionConfig) -> Dict[str, str]:
        """The pinned identity fields as TelegramClient keyword arguments.
        Unpinned fields are left out, so Telethon applies its own defaults."""
        return {key: getattr(config, key) for key in IDENTITY_KEYS if getattr(config, key)}

    def device_identity(self) -> Dict[str, Any]:
        """
        What every connection for this account tells Telegram it is running
        on — computed locally, with no network and no session file.

        Telethon itself is asked rather than its defaults re-derived: a client
        on an in-memory session is built exactly as _new_client() would build
        it (never connected), and the identity it would send is read back.

        Returns:
            {
              'presented': {field: value} for all five fields,
              'pinned': [the fields set in the config],
              'config_lines': ready-to-paste [Telegram] lines that pin exactly
                              what is presented now
            }

        Pinning: run it on the machine an account normally runs on, paste
        `config_lines` into that account's config, and from then on the account
        presents the same device from any machine and after any upgrade.
        """
        config = self._load_config()
        probe = TelegramClient(StringSession(), config.api_id, config.api_hash,
                               **self._identity_kwargs(config))
        # _init_request is Telethon's InitConnection, the request that carries
        # the identity to Telegram on every connect (stable through 1.x).
        request = getattr(probe, '_init_request', None)
        presented = {key: (getattr(request, key, None) if request is not None else getattr(config, key))
                     for key in IDENTITY_KEYS}
        return {
            'presented': presented,
            'pinned': [key for key in IDENTITY_KEYS if getattr(config, key)],
            'config_lines': "\n".join(f"{key} = {presented[key]}" for key in IDENTITY_KEYS
                                      if presented[key] is not None),
        }

    def _new_client(self, session_file: Optional[str] = None) -> TelegramClient:
        """
        THE door to Telegram: every client tgdata opens — the persistent one,
        each pool connection, and every use-and-close lookup — is built here.

        With a proxy configured, the client carries it and ALL its traffic
        (including Telethon's own reconnects) goes through it; if the proxy is
        down, connecting fails with ConnectionError — nothing retries directly.
        With no proxy configured the client is direct, exactly as before.
        The config is read first, so a ProxyConfigError (bad URL, missing
        library, require_proxy without a proxy) stops before any socket opens.

        Every client also carries the account's pinned device identity, if the
        config sets one; unpinned fields keep Telethon's machine defaults.

        And every client honours a per-request flood_sleep_threshold —
        client(request, flood_sleep_threshold=0) raises a flood wait instead of
        sleeping through it — which Telethon itself ignores (see
        _PerCallFloodThreshold). Requests sent without one behave exactly as
        Telethon's own.

        Args:
            session_file: Session name for this client (default: the config's)
        """
        config = self._load_config()
        identity = self._identity_kwargs(config)
        if not self._route_logged:
            if config.proxy:
                logger.info(f"Telegram connections go via proxy {config.proxy_display}")
            else:
                logger.info("Telegram connections are direct (no proxy configured)")
            if identity:
                logger.info("Device identity pinned: " +
                            ", ".join(f"{key}={value!r}" for key, value in identity.items()))
            else:
                logger.info("Device identity not pinned: Telethon's defaults for this machine")
            self._route_logged = True
        # TelegramClient is looked up here, at call time, so a test that stands
        # in for it (test_13) still controls what is built.
        return _client_class(TelegramClient)(
            session_file or config.session_file,
            config.api_id,
            config.api_hash,
            proxy=dict(config.proxy) if config.proxy else None,
            **identity
        )
        
    async def get_client(self) -> TelegramClient:
        """
        Return a connected, authenticated client.

        The connection is PERSISTENT: authentication happens once (on first use)
        and the socket is kept open across operations. Prefer
        ``async with engine.session() as client:`` at call sites so the
        connection is reused rather than torn down after each call — only
        close() disconnects.
        """
        # Use pool if enabled
        if self.pool_size > 1 and self._pool:
            conn = await self._pool.get_connection()
            await self._ensure_connected(conn)
            return conn

        # First use: create + authenticate the primary client exactly once
        if not self._primary_client:
            await self._init_primary_client()

        # Runtime: cheaply re-open the socket only if it dropped (no re-auth)
        await self._ensure_connected(self._primary_client)
        return self._primary_client

    @asynccontextmanager
    async def session(self):
        """
        Yield the persistent, connected client for a unit of work WITHOUT
        disconnecting on exit — the connection is long-lived and reused.

        This replaces the old per-call ``async with client:`` pattern, which
        ran start() and disconnect() on every operation (a full reconnect +
        re-auth each time). Teardown happens only in close() / __aexit__.
        """
        client = await self.get_client()
        yield client
        # Intentionally NO disconnect here — the connection is persistent.

    @asynccontextmanager
    async def ephemeral_client(self):
        """USE-AND-CLOSE (2026-08-05): a fresh client on the same resolved
        session, connected WITHOUT start() (never interactive), disconnected
        in finally — for short, human-triggered lookups (identity fetch,
        access probe) that must not park a live transport next to a standing
        loop sharing the session file. The persistent session()/pool path
        above is untouched — it remains correct for the loop's own fetches,
        where ONE process owns the session for its lifetime.

        Raises AuthRequiredError when Telegram says the session is not logged
        in — with Telegram's reason, so a ban is told from a logout — and
        never requests a login code. A flood wait is raised as the wait
        (FloodWaitError), never mistaken for "not logged in", which is what
        Telethon's is_user_authorized() does with any error."""
        config = self._load_config()
        client = self._new_client()
        first_login = client.session.auth_key is None
        try:
            await client.connect()
            problem = await self._authorization_problem(client)
            if problem is not None:
                raise self._auth_required(config.session_file, problem, first_login) from problem
            yield client
        finally:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001 — teardown must never mask the work
                pass

    async def _init_primary_client(self):
        """Create and authenticate the primary client once. A failed login
        leaves nothing behind, so the next get_client() checks again instead
        of handing out a client that never logged in."""
        config = self._load_config()

        # Session naming is resolved ONCE in _load_config (explicit
        # session_file > username > default) — config.session_file IS the
        # resolved name, so the primary client and the pool clients below
        # can never disagree about where the session lives.
        self._primary_client = self._new_client(config.session_file)

        try:
            await self._authenticate(self._primary_client)

            # Initialize pool if needed
            if self.pool_size > 1:
                await self._init_pool()
        except Exception:
            await self._discard_clients()
            raise

    async def _discard_clients(self):
        """Disconnect and forget the primary client and the pool."""
        clients = list(self._pool.connections) if self._pool else []
        if self._primary_client is not None and self._primary_client not in clients:
            clients.append(self._primary_client)
        for client in clients:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001 — teardown must never mask the error being raised
                pass
        self._primary_client = None
        self._pool = None

    async def _init_pool(self):
        """Initialize connection pool"""
        config = self._load_config()
        self._pool = ConnectionPool(self.pool_size)
        
        # Add primary client to pool
        if self._primary_client:
            self._pool.add_connection(self._primary_client)
            
        # Create additional connections
        for i in range(1, self.pool_size):
            session_file = f"{config.session_file}_{i}"
            client = self._new_client(session_file)

            try:
                await self._authenticate(client)
            except Exception:
                try:
                    await client.disconnect()      # not in the pool yet: close it here
                except Exception:  # noqa: BLE001 — never mask the login error
                    pass
                raise
            self._pool.add_connection(client)
            
        logger.info(f"Initialized connection pool with {self.pool_size} connections")
        
    async def _authenticate(self, client: TelegramClient):
        """
        One-time authentication (login). Runs once per client — NOT per
        operation. After this the session is logged in and its auth key
        persists on disk.

        It asks Telegram directly whether the session is logged in, and runs
        Telethon's interactive login — which asks Telegram to send a code to
        the account owner, then waits for it on stdin — only when someone can
        type the code (see interactive_login). Otherwise a session that is
        not logged in raises AuthRequiredError, and no code is requested: a
        background loop that retries fails the same way each time, instead of
        sending the owner one login code per retry.
        """
        config = self._load_config()
        first_login = client.session.auth_key is None     # no key yet: never connected before

        try:
            await self._log_in(client, config, first_login)

        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"Rate limited during authentication, waiting {wait_time} seconds...")
            await health.report(e, 'handled')
            if self._pool:
                self._pool.mark_rate_limited(client, wait_time)
            await asyncio.sleep(wait_time)
            await self._log_in(client, config, first_login)

        except AuthRequiredError as e:
            logger.error(f"Authentication failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise ConnectionError(f"Failed to authenticate: {e}")

    async def _log_in(self, client: TelegramClient, config: ConnectionConfig, first_login: bool):
        """Connect, ask Telegram whether the session is logged in, and log in
        interactively only when that is allowed."""
        if not client.is_connected():
            await client.connect()
        problem = await self._authorization_problem(client)
        if problem is None:
            logger.info("Authenticated with Telegram")
            return
        if not self._may_prompt(problem, first_login):
            raise self._auth_required(config.session_file, problem, first_login) from problem
        logger.info(f"Session not logged in ({_telegram_error_name(problem)}) — "
                    f"interactive login: Telegram will send a code")
        await client.start(phone=config.phone)
        logger.info("Authenticated with Telegram")

    @staticmethod
    async def _authorization_problem(client: TelegramClient) -> Optional[Exception]:
        """None when Telegram says this session is logged in; otherwise the
        Telegram error that says it is not (logged out, banned, ...).

        Asks Telegram directly, with the request Telethon's own
        is_user_authorized() uses (GetState), because is_user_authorized()
        turns EVERY error into "no" — a long flood wait included — and
        get_me() reads a ban as "not logged in". Any other error, a flood
        wait above the threshold included, propagates as itself."""
        try:
            await client(functions.updates.GetStateRequest())
            return None
        except (UnauthorizedError, AuthKeyError) as e:
            return e

    def _may_prompt(self, problem: Exception, first_login: bool) -> bool:
        """Whether Telethon's interactive login may run: never for a banned
        account; as interactive_login says when set; otherwise only a first
        login on a brand-new session, with someone at a terminal."""
        if _telegram_error_name(problem) in _BANNED:
            return False
        if self.interactive_login is not None:
            return bool(self.interactive_login)
        return first_login and _human_at_terminal()

    @staticmethod
    def _auth_required(session_file: str, problem: Exception, first_login: bool) -> AuthRequiredError:
        reason = _telegram_error_name(problem)
        if reason in _BANNED:
            return AuthRequiredError(
                f"session {session_file!r}: Telegram reports the account banned or deleted "
                f"({reason}) — logging in again will not help",
                reason=reason, banned=True)
        if first_login:
            return AuthRequiredError(
                f"session {session_file!r} has never been logged in ({reason}), and there is no "
                f"terminal to type the login code into — run it once by hand in a terminal, "
                f"or pass interactive_login=True", reason=reason, first_login=True)
        return AuthRequiredError(
            f"session {session_file!r} is not logged in ({reason}) — Telegram logged it out. "
            f"tgdata never asks for a login code on its own; log in again by hand: "
            f"TgData(..., interactive_login=True) in a terminal", reason=reason)

    async def _ensure_connected(self, client: TelegramClient):
        """
        Runtime connect: ensure the socket is open. Non-interactive — it uses the
        low-level connect() (never start()), so it never prompts, because the
        session was already authorized by _authenticate(). No-ops when already
        connected, so the persistent connection is reused instead of rebuilt.
        """
        if client.is_connected():
            return

        try:
            await client.connect()
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"Rate limited on connect, waiting {wait_time} seconds...")
            await health.report(e, 'handled')
            if self._pool:
                self._pool.mark_rate_limited(client, wait_time)
            await asyncio.sleep(wait_time)
            await client.connect()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect: {e}")
                    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all connections.
        
        Returns:
            Dictionary with health status
        """
        logger.info("Performing connection health check...")
        
        status = {
            'timestamp': time.time(),
            'primary_connection': False,
            'pool_connections': [],
            'proxy': self._config.proxy_display if self._config else None,  # masked; None = direct
            'device_identity': None,   # what connections present; filled below once the config is read
            'errors': []
        }
        if self._config:
            try:
                status['device_identity'] = self.device_identity()['presented']
            except Exception as e:  # noqa: BLE001 — a health check reports, it never raises
                status['errors'].append(f"Device identity unavailable: {e}")
        
        try:
            # Check primary connection
            if self._primary_client:
                try:
                    if self._primary_client.is_connected():
                        await self._primary_client.get_me()
                        status['primary_connection'] = True
                        logger.info("Primary connection healthy")
                except Exception as e:
                    status['errors'].append(f"Primary connection error: {e}")
                    logger.warning(f"Primary connection unhealthy: {e}")
                    
            # Check pool connections
            if self._pool:
                for i, conn in enumerate(self._pool.connections):
                    try:
                        if conn.is_connected():
                            await conn.get_me()
                            status['pool_connections'].append({
                                'index': i,
                                'healthy': True,
                                'rate_limited': time.time() < self._pool.rate_limits.get(
                                    id(conn), RateLimitInfo()
                                ).flood_wait_until
                            })
                        else:
                            status['pool_connections'].append({
                                'index': i,
                                'healthy': False
                            })
                    except Exception as e:
                        status['errors'].append(f"Pool connection {i} error: {e}")
                        status['pool_connections'].append({
                            'index': i,
                            'healthy': False,
                            'error': str(e)
                        })
                        
        except Exception as e:
            status['errors'].append(f"Health check error: {e}")
            logger.error(f"Health check failed: {e}")
            
        return status
        
    async def validate_connection(self) -> bool:
        """
        Validate that we have a working connection.

        Returns True or False, and on False says why: a Telegram verdict
        (logged out, banned, restricted, a wait, ...) is logged at WARNING
        with Telegram's name for it and reported as a health event; any other
        failure keeps the ERROR line.

        Returns:
            True if connection is valid
        """
        try:
            client = await self.get_client()
            if await client.get_me() is None:
                # Telethon's get_me() answers a logout or a ban with None, not
                # an error: ask Telegram directly, as the login check does
                problem = await self._authorization_problem(client)
                if problem is not None:
                    raise problem
            return True
        except Exception as e:
            finding = health.classify(e, include_reported=True)
            if finding is not None:
                logger.warning(f"Connection validation failed: {finding.verdict} ({finding.error})")
            else:
                logger.error(f"Connection validation failed: {e}")
            await health.report(e, 'swallowed')
            return False
            
    async def handle_rate_limit(self, error: FloodWaitError, client: Optional[TelegramClient] = None, strategy: str = 'wait'):
        """
        Handle rate limit errors with configurable strategy.
        
        Args:
            error: The FloodWaitError from Telegram
            client: The client that hit the rate limit
            strategy: 'wait' (wait exact time) or 'exponential' (exponential backoff)
        """
        base_wait_time = error.seconds
        
        if strategy == 'exponential':
            # Add random jitter (0-30% extra) to prevent thundering herd
            import random
            jitter = random.uniform(0, 0.3)
            wait_time = base_wait_time * (1 + jitter)
            logger.warning(f"Rate limit hit! Using exponential backoff: waiting {wait_time:.1f}s (base: {base_wait_time}s)")
        else:
            wait_time = base_wait_time
            logger.warning(f"Rate limit hit! Waiting {wait_time} seconds...")
        
        if self._pool and client:
            self._pool.mark_rate_limited(client, wait_time)
            
        await asyncio.sleep(wait_time)
        
    async def close(self):
        """Close all connections"""
        if self._pool:
            await self._pool.close_all()
        elif self._primary_client:
            await self._primary_client.disconnect()
            
        self._primary_client = None
        self._pool = None
        logger.info("All connections closed")