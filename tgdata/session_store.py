"""
Sessions kept by a store instead of a .session file (issue #5).

Pass one object to TgData(..., session_store=store), and every client of the
account keeps its Telegram session there instead of in a .session file:

    load(name) -> str | None    the saved session, or None when there is none yet
    save(name, data: str)       keep it — as text: the string is opaque
    delete(name)                optional: called when Telethon logs the account out

The methods are plain functions, called on the event loop, so they should
return quickly: a local database, or an in-memory cache that writes behind.
Encrypting the string, if wanted, is the store's business.

StoredSession is Telethon's in-memory session — which already does all the
session work — plus:
  - it loads its state from the store when built, and raises if it cannot,
    so a store that fails never looks like a session that was never logged
    in (that decides whether a login code may be requested);
  - it saves whenever Telethon saves (connect, a data-centre switch, a new
    auth key, once a minute while connected) and at close;
  - it keeps only what a restart needs: groups and channels with their
    access hashes, and the account's own rows — never message senders;
  - it never overwrites a login it did not load or make;
  - a failed save is logged without the error's text, which may quote the
    session: the account's login key.
"""

from __future__ import annotations

import base64
import datetime
import json
import logging
from typing import Optional

from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
from telethon.tl import types

logger = logging.getLogger(__name__)

FORMAT = 1
_PREFIX = f"{FORMAT}:"


def _ordered(rows):
    """Rows in one stable order. Rows mix text and None — a room cached once
    with its username and once without — so they are ordered by their JSON
    text, never compared directly."""
    return sorted(rows, key=json.dumps)


def _timestamp(value) -> float:
    """An update state's date as seconds. Telethon's connect() reads the
    account's state date back as a datetime, so it is always stored."""
    if isinstance(value, datetime.datetime):
        return value.timestamp()
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


class StoredSession(MemorySession):
    """A Telethon session kept by a session store (see the module docstring)."""

    def __init__(self, store, name: str):
        super().__init__()
        self._store = store
        self._name = name
        self._synced: Optional[str] = None          # the string last loaded from or written to the store
        self._synced_key: Optional[bytes] = None    # the login key in it
        self._warned = False
        data = store.load(name)                     # a store error propagates as itself
        if data is not None:
            self._restore(data)
            self._synced, self._synced_key = data, self._key_bytes()

    # -- what is kept ---------------------------------------------------------

    def _entity_to_row(self, e):
        # Message senders are read from the messages they arrive with, never
        # from this cache. Keeping every author a scraping account meets would
        # grow the session without bound, so only groups, channels and the
        # account itself are kept. The id-0 row Telethon uses to remember the
        # account's id arrives as an InputPeerUser, not a User, and is kept.
        if isinstance(e, types.User) and not e.is_self:
            return None
        return super()._entity_to_row(e)

    # -- the stored string ----------------------------------------------------

    def _key_bytes(self) -> Optional[bytes]:
        return getattr(self._auth_key, 'key', None) or None

    def dump(self) -> str:
        """The whole restartable state as one opaque string: "1:" and the
        URL-safe base64 of compact JSON. Opaque, so a store that parses JSON
        can never turn the 64-bit access hashes into floats."""
        key = self._key_bytes()
        state = {
            'format': FORMAT,
            'dc_id': self._dc_id,
            'server_address': self._server_address,
            'port': self._port,
            'auth_key': base64.b64encode(key).decode() if key else None,
            'takeout_id': self._takeout_id,
            'entities': _ordered(list(row) for row in self._entities),
            'update_states': _ordered(
                [entity_id, state.pts, state.qts, _timestamp(state.date), state.seq, state.unread_count]
                for entity_id, state in self._update_states.items()),
        }
        raw = json.dumps(state, sort_keys=True, separators=(',', ':'))
        return _PREFIX + base64.urlsafe_b64encode(raw.encode()).decode()

    def _parse(self, data: str) -> dict:
        """The state in a stored string. Raises ValueError naming only the
        session: the string is never quoted, and the parse error never
        chained, because the string holds the account's login key."""
        try:
            if not data.startswith(_PREFIX):
                raise ValueError('unknown format')
            state = json.loads(base64.b64decode(data[len(_PREFIX):].encode('ascii'),
                                               altchars=b'-_', validate=True))
            if state['format'] != FORMAT:
                raise ValueError('unknown format')
            key = state['auth_key']
            if key is not None:
                # Permissive base64 decoding can turn corrupt text into b'',
                # which would look like a first login and permit a code prompt.
                key = base64.b64decode(key, validate=True)
                if len(key) != 256:
                    raise ValueError('invalid auth key length')
            return {
                'dc': (state['dc_id'], state['server_address'], state['port']),
                'auth_key': key,
                'takeout_id': state['takeout_id'],
                'entities': {tuple(row) for row in state['entities']},
                'update_states': {
                    entity_id: types.updates.State(
                        pts=pts, qts=qts, seq=seq, unread_count=unread,
                        date=datetime.datetime.fromtimestamp(ts, datetime.timezone.utc))
                    for entity_id, pts, qts, ts, seq, unread in state['update_states']},
            }
        except Exception as e:  # noqa: BLE001
            reason = type(e).__name__
        raise ValueError(f"stored session {self._name!r} cannot be read ({reason})") from None

    def _restore(self, data: str) -> None:
        state = self._parse(data)
        self.set_dc(*state['dc'])
        self._auth_key = AuthKey(state['auth_key']) if state['auth_key'] else None
        self._takeout_id = state['takeout_id']
        self._entities = state['entities']
        self._update_states = state['update_states']

    # -- Telethon's save points -----------------------------------------------

    def save(self) -> None:
        """Called by Telethon whenever it saves, and by close(). Writes only
        when something changed, and never over a login this session did not
        load or make. Never raises into Telethon's loops."""
        try:
            data = self.dump()
            if data == self._synced:
                return
            stored = self._store.load(self._name)
            stored_key = self._parse(stored)['auth_key'] if stored is not None else None
            if stored_key != self._synced_key:
                if not self._warned:
                    self._warned = True
                    logger.warning(f"Session {self._name!r} was logged in or removed elsewhere — "
                                   f"not overwritten, and this client's changes are not saved")
                return
            self._store.save(self._name, data)
            self._synced, self._synced_key = data, self._key_bytes()
        except Exception as e:  # noqa: BLE001 — the error's text may quote the session: never logged
            logger.error(f"Could not save session {self._name!r} to the session store "
                         f"({type(e).__name__}) — retried at the next save point")

    def close(self) -> None:
        # Telethon flushes its last state into the session, then closes it.
        self.save()

    def delete(self) -> None:
        # Telethon's log_out(): it disconnects (which saves), then deletes.
        delete = getattr(self._store, 'delete', None)
        if delete is None:
            return
        try:
            delete(self._name)
            self._synced, self._synced_key = None, None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Could not delete session {self._name!r} from the session store "
                         f"({type(e).__name__})")

    def clone(self, to_instance=None):
        # Telethon copies a session for a side connection — media from its CDN,
        # for instance — by building the session class with no arguments. That
        # copy lives in memory only: a store-backed copy would save its own
        # login over the account's. Telethon's own file session copies the
        # same way: SQLiteSession() with no name lives in memory.
        return to_instance or MemorySession()
