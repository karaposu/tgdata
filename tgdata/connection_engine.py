"""
Connection management engine for Telegram.
Handles connection pooling, rate limiting, retries, and health checks.
"""

import asyncio
import configparser
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Union
from telethon import TelegramClient
from telethon.errors import FloodWaitError, AuthKeyUnregisteredError
from telethon.sessions import StringSession

from .models import ConnectionConfig, RateLimitInfo

logger = logging.getLogger(__name__)


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


class ConnectionEngine:
    """
    Manages Telegram connections with advanced features.
    """
    
    def __init__(self, 
                 config_path: str = "config.ini",
                 pool_size: int = 1,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 exponential_backoff: bool = True):
        """
        Initialize connection engine.
        
        Args:
            config_path: Path to configuration file
            pool_size: Number of connections in pool (1 = no pooling)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            exponential_backoff: Whether to use exponential backoff
        """
        self.config_path = config_path
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        
        self._config: Optional[ConnectionConfig] = None
        self._primary_client: Optional[TelegramClient] = None
        self._pool: Optional[ConnectionPool] = None
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = 0
        
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

        self._config = ConnectionConfig(
            api_id=_unquote(section['api_id']),
            api_hash=_unquote(section['api_hash']),
            session_file=session_name,
            phone=_unquote(section.get('phone')),
            username=raw_username,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            exponential_backoff=self.exponential_backoff
        )

        return self._config
        
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

    async def _init_primary_client(self):
        """Create and authenticate the primary client once (may be interactive)."""
        config = self._load_config()

        # Session naming is resolved ONCE in _load_config (explicit
        # session_file > username > default) — config.session_file IS the
        # resolved name, so the primary client and the pool clients below
        # can never disagree about where the session lives.
        self._primary_client = TelegramClient(
            config.session_file,
            config.api_id,
            config.api_hash
        )

        await self._authenticate(self._primary_client)

        # Initialize pool if needed
        if self.pool_size > 1:
            await self._init_pool()
            
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
            client = TelegramClient(
                session_file,
                config.api_id,
                config.api_hash
            )
            
            await self._authenticate(client)
            self._pool.add_connection(client)
            
        logger.info(f"Initialized connection pool with {self.pool_size} connections")
        
    async def _authenticate(self, client: TelegramClient):
        """
        One-time authentication (login). Uses start(), which may prompt for a
        login code on first run. Runs once per client — NOT per operation.
        After this the session is authorized and its auth key persists on disk.
        """
        config = self._load_config()

        try:
            await client.start(phone=config.phone)
            logger.info("Authenticated with Telegram")

        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"Rate limited during authentication, waiting {wait_time} seconds...")
            if self._pool:
                self._pool.mark_rate_limited(client, wait_time)
            await asyncio.sleep(wait_time)
            await client.start(phone=config.phone)

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise ConnectionError(f"Failed to authenticate: {e}")

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
            'errors': []
        }
        
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
        
        Returns:
            True if connection is valid
        """
        try:
            client = await self.get_client()
            await client.get_me()
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
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