"""
Group discovery engine for Telegram.

Finds groups and channels three ways — Telegram's global NAME search, its
"similar channels" recommendations, and t.me links in a room's recent posts —
and returns them in the list_groups row shape, deduplicated by id, paced,
and flood-safe. Every room returned is already usable by get_messages:
Telethon writes each result into the session cache with its access hash
(observed live, devdocs/scoped/10).

Two rules, learned the hard way on a production account:

  1. Never resolve a username you already hold as an object. Round two of
     "similar" reuses the Channel objects round one returned.
  2. Never sleep on a username resolution — it is the request Telegram
     punishes hardest (8 h and 21 h blocks). Resolution is budgeted
     (max_resolve), and a wait on it is skipped or stopped, never waited out.

Everything else the engine does is paced (`pace` seconds after each request),
obeys flood waits exactly and visibly (per-call threshold 0 + a beating
sleep; reading posts for links and the dialog sync for a numeric id keep
Telethon's own silent sleeps of up to a minute), waits for a dropped
connection to come back, and never loses what it has found: an interruption
raises DiscoveryInterrupted carrying `.found`.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

import pandas as pd
from telethon import functions
from telethon import utils as tl_utils
from telethon.errors import RPCError
from telethon.tl import types as tl_types

from . import health
from .connection_engine import ConnectionEngine
from .health import WAIT_ERRORS as _WAIT_ERRORS
from .message_engine import MessageEngine, GroupAccessError
from .models import GroupInfo

logger = logging.getLogger(__name__)

DEFAULT_PACE_S = 2.0             # after every network request — the proven personal-account pace
DEFAULT_MAX_FLOOD_WAIT_S = 3600  # a longer mandated wait raises DiscoveryInterrupted
DEFAULT_MAX_OFFLINE_S = 3600     # how long to wait for the network to come back before giving up
DEFAULT_LINK_SOURCES = 50        # rooms mined for links per discover_groups call
DEFAULT_MAX_RESOLVE = 100        # username resolutions per call — the punished request
SEARCH_LIMIT = 100               # Telegram caps lower; ask for the most
LINK_POSTS = 100                 # posts read per room when mining links
SIMILAR_ROUNDS = 2               # a third round drifts out of the topic
NET_ERRORS = (ConnectionError, OSError, asyncio.TimeoutError, asyncio.IncompleteReadError)
# _WAIT_ERRORS (from health.WAIT_ERRORS): every wait Telethon's own sleep branch
# handles (UserMethods._call). Discovery sends with a per-call flood threshold
# of 0, so Telethon never sleeps for it and it must handle all of them itself —
# every one carries .seconds.
COLUMNS = ['GroupID', 'Title', 'Username', 'Identifier', 'IsChannel', 'IsMegagroup',
           'ParticipantsCount', 'FoundVia', 'FoundBy']

# t.me/<name>, t.me/<name>/123, t.me/s/<name> (web preview), t.me/boost/<name>,
# telegram.me/<name>. Usernames are 5–32 characters starting with a letter.
# t.me/+invite and t.me/c/<id> never match; reserved paths are filtered after.
TME_LINK = re.compile(
    r"(?:t\.me|telegram\.me)/(?:s/|boost/)?([A-Za-z][A-Za-z0-9_]{4,31})(?![A-Za-z0-9_])", re.I)
RESERVED_PATHS = {"joinchat", "addstickers", "addemoji", "addtheme", "share", "proxy",
                  "socks", "setlanguage", "confirmphone", "login", "invoice", "boost",
                  "giftcode", "addlist", "contact", "premium", "settings"}


class DiscoveryInterrupted(RuntimeError):
    """The run could not continue: Telegram demanded a wait longer than
    max_flood_wait, the network stayed down past max_offline, or — in
    linked_groups — looking up a source room's name must wait. Lookups are
    never slept through, so in that case retry_after can be below
    max_flood_wait.

    Nothing found so far is lost: ``.found`` is the DataFrame collected up
    to the interruption, ``.retry_after`` the seconds Telegram asked for
    (0 for a network give-up)."""

    def __init__(self, message: str, found: pd.DataFrame, retry_after: int):
        super().__init__(message)
        self.found = found
        self.retry_after = retry_after


class _BudgetExhausted(Exception):
    """Internal: a username resolution would exceed max_resolve."""


@dataclass
class _State:
    """Bookkeeping shared by the operations of one public call."""
    beat: Callable[[str], None]
    pace: float = DEFAULT_PACE_S
    max_flood_wait: int = DEFAULT_MAX_FLOOD_WAIT_S
    max_offline: int = DEFAULT_MAX_OFFLINE_S
    max_resolve: int = DEFAULT_MAX_RESOLVE
    found_callback: Optional[Callable] = None
    seen: set = field(default_factory=set)          # marked peer id, or '@name' while unresolved
    rows: list = field(default_factory=list)        # row dicts in discovery order
    entities: dict = field(default_factory=dict)    # key -> entity, so link mining uses objects
    resolved: int = 0                               # resolutions spent so far
    resolve_stopped: bool = False                   # first wait or the cap: no more resolving


class DiscoveryEngine:
    """
    Handles group discovery on the persistent connection.
    """

    def __init__(self, connection_engine: ConnectionEngine):
        self.connection_engine = connection_engine

    # ------------------------------------------------------------ helpers --

    @staticmethod
    def _make_beat(heartbeat: Optional[Callable]) -> Callable[[str], None]:
        """The same exception-safe liveness closure fetch_messages uses."""
        def _beat(phase: str) -> None:
            if heartbeat is not None:
                try:
                    heartbeat(phase)
                except Exception:  # noqa: BLE001 — a broken callback never kills a run
                    pass
        return _beat

    def _new_state(self, heartbeat, pace, max_flood_wait, max_offline, max_resolve,
                   found_callback) -> _State:
        return _State(beat=self._make_beat(heartbeat), pace=float(pace),
                      max_flood_wait=int(max_flood_wait), max_offline=int(max_offline),
                      max_resolve=int(max_resolve), found_callback=found_callback)

    @staticmethod
    def _frame(rows: List[dict]) -> pd.DataFrame:
        """Always the fixed columns (an empty result still has every one),
        with nullable dtypes so resolved and unresolved rows share one dtype
        per column."""
        df = pd.DataFrame(rows, columns=COLUMNS)
        df['GroupID'] = df['GroupID'].astype('Int64')
        df['ParticipantsCount'] = df['ParticipantsCount'].astype('Int64')
        df['IsChannel'] = df['IsChannel'].astype('boolean')
        df['IsMegagroup'] = df['IsMegagroup'].astype('boolean')
        return df

    @staticmethod
    def _key(entity_or_name) -> str:
        """Dedup key: Telethon's MARKED peer id for an entity (a basic group
        and a channel can never collide), else the lowercased @username.
        GroupID in the row stays the bare id, as in list_groups."""
        if hasattr(entity_or_name, 'id'):
            return str(tl_utils.get_peer_id(entity_or_name))
        return f"@{str(entity_or_name).lstrip('@').lower()}"

    @staticmethod
    def _token(entity) -> str:
        """How a room is named in FoundBy: '@name' when it has one, else 'id:N'."""
        username = getattr(entity, 'username', None)
        return f"@{username}" if username else f"id:{entity.id}"

    @staticmethod
    def _unresolved_row(username: str, by: str) -> dict:
        """A linked room whose name was not resolved: id and flags unknown."""
        return {'GroupID': pd.NA, 'Title': None,
                'Username': f"@{username}", 'Identifier': f"@{username}",
                'IsChannel': pd.NA, 'IsMegagroup': pd.NA, 'ParticipantsCount': pd.NA,
                'FoundVia': 'link', 'FoundBy': by}

    @staticmethod
    def _as_list(value) -> list:
        if value is None:
            return []
        if isinstance(value, (str, int, tl_types.Channel, tl_types.Chat)):
            return [value]
        return list(value)

    @staticmethod
    async def _notify(st: _State, row: dict) -> None:
        """found_callback(row) for every new row, sync or async. Like
        batch_callback in fetch_messages, an exception here propagates."""
        if st.found_callback is None:
            return
        result = st.found_callback(dict(row))
        if inspect.isawaitable(result):
            await result

    async def _add(self, st: _State, entity, via: str, by: str) -> bool:
        """Append a row for a Channel/Chat whose key is new; first discovery
        wins, so FoundVia records the cheapest route. Forbidden objects and
        anything else are skipped."""
        if not isinstance(entity, (tl_types.Channel, tl_types.Chat)):
            return False
        key = self._key(entity)
        if key in st.seen:
            return False
        st.seen.add(key)
        st.entities[key] = entity
        row = GroupInfo.from_entity(entity).to_dict()
        row['FoundVia'] = via
        row['FoundBy'] = by
        st.rows.append(row)
        await self._notify(st, row)
        return True

    async def _pause(self, st: _State) -> None:
        if st.pace > 0:
            st.beat("pause")
            await asyncio.sleep(st.pace)

    @staticmethod
    async def _sleep_beating(seconds: float, beat: Callable[[str], None], phase: str) -> None:
        """Sleep in ten-second slices that beat with the remaining time."""
        left = float(seconds)
        while left > 0:
            beat(f"{phase} {int(left)}s")
            step = min(10.0, left)
            await asyncio.sleep(step)
            left -= step

    async def _wait_for_network(self, client, st: _State) -> None:
        """Block until Telegram answers again, beating, up to max_offline.

        A sleeping laptop drops the socket and Telethon stops reconnecting on
        its own after a few tries; every request here is idempotent, so the
        caller simply retries once this returns. Past max_offline the run
        gives up WITH everything it has found."""
        waited = 0
        while True:
            try:
                if not client.is_connected():
                    await client.connect()
                await client.get_me()
                logger.info(f"Connection is back after {waited // 60} min — continuing")
                return
            except Exception:  # noqa: BLE001 — still down
                if waited >= st.max_offline:
                    raise DiscoveryInterrupted(
                        f"No connection to Telegram for {waited // 60} min "
                        f"(max_offline={st.max_offline}); {len(st.rows)} rooms found so far",
                        self._frame(st.rows), 0)
                if waited % 600 == 0:
                    logger.warning(f"No connection to Telegram — waiting ({waited // 60} min so far)")
                st.beat(f"reconnecting {waited // 60}min")
                await asyncio.sleep(30)
                waited += 30

    async def _request(self, client, request, st: _State, phase: str):
        """One raw request with EVERY wait surfaced: sent with a per-call
        flood threshold of 0, so Telethon never sleeps silently (Telethon's
        own __call__ ignores a per-call threshold; every client tgdata builds
        honours it — connection_engine._PerCallFloodThreshold). Every kind of
        wait Telethon would have slept is handled here (_WAIT_ERRORS). A wait
        within max_flood_wait is slept in beating slices and the same
        request retried; a longer one raises DiscoveryInterrupted with
        everything found so far. A transport failure waits for the network
        and retries the same request."""
        while True:
            try:
                st.beat(phase)
                return await client(request, flood_sleep_threshold=0)
            except _WAIT_ERRORS as e:
                name = type(request).__name__
                if e.seconds > st.max_flood_wait:
                    raise DiscoveryInterrupted(
                        f"Telegram wants a {e.seconds}s wait on {name} "
                        f"(max_flood_wait={st.max_flood_wait}); {len(st.rows)} rooms found so far",
                        self._frame(st.rows), e.seconds) from e
                logger.warning(f"FloodWait {e.seconds}s on {name} — waiting, then retrying")
                await health.report(e, 'handled')
                await self._sleep_beating(e.seconds, st.beat, "flood-wait")
            except NET_ERRORS as e:
                logger.warning(f"Connection lost during {type(request).__name__} "
                               f"({type(e).__name__}) — waiting for the network")
                await self._wait_for_network(client, st)

    async def _resolve(self, client, ref, st: _State):
        """A seed or a mined name -> a full Channel/Chat, WITHOUT ever sleeping
        on ResolveUsername and WITHOUT touching the shared client's flood
        threshold (a real-time handler or a concurrent fetch on the same
        client keeps its own behaviour).

        Entities pass through untouched. Otherwise the session cache is read
        directly (pure, no network). On a miss, a STRING sends ResolveUsername
        through the per-call path with threshold 0 — never through _request,
        and honoured because tgdata's clients make that per-call threshold
        work (connection_engine._PerCallFloodThreshold) — so a wait (any of
        _WAIT_ERRORS) propagates unslept for the caller to skip or stop on,
        and it counts against max_resolve; an INT uses the message engine's
        dialog-sync fallback, so GroupAccessError keeps its meaning (that sync
        is Telethon's own: a wait of up to a minute there is slept, silently).
        A cached peer becomes the full object by id + access hash
        (GetChannels / GetChats), which beats and carries no resolution risk."""
        if isinstance(ref, (tl_types.Channel, tl_types.Chat)):
            return ref
        if isinstance(ref, str):
            ref = ref.strip()
            if ref.lstrip('-').isdigit():
                ref = int(ref)
        st.beat("resolve")
        try:
            peer = client.session.get_input_entity(ref)     # cache only; ValueError = never seen
        except ValueError:
            peer = None
        if peer is None:
            if isinstance(ref, int):
                # the message engine's fallback, shared across engines on purpose
                return await MessageEngine._entity_after_dialog_sync(client, ref, st.beat)
            if st.resolved >= st.max_resolve:
                raise _BudgetExhausted(ref)
            name = str(ref).lstrip('@')
            st.resolved += 1
            r = await client(functions.contacts.ResolveUsernameRequest(username=name),
                             flood_sleep_threshold=0)        # NOT _request: a wait here is never slept
            entity = next((c for c in r.chats if isinstance(c, (tl_types.Channel, tl_types.Chat))), None)
            if entity is None:
                raise ValueError(f"{ref!r} is not a group or channel")
            return entity
        if isinstance(peer, tl_types.InputPeerChannel):
            r = await self._request(client, functions.channels.GetChannelsRequest(
                id=[tl_utils.get_input_channel(peer)]), st, "resolve")
        elif isinstance(peer, tl_types.InputPeerChat):
            r = await self._request(client, functions.messages.GetChatsRequest(
                id=[peer.chat_id]), st, "resolve")
        else:
            raise ValueError(f"{ref!r} is a user, not a group or channel")
        if not r.chats:
            raise ValueError(f"{ref!r} could not be fetched")
        return r.chats[0]

    # --------------------------------------------------------- operations --

    async def _search(self, client, st: _State, query: str, limit: int) -> None:
        """Telegram's global search: names and @usernames only, never post text."""
        try:
            r = await self._request(client, functions.contacts.SearchRequest(q=query, limit=limit),
                                    st, "search")
        except RPCError as e:                       # an empty or too-short query, for instance
            logger.warning(f"Search {query!r} failed ({type(e).__name__}) — skipped")
            await health.report(e, 'swallowed')
            await self._pause(st)
            return
        new = 0
        for chat in r.chats:
            if await self._add(st, chat, 'search', query):
                new += 1
        logger.info(f"search {query!r}: {len(r.chats)} rooms, {new} new")
        await self._pause(st)

    async def _similar(self, client, st: _State, seeds: list, rounds: int) -> None:
        """Telegram's 'similar channels', `rounds` rounds out from the seeds.
        Round one resolves the seeds; every later round asks about the
        Channel objects the previous round returned, so it costs no lookups."""
        layer: list = []
        for seed in seeds:
            try:
                entity = await self._resolve(client, seed, st)
            except _WAIT_ERRORS as e:
                logger.warning(f"Seed {seed!r} skipped — Telegram wants {e.seconds}s on username lookups")
                await health.report(e, 'swallowed', group=seed)
                continue
            except _BudgetExhausted:
                logger.warning(f"Seed {seed!r} skipped — resolution budget exhausted (max_resolve={st.max_resolve})")
                continue
            except (ValueError, TypeError, GroupAccessError, RPCError) as e:
                logger.warning(f"Seed {seed!r} skipped ({type(e).__name__}: {e})")
                await health.report(e, 'swallowed', group=seed)
                continue
            if not isinstance(entity, tl_types.Channel):
                logger.warning(f"Seed {seed!r} is a basic group — Telegram only recommends similar CHANNELS; skipped")
                continue
            key = self._key(entity)
            st.seen.add(key)                        # a seed is never returned as a find
            st.entities.setdefault(key, entity)
            layer.append(entity)
            await self._pause(st)

        for round_no in range(1, rounds + 1):
            if not layer:
                break
            next_layer: list = []
            for entity in layer:
                by = self._token(entity)
                try:
                    r = await self._request(
                        client, functions.channels.GetChannelRecommendationsRequest(channel=entity),
                        st, "similar")
                except (RPCError, TypeError) as e:  # a private channel, a min object, ...
                    logger.warning(f"similar: {by} skipped ({type(e).__name__})")
                    await health.report(e, 'swallowed', group=entity)
                    await self._pause(st)
                    continue
                new = 0
                for chat in r.chats:
                    if await self._add(st, chat, 'similar', by):
                        next_layer.append(chat)
                        new += 1
                logger.info(f"similar round {round_no}: {by} -> {len(r.chats)} recommended, {new} new")
                await self._pause(st)
            layer = next_layer

    @staticmethod
    def _link_sources_of(m) -> List[str]:
        """Every string in a message that can carry a t.me link: the visible
        text, the URL behind each hyperlinked span (MessageEntityTextUrl —
        where channels put nearly all their links; 87 of 100 posts in one
        news channel, none in the visible text), and URL buttons."""
        out = [m.message] if m.message else []
        for e in (m.entities or []):
            url = getattr(e, 'url', None)          # MessageEntityTextUrl
            if url:
                out.append(url)
        rows = getattr(m.reply_markup, 'rows', None) if m.reply_markup else None
        for row in rows or []:
            for button in getattr(row, 'buttons', []) or []:
                url = getattr(button, 'url', None)  # KeyboardButtonUrl
                if url:
                    out.append(url)
        return out

    async def _mine_room(self, client, entity, posts: int, st: _State) -> List[str]:
        """Usernames linked from a room's last `posts` messages — visible text,
        hyperlink entities and URL buttons — in order of first appearance,
        minus reserved paths, bots (a username ending in 'bot' is never a
        room and would waste a resolution) and the room's own name."""
        while True:
            try:
                st.beat("links")
                texts = []
                async for m in client.iter_messages(entity, limit=posts):
                    texts.extend(self._link_sources_of(m))
                break
            except _WAIT_ERRORS as e:
                if e.seconds > st.max_flood_wait:
                    raise DiscoveryInterrupted(
                        f"Telegram wants a {e.seconds}s wait while reading posts "
                        f"(max_flood_wait={st.max_flood_wait}); {len(st.rows)} rooms found so far",
                        self._frame(st.rows), e.seconds) from e
                logger.warning(f"FloodWait {e.seconds}s while reading posts — waiting, then retrying")
                await health.report(e, 'handled')
                await self._sleep_beating(e.seconds, st.beat, "flood-wait")
            except NET_ERRORS as e:
                logger.warning(f"Connection lost while reading posts ({type(e).__name__}) — waiting for the network")
                await self._wait_for_network(client, st)
        own = (getattr(entity, 'username', None) or '').lower()
        names, local = [], set()
        for text in texts:
            for name in TME_LINK.findall(text):
                low = name.lower()
                if low in RESERVED_PATHS or low == own or low in local or low.endswith('bot'):
                    continue
                local.add(low)
                names.append(name)
        return names

    async def _links(self, client, st: _State, sources: list, posts: int, resolve: bool) -> None:
        """Link mining over `sources` (entities). Unresolved names become rows
        with only Username/Identifier; with resolve=True each new name is
        resolved until max_resolve or the first flood wait, then the rest are
        returned unresolved — the finder's 'abandon the mined tail' rule as a
        return value instead of a lost list."""
        for entity in sources:
            by = self._token(entity)
            try:
                names = await self._mine_room(client, entity, posts, st)
            except RPCError as e:
                logger.warning(f"links: {by} skipped ({type(e).__name__})")
                await health.report(e, 'swallowed', group=entity)
                await self._pause(st)
                continue
            new = 0
            for name in names:
                key = self._key(name)
                if key in st.seen:
                    continue
                if resolve and not st.resolve_stopped:
                    try:
                        target = await self._resolve(client, name, st)
                    except _WAIT_ERRORS as e:
                        st.resolve_stopped = True
                        logger.warning(
                            f"Stopped resolving links — Telegram wants {e.seconds}s on username lookups; "
                            f"the remaining links are returned unresolved (Username only)")
                        await health.report(e, 'swallowed', group=name)
                    except _BudgetExhausted:
                        st.resolve_stopped = True
                        logger.warning(
                            f"Stopped resolving links at the {st.max_resolve}-username bound; the remaining "
                            f"links are returned unresolved — pass max_resolve=... to resolve more")
                    except (ValueError, RPCError) as e:     # not a room, or a dead name
                        logger.debug(f"links: {name} dropped ({type(e).__name__})")
                        await health.report(e, 'swallowed', group=name)
                        st.seen.add(key)
                        continue
                    else:
                        st.seen.add(key)
                        if await self._add(st, target, 'link', by):
                            new += 1
                        await self._pause(st)
                        continue
                st.seen.add(key)
                row = self._unresolved_row(name, by)
                st.rows.append(row)
                await self._notify(st, row)
                new += 1
            logger.info(f"links: {by} -> {len(names)} linked rooms, {new} new")
            await self._pause(st)

    # ---------------------------------------------------------- public API --

    async def search_groups(self, query: str, limit: int = SEARCH_LIMIT, *,
                            pace: float = DEFAULT_PACE_S,
                            max_flood_wait: int = DEFAULT_MAX_FLOOD_WAIT_S,
                            max_offline: int = DEFAULT_MAX_OFFLINE_S,
                            heartbeat: Optional[Callable] = None,
                            found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """Telegram's global search for groups and channels matching `query`
        by NAME or @username (never by post content). See TgData.search_groups."""
        st = self._new_state(heartbeat, pace, max_flood_wait, max_offline, DEFAULT_MAX_RESOLVE, found_callback)
        async with self.connection_engine.session() as client:
            await self._search(client, st, query, limit)
        logger.info(f"search_groups: {len(st.rows)} rooms")
        return self._frame(st.rows)

    async def similar_groups(self, seeds, rounds: int = SIMILAR_ROUNDS, *,
                             max_resolve: int = DEFAULT_MAX_RESOLVE,
                             pace: float = DEFAULT_PACE_S,
                             max_flood_wait: int = DEFAULT_MAX_FLOOD_WAIT_S,
                             max_offline: int = DEFAULT_MAX_OFFLINE_S,
                             heartbeat: Optional[Callable] = None,
                             found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """Telegram's 'similar channels' recommendations, `rounds` rounds out
        from the seeds. See TgData.similar_groups."""
        st = self._new_state(heartbeat, pace, max_flood_wait, max_offline, max_resolve, found_callback)
        async with self.connection_engine.session() as client:
            await self._similar(client, st, self._as_list(seeds), rounds)
        logger.info(f"similar_groups: {len(st.rows)} rooms")
        return self._frame(st.rows)

    async def linked_groups(self, group_id, posts: int = LINK_POSTS, resolve: bool = False, *,
                            max_resolve: int = DEFAULT_MAX_RESOLVE,
                            pace: float = DEFAULT_PACE_S,
                            max_flood_wait: int = DEFAULT_MAX_FLOOD_WAIT_S,
                            max_offline: int = DEFAULT_MAX_OFFLINE_S,
                            heartbeat: Optional[Callable] = None,
                            found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """Rooms linked (t.me/...) from the last `posts` messages of one or
        more rooms. See TgData.linked_groups."""
        st = self._new_state(heartbeat, pace, max_flood_wait, max_offline, max_resolve, found_callback)
        async with self.connection_engine.session() as client:
            sources = []
            for ref in self._as_list(group_id):
                try:
                    entity = await self._resolve(client, ref, st)
                except _WAIT_ERRORS as e:
                    raise DiscoveryInterrupted(
                        f"Telegram wants a {e.seconds}s wait to resolve {ref!r}",
                        self._frame(st.rows), e.seconds) from e
                except _BudgetExhausted:
                    raise ValueError(f"cannot resolve {ref!r}: max_resolve={max_resolve} exhausted")
                key = self._key(entity)
                st.seen.add(key)                    # a source is never returned as a find
                st.entities.setdefault(key, entity)
                sources.append(entity)
            await self._links(client, st, sources, posts, resolve)
        logger.info(f"linked_groups: {len(st.rows)} rooms")
        return self._frame(st.rows)

    async def discover_groups(self, seeds=(), queries=(), similar_rounds: int = SIMILAR_ROUNDS,
                              mine_links: bool = False, link_posts: int = LINK_POSTS,
                              link_sources: int = DEFAULT_LINK_SOURCES,
                              resolve_links: bool = False,
                              max_resolve: int = DEFAULT_MAX_RESOLVE, *,
                              pace: float = DEFAULT_PACE_S,
                              max_flood_wait: int = DEFAULT_MAX_FLOOD_WAIT_S,
                              max_offline: int = DEFAULT_MAX_OFFLINE_S,
                              heartbeat: Optional[Callable] = None,
                              found_callback: Optional[Callable] = None) -> pd.DataFrame:
        """The whole pipeline on one session, in cost order: similar (rounds),
        then every query, then link mining from the first `link_sources` rooms
        found. See TgData.discover_groups."""
        st = self._new_state(heartbeat, pace, max_flood_wait, max_offline, max_resolve, found_callback)
        seeds = self._as_list(seeds)
        queries = [queries] if isinstance(queries, str) else list(queries or [])
        async with self.connection_engine.session() as client:
            if seeds:
                await self._similar(client, st, seeds, similar_rounds)
            for query in queries:
                await self._search(client, st, query, SEARCH_LIMIT)
            if mine_links:
                sources = list(st.entities.values())          # discovery order: seeds, similar, search
                if len(sources) > link_sources:
                    logger.warning(
                        f"Mining links from the first {link_sources} of {len(sources)} rooms found; "
                        f"pass link_sources=... to mine more")
                    sources = sources[:link_sources]
                await self._links(client, st, sources, link_posts, resolve_links)
        logger.info(f"discover_groups: {len(st.rows)} rooms "
                    f"({st.resolved} username resolutions spent of {st.max_resolve})")
        return self._frame(st.rows)
