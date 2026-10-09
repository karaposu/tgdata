"""
Unified Telegram Group Message Crawler.
Single class with all features, delegating to specialized engines.
"""

import asyncio
import functools
import inspect
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union, Callable
import pandas as pd

from . import health
from .account_operation import _expected_account_id
from .owned_health import _OwnedHealthMonitor, _retire_notifications
from .connection_engine import ConnectionEngine, AuthRequiredError, ProxyConfigError
from .message_engine import MessageEngine
from .discovery_engine import DiscoveryEngine
from .batch_engine import BatchEngine
from .message_batch import MessageBatch
from .sync_engine import SyncEngine
from .backfill_engine import BackfillEngine
from .backfill import (
    BackfillStartRequest, BackfillRunRef, BackfillPrepareContext,
    BackfillDeliveryRef, BackfillConfigurationError,
)
from .models import GroupInfo
from .read_budget import ReadBudgetError, ReadBudgetExceeded
from .utils import (
    format_message_for_display,
    export_to_json,
    export_to_csv,
    filter_messages_by_sender,
    filter_messages_by_content,
    get_message_statistics,
    save_profile_photos,
    create_metrics_report
)

logger = logging.getLogger(__name__)


def _reported(group_param: Optional[str] = None, recover: bool = True,
              success_if: Optional[Callable[[Any], bool]] = None):
    """Run a public method that talks to Telegram as one health call (issue
    #4): a Telegram verdict that escapes it is reported, then re-raised
    unchanged; a success sends "ok" for what it proves has ended.

    group_param names the argument holding the group (the current group when
    it is not given); recover=False leaves recovering to the calls made inside;
    success_if marks a result that means failure, so it is never a recovery."""
    def decorate(method):
        signature = inspect.signature(method)
        name = method.__name__

        @functools.wraps(method)
        async def wrapper(self, *args, **kwargs):
            monitor = getattr(self, '_health', None)
            if monitor is None:
                return await method(self, *args, **kwargs)
            group = None
            if group_param is not None:
                try:
                    group = signature.bind_partial(self, *args, **kwargs).arguments.get(group_param)
                except TypeError:              # a wrong call: the method raises its own error
                    group = None
                current = getattr(self, 'current_group', None)
                if group is None and current is not None:
                    group = current.id
            async with monitor.call(name, health.normalise_group(group), recover) as call:
                result = await method(self, *args, **kwargs)
                if success_if is not None and not success_if(result):
                    call.failed = True
                return result
        return wrapper
    return decorate


def _polling_cannot_recover(error: BaseException) -> bool:
    """Whether polling again at the next interval cannot help: the session is
    not logged in, proxy/budget policy blocks reading, or Telegram's verdict is
    that the account is logged out, banned or restricted, or cannot read the group."""
    if isinstance(error, (AuthRequiredError, ProxyConfigError, ReadBudgetError)):
        return True
    finding = health.classify(error, include_reported=True)
    return finding is not None and finding.verdict in health.TERMINAL


def _health_check_passed(status: Dict[str, Any]) -> bool:
    """Whether a health_check() reached Telegram and found every connection
    logged in — the only kind that may count as a recovery."""
    return (status.get('primary_connection') is True
            and all(entry.get('healthy') for entry in status.get('pool_connections', [])))


class TgData:
    """
    Unified interface for Telegram group operations.
    All features in one place, with clean delegation to specialized engines.
    """
    
    def __init__(self,
                 config_path: str = "config.ini",
                 connection_pool_size: int = 1,
                 log_file: Optional[str] = None,
                 interactive_login: Optional[bool] = None,
                 health_callback: Optional[Callable] = None,
                 account_label: Optional[str] = None,
                 session_store=None,
                 read_budget=None,
                 sync_store=None,
                 backfill_store=None):
        """
        Initialize Telegram group handler.

        Args:
            config_path: Path to configuration file
            connection_pool_size: Number of connections (1 = no pooling)
            log_file: Optional log file path
            interactive_login: When tgdata may ask Telegram for a login code
                and wait for it on stdin. None (default): only the first
                login of a brand-new session, run by hand in a terminal.
                True: also log a session back in after Telegram logged it out —
                run that by hand. False: never. Otherwise a session that is
                not logged in raises AuthRequiredError (with .reason and
                .banned), and no code is ever requested.
            health_callback: Called with a plain, JSON-ready dict every time
                Telegram says no to this account — a wait, a logout, a ban, a
                restriction, no access to a group — and with verdict "ok" when
                that ends. A function or a coroutine function; an exception in
                it is logged, never raised. Events caused by tgdata calls it
                makes itself are logged and counted, not delivered back to it.
                See the README, "Account health events".
                health_check()["health"] summarises legacy public calls;
                get_account_health(id) is the separate verified-operation view.
            account_label: A name for this account in those events (default:
                None; the session name and the account id are always included)
            session_store: Optional object with synchronous load(name) -> str
                or None, save(name, data), and optional delete(name) methods.
                Stores the login, group cache and update states without a
                .session file. Methods run on the event loop and should return
                quickly. None keeps the existing file sessions.
            read_budget: Optional ReadBudget sharing a rolling 24-hour message
                allowance by authenticated account ID. None keeps reads unlimited
                by account quota. See the README's read-budget contract.
            sync_store: Optional async load/compare_and_swap backend for durable
                daily continuation. SQLiteSyncStore provides local persistence.
                Progress advances only on explicit acknowledge_sync.
            backfill_store: Optional async load/compare_and_swap backend in a
                separate historical collection namespace. The caller configures
                that namespace; collection_id does not route to another backend.
                Progress advances only on acknowledge_backfill. None disables
                the backfill facade. See docs/backfill_runs.md.
        """
        # Set up logging
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)
            
        # Initialize engines
        self.connection_engine = ConnectionEngine(
            config_path=config_path,
            pool_size=connection_pool_size,
            interactive_login=interactive_login,
            session_store=session_store,
            read_budget=read_budget
        )
        
        self.message_engine = MessageEngine(
            connection_engine=self.connection_engine
        )

        self.discovery_engine = DiscoveryEngine(
            connection_engine=self.connection_engine
        )
        self.batch_engine = BatchEngine(self.connection_engine)
        self.sync_engine = SyncEngine(self.get_message_batch, sync_store)
        self._backfill_store = backfill_store
        # Keep local activity, known ends and monotonic minima across operations.
        # A collection cache key is identity, not automatic backend namespacing.
        self._backfill_engines = {}

        # State
        self.current_group: Optional[GroupInfo] = None
        self._metrics: Dict[str, Any] = {}
        self._health = health.HealthMonitor(health_callback, account_label, self._health_identity)
        self._account_health = {}
        
        logger.info("TgData initialized")

    def _health_identity(self):
        """(session, user_id) for health events: the session file's name
        without folder or .session, and the account id Telethon restored for
        the client, when known. Never raises."""
        session = user_id = None
        try:
            config = self.connection_engine._config      # read only once loaded: no side effect
            if config is not None and config.session_file:
                name = os.path.basename(str(config.session_file))
                session = name[:-len('.session')] if name.endswith('.session') else name
        except Exception:  # noqa: BLE001
            pass
        try:
            client = self.connection_engine._primary_client
            user_id = client._self_id if client is not None else None
        except Exception:  # noqa: BLE001
            pass
        return session, user_id

    def get_account_health(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Local health observed through verified operations, or None if unknown.

        No I/O or authentication. Legacy reads/health_check() keep their separate
        health view; cached session identities never populate this owned ledger.
        """
        account_id = _expected_account_id(account_id)
        monitor = self._account_health.get(account_id)
        return monitor.snapshot() if monitor is not None else None

    @asynccontextmanager
    async def _account_health_operation(self, expected_account_id, method, group=None):
        """Private Stage 1 composition; yield (verified handle, health observation).

        Group code must explicitly confirm proven access on the observation.
        Caller work stays in the opening task; notifications run after cleanup.
        """
        started = next(health._TICKS)
        monitor = observation = None
        with health.isolate_call():
            try:
                async with self.connection_engine._account_operation(expected_account_id) as operation:
                    monitor = self._account_health.get(operation.account_id)
                    if monitor is None:
                        monitor = _OwnedHealthMonitor(operation.account_id, self._health_identity()[0],
                                                      self._health.callback, self._health.label)
                        self._account_health[operation.account_id] = monitor
                    async with monitor.observe(operation, method, health.normalise_group(group),
                                               started) as observation:
                        yield operation, observation
            finally:
                if observation is not None:
                    monitor.dispatch(observation)

    # ==================== Group Management ====================
    
    @_reported()
    async def list_groups(self) -> pd.DataFrame:
        """
        List all accessible groups/channels.
        
        Returns:
            DataFrame with group information
        """
        try:
            groups_data = []

            async with self.connection_engine.session() as client:
                async for dialog in client.iter_dialogs():
                    if dialog.is_group or dialog.is_channel:
                        entity = dialog.entity
                        
                        group_info = {
                            'GroupID': entity.id,
                            'Title': entity.title,
                            'Username': f"@{entity.username}" if hasattr(entity, 'username') and entity.username else None,
                            'Identifier': f"@{entity.username}" if hasattr(entity, 'username') and entity.username else str(entity.id),
                            'IsChannel': dialog.is_channel,
                            'IsMegagroup': getattr(entity, 'megagroup', False),
                            'ParticipantsCount': getattr(entity, 'participants_count', None)
                        }
                        
                        groups_data.append(group_info)
                        
            df = pd.DataFrame(groups_data)
            logger.info(f"Found {len(df)} groups/channels")
            return df
            
        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            raise
            
    def set_group(self, group_id: int) -> None:
        """
        Set the current group for operations.
        
        Args:
            group_id: Telegram group/channel ID
        """
        self.current_group = GroupInfo(
            id=group_id,
            title="",  # Will be populated on first operation
            username=None
        )
        logger.info(f"Set current group to {group_id}")
        
    # ==================== Message Operations ====================

    async def initialize_sync(self, chat_id, *, after_id, media_mode='references',
                              start_date=None, end_date=None, last_days=None):
        """Enroll a canonical negative chat ID at an explicit initial cursor.

        Zero starts at the oldest visible history. Matching repeated enrollment
        preserves current progress; a different initial cursor or mode raises.
        This only accesses the configured sync_store, never Telegram.
        For a historical collection, supply timezone-aware start_date/end_date
        or last_days (N*24 hours ending at first enrollment). Matching repeated
        relative enrollment reuses the saved dates. Dates include start and
        exclude end, intersecting after_id. A conflicting window raises; use
        separate progress stores for daily and historical collections.
        """
        return await self.sync_engine.initialize(
            chat_id, after_id=after_id, media_mode=media_mode,
            start_date=start_date, end_date=end_date, last_days=last_days)

    async def sync_group(self, chat_id, *, limit=200, download_media_to=None):
        """Prepare/replay one durable pending MessageBatch, or None if empty.

        Enroll the canonical chat ID first. Pending replay does not contact
        Telegram or spend budget. Deliver the batch durably, then explicitly
        acknowledge_sync(chat_id, batch.batch_id). One reader per group/store
        is supported; this method performs no scheduling or account failover.

        An ordinary read error's nonempty partial_result is saved as pending
        before that same error is re-raised. A failed partial save raises a
        local SyncError with the original exception in read_error instead.
        Download-mode replay verifies every referenced blob at the given root.
        """
        # Only the actual get_message_batch call carries a health context.
        # Local replay must not count as fresh Telegram recovery evidence.
        return await self.sync_engine.prepare(chat_id, limit=limit,
                                              download_media_to=download_media_to)

    async def acknowledge_sync(self, chat_id, batch_id):
        """Assert durable destination acceptance and atomically advance progress.

        The next cursor comes from the saved batch, never from the caller.
        Repeating the latest acknowledgment is harmless; wrong/older IDs raise
        without clearing newer work. No Telegram connection is needed.
        """
        return await self.sync_engine.acknowledge(chat_id, batch_id)

    async def get_sync_status(self, chat_id):
        """Return immutable SyncStatus, or None if not enrolled; storage only."""
        return await self.sync_engine.status(chat_id)

    def _backfill_for(self, address, expected_type):
        if not isinstance(address, expected_type):
            raise BackfillConfigurationError('{} is required'.format(expected_type.__name__))
        owned = expected_type.from_dict(address.to_dict())
        if self._backfill_store is None:
            raise BackfillConfigurationError('configure a backfill_store in its own collection namespace')
        collection = (owned.run.collection_id if isinstance(owned, (BackfillPrepareContext, BackfillDeliveryRef))
                      else owned.collection_id)
        engine = self._backfill_engines.get(collection)
        if engine is None:
            engine = BackfillEngine(self._backfill_store, collection, read_batch=self.get_message_batch)
            self._backfill_engines[collection] = engine
        return engine, owned

    async def start_backfill(self, start_request: BackfillStartRequest, *, submission):
        """Create explicit new intent or recognize its retained original request.

        submission is required: 'new' or 'retry'. Retain the request before
        submission; an unknown retry never creates. This is storage-only.
        """
        engine, request = self._backfill_for(start_request, BackfillStartRequest)
        return await engine.start(request, submission=submission)

    async def get_backfill_status(self, run: BackfillRunRef):
        """Return immutable stored facts for this complete run reference.

        Missing/pruned/corrupt/unavailable state raises; it never implies new
        intent or readiness. No source, credential or account refresh occurs.
        """
        engine, run = self._backfill_for(run, BackfillRunRef)
        return await engine.status(run)

    async def prepare_backfill(self, context: BackfillPrepareContext, *, download_media_to=None):
        """Prepare/replay one exact delivery, or return stored status/local wait.

        A stale cursor/control context refuses without auto-rebase. Until ack,
        pending replay uses saved bytes and does not contact Telegram. Only an
        eligible new attempt calls the existing get_message_batch health boundary.
        Ordinary source errors retain a valid prefix before re-raising; obtain
        its full delivery reference by replaying the stored pending observation.
        """
        engine, context = self._backfill_for(context, BackfillPrepareContext)
        return await engine.prepare(context, download_media_to=download_media_to)

    async def acknowledge_backfill(self, delivery: BackfillDeliveryRef):
        """Assert durable receiver acceptance of the exact full delivery reference.

        Advances only to the saved next cursor. It neither contacts the source
        nor checks/deletes media. Retained duplicate receipts are harmless;
        another run's equal hash cannot settle this run's obligation.
        """
        engine, delivery = self._backfill_for(delivery, BackfillDeliveryRef)
        return await engine.acknowledge(delivery)

    async def control_backfill(self, run: BackfillRunRef, *, command_id,
                               expected_control_revision, action):
        """Record pause/resume/cancel/abandon with its original exact context.

        Pause/cancel preserve admitted work and owed output; resume grants only
        operator permission. Only explicit quiescent abandonment withdraws an
        obligation. A recognized retry does not apply again or reset any wait.
        """
        engine, run = self._backfill_for(run, BackfillRunRef)
        return await engine.control(run, command_id=command_id,
                                    expected_control_revision=expected_control_revision, action=action)

    async def recover_backfill(self, run: BackfillRunRef, *, attempt_id, command_id,
                               expected_control_revision, previous_reader_stopped):
        """Reconcile one exact interrupted attempt after its worker actually stopped.

        The required true assertion does not terminate a worker or provide a
        distributed lease. Active local preparation refuses. Recovery preserves
        facts, uses known end evidence or one conservative wait, and never reads,
        acknowledges, resumes or refunds quota. Retain unchanged retry arguments.
        """
        engine, run = self._backfill_for(run, BackfillRunRef)
        return await engine.recover(run, attempt_id=attempt_id, command_id=command_id,
                                    expected_control_revision=expected_control_revision,
                                    previous_reader_stopped=previous_reader_stopped)

    @_reported('group_id')
    async def get_message_batch(self, group_id: Union[int, str], *,
                                after_id: int = 0, limit: int = 200,
                                download_media_to=None,
                                start_date=None, end_date=None) -> MessageBatch:
        """Read a bounded oldest-first raw snapshot after an exclusive ID.

        Returns a versioned MessageBatch with canonical JSON, a batch_id and
        next_after_id. Pass download_media_to for hash-named photo/document
        files; otherwise only references are returned. The existing client,
        proxy/session configuration and optional read budget apply.

        Once a chat is resolved, an ordinary failure carries a MessageBatch
        of completed records in error.partial_result and is re-raised unchanged.
        Persist/replay that value and advance your durable cursor only after
        the receiver acknowledges it. This method does not change current_group.

        group_id must name a group/channel explicitly; after_id is 0..2**31-1,
        limit is 1..10000. See docs/message_batch_v1.md for the exact wire contract.
        Optional timezone-aware start_date/end_date constrain message dates to
        [start_date, end_date). Supply both; the ID cursor still applies. Reads
        outside the interval spend normal budget but do not download media.
        """
        options = dict(after_id=after_id, limit=limit, download_media_to=download_media_to)
        if start_date is not None or end_date is not None:
            options.update(start_date=start_date, end_date=end_date)
        return await self.batch_engine.fetch_batch(group_id, **options)
    
    @_reported('group_id')
    async def get_messages(self,
                          group_id: Optional[int] = None,
                          limit: Optional[int] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          after_id: int = 0,
                          include_profile_photos: bool = False,
                          with_progress: bool = False,
                          progress_callback: Optional[Callable] = None,
                          batch_size: Optional[int] = None,
                          batch_callback: Optional[Callable] = None,
                          batch_delay: float = 0.0,
                          rate_limit_strategy: str = 'wait',
                          allow_full_fetch: bool = False,
                          download_media_to: Optional[str] = None,
                          include_media: bool = False,
                          heartbeat: Optional[Callable] = None) -> pd.DataFrame:
        """
        Get messages from a group with various options.
        
        Args:
            group_id: Target group ID (uses current if not specified)
            limit: Maximum number of messages
            start_date: Get messages after this date
            end_date: Get messages before this date
            after_id: Get messages after this message ID (for incremental extraction)
            include_profile_photos: Whether to download profile photos
            with_progress: Enable progress tracking
            progress_callback: Optional callback for progress updates
            batch_size: If specified, process messages in batches of this size
            batch_callback: Optional async callback called for each batch (batch_df, batch_info)
            batch_delay: Delay in seconds between batches to avoid rate limits (default: 0)
            rate_limit_strategy: How to handle rate limits - 'wait' or 'exponential' (default: 'wait')
            allow_full_fetch: With no limit given, fetches are bounded at 750 messages
                (a warning is logged when the bound is hit); set True to permit a
                genuinely unbounded fetch (default: False)
            download_media_to: If set to a directory path, each message's own media
                (photos/videos/...) is downloaded there during the fetch, with the
                local path recorded in the MediaPath column. One call = data + files.
                (default: None = references only). Note: downloads everything matched,
                so scope with a limit/date range on large groups.
            include_media: If True, each message's media is loaded in-memory as raw
                bytes into the MediaData column (like include_profile_photos). Handy
                for small scrapes; holds every file in RAM, so scope it. CSV export
                drops MediaData; JSON stores a "[Binary data]" placeholder. (default: False)

        Returns:
            DataFrame with messages
        """
        # Use provided group_id or current
        target_group_id = group_id or (self.current_group.id if self.current_group else None)
        if not target_group_id:
            raise ValueError("No group specified. Use set_group() or provide group_id")
            
        # Set as current if different
        if group_id and (not self.current_group or self.current_group.id != group_id):
            self.set_group(group_id)
            
        # Enable progress callback if requested
        if with_progress and not progress_callback:
            def default_progress(current, total, rate):
                if total:
                    percent = (current / total) * 100
                    print(f"\rProgress: {current}/{total} ({percent:.1f}%) - {rate:.1f} msg/s", end="")
                else:
                    print(f"\rProgress: {current} messages - {rate:.1f} msg/s", end="")
                    
            progress_callback = default_progress
            
        # Fetch messages
        df = await self.message_engine.fetch_messages(
            group_id=target_group_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            min_id=after_id if after_id > 0 else None,  # Telethon's min_id is exclusive: returns ids > after_id
            include_profile_photos=include_profile_photos,
            progress_callback=progress_callback,
            batch_size=batch_size,
            batch_callback=batch_callback,
            batch_delay=batch_delay,
            rate_limit_strategy=rate_limit_strategy,
            allow_full_fetch=allow_full_fetch,
            download_media_to=download_media_to,
            include_media=include_media,
            heartbeat=heartbeat
        )
        
        if with_progress:
            print()  # New line after progress
         
        return df
        
        
    @_reported('group_id')
    async def get_message_count(self, group_id: Optional[int] = None) -> int:
        """
        Get total message count for a group without fetching all messages.
        
        Args:
            group_id: Target group ID (uses current if not specified)
            
        Returns:
            Total message count
        """
        target_group_id = group_id or (self.current_group.id if self.current_group else None)
        if not target_group_id:
            raise ValueError("No group specified")
            
        return await self.message_engine.get_message_count(target_group_id)
        
    @_reported('group_id')
    async def search_messages(self,
                            query: str,
                            group_id: Optional[int] = None,
                            limit: Optional[int] = None) -> pd.DataFrame:
        """
        Search for messages containing specific text.
        
        Args:
            query: Search query
            group_id: Target group ID or username (e.g., '@channelname') - uses current if not specified
            limit: Maximum number of results
            
        Returns:
            DataFrame with matching messages
        """
        target_group_id = group_id or (self.current_group.id if self.current_group else None)
        if not target_group_id:
            raise ValueError("No group specified")
            
        return await self.message_engine.search_messages(
            group_id=target_group_id,
            query=query,
            limit=limit
        )
        
    # ==================== Group Discovery ====================

    @_reported()
    async def search_groups(self,
                            query: str,
                            limit: int = 100,
                            pace: float = 2.0,
                            max_flood_wait: int = 3600,
                            max_offline: int = 3600,
                            heartbeat: Optional[Callable] = None,
                            found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        Telegram's global search for groups and channels.

        Matches room NAMES and @usernames only — never post content. A room
        about your topic under an unrelated name is invisible to every query;
        reach those with similar_groups and linked_groups.

        Args:
            query: The search text (rooms name themselves "place + topic";
                build_search_queries() makes the combinations)
            limit: Results to ask for (Telegram caps it lower; default 100)
            pace: Seconds to sleep after each request (default 2.0 — the
                proven pace for a personal account)
            max_flood_wait: A rate-limit wait up to this many seconds is
                obeyed exactly, with heartbeat ticks; a longer one raises
                DiscoveryInterrupted (default 3600). A wait on a username
                lookup is never slept: it skips the seed or stops resolving
                (for a linked_groups source it raises DiscoveryInterrupted).
                Reading a room's posts for links, and the dialog sync for a
                numeric id, keep Telethon's own handling: a wait of up to a
                minute there is slept without ticks.
            max_offline: How long to wait for a dropped connection to come
                back before giving up (default 3600)
            heartbeat: Liveness callback(phase) — see get_messages
            found_callback: callback(row_dict) for every room as it is found,
                sync or async, so a long run can be persisted incrementally;
                an exception in it ends the run

        Returns:
            DataFrame with the list_groups columns plus FoundVia ('search')
            and FoundBy (the query). Every row is already usable by
            get_messages(row['GroupID']) — no dialog sync needed.

        Raises:
            DiscoveryInterrupted: carrying .found (everything collected so
                far) and .retry_after — nothing found is lost.
        """
        return await self.discovery_engine.search_groups(
            query, limit, pace=pace, max_flood_wait=max_flood_wait, max_offline=max_offline,
            heartbeat=heartbeat, found_callback=found_callback)

    @_reported()
    async def similar_groups(self,
                             seeds,
                             rounds: int = 2,
                             max_resolve: int = 100,
                             pace: float = 2.0,
                             max_flood_wait: int = 3600,
                             max_offline: int = 3600,
                             heartbeat: Optional[Callable] = None,
                             found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        Telegram's "similar channels" recommendations, `rounds` rounds out
        from the seeds — rooms found without any keyword at all, matched by
        shared subscribers.

        Round one resolves the seeds; every later round asks about the
        channel objects the previous round returned, so it costs no username
        lookups. Two rounds by default — a third drifts off topic. Only
        CHANNELS (broadcast or megagroup) can be asked; a basic-group seed is
        skipped with a warning. Yield depends on the account: a Premium
        account got 64 recommendations from one seed; a normal account
        reportedly gets about 10.

        Args:
            seeds: One or a list of '@username', numeric id, or entity
            rounds: How many rounds of recommendations (default 2)
            max_resolve: Username lookups this call may spend on seeds
                (default 100) — lookups are the request Telegram punishes
                hardest, so they are budgeted and never waited out
            pace, max_flood_wait, max_offline, heartbeat, found_callback:
                as in search_groups

        Returns:
            DataFrame in the search_groups shape, FoundVia 'similar', FoundBy
            the seed's '@name' or 'id:N'. Seeds themselves are never rows.
        """
        return await self.discovery_engine.similar_groups(
            seeds, rounds, max_resolve=max_resolve, pace=pace, max_flood_wait=max_flood_wait,
            max_offline=max_offline, heartbeat=heartbeat, found_callback=found_callback)

    @_reported('group_id')
    async def linked_groups(self,
                            group_id,
                            posts: int = 100,
                            resolve: bool = False,
                            max_resolve: int = 100,
                            pace: float = 2.0,
                            max_flood_wait: int = 3600,
                            max_offline: int = 3600,
                            heartbeat: Optional[Callable] = None,
                            found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        Rooms linked (t.me/name, t.me/name/123, t.me/s/name, t.me/boost/name,
        telegram.me/name) from the last `posts` messages of one or more rooms.
        Invite links (t.me/+...) and t.me/c/... are never followed — discovery
        reads, it never joins.

        Args:
            group_id: One or a list of numeric id, '@username', or entity —
                e.g. the GroupIDs a previous call found
            posts: Messages to read per room (default 100)
            resolve: False (default) returns each linked name as a row with
                Username and Identifier only (GroupID and the flags are NA) —
                this costs nothing. True resolves each new name to a full row
                until max_resolve or the first rate-limit wait on lookups,
                then returns the rest unresolved with a warning.
            max_resolve: Username lookups this call may spend (default 100)
            pace, max_flood_wait, max_offline, heartbeat, found_callback:
                as in search_groups

        Returns:
            DataFrame in the search_groups shape, FoundVia 'link', FoundBy the
            source room's '@name' or 'id:N'. Source rooms are never rows.

        Raises:
            DiscoveryInterrupted: when looking up a source room's name must
                wait (lookups are never slept through), or as in search_groups.
        """
        return await self.discovery_engine.linked_groups(
            group_id, posts, resolve, max_resolve=max_resolve, pace=pace,
            max_flood_wait=max_flood_wait, max_offline=max_offline,
            heartbeat=heartbeat, found_callback=found_callback)

    @_reported()
    async def discover_groups(self,
                              seeds=(),
                              queries=(),
                              similar_rounds: int = 2,
                              mine_links: bool = False,
                              link_posts: int = 100,
                              link_sources: int = 50,
                              resolve_links: bool = False,
                              max_resolve: int = 100,
                              pace: float = 2.0,
                              max_flood_wait: int = 3600,
                              max_offline: int = 3600,
                              heartbeat: Optional[Callable] = None,
                              found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        The whole discovery pipeline on one session, deduplicated by id, in
        cost order: similar channels (rounds), then every query, then link
        mining from the first `link_sources` rooms found.

        Args:
            seeds: Seeds for similar_groups (one or a list; may be empty)
            queries: Search strings (one or a list; may be empty) — see
                build_search_queries()
            similar_rounds: Rounds of recommendations (default 2)
            mine_links: Also read the found rooms' posts for t.me links
                (default False)
            link_posts: Posts to read per mined room (default 100)
            link_sources: Rooms to mine, taken in discovery order — seeds
                first, then their neighbourhood — with a warning when the
                bound truncates (default 50)
            resolve_links: Resolve mined names to full rows (default False:
                they come back as Username-only rows, which costs nothing).
                Opt in knowingly — each resolution is one of the request type
                that has earned accounts day-long lookup blocks.
            max_resolve: Username lookups the whole call may spend, seeds and
                links together (default 100)
            pace, max_flood_wait, max_offline, heartbeat, found_callback:
                as in search_groups

        Returns:
            DataFrame in the search_groups shape; FoundVia records the
            cheapest route that found each room ('similar' | 'search' |
            'link') and FoundBy the seed, query, or source room.

        Raises:
            DiscoveryInterrupted: carrying .found and .retry_after when a
                rate-limit wait exceeds max_flood_wait or the network stays
                down past max_offline — nothing found is lost.

        Example:
            df = await tg.discover_groups(
                seeds=["@antalyadaa"],
                queries=build_search_queries(["Анталия", "Antalya"], topics=["чат", "аренда"]),
                mine_links=True, heartbeat=lambda phase: print(phase))
        """
        return await self.discovery_engine.discover_groups(
            seeds, queries, similar_rounds, mine_links, link_posts, link_sources, resolve_links,
            max_resolve, pace=pace, max_flood_wait=max_flood_wait, max_offline=max_offline,
            heartbeat=heartbeat, found_callback=found_callback)

    # ==================== Message Display and Export ====================
    
    def print_messages(self, 
                      df: pd.DataFrame, 
                      limit: Optional[int] = None,
                      max_length: int = 100) -> None:
        """
        Print messages in a readable format.
        
        Args:
            df: DataFrame with messages
            limit: Maximum number of messages to print
            max_length: Maximum message length to display
        """
        if df.empty:
            print("No messages to display")
            return
            
        messages_to_print = df.head(limit) if limit else df
        
        print(f"\n{'='*80}")
        print(f"Displaying {len(messages_to_print)} of {len(df)} messages")
        print(f"{'='*80}\n")
        
        for _, msg in messages_to_print.iterrows():
            print(format_message_for_display(msg, max_length))
            print(f"{'-'*80}")
            
    def filter_messages(self,
                       df: pd.DataFrame,
                       sender_id: Optional[int] = None,
                       username: Optional[str] = None,
                       keyword: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Filter messages by various criteria.
        
        Args:
            df: Messages DataFrame
            sender_id: Filter by sender ID
            username: Filter by username
            keyword: Filter by message content
            start_date: Filter messages after this date
            end_date: Filter messages before this date
            
        Returns:
            Filtered DataFrame
        """
        # Apply filters
        if sender_id or username:
            df = filter_messages_by_sender(df, sender_id, username)
            
        if keyword:
            df = filter_messages_by_content(df, keyword)
            
        if start_date:
            df = df[df['Date'] >= start_date]
            
        if end_date:
            df = df[df['Date'] <= end_date]
            
        return df
        
    def export_messages(self,
                       df: pd.DataFrame,
                       filepath: str,
                       format: str = 'csv') -> None:
        """
        Export messages to file.
        
        Args:
            df: Messages DataFrame
            filepath: Output file path
            format: Export format ('csv', 'json')
        """
        if format.lower() == 'csv':
            export_to_csv(df, filepath)
        elif format.lower() == 'json':
            export_to_json(df, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    # ==================== Statistics and Metrics ====================
    
    def get_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about messages.
        
        Args:
            df: Messages DataFrame
            
        Returns:
            Dictionary with statistics
        """
        return get_message_statistics(df)
        
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current session metrics.
        
        Returns:
            Dictionary with metrics
        """
        health_status = await self.connection_engine.health_check()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'current_group': self.current_group.id if self.current_group else None,
            'connection_health': health_status
        }
                
        return metrics
        
    async def export_metrics(self, filepath: str = "telegram_metrics.json") -> None:
        """
        Export session metrics to file.
        
        Args:
            filepath: Output file path
        """
        metrics = await self.get_metrics()
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        logger.info(f"Exported metrics to {filepath}")
        
    # ==================== Utility Methods ====================
    
    @_reported(success_if=bool)
    async def validate_connection(self) -> bool:
        """
        Validate connection status.

        Still True or False — and on False it says why: a Telegram verdict
        (logged out, banned, restricted, a wait, ...) is logged at WARNING
        with Telegram's name for it and reported as a health event; any other
        failure is logged at ERROR. A False result never counts as recovery.

        Returns:
            True if connection is valid
        """
        return await self.connection_engine.validate_connection()
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        A connection is healthy only when Telegram confirms its session is
        logged in. A logout or a ban it finds is named in 'errors' —
        'logged out (AUTH_KEY_UNREGISTERED)' — and reported as a health event.
        
        Returns:
            Health check results. ['health'] summarises this instance's
            account health events (see health_callback), what this check
            found included: the account's verdict and since when, open waits
            per request type, groups without access, wait and event counts,
            the last unclassified error. JSON-ready.
        """
        # One health call, opened here rather than by @_reported, so the
        # summary is read after it closes: a recovery this check proves is
        # already in it. Only a check that reached Telegram and found every
        # connection logged in counts as one.
        async with self._health.call('health_check') as call:
            status = await self.connection_engine.health_check()
            if not _health_check_passed(status):
                call.failed = True
        status['health'] = self._health.snapshot()
        return status

    def device_identity(self) -> Dict[str, Any]:
        """
        What every connection for this account tells Telegram it is running
        on: device model, system version, app version and language codes.
        Computed locally — no network, no session file.

        Without `device_model` / `system_version` / `app_version` /
        `lang_code` / `system_lang_code` in the config, Telethon derives them
        from the machine and its own version, so the same account presents a
        different device on another machine and after a Telethon upgrade.
        To pin it, paste `config_lines` into the account's [Telegram] section;
        it applies from the next connection, without logging in again.

        Returns:
            {'presented': {field: value}, 'pinned': [fields set in the config],
             'config_lines': ready-to-paste lines pinning what is presented now}

        Example:
            print(TgData("config.ini").device_identity()['config_lines'])
        """
        return self.connection_engine.device_identity()

    @_reported()
    async def get_read_budget(self):
        """Current authenticated account's ReadBudgetStatus, or None if disabled.

        No connection is opened when disabled. Enabled budgets verify the
        account using Telegram's self response before reading the ledger.
        """
        budget = self.connection_engine.read_budget
        if budget is None:
            return None
        client = await self.connection_engine.get_client()
        return budget.status(await client._read_budget_account())

    @_reported('group_id')
    async def download_media_by_id(self,
                             group_id: Union[int, str],
                             message_ids: Union[int, List[int]],
                             output_dir: Optional[str] = None) -> Dict[int, Any]:
        """
        Download media attached to specific messages, on demand.

        Pairs with the reference columns from get_messages (MediaType, GroupedId,
        ChatId, MessageId): fetch references cheaply, then download only the
        listings you keep. For a multi-photo album, pass every MessageId that
        shares a GroupedId.

        Args:
            group_id: Target group id or '@username'
            message_ids: A single MessageId, or a list of them
            output_dir: Directory to save files into; if None, returns raw bytes

        Returns:
            {message_id: filepath | bytes | None}  (None = no downloadable media)

        Example:
            df = await tg.get_messages(group_id=gid, limit=50)
            keep = df[df['MediaType'] == 'photo']
            paths = await tg.download_media_by_id(gid, keep['MessageId'].tolist(), output_dir="photos")
        """
        return await self.message_engine.download_media_by_id(
            group_id=group_id,
            message_ids=message_ids,
            output_dir=output_dir
        )

    def save_photos(self, df: pd.DataFrame, output_dir: str) -> None:
        """
        Save profile photos from messages.
        
        Args:
            df: Messages DataFrame with PhotoData
            output_dir: Directory to save photos
        """
        save_profile_photos(df, output_dir)
        
    async def close(self) -> None:
        """Close all connections."""
        try:
            await self.connection_engine.close()
        finally:
            await _retire_notifications(self._account_health.values())
        logger.info("TgData closed")
        
    # ==================== Polling and Real-time Updates ====================
    
    def on_new_message(self, group_id: Optional[Union[int, str]] = None):
        """
        Decorator to register a handler for new messages in real-time.
        Uses Telethon's event system.
        
        Args:
            group_id: Optional group ID or username (e.g., '@channelname') to filter messages. If None, receives from all groups.
            
        Example:
            @tg.on_new_message(group_id=12345)
            async def handler(event):
                print(f"New message: {event.message.text}")
        """
        from telethon import events
        
        def decorator(func):
            # Store the handler function for later registration
            if not hasattr(self, '_pending_handlers'):
                self._pending_handlers = []
            
            self._pending_handlers.append((func, group_id))
            logger.info(f"Queued handler for group {group_id or 'all groups'}")
            
            return func
        
        return decorator
    
    async def _register_pending_handlers(self):
        """Register all pending event handlers"""
        if not hasattr(self, '_pending_handlers'):
            return
            
        from telethon import events
        client = await self.connection_engine.get_client()
        
        for func, group_id in self._pending_handlers:
            def make_safe_handler(f):
                # Plain factory: binds f per iteration (avoids the loop-closure
                # capture gotcha). Filtering is done ENTIRELY by Telethon's
                # chats= filter below — it correctly handles numeric ids and
                # @usernames; no manual re-check (see devdocs/scoped/7).
                async def safe_handler(event):
                    try:
                        await f(event)
                    except Exception:
                        logger.exception(f"Unhandled error in message handler {getattr(f, '__name__', f)}")
                return safe_handler
            
            handler = make_safe_handler(func)
            
            if group_id:
                client.add_event_handler(handler, events.NewMessage(chats=group_id))
            else:
                client.add_event_handler(handler, events.NewMessage())
            
            logger.info(f"Registered handler for group {group_id or 'all groups'}")
        
        self._pending_handlers.clear()
    
    @_reported('group_id', recover=False)
    async def poll_for_messages(self, 
                               group_id: Union[int, str],
                               interval: int = 60,
                               after_id: int = 0,
                               callback: Optional[Callable] = None,
                               max_iterations: Optional[int] = None) -> None:
        """
        Poll for new messages at specified intervals.

        A failure polling again cannot fix ends the polling with that error
        (the same exception object): the account is logged out, banned or
        restricted, it cannot read this group (CHANNEL_PRIVATE,
        GroupAccessError, ...), the session is not logged in
        (AuthRequiredError) or the proxy setting is unusable
        (ProxyConfigError). Any other failure — the network, a rate-limit
        wait, a server error — is logged and retried at the next interval.
        An exception raised by `callback` propagates, like batch_callback's.
        
        Args:
            group_id: Group ID or username (e.g., '@channelname') to poll messages from
            interval: Polling interval in seconds (default: 60)
            after_id: Message ID to start polling after (default: 0)
            callback: Optional async callback function to process new messages
            max_iterations: Maximum number of polling iterations (None = infinite)
            
        Example:
            async def process_messages(messages_df):
                print(f"Got {len(messages_df)} new messages")
                
            await tg.poll_for_messages(
                group_id=12345,
                interval=30,
                callback=process_messages
            )
        """
        logger.info(f"Starting polling for group {group_id} with interval {interval}s")
        
        current_after_id = after_id
        iterations = 0
        seen_message_ids = set()  # Track all message IDs we've already processed
        
        while max_iterations is None or iterations < max_iterations:
            # Get new messages since last check
            logger.info(f"Poll iteration {iterations + 1}: Checking for messages after ID {current_after_id}")
            budget_stop = None
            try:
                new_messages = await self.get_messages(
                    group_id=group_id,
                    after_id=current_after_id
                )
            except ReadBudgetExceeded as e:
                budget_stop = e
                new_messages = e.partial_result if isinstance(e.partial_result, pd.DataFrame) else pd.DataFrame()
            except Exception as e:
                if _polling_cannot_recover(e):
                    logger.error(f"Polling {group_id} stopped: {e}")
                    raise
                logger.error(f"Error during polling: {e}")
                iterations += 1  # Increment even on error to respect max_iterations
                
                # Continue polling after error (unless we've reached max iterations)
                if max_iterations is None or iterations < max_iterations:
                    await asyncio.sleep(interval)
                continue
            
            if not new_messages.empty:
                # Get all message IDs and filter out already seen ones
                all_message_ids = new_messages['MessageId'].tolist()
                new_message_ids = [msg_id for msg_id in all_message_ids if msg_id not in seen_message_ids]
                
                if new_message_ids:
                    # Filter DataFrame to only include truly new messages
                    truly_new_messages = new_messages[new_messages['MessageId'].isin(new_message_ids)]
                    
                    # Add new IDs to seen set
                    seen_message_ids.update(new_message_ids)
                    
                    # Simply update to the maximum ID we've seen
                    max_id = max(all_message_ids)
                    logger.info(f"Poll iteration {iterations + 1}: Found {len(truly_new_messages)} new messages, IDs: {sorted(new_message_ids)}")
                    logger.info(f"Updating after_id from {current_after_id} to {max_id}")
                    current_after_id = max_id
                    
                    # Call the callback only with truly new messages — an
                    # exception in it propagates instead of losing them silently
                    if callback:
                        await callback(truly_new_messages)
                else:
                    # All messages were duplicates, but still update after_id to the max
                    max_id = max(all_message_ids)
                    logger.info(f"Poll iteration {iterations + 1}: Found {len(new_messages)} messages but all were duplicates")
                    logger.info(f"Updating after_id from {current_after_id} to {max_id}")
                    current_after_id = max_id
            else:
                logger.debug(f"Poll iteration {iterations + 1}: No new messages")

            if budget_stop is not None:
                raise budget_stop
            
            iterations += 1
            
            # Wait for next interval (unless this is the last iteration)
            if max_iterations is None or iterations < max_iterations:
                await asyncio.sleep(interval)
    
    @_reported()
    async def run_with_event_loop(self):
        """
        Run the Telegram client with event loop to handle real-time events.
        This method blocks until disconnected.
        
        Example:
            tg = TgData()
            
            @tg.on_new_message()
            async def handler(event):
                print(f"New message: {event.message.text}")
                
            await tg.run_with_event_loop()
        """
        # Register any pending handlers first
        await self._register_pending_handlers()
        
        client = await self.connection_engine.get_client()
        logger.info("Running with event loop. Press Ctrl+C to stop...")
        await client.run_until_disconnected()
        
    # ==================== Context Manager Support ====================
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Example usage
if __name__ == "__main__":
    async def main():
        # Simple usage
        tg = TgData()
        
        # List groups
        groups = await tg.list_groups()
        print(f"Found {len(groups)} groups")
        
        if not groups.empty:
            # Select first group
            group_id = groups.iloc[0]['GroupID']
            tg.set_group(group_id)
            
            # Get recent messages with progress
            messages = await tg.get_messages(
                limit=100,
                with_progress=True
            )
            
            # Display messages
            tg.print_messages(messages, limit=10)
            
            # Get statistics
            stats = tg.get_statistics(messages)
            print(f"\nStatistics: {stats}")
            
            # Export
            tg.export_messages(messages, "messages.csv")
            
    asyncio.run(main())
