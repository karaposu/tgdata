"""
Smoke test for the per-request flood-wait threshold.

Telethon documents client(request, flood_sleep_threshold=N) as a per-request
override of how long a flood wait it sleeps through silently — and ignores it
(every release checked, 1.33.1 to 1.45.0): a wait up to the client-wide
threshold (60 s) is slept whatever the request says. Every client tgdata builds
honours it (connection_engine._PerCallFloodThreshold), and discovery relies on
that to see every wait. This test is the canary for that workaround:
RUN IT AFTER ANY TELETHON UPGRADE.

Everything runs offline. Telethon's real request code is driven by a scripted
stand-in for its connection (client._sender): no network, no login, no account.

Telethon level                                                                (no network)
  1. a per-request 0 raises a 1 s wait at once (and: does plain Telethon honour it?)
  2. requests without it are unchanged: the wait is slept and the request retried
  3. on one client, a per-request 0 and a plain request at once keep their own behaviour
  4. no side effects: the override does not stick; the setter and its 24 h cap; a task
     started mid-request does not inherit the override
  5. a wait Telethon already knows about is raised before anything is sent
  6. exact per-request scope: a request without its own value does not inherit one
  7. every connection path (use-and-close, persistent, pool) builds the honouring class

Discovery level                                                               (no network)
  8. a short wait on a raw discovery request: heartbeat ticks, then the same request retried
  9. a wait above max_flood_wait raises DiscoveryInterrupted with retry_after
 10. a wait on a username lookup is never slept: a seed is skipped; a linked_groups
     source raises DiscoveryInterrupted
 11. premium flood waits are handled as waits too
"""
# To run: python -m tgdata.smoke_tests.test_14_flood_threshold

import asyncio
import datetime
import logging
import os
import shutil
import sys
import tempfile
import time
from contextlib import asynccontextmanager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import telethon
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl import types
from telethon.tl.functions.contacts import ResolveUsernameRequest, SearchRequest
from telethon.tl.functions.help import GetConfigRequest
from telethon.tl.functions.updates import GetStateRequest

import tgdata.connection_engine as ce
from tgdata.connection_engine import ConnectionEngine
from tgdata.discovery_engine import DiscoveryEngine, DiscoveryInterrupted

TMP = tempfile.mkdtemp(prefix="tgdata_flood_test_")
API_HASH = "0123456789abcdef0123456789abcdef"
PREMIUM_WAIT = getattr(errors, 'FloodPremiumWaitError', None)
ENGINE = None                   # built in main()
_session_no = 0


def write_ini(name: str) -> str:
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write("[Telegram]\napi_id = 12345\n"
                f"api_hash = {API_HASH}\n"
                f"session_file = {os.path.join(TMP, 'throwaway_' + name)}\n")
    return path


def new_client():
    """A client from tgdata's factory, on its own throwaway session file."""
    global _session_no
    _session_no += 1
    return ENGINE._new_client(os.path.join(TMP, f"session_{_session_no}"))


class Scripted:
    """Stands in for a client's connection (client._sender). Answers each
    request from a script — an exception to raise or a result to return —
    either one queue for every request, or one queue per request type —
    and records what was sent."""

    def __init__(self, script):
        self.script = script
        self.sent = []

    def send(self, request, ordered=False):
        self.sent.append(type(request).__name__)
        queue = self.script[type(request)] if isinstance(self.script, dict) else self.script
        item = queue.pop(0)
        future = asyncio.get_running_loop().create_future()
        if isinstance(item, BaseException):
            future.set_exception(item)
        else:
            future.set_result(item)
        return future


def wait(seconds: int, kind=errors.FloodWaitError):
    return kind(request=None, capture=seconds)


def state():
    return types.updates.State(pts=1, qts=1, date=datetime.datetime.now(), seq=1, unread_count=0)


def found():
    return types.contacts.Found(my_results=[], results=[], chats=[], users=[])


class StandInEngine:
    """Stands in for ConnectionEngine.session(): yields one factory-built client."""

    def __init__(self, client):
        self.client = client

    @asynccontextmanager
    async def session(self):
        yield self.client


def discovery(script):
    client = new_client()
    client._sender = Scripted(script)
    return DiscoveryEngine(StandInEngine(client)), client


class Warnings(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


# ------------------------------------------------------- Telethon level --

async def test_option_works():
    print("\nTEST 1: a per-request threshold of 0 raises a short wait at once...")
    try:
        client = new_client()
        client._sender = Scripted([wait(1), state()])
        start = time.monotonic()
        try:
            await client(GetStateRequest(), flood_sleep_threshold=0)
            raise AssertionError("the 1 s wait was slept, not raised")
        except errors.FloodWaitError as e:
            took = time.monotonic() - start
            assert e.seconds == 1, e.seconds
            assert took < 0.5, f"took {took:.2f}s"
            assert client._sender.sent == ['GetStateRequest'], client._sender.sent
        print(f"✓ FloodWaitError (1 s) raised after {took:.2f}s and one send")

        plain = TelegramClient(StringSession(), 12345, API_HASH)
        plain._sender = Scripted([wait(1), state()])
        try:
            await plain(GetStateRequest(), flood_sleep_threshold=0)
            print("  note: Telethon's own client ignores the per-request value — "
                  "the known defect this works around")
        except errors.FloodWaitError:
            print("  note: Telethon's own client now honours the per-request value itself — "
                  "the workaround is redundant but harmless")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_plain_requests_unchanged():
    print("\nTEST 2: requests without the option still sleep a short wait and retry...")
    try:
        client = new_client()
        client._sender = Scripted([wait(1), state()])
        start = time.monotonic()
        result = await client(GetStateRequest())
        took = time.monotonic() - start
        assert isinstance(result, types.updates.State), type(result)
        assert took >= 0.9, f"took {took:.2f}s"
        assert client._sender.sent == ['GetStateRequest', 'GetStateRequest'], client._sender.sent
        print(f"✓ Slept {took:.1f}s, retried once, returned the result — Telethon's normal behaviour")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_concurrent_requests():
    print("\nTEST 3: one client, a per-request 0 and a plain request at the same time...")
    try:
        client = new_client()
        client._sender = Scripted({GetConfigRequest: [wait(1)], GetStateRequest: [wait(1), state()]})

        async def with_zero():
            try:
                await client(GetConfigRequest(), flood_sleep_threshold=0)
                return 'returned'
            except errors.FloodWaitError:
                return 'raised'

        async def plain():
            return type(await client(GetStateRequest())).__name__

        outcome = await asyncio.gather(with_zero(), plain())
        assert outcome == ['raised', 'State'], outcome
        print("✓ The per-request 0 raised while the plain request slept and returned")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_no_side_effects():
    print("\nTEST 4: no side effects on the client or on tasks started mid-request...")
    try:
        client = new_client()
        client._sender = Scripted([wait(1)])
        seen = {}
        send = client._sender.send

        def spying_send(request, ordered=False):
            async def started_mid_request():
                seen['task started mid-request'] = client.flood_sleep_threshold
            seen['pending'] = asyncio.get_running_loop().create_task(started_mid_request())
            seen['the requesting task'] = client.flood_sleep_threshold
            return send(request, ordered)

        client._sender.send = spying_send
        try:
            await client(GetStateRequest(), flood_sleep_threshold=0)
        except errors.FloodWaitError:
            pass
        await seen.pop('pending')
        assert seen == {'the requesting task': 0, 'task started mid-request': 60}, seen
        assert client.flood_sleep_threshold == 60, client.flood_sleep_threshold
        client.flood_sleep_threshold = 5
        assert client.flood_sleep_threshold == 5, client.flood_sleep_threshold
        client.flood_sleep_threshold = 10 ** 9
        assert client.flood_sleep_threshold == 24 * 60 * 60, client.flood_sleep_threshold
        print("✓ Requesting task saw 0, a task started mid-request saw 60; "
              "afterwards 60; setter stores 5 and caps 10**9 at 86400")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_known_wait_raised_before_sending():
    print("\nTEST 5: a wait Telethon already knows about is raised before sending...")
    try:
        client = new_client()
        client._sender = Scripted([wait(10)])
        try:
            await client(GetStateRequest(), flood_sleep_threshold=0)      # Telethon records 10 s
        except errors.FloodWaitError:
            pass
        client._sender = Scripted([state()])
        start = time.monotonic()
        try:
            await client(GetStateRequest(), flood_sleep_threshold=0)
            raise AssertionError("the known wait was not raised")
        except errors.FloodWaitError:
            pass
        took = time.monotonic() - start
        assert client._sender.sent == [], client._sender.sent
        assert took < 0.5, f"took {took:.2f}s"
        print("✓ Raised from Telethon's pending-wait check; nothing was sent")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_exact_request_scope():
    print("\nTEST 6: a request without its own value does not inherit an enclosing one...")
    try:
        client = new_client()
        client._sender = Scripted([wait(1), state()])
        enclosing = (asyncio.current_task(), 0)          # as if inside a request sent with 0
        token = ce._PER_CALL_FLOOD_THRESHOLD.set(enclosing)
        try:
            start = time.monotonic()
            result = await client(GetStateRequest())    # e.g. a name Telethon resolves internally
            took = time.monotonic() - start
            assert isinstance(result, types.updates.State), type(result)
            assert took >= 0.9, f"took {took:.2f}s — the enclosing 0 leaked into this request"
            assert ce._PER_CALL_FLOOD_THRESHOLD.get() == enclosing, "the enclosing value was not restored"
        finally:
            ce._PER_CALL_FLOOD_THRESHOLD.reset(token)
        print(f"✓ Slept {took:.1f}s as normal; the enclosing value was intact afterwards")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_connection_paths():
    print("\nTEST 7: every connection path builds the honouring client...")
    built = []

    class StandIn(ce.TelegramClient):
        """Records what each path builds, and refuses to open a connection."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            built.append(self)

        async def connect(self):
            raise ConnectionError("stand-in: no network in this test")

    original = ce.TelegramClient
    ce.TelegramClient = StandIn
    try:
        eng = ConnectionEngine(write_ini("paths.ini"), pool_size=3)
        try:
            async with eng.ephemeral_client():
                raise AssertionError("the stand-in connected")
        except ConnectionError:
            pass
        try:
            await eng.get_client()
            raise AssertionError("the stand-in connected")
        except ConnectionError:
            pass
        eng._new_client(eng._load_config().session_file + "_1")      # a pool connection
        assert len(built) == 3, len(built)
        for client in built:
            assert isinstance(client, StandIn), type(client)
            assert isinstance(client, ce._PerCallFloodThreshold), type(client)
            client._sender = Scripted([wait(1)])
            try:
                await client(GetStateRequest(), flood_sleep_threshold=0)
                raise AssertionError(f"{type(client).__name__} slept through the wait")
            except errors.FloodWaitError:
                pass
        print(f"✓ Use-and-close, persistent and pool clients all honour the option ({len(built)} built)")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False
    finally:
        ce.TelegramClient = original


# ------------------------------------------------------ discovery level --

async def test_discovery_beats_and_retries():
    print("\nTEST 8: a short wait on a discovery request: heartbeat ticks, then a retry...")
    try:
        engine, client = discovery({SearchRequest: [wait(2), found()]})
        beats = []
        df = await engine.search_groups("x", pace=0, heartbeat=beats.append)
        assert client._sender.sent == ['SearchRequest', 'SearchRequest'], client._sender.sent
        assert "flood-wait 2s" in beats, beats
        assert len(df) == 0, len(df)
        print(f"✓ Beats {beats}; the same search was sent again and returned")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_discovery_interrupts_above_max():
    print("\nTEST 9: a wait above max_flood_wait raises DiscoveryInterrupted...")
    try:
        engine, client = discovery({SearchRequest: [wait(2)]})
        start = time.monotonic()
        try:
            await engine.search_groups("x", pace=0, max_flood_wait=1)
            raise AssertionError("no DiscoveryInterrupted")
        except DiscoveryInterrupted as e:
            assert e.retry_after == 2, e.retry_after
        took = time.monotonic() - start
        assert took < 0.5, f"took {took:.2f}s"
        print(f"✓ DiscoveryInterrupted(retry_after=2) after {took:.2f}s")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def test_lookup_waits_never_slept():
    print("\nTEST 10: a wait on a username lookup is never slept through...")
    log = logging.getLogger('tgdata.discovery_engine')
    caught = Warnings()
    log.addHandler(caught)
    try:
        engine, client = discovery({ResolveUsernameRequest: [wait(5)]})
        start = time.monotonic()
        df = await engine.similar_groups(["@seedname"], pace=0)
        took = time.monotonic() - start
        assert len(df) == 0, len(df)
        assert took < 1, f"took {took:.2f}s"
        assert client._sender.sent == ['ResolveUsernameRequest'], client._sender.sent
        assert any("Seed '@seedname' skipped" in m for m in caught.messages), caught.messages
        print(f"✓ similar_groups: the seed was skipped after {took:.2f}s, with a warning")

        engine, client = discovery({ResolveUsernameRequest: [wait(5)]})
        start = time.monotonic()
        try:
            await engine.linked_groups("@source", pace=0)
            raise AssertionError("no DiscoveryInterrupted")
        except DiscoveryInterrupted as e:
            assert e.retry_after == 5, e.retry_after
        took = time.monotonic() - start
        assert took < 1, f"took {took:.2f}s"
        print(f"✓ linked_groups: DiscoveryInterrupted(retry_after=5) after {took:.2f}s")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False
    finally:
        log.removeHandler(caught)


async def test_premium_waits_are_waits():
    print("\nTEST 11: premium flood waits are handled as waits...")
    if PREMIUM_WAIT is None:
        print(f"! skipped — Telethon {telethon.__version__} has no FloodPremiumWaitError")
        return True
    try:
        engine, client = discovery({SearchRequest: [wait(2, PREMIUM_WAIT), found()]})
        beats = []
        await engine.search_groups("x", pace=0, heartbeat=beats.append)
        assert client._sender.sent == ['SearchRequest', 'SearchRequest'], client._sender.sent
        assert "flood-wait 2s" in beats, beats
        print("✓ search_groups: the premium wait was slept with ticks and the search retried")

        engine, client = discovery({ResolveUsernameRequest: [wait(5, PREMIUM_WAIT)]})
        try:
            await engine.linked_groups("@source", pace=0)
            raise AssertionError("no DiscoveryInterrupted")
        except DiscoveryInterrupted as e:
            assert e.retry_after == 5, e.retry_after
        print("✓ linked_groups: a premium lookup wait raised DiscoveryInterrupted(retry_after=5)")
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {e}")
        return False


async def main():
    global ENGINE
    print("Per-Request Flood Threshold Tests")
    print("=" * 60)
    print(f"Telethon {telethon.__version__}")
    ENGINE = ConnectionEngine(write_ini("flood.ini"))
    tests = [test_option_works, test_plain_requests_unchanged, test_concurrent_requests,
             test_no_side_effects, test_known_wait_raised_before_sending, test_exact_request_scope,
             test_connection_paths, test_discovery_beats_and_retries,
             test_discovery_interrupts_above_max, test_lookup_waits_never_slept,
             test_premium_waits_are_waits]
    results = []
    try:
        for test in tests:
            results.append(await asyncio.wait_for(test(), timeout=60))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("\nSummary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
