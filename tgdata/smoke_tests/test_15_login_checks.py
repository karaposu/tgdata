"""
Smoke test: logging in never sends a login code nobody can type.

When Telegram logs an account out, Telethon's interactive login (start()) asks
Telegram to send a code to the account owner and waits for it on stdin. In a
background job nobody answers, it fails, and every retry sends another code.
tgdata now asks Telegram directly whether a session is logged in, and runs the
interactive login only when someone can type the code
(TgData(interactive_login=...)). Otherwise it raises AuthRequiredError — with
Telegram's reason, telling a ban from a logout — and requests no code.

Everything runs offline: a stand-in client that never opens a socket and fails
loudly if a code is requested, Telethon's real request code answering the
status check from a script, and a stand-in for the terminal check.

Persistent connection                                                          (no network)
  1. a logged-in session connects; no interactive login, no code
  2. logged out, used before, even at a terminal: AuthRequiredError with the reason, no code
  3. asking again checks again — no logged-out client is handed out — still no code
  4. banned, even with interactive_login=True: AuthRequiredError(banned=True), no code
  5. a brand-new session with no terminal: AuthRequiredError, no code
  6. a brand-new session at a terminal: the interactive login runs (first login still works)
  7. logged out, interactive_login=True, at a terminal: the interactive login runs
  8. interactive_login=False: never, not even a first login at a terminal
  9. a flood wait during the check is waited out and the check repeated — never "not logged in"
Use-and-close client                                                           (no network)
 10. logged out / banned raise AuthRequiredError with the reason; a long wait raises as the wait
 11. AuthRequiredError is still a RuntimeError, and now also a ConnectionError
Connection pool                                                                (no network)
 12. a logged-out pool connection fails start-up and leaves nothing open or half-made
"""
# To run: python -m tgdata.smoke_tests.test_15_login_checks

import asyncio
import datetime
import os
import shutil
import sys
import tempfile
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from telethon import errors
from telethon.crypto import AuthKey
from telethon.tl import types

import tgdata.connection_engine as ce
from tgdata import AuthRequiredError

TMP = tempfile.mkdtemp(prefix="tgdata_login_test_")
_ini_no = 0

# what the next stand-in client will see
REPLIES = []                    # one list of replies per client built, in build order
SESSION_HAS_KEY = {'on': False}  # the session file already holds a key (it was used before)
TERMINAL = {'on': False}        # someone is at a terminal
BUILT = []


def write_ini() -> str:
    global _ini_no
    _ini_no += 1
    path = os.path.join(TMP, f"c{_ini_no}.ini")
    with open(path, "w") as f:
        f.write("[Telegram]\napi_id = 12345\napi_hash = 0123456789abcdef0123456789abcdef\n"
                "phone = +10000000000\n"
                f"session_file = {os.path.join(TMP, f'session_{_ini_no}')}\n")
    return path


class Scripted:
    """Stands in for the connection: answers each request from a list."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def send(self, request, ordered=False):
        self.sent.append(type(request).__name__)
        item = self.replies.pop(0)
        future = asyncio.get_running_loop().create_future()
        if isinstance(item, BaseException):
            future.set_exception(item)
        else:
            future.set_result(item)
        return future


class StandIn(ce.TelegramClient):
    """Never opens a socket; records interactive logins; refuses to request a code."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.starts = 0
        self.codes = 0
        self._up = False
        if SESSION_HAS_KEY['on']:
            self.session.auth_key = AuthKey(bytes(256))
        self.flood_sleep_threshold = 0               # every wait raises: test 9 needs no long sleep
        self._sender = Scripted(REPLIES.pop(0) if REPLIES else [])
        BUILT.append(self)

    async def connect(self):
        if self.session.auth_key is None:            # what a real connect does on a new session
            self.session.auth_key = AuthKey(bytes(256))
        self._up = True

    def is_connected(self):
        return self._up

    async def disconnect(self):                      # like Telethon's: the session file is closed
        self._up = False
        self.session.close()

    async def send_code_request(self, *args, **kwargs):
        self.codes += 1
        raise AssertionError("a login code was requested")

    async def start(self, *args, **kwargs):          # Telethon's interactive login
        self.starts += 1
        return self


def logged_in():
    return types.updates.State(pts=1, qts=1, date=datetime.datetime.now(), seq=1, unread_count=0)


def logged_out():
    return errors.AuthKeyUnregisteredError(request=None)


def banned():
    return errors.UserDeactivatedBanError(request=None)


def wait(seconds):
    return errors.FloodWaitError(request=None, capture=seconds)


def setup(replies, has_key, terminal):
    REPLIES[:] = replies
    SESSION_HAS_KEY['on'] = has_key
    TERMINAL['on'] = terminal
    BUILT.clear()


def codes_requested():
    return sum(c.codes for c in BUILT)


async def persistent(interactive_login=None):
    """get_client() on a fresh engine; returns (client, error, engine)."""
    engine = ce.ConnectionEngine(write_ini(), interactive_login=interactive_login)
    try:
        return await engine.get_client(), None, engine
    except Exception as e:  # noqa: BLE001
        return None, e, engine


def check(condition, message):
    if not condition:
        raise AssertionError(message)


# ------------------------------------------------------------ persistent --

async def test_logged_in():
    print("\nTEST 1: a logged-in session connects — no interactive login, no code...")
    setup([[logged_in()]], has_key=True, terminal=True)
    client, error, _ = await persistent()
    check(error is None, f"raised {error!r}")
    check(client.starts == 0 and codes_requested() == 0, "interactive login or a code")
    check(client._sender.sent == ['GetStateRequest'], client._sender.sent)
    print("✓ Connected after one status check")
    return True


async def test_logged_out():
    print("\nTEST 2+3: logged out, used before, at a terminal — refused, and refused again...")
    setup([[logged_out()], [logged_out()]], has_key=True, terminal=True)
    client, error, engine = await persistent()
    check(isinstance(error, AuthRequiredError), f"got {error!r}")
    check(error.reason == 'AUTH_KEY_UNREGISTERED' and not error.banned, (error.reason, error.banned))
    check(isinstance(error.__cause__, errors.AuthKeyUnregisteredError), repr(error.__cause__))
    check(BUILT[0].starts == 0 and codes_requested() == 0, "interactive login or a code")
    print(f"✓ AuthRequiredError ({error.reason}); no interactive login, no code")
    try:
        await engine.get_client()
        raise AssertionError("the second get_client() handed out a logged-out client")
    except AuthRequiredError:
        pass
    check(len(BUILT) == 2 and codes_requested() == 0, (len(BUILT), codes_requested()))
    print("✓ Asked again: a fresh check, refused again, still no code")
    return True


async def test_banned():
    print("\nTEST 4: banned, even with interactive_login=True at a terminal...")
    setup([[banned()]], has_key=True, terminal=True)
    client, error, _ = await persistent(interactive_login=True)
    check(isinstance(error, AuthRequiredError) and error.banned, f"got {error!r}")
    check(error.reason == 'USER_DEACTIVATED_BAN', error.reason)
    check(BUILT[0].starts == 0 and codes_requested() == 0, "interactive login or a code")
    print(f"✓ AuthRequiredError(banned=True, {error.reason}); no code")
    return True


async def test_first_login_without_terminal():
    print("\nTEST 5: a brand-new session with no terminal...")
    setup([[logged_out()]], has_key=False, terminal=False)
    client, error, _ = await persistent()
    check(isinstance(error, AuthRequiredError), f"got {error!r}")
    check("never been logged in" in str(error), str(error))
    check(BUILT[0].starts == 0 and codes_requested() == 0, "interactive login or a code")
    print("✓ AuthRequiredError (never logged in, no terminal); no code")
    return True


async def test_first_login_at_terminal():
    print("\nTEST 6: a brand-new session at a terminal — first login still works...")
    setup([[logged_out()]], has_key=False, terminal=True)
    client, error, _ = await persistent()
    check(error is None, f"raised {error!r}")
    check(client.starts == 1, client.starts)
    print("✓ The interactive login ran once")
    return True


async def test_deliberate_relogin():
    print("\nTEST 7: logged out, interactive_login=True, at a terminal — deliberate re-login...")
    setup([[logged_out()]], has_key=True, terminal=True)
    client, error, _ = await persistent(interactive_login=True)
    check(error is None, f"raised {error!r}")
    check(client.starts == 1, client.starts)
    print("✓ The interactive login ran once")
    return True


async def test_never():
    print("\nTEST 8: interactive_login=False — not even a first login at a terminal...")
    setup([[logged_out()]], has_key=False, terminal=True)
    client, error, _ = await persistent(interactive_login=False)
    check(isinstance(error, AuthRequiredError), f"got {error!r}")
    check(BUILT[0].starts == 0 and codes_requested() == 0, "interactive login or a code")
    print("✓ AuthRequiredError; no interactive login")
    return True


async def test_wait_during_check():
    print("\nTEST 9: a flood wait during the check is waited out, then the check repeats...")
    setup([[wait(2), logged_in()]], has_key=True, terminal=False)
    start = time.monotonic()
    client, error, _ = await persistent()
    took = time.monotonic() - start
    check(error is None, f"raised {error!r}")
    check(took >= 1.9, f"took {took:.1f}s")
    check(client._sender.sent == ['GetStateRequest', 'GetStateRequest'], client._sender.sent)
    check(client.starts == 0 and codes_requested() == 0, "interactive login or a code")
    print(f"✓ Waited {took:.1f}s, checked again, connected")
    return True


# ---------------------------------------------------------- use-and-close --

async def test_use_and_close():
    print("\nTEST 10: the use-and-close client tells a logout, a ban and a wait apart...")
    for replies, expect in (([logged_out()], 'AUTH_KEY_UNREGISTERED'), ([banned()], 'USER_DEACTIVATED_BAN')):
        setup([replies], has_key=True, terminal=True)
        engine = ce.ConnectionEngine(write_ini())
        try:
            async with engine.ephemeral_client():
                raise AssertionError("connected")
        except AuthRequiredError as e:
            check(e.reason == expect, e.reason)
            check(e.banned == (expect == 'USER_DEACTIVATED_BAN'), e.banned)
        check(codes_requested() == 0 and BUILT[0].starts == 0, "interactive login or a code")
        print(f"✓ AuthRequiredError({expect})")
    setup([[wait(120)]], has_key=True, terminal=True)
    engine = ce.ConnectionEngine(write_ini())
    try:
        async with engine.ephemeral_client():
            raise AssertionError("connected")
    except errors.FloodWaitError as e:
        check(e.seconds == 120, e.seconds)
    print("✓ A 120 s wait raised as FloodWaitError, not as 'not logged in'")
    return True


async def test_error_type():
    print("\nTEST 11: AuthRequiredError keeps its old type and gains the persistent path's...")
    check(issubclass(AuthRequiredError, RuntimeError), "not a RuntimeError")
    check(issubclass(AuthRequiredError, ConnectionError), "not a ConnectionError")
    print("✓ Both a RuntimeError and a ConnectionError")
    return True


async def test_pool():
    print("\nTEST 12: a logged-out pool connection fails start-up and leaves nothing open...")
    setup([[logged_in()], [logged_out()]], has_key=True, terminal=True)
    engine = ce.ConnectionEngine(write_ini(), pool_size=2)
    try:
        await engine.get_client()
        raise AssertionError("connected")
    except AuthRequiredError as e:
        check(e.reason == 'AUTH_KEY_UNREGISTERED', e.reason)
    check(len(BUILT) == 2, len(BUILT))
    check(not any(c.is_connected() for c in BUILT), "a client was left connected")
    check(engine._primary_client is None and engine._pool is None, "half-made clients kept")
    check(codes_requested() == 0, "a code was requested")
    print("✓ AuthRequiredError; both clients closed; nothing kept; no code")
    return True


async def main():
    print("Login Check Tests")
    print("=" * 60)
    tests = [test_logged_in, test_logged_out, test_banned, test_first_login_without_terminal,
             test_first_login_at_terminal, test_deliberate_relogin, test_never,
             test_wait_during_check, test_use_and_close, test_error_type, test_pool]
    original_client, original_terminal = ce.TelegramClient, ce._human_at_terminal
    ce.TelegramClient = StandIn
    ce._human_at_terminal = lambda: TERMINAL['on']
    results = []
    try:
        for test in tests:
            try:
                results.append(await asyncio.wait_for(test(), timeout=60))
            except Exception as e:  # noqa: BLE001
                print(f"✗ {type(e).__name__}: {e}")
                results.append(False)
    finally:
        ce.TelegramClient, ce._human_at_terminal = original_client, original_terminal
        shutil.rmtree(TMP, ignore_errors=True)
    print("\nSummary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
