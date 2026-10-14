"""
Smoke test: account health events (issue #4).

Every time Telegram says no to an account — a wait, a logout, a ban, a
restriction, no access to a group — tgdata reports it to health_callback, to
the 'tgdata.tgdata.health' logger and in health_check()["health"], and says
"ok" when it ends. It reports and never acts — except that polling now stops
on what retrying cannot fix, and validate_connection() says why it failed.

Everything runs offline. Engine methods are replaced by small stand-ins that
raise or return; where it matters, Telethon's real request code runs on a
client from tgdata's own factory whose connection (client._sender) is
scripted: no network, no login, no account.

Classification and events                                                     (no network)
  1. the verdict table, by Telegram's own names; wrappers unwrapped; non-verdicts ignored
  2. the boundary: the same exception re-raised, one JSON-ready event, delivered first
  3. delivery: an async callback is awaited; a raising callback breaks nothing
  4. Telethon's silent sleeps become waiting events, then "ok"; console output unchanged
  5. two accounts at once: each callback receives only its own account's sleeps
  6. counted once: the fetch loop waiting four times, then giving up = four events
  7. recovery: "ok" only when a separate, later success proves the condition ended
  8. the summary in health_check()["health"]
  9. the log mirror's levels per verdict
The two fixes                                                                  (no network)
 10. polling stops on what retrying cannot fix; transient errors retried; callback errors propagate
 11. validate_connection(): False with the reason, reported, never a recovery
 18. health_check(): a logged-out connection is unhealthy, named, reported, and in ['health']
Sources and safety                                                             (no network)
 12. the real-time listener's logout is reported, and still raised
 13. without a health_callback everything behaves as before
 14. a bug in the health code never changes what a call raises or returns
 15. a sleep in a task started during a call is the account's, not the call's
 16. a call never recovers from what it reported itself (discovery's real code)
 17. a per-item group is the item, normalised — and a later call naming it recovers it
 19. a call answered before a logout, finishing after it, is no recovery
 20. a call that sends no request recovers nothing
 21. a callback that calls tgdata is not called back for its own calls' events
"""
# To run: python -m tgdata.smoke_tests.test_16_health_events

import asyncio
import datetime
import inspect
import json
import logging
import logging.config
import os
import shutil
import sys
import tempfile
from contextlib import asynccontextmanager, contextmanager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from telethon import errors
from telethon.errors import rpc_message_to_error
from telethon.tl import types
from telethon.tl.functions.contacts import ResolveUsernameRequest, SearchRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.updates import GetStateRequest

from tgdata import TgData, AuthRequiredError, GroupAccessError
from tgdata import health
from tgdata.connection_engine import ConnectionPool

TMP = tempfile.mkdtemp(prefix="tgdata_health_test_")
API_HASH = "0123456789abcdef0123456789abcdef"
HISTORY = GetHistoryRequest(peer=types.InputPeerEmpty(), offset_id=0, offset_date=None,
                            add_offset=0, limit=1, max_id=0, min_id=0, hash=0)
_file_no = 0


# ----------------------------------------------------------------- helpers --

def write_ini() -> str:
    global _file_no
    _file_no += 1
    path = os.path.join(TMP, f"c{_file_no}.ini")
    with open(path, "w") as f:
        f.write(f"[Telegram]\napi_id = 12345\napi_hash = {API_HASH}\n"
                f"session_file = {os.path.join(TMP, f'account_{_file_no}.session')}\n")
    return path


class Events:
    """A health_callback that keeps what it receives."""
    def __init__(self):
        self.list = []

    def __call__(self, event):
        self.list.append(event)

    def verdicts(self):
        return [e['verdict'] for e in self.list]


def tg(callback=None, label=None) -> TgData:
    return TgData(write_ini(), health_callback=callback, account_label=label)


def rpc(code: int, name: str, request=HISTORY):
    """A Telegram error exactly as Telethon builds it from Telegram's answer."""
    return rpc_message_to_error(types.RpcError(error_code=code, error_message=name), request)


def wait(seconds: int, request=HISTORY, kind=errors.FloodWaitError):
    return kind(request=request, capture=seconds)


def state():
    return types.updates.State(pts=1, qts=1, date=datetime.datetime.now(), seq=1, unread_count=0)


def found():
    return types.contacts.Found(my_results=[], results=[], chats=[], users=[])


def raising(error):
    async def stand_in(*args, **kwargs):
        raise error
    return stand_in


def returning(value):
    async def stand_in(*args, **kwargs):
        return value
    return stand_in


def yielding(client):
    """Stands in for ConnectionEngine.session(): yields one client."""
    @asynccontextmanager
    async def session():
        yield client
    return session


class Scripted:
    """Stands in for a client's connection (client._sender): answers each
    request from a script — one queue, or one queue per request type — and,
    like Telegram's real answers, an error carries the request it answers."""
    def __init__(self, script):
        self.script = script
        self.sent = []

    def send(self, request, ordered=False):
        self.sent.append(type(request).__name__)
        queue = self.script[type(request)] if isinstance(self.script, dict) else self.script
        item = queue.pop(0)
        if isinstance(item, errors.RPCError):
            item.request = request
        future = asyncio.get_running_loop().create_future()
        if isinstance(item, BaseException):
            future.set_exception(item)
        else:
            future.set_result(item)
        return future


def scripted_client(t: TgData, script):
    """A client from this TgData's own factory — Telethon's real request
    code, tgdata's client class — on its own session file, scripted."""
    global _file_no
    _file_no += 1
    client = t.connection_engine._new_client(os.path.join(TMP, f"client_{_file_no}"))
    client._sender = Scripted(script)
    return client


def answered(t: TgData, value):
    """A stand-in engine method whose work Telegram answers: one request
    through a client from t's own factory, so the answer is observed where
    tgdata observes every answer — then `value`. Recovery needs that evidence;
    a bare return value is a call that never reached Telegram."""
    async def stand_in(*args, **kwargs):
        await scripted_client(t, [state()])(GetStateRequest())
        return value
    return stand_in


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.NOTSET)
        self.records = []

    def emit(self, record):
        self.records.append(record)


@contextmanager
def captured(name: str, level=logging.DEBUG):
    """Records on one logger, at `level`, for the duration."""
    target = logging.getLogger(name)
    handler, before = Capture(), target.level
    target.addHandler(handler)
    target.setLevel(level)
    try:
        yield handler
    finally:
        target.removeHandler(handler)
        target.setLevel(before)


async def caught(awaitable):
    try:
        return await awaitable, None
    except Exception as e:  # noqa: BLE001
        return None, e


def check(condition, message):
    if not condition:
        raise AssertionError(message)


# ------------------------------------------------- classification + events --

async def test_classifier():
    print("\nTEST 1: verdicts come only from Telegram's own names...")
    table = {
        'waiting': [(420, 'FLOOD_WAIT_5'), (420, 'FLOOD_PREMIUM_WAIT_5'), (420, 'SLOWMODE_WAIT_5'),
                    (420, 'FLOOD_TEST_PHONE_WAIT_5')],
        'logged out': [(401, 'AUTH_KEY_UNREGISTERED'), (401, 'SESSION_REVOKED'), (401, 'SESSION_EXPIRED'),
                       (401, 'AUTH_KEY_INVALID'), (406, 'AUTH_KEY_DUPLICATED')],
        'banned': [(401, 'USER_DEACTIVATED_BAN'), (401, 'USER_DEACTIVATED'), (400, 'PHONE_NUMBER_BANNED')],
        'restricted': [(420, 'FROZEN_METHOD_INVALID'), (400, 'FROZEN_PARTICIPANT_MISSING'),
                       (403, 'USER_RESTRICTED'), (400, 'PEER_FLOOD')],
        'no access': [(400, 'CHANNEL_PRIVATE'), (403, 'CHAT_FORBIDDEN'), (400, 'CHANNEL_INVALID'),
                      (400, 'USER_BANNED_IN_CHANNEL'), (406, 'CHANNEL_PUBLIC_GROUP_NA'), (400, 'CHANNEL_BANNED')],
    }
    scope = {'waiting': 'request', 'logged out': 'account', 'banned': 'account',
             'restricted': 'account', 'no access': 'group'}
    for verdict, names in table.items():
        for code, name in names:
            f = health.classify(rpc(code, name))
            check(f is not None and (f.verdict, f.scope) == (verdict, scope[verdict]), (name, f))
            check(f.request == 'GetHistoryRequest', (name, f.request))
    check(health.classify(rpc(420, 'FLOOD_WAIT_5')).wait_seconds == 5, "wait seconds")
    print(f"✓ {sum(len(v) for v in table.values())} names give the desc's verdict and scope")
    for code in (401, 403, 406, 420):
        f = health.classify(rpc(code, f'SOMETHING_NEW_{code}'))
        check(f is not None and f.verdict == 'unclassified' and f.scope is None
              and f.error == f'SOMETHING_NEW_{code}', (code, f))
    for code, name in ((400, 'SOME_BAD_REQUEST'), (500, 'SOME_SERVER_ERROR'), (400, 'FILE_REFERENCE_EXPIRED'),
                       (406, 'FILEREF_UPGRADE_NEEDED'), (400, 'USERNAME_NOT_OCCUPIED')):
        check(health.classify(rpc(code, name)) is None, name)
    print("✓ unknown 401/403/406/420 are unclassified, with the name; 400, 5xx, file references: nothing")

    try:
        try:
            raise wait(30)
        except errors.FloodWaitError as e:
            raise RuntimeError("Giving up after 4 rate-limit interruptions") from e
    except RuntimeError as wrapped:
        f = health.classify(wrapped)
        check(f is not None and f.verdict == 'waiting' and f.wait_seconds == 30, f)
    try:
        try:
            raise rpc(401, 'USER_DEACTIVATED_BAN')
        except errors.RPCError as e:
            raise ConnectionError(f"Failed to authenticate: {e}")      # no `from`: the context is kept
    except ConnectionError as wrapped:
        check(health.classify(wrapped).verdict == 'banned', "implicit context")
    try:
        try:
            raise rpc(401, 'USER_DEACTIVATED_BAN')
        except errors.RPCError:
            raise ValueError("unrelated") from None                   # suppressed: not followed
    except ValueError as wrapped:
        check(health.classify(wrapped) is None, "a suppressed context was followed")
    print("✓ the cause chain is followed (explicit cause, implicit context; never a suppressed one)")

    first = AuthRequiredError("never logged in", reason='AUTH_KEY_UNREGISTERED', first_login=True)
    check(health.classify(first) is None, "a first login is configuration, not a verdict")
    try:
        try:
            raise rpc(401, 'AUTH_KEY_UNREGISTERED')
        except errors.RPCError as problem:
            raise AuthRequiredError("logged out", reason='AUTH_KEY_UNREGISTERED') from problem
    except AuthRequiredError as e:
        check(health.classify(e).verdict == 'logged out', "AuthRequiredError from a logout")
    bare = AuthRequiredError("banned", reason='USER_DEACTIVATED_BAN', banned=True)
    check(health.classify(bare).verdict == 'banned', "AuthRequiredError's .reason")
    check(health.classify(GroupAccessError("no access")).verdict == 'no access', "GroupAccessError")
    check(health.classify(ConnectionError("network down")) is None, "transport is not a verdict")
    check(health.classify(ValueError("not a group")) is None, "a lookup miss is not a verdict")
    print("✓ AuthRequiredError by .reason and cause (a first login: nothing); GroupAccessError; "
          "transport and lookup misses: nothing")
    return True


async def test_boundary():
    print("\nTEST 2: the boundary re-raises the same exception after one JSON-ready event...")
    events = Events()
    t = tg(events, label='acct-2')
    t.connection_engine._load_config()            # as after a first connection: the session name is known
    error = rpc(400, 'CHANNEL_PRIVATE')
    t.message_engine.get_message_count = raising(error)
    seen_when_raised = None
    try:
        await t.get_message_count(123)
        raise AssertionError("no exception")
    except errors.ChannelPrivateError as e:
        seen_when_raised = len(events.list)
        check(e is error, "a different exception object reached the caller")
    check(seen_when_raised == 1, f"{seen_when_raised} events when the exception reached the caller")
    event = events.list[0]
    expected = {'kind': 'health', 'verdict': 'no access', 'scope': 'group', 'group': 123,
                'call': 'get_message_count', 'request': 'GetHistoryRequest', 'wait_seconds': None,
                'error': 'CHANNEL_PRIVATE', 'source': 'error'}
    check({k: event[k] for k in expected} == expected, event)
    check(event['account'] == {'label': 'acct-2', 'session': f'account_{_file_no}', 'user_id': None},
          event['account'])
    check(datetime.datetime.fromisoformat(event['time']).utcoffset() == datetime.timedelta(0), event['time'])
    check(json.loads(json.dumps(event)) == event, "the event does not survive json.dumps")
    print(f"✓ same object; one event before the caller saw it: {json.dumps(event)}")
    return True


async def test_delivery():
    print("\nTEST 3: delivery — async callbacks awaited, raising callbacks harmless...")
    got = []

    async def async_callback(event):
        await asyncio.sleep(0.01)
        got.append(event)

    t = tg(async_callback)
    t.message_engine.get_message_count = raising(rpc(400, 'CHANNEL_PRIVATE'))
    try:
        await t.get_message_count(3)
    except errors.ChannelPrivateError:
        check(len(got) == 1, "the async callback was not awaited before the exception")
    print("✓ an async callback is awaited before the exception reaches the caller")

    def broken(event):
        raise ValueError("a bug in the caller's callback")

    async def broken_async(event):
        raise ValueError("a bug in the caller's async callback")

    for callback in (broken, broken_async):
        t = tg(callback)
        with captured('tgdata.health') as log:
            for _ in range(3):
                error = rpc(400, 'CHANNEL_PRIVATE')
                t.message_engine.get_message_count = raising(error)
                _, raised = await caught(t.get_message_count(4))
                check(raised is error, f"the call raised {raised!r}")
            t.message_engine.get_message_count = returning(9)
            check(await t.get_message_count(4) == 9, "a success changed its result")
        warnings = [r for r in log.records if r.levelno == logging.WARNING]
        debugs = [r for r in log.records if r.levelno == logging.DEBUG]
        check(len(warnings) == 1 and warnings[0].exc_info, [r.getMessage() for r in log.records])
        check(len(debugs) >= 2, f"{len(debugs)} DEBUG records")
    print("✓ a raising callback (sync or async) changes nothing; WARNING with traceback once, then DEBUG")
    return True


async def test_silent_sleeps():
    print("\nTEST 4: Telethon's silent sleeps become events; the console shows what it showed...")
    events = Events()
    t = tg(events, label='acct-4')
    root, console = logging.getLogger(), Capture()
    root.addHandler(console)
    users = logging.getLogger('telethon.client.users')
    try:
        client = scripted_client(t, [wait(1), state()])

        async def count(group_id):
            await client(GetStateRequest())          # Telethon sleeps 1 s silently, then retries
            return 7

        t.message_engine.get_message_count = count
        check(await t.get_message_count(55) == 7, "wrong result")
        check(events.verdicts() == ['waiting', 'ok'], events.verdicts())
        sleep, ok = events.list
        check((sleep['source'], sleep['request'], sleep['wait_seconds'], sleep['call'], sleep['group'],
               sleep['error']) == ('sleep', 'GetStateRequest', 1, 'get_message_count', 55, 'FLOOD_WAIT_X'), sleep)
        check((ok['scope'], ok['request'], ok['source']) == ('request', 'GetStateRequest', 'recovery'), ok)
        check(not [r for r in console.records if r.name == 'telethon.client.users'],
              "the console received Telethon's INFO sleep line")
        print("✓ waiting (sleep, GetStateRequest, 1 s, FLOOD_WAIT_X, get_message_count), then ok; "
              "the console received nothing")

        logging.getLogger('telethon').setLevel(logging.INFO)     # a user who asked for Telethon's INFO lines
        try:
            client = scripted_client(t, [wait(1), state()])
            await t.get_message_count(55)
            lines = [r for r in console.records if r.name == 'telethon.client.users']
            check(len(lines) == 1 and 'flood wait' in lines[0].getMessage(), [r.getMessage() for r in lines])
        finally:
            logging.getLogger('telethon').setLevel(logging.NOTSET)
        users.warning("a warning from telethon.client.users")
        check(console.records[-1].getMessage() == "a warning from telethon.client.users",
              "Telethon's warning did not reach the console")
        print("✓ a user who asked for the sleep lines still gets them; Telethon's warnings still arrive")

        logging.config.dictConfig({'version': 1, 'disable_existing_loggers': True})
        check(users.disabled, "dictConfig did not disable the logger")
        before = len(console.records)
        client = scripted_client(t, [wait(1), state()])
        await t.get_message_count(55)
        check(events.verdicts()[-2:] == ['waiting', 'ok'], events.verdicts())
        check(len(console.records) == before, "a logger the user disabled printed")
        print("✓ after dictConfig disabled every logger: still captured, still nothing printed")
    finally:
        root.removeHandler(console)
        for logger in logging.root.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                logger.disabled = False
        if health._capture is not None:
            health._capture.user_disabled = False
    return True


async def test_two_accounts():
    print("\nTEST 5: two accounts at once — each callback gets only its own sleeps...")
    first, second = Events(), Events()
    a, b = tg(first, label='A'), tg(second, label='B')
    for t, group in ((a, 1), (b, 2)):
        client = scripted_client(t, [wait(1), state()])

        async def count(group_id, client=client):
            await client(GetStateRequest())
            return group_id

        t.message_engine.get_message_count = count
    results = await asyncio.gather(a.get_message_count(1), b.get_message_count(2))
    check(results == [1, 2], results)
    for events, label, group in ((first, 'A', 1), (second, 'B', 2)):
        check(events.verdicts() == ['waiting', 'ok'], (label, events.verdicts()))
        sleep = events.list[0]
        check((sleep['account']['label'], sleep['group'], sleep['call']) == (label, group, 'get_message_count'),
              sleep)
    print("✓ A received only A's sleep, B only B's — concurrent, one process")
    return True


async def test_counted_once():
    print("\nTEST 6: counted once — four waits in the fetch loop, then the give-up...")

    class Room:
        id, title, username = 5, "Room", "room"

    class Flooded:
        calls = 0

        async def get_entity(self, group_id):
            return Room()

        def iter_messages(self, **kwargs):
            Flooded.calls += 1

            async def messages():
                raise wait(0)
                yield  # noqa: unreachable — makes this an async generator
            return messages()

    events = Events()
    t = tg(events)
    t.connection_engine.session = yielding(Flooded())
    _, error = await caught(t.get_messages(group_id=5))
    check(isinstance(error, RuntimeError) and isinstance(error.__cause__, errors.FloodWaitError), repr(error))
    check(Flooded.calls == 4, f"{Flooded.calls} fetch attempts")
    check(len(events.list) == 4, f"{len(events.list)} events: {events.verdicts()}")
    check(all((e['verdict'], e['source'], e['request']) == ('waiting', 'handled', 'GetHistoryRequest')
              for e in events.list), events.list)
    print("✓ four waiting events (handled), none for the RuntimeError that wraps the last")
    return True


async def test_recovery():
    print("\nTEST 7: 'ok' only when a later success proves the condition ended...")
    events = Events()
    t = tg(events)
    t.message_engine.get_message_count = raising(rpc(401, 'AUTH_KEY_UNREGISTERED'))
    await caught(t.get_message_count(1))
    t.message_engine.get_message_count = answered(t, 5)
    await t.get_message_count(1)
    check(events.verdicts() == ['logged out', 'ok'], events.verdicts())
    check((events.list[1]['scope'], events.list[1]['source']) == ('account', 'recovery'), events.list[1])
    print("✓ logged out, then any success: ok for the account")

    events = Events()
    t = tg(events)
    t.message_engine.fetch_messages = raising(rpc(420, 'FROZEN_METHOD_INVALID'))
    await caught(t.get_messages(group_id=9))
    t.message_engine.get_message_count = answered(t, 3)
    await t.get_message_count(9)
    check(events.verdicts() == ['restricted'], events.verdicts())
    t.message_engine.fetch_messages = answered(t, pd.DataFrame())
    await t.get_messages(group_id=9)
    check(events.verdicts() == ['restricted', 'ok'], events.verdicts())
    print("✓ restricted from get_messages: get_message_count succeeding is no ok; get_messages is")

    events = Events()
    t = tg(events)
    t.message_engine.get_message_count = raising(rpc(400, 'CHANNEL_PRIVATE'))
    await caught(t.get_message_count(123))
    t.message_engine.get_message_count = answered(t, 1)
    await t.get_message_count(456)
    check(events.verdicts() == ['no access'], events.verdicts())
    await t.get_message_count(123)
    check(events.verdicts() == ['no access', 'ok'], events.verdicts())
    check((events.list[1]['scope'], events.list[1]['group']) == ('group', 123), events.list[1])
    print("✓ no access to 123: a success on 456 is no ok; a success on 123 is")
    return True


async def test_summary():
    print("\nTEST 8: the summary in health_check()['health']...")
    t = tg(label='acct-8')
    for error, group in ((rpc(420, 'FLOOD_WAIT_120'), 1), (rpc(400, 'CHANNEL_PRIVATE'), 321),
                         (rpc(401, 'USER_DEACTIVATED_BAN'), 1), (rpc(403, 'SOMETHING_NEW_403'), 1)):
        t.message_engine.get_message_count = raising(error)
        await caught(t.get_message_count(group))
    status = await t.health_check()
    h = status['health']
    check((h['verdict'], h['error']) == ('banned', 'USER_DEACTIVATED_BAN'), h)
    check(datetime.datetime.fromisoformat(h['since']).utcoffset() == datetime.timedelta(0), h['since'])
    check(h['waiting'].get('GetHistoryRequest', {}).get('seconds') == 120, h['waiting'])
    check(list(h['no_access']) == ['321'] and h['no_access']['321']['error'] == 'CHANNEL_PRIVATE', h['no_access'])
    check((h['waits'], h['wait_seconds'], h['events'], h['last_unclassified'])
          == (1, 120, 4, 'SOMETHING_NEW_403'), h)
    check(h['account']['label'] == 'acct-8', h['account'])
    json.dumps(status)
    print(f"✓ {json.dumps(h)}")
    return True


async def test_log_mirror():
    print("\nTEST 9: one log line per event, at the verdict's level...")
    t = tg(label='acct-9')
    expected = {'waiting': logging.INFO, 'no access': logging.INFO, 'ok': logging.INFO,
                'logged out': logging.WARNING, 'banned': logging.WARNING,
                'restricted': logging.WARNING, 'unclassified': logging.WARNING}
    with captured('tgdata.tgdata.health') as log:
        for code, name in ((420, 'FLOOD_WAIT_5'), (400, 'CHANNEL_PRIVATE'), (401, 'AUTH_KEY_UNREGISTERED'),
                           (401, 'USER_DEACTIVATED_BAN'), (403, 'USER_RESTRICTED'), (401, 'SOMETHING_NEW_401')):
            t.message_engine.get_message_count = raising(rpc(code, name))
            await caught(t.get_message_count(8))
        t.message_engine.get_message_count = answered(t, 1)
        await t.get_message_count(8)              # restricted by this same method, answered: ok
    levels = {}
    for record in log.records:
        verdict = record.getMessage().split('health: ', 1)[1].split(' [', 1)[0]
        levels[verdict] = record.levelno
        check('call=get_message_count' in record.getMessage() and 'account=acct-9' in record.getMessage(),
              record.getMessage())
    check(levels == expected, {v: logging.getLevelName(n) for v, n in levels.items()})
    print("✓ WARNING: logged out, banned, restricted, unclassified; INFO: waiting, no access, ok")
    print(f"  e.g. {log.records[2].getMessage()}")
    return True


# ------------------------------------------------------------ the fixes --

async def test_polling():
    print("\nTEST 10: polling stops on what retrying cannot fix, and only on that...")
    for make, name in ((lambda: rpc(400, 'CHANNEL_PRIVATE'), 'CHANNEL_PRIVATE'),
                       (lambda: rpc(401, 'USER_DEACTIVATED_BAN'), 'a ban'),
                       (lambda: GroupAccessError("no access"), 'GroupAccessError'),
                       (lambda: AuthRequiredError("never logged in", reason='AUTH_KEY_UNREGISTERED',
                                                  first_login=True), 'AuthRequiredError')):
        events = Events()
        t = tg(events)
        error, calls = make(), []

        async def fetch(**kwargs):
            calls.append(1)
            raise error

        t.message_engine.fetch_messages = fetch
        _, raised = await caught(t.poll_for_messages(7, interval=0, max_iterations=5))
        check(raised is error, f"{name}: raised {raised!r}")
        check(len(calls) == 1, f"{name}: {len(calls)} iterations")
        if name != 'AuthRequiredError':
            check(len(events.list) == 1 and events.list[0]['call'] == 'get_messages', events.list)
    print("✓ CHANNEL_PRIVATE, a ban, GroupAccessError, AuthRequiredError: stopped after one "
          "iteration with the same exception, reported once")

    def gave_up():
        try:
            raise wait(5)
        except errors.FloodWaitError as e:
            try:
                raise RuntimeError("Giving up after 4 rate-limit interruptions") from e
            except RuntimeError as r:
                return r

    for make, name in ((lambda: ConnectionError("network down"), 'ConnectionError'),
                       (gave_up, "the fetch loop's give-up"),
                       (lambda: rpc(500, 'SOME_SERVER_ERROR'), 'a 500')):
        t, calls = tg(), []

        async def fetch(**kwargs):
            calls.append(1)
            raise make()

        t.message_engine.fetch_messages = fetch
        result, raised = await caught(t.poll_for_messages(7, interval=0, max_iterations=3))
        check(raised is None and len(calls) == 3, f"{name}: raised {raised!r} after {len(calls)}")
    print("✓ a network error, the give-up after flood waits, a 500: retried until max_iterations")

    t = tg()
    t.message_engine.fetch_messages = returning(pd.DataFrame({'MessageId': [1, 2]}))
    callback_error = ValueError("a bug in the caller's callback")

    async def callback(df):
        raise callback_error

    _, raised = await caught(t.poll_for_messages(7, interval=0, max_iterations=3, callback=callback))
    check(raised is callback_error, f"raised {raised!r}")
    print("✓ an exception in the callback reaches the caller")
    return True


async def test_validate_connection():
    print("\nTEST 11: validate_connection() — False with the reason, reported, never a recovery...")
    events = Events()
    t = tg(events)
    try:
        try:
            raise rpc(401, 'AUTH_KEY_UNREGISTERED', request=GetStateRequest())
        except errors.RPCError as problem:
            raise AuthRequiredError("logged out", reason='AUTH_KEY_UNREGISTERED') from problem
    except AuthRequiredError as e:
        logout = e
    t.connection_engine.get_client = raising(logout)
    with captured('tgdata.connection_engine') as log:
        check(await t.validate_connection() is False, "validate_connection() did not return False")
    check(events.verdicts() == ['logged out'], events.verdicts())
    check((events.list[0]['source'], events.list[0]['call']) == ('swallowed', 'validate_connection'),
          events.list[0])
    lines = [(r.levelno, r.getMessage()) for r in log.records]
    check((logging.WARNING, "Connection validation failed: logged out (AUTH_KEY_UNREGISTERED)") in lines, lines)
    print("✓ False; WARNING 'Connection validation failed: logged out (AUTH_KEY_UNREGISTERED)'; "
          "one swallowed event; no ok")

    client = scripted_client(t, [rpc(401, 'AUTH_KEY_UNREGISTERED'), rpc(401, 'AUTH_KEY_UNREGISTERED')])
    t.connection_engine.get_client = returning(client)
    check(await t.validate_connection() is False, "a logout behind get_me() returning None passed")
    check(client._sender.sent == ['GetUsersRequest', 'GetStateRequest'], client._sender.sent)
    check(events.verdicts() == ['logged out', 'logged out'], events.verdicts())
    print("✓ a logout Telethon's get_me() turns into None is asked about directly: False, reported")

    me = types.User(id=1, is_self=True, access_hash=1, first_name='me')
    t.connection_engine.get_client = returning(scripted_client(t, [[me]]))
    check(await t.validate_connection() is True, "a healthy connection failed")
    check(events.verdicts() == ['logged out', 'logged out', 'ok'], events.verdicts())
    print("✓ a later True is a recovery: ok")
    return True


# ---------------------------------------------------- sources and safety --

async def test_real_time():
    print("\nTEST 12: the real-time listener's logout is reported and still raised...")
    events = Events()
    t = tg(events)
    error = rpc(401, 'AUTH_KEY_UNREGISTERED')

    class Listener:
        async def run_until_disconnected(self):
            raise error

    t.connection_engine.get_client = returning(Listener())
    _, raised = await caught(t.run_with_event_loop())
    check(raised is error, f"raised {raised!r}")
    check(events.verdicts() == ['logged out'] and events.list[0]['call'] == 'run_with_event_loop', events.list)
    print("✓ logged out, call=run_with_event_loop; the same exception propagated")
    return True


async def test_no_callback():
    print("\nTEST 13: without a health_callback, everything behaves as before...")
    t = TgData(write_ini())
    error = rpc(400, 'CHANNEL_PRIVATE')
    t.message_engine.get_message_count = raising(error)
    _, raised = await caught(t.get_message_count(77))
    check(raised is error, f"raised {raised!r}")
    t.message_engine.get_message_count = answered(t, 42)
    check(await t.get_message_count(77) == 42, "a different result")
    t.message_engine.fetch_messages = returning(pd.DataFrame({'MessageId': [3]}))
    df = await t.get_messages(group_id=77)
    check(list(df['MessageId']) == [3], "a different DataFrame")
    check(t.get_message_count.__name__ == 'get_message_count'
          and 'group_id' in inspect.signature(t.get_message_count).parameters, "the method's signature changed")
    check((await t.health_check())['health']['events'] == 2, "the summary is still kept")
    print("✓ same exception object, same results, same signatures; the summary is kept anyway")
    return True


async def test_fail_safe():
    print("\nTEST 14: a bug in the health code never changes what a call raises or returns...")
    events = Events()
    t = tg(events)
    t.message_engine.get_message_count = raising(rpc(401, 'AUTH_KEY_UNREGISTERED'))
    await caught(t.get_message_count(1))                   # a pending recovery for the next success

    async def broken(*args, **kwargs):
        raise KeyError("a bug in the health code")

    t._health._emit = broken
    t._health._deliver = broken
    with captured('tgdata.health') as log:
        error = rpc(400, 'CHANNEL_PRIVATE')
        t.message_engine.get_message_count = raising(error)
        _, raised = await caught(t.get_message_count(2))
        check(raised is error, f"a failing call raised {raised!r}")
        t.message_engine.get_message_count = answered(t, 11)
        check(await t.get_message_count(2) == 11, "a succeeding call lost its result")

        async def swallowing(group_id):
            await health.report(rpc(401, 'SESSION_REVOKED'), 'swallowed')    # an engine site
            return 12

        t.message_engine.get_message_count = swallowing
        check(await t.get_message_count(2) == 12, "an engine report broke the call")
    warnings = [r for r in log.records if r.levelno == logging.WARNING]
    check(len(warnings) == 1 and 'health reporting failed' in warnings[0].getMessage() and warnings[0].exc_info,
          [r.getMessage() for r in log.records])
    print("✓ the same exception; the same results; 'health reporting failed' once at WARNING")

    t = tg(Events())

    def broken_record(*args, **kwargs):
        raise KeyError("a bug in the health code")

    t._health._record = broken_record
    client = scripted_client(t, [wait(1), state()])

    async def count(group_id):
        await client(GetStateRequest())
        return 13

    t.message_engine.get_message_count = count
    check(await t.get_message_count(3) == 13, "a broken sleep capture broke Telethon's request")
    print("✓ a bug while capturing a silent sleep never reaches Telethon's request")
    return True


async def test_owner_task():
    print("\nTEST 15: a sleep in a task started during a call belongs to the account, not the call...")
    events = Events()
    t = tg(events)
    client = scripted_client(t, [wait(1), state()])

    async def count(group_id):
        task = asyncio.get_running_loop().create_task(client(GetStateRequest()))
        await task                                   # the call is still active while the task sleeps
        return 1

    t.message_engine.get_message_count = count
    await t.get_message_count(5)
    check(events.verdicts() == ['waiting'], events.verdicts())
    sleep = events.list[0]
    check((sleep['source'], sleep['call'], sleep['group']) == ('sleep', None, None), sleep)
    check(t._health.snapshot()['waiting'] == {}, t._health.snapshot()['waiting'])
    print("✓ waiting with call=None, no open wait, no ok")
    return True


async def test_no_self_recovery():
    print("\nTEST 16: a call never recovers from what it reported itself (discovery's real code)...")
    events = Events()
    t = tg(events)
    t.connection_engine.session = yielding(scripted_client(t, {SearchRequest: [rpc(401, 'AUTH_KEY_UNREGISTERED')]}))
    df = await t.search_groups("rooms", pace=0)
    check(df.empty, "rows from nowhere")
    check(events.verdicts() == ['logged out'], events.verdicts())
    check((events.list[0]['source'], events.list[0]['call']) == ('swallowed', 'search_groups'), events.list[0])
    check(t._health.snapshot()['verdict'] == 'logged out', "the summary forgot the logout")
    print("✓ a search that swallowed a logout and returned: logged out, no ok")

    events = Events()
    t = tg(events)
    t.connection_engine.session = yielding(scripted_client(t, {SearchRequest: [wait(1), found()]}))
    await t.search_groups("rooms", pace=0)
    check(events.verdicts() == ['waiting', 'ok'], events.verdicts())
    check([(e['source'], e['request']) for e in events.list]
          == [('handled', 'SearchRequest'), ('recovery', 'SearchRequest')], events.list)
    print("✓ a wait discovery slept, then the retried request succeeded: ok for SearchRequest")

    events = Events()
    t = tg(events)
    t.connection_engine.session = yielding(scripted_client(t, {ResolveUsernameRequest: [wait(30)]}))
    df = await t.similar_groups("@SeedRoom", pace=0)
    check(df.empty, "rows from nowhere")
    check(events.verdicts() == ['waiting'], events.verdicts())
    event = events.list[0]
    check((event['source'], event['request'], event['group'], event['wait_seconds'])
          == ('swallowed', 'ResolveUsernameRequest', 'seedroom', 30), event)
    check('ResolveUsernameRequest' in t._health.snapshot()['waiting'], t._health.snapshot()['waiting'])
    print("✓ a lookup wait discovery skipped: waiting, still open in the summary, no ok")
    return True


async def test_per_item_group():
    print("\nTEST 17: a per-item group is the item itself, normalised...")
    events = Events()
    t = tg(events)
    t.connection_engine.session = yielding(scripted_client(t, {ResolveUsernameRequest: [rpc(400, 'CHANNEL_PRIVATE')]}))
    await t.similar_groups("@RoomName", pace=0)
    check(events.verdicts() == ['no access'], events.verdicts())
    check((events.list[0]['group'], events.list[0]['source']) == ('roomname', 'swallowed'), events.list[0])
    check(list(t._health.snapshot()['no_access']) == ['roomname'], t._health.snapshot()['no_access'])
    t.message_engine.fetch_messages = answered(t, pd.DataFrame())
    await t.get_messages(group_id="https://t.me/RoomName")
    check(events.verdicts() == ['no access', 'ok'] and events.list[1]['group'] == 'roomname', events.list)
    print("✓ group 'roomname' (from '@RoomName'); a later get_messages naming it recovered it")
    return True


async def test_health_check():
    print("\nTEST 18: health_check() asks Telegram — a logout behind get_me() is found and reported...")
    events = Events()
    t = tg(events)
    client = scripted_client(t, [rpc(401, 'AUTH_KEY_UNREGISTERED'), rpc(401, 'AUTH_KEY_UNREGISTERED')])
    client.is_connected = lambda: True
    t.connection_engine._primary_client = client          # logged in once, logged out since
    status = await t.health_check()
    check(status['primary_connection'] is False, "a logged-out connection was called healthy")
    check(status['errors'] == ["Primary connection error: logged out (AUTH_KEY_UNREGISTERED)"], status['errors'])
    check(client._sender.sent == ['GetUsersRequest', 'GetStateRequest'], client._sender.sent)
    check(events.verdicts() == ['logged out'], events.verdicts())
    check((events.list[0]['source'], events.list[0]['call']) == ('swallowed', 'health_check'), events.list[0])
    check(status['health']['verdict'] == 'logged out', "['health'] disagrees with the same result")
    json.dumps(status)
    print("✓ unhealthy; errors: 'logged out (AUTH_KEY_UNREGISTERED)'; one event; ['health'] agrees")

    client._sender.script.append([types.User(id=1, is_self=True, access_hash=1, first_name='me')])  # logged in again
    status = await t.health_check()
    check(status['primary_connection'] is True and not status['errors'], status)
    check(events.verdicts() == ['logged out', 'ok'], events.verdicts())
    check((events.list[1]['scope'], events.list[1]['source'], events.list[1]['call'])
          == ('account', 'recovery', 'health_check'), events.list[1])
    check(status['health']['verdict'] == 'ok', "the recovery is missing from the same result's ['health']")
    print("✓ a later healthy check is a recovery, already in the same result's ['health']")

    events = Events()
    t = tg(events)
    t.message_engine.get_message_count = raising(rpc(401, 'AUTH_KEY_UNREGISTERED'))
    await caught(t.get_message_count(1))
    status = await t.health_check()                        # no connection yet: Telegram never asked
    check(status['primary_connection'] is False and events.verdicts() == ['logged out'], events.verdicts())
    check(status['health']['verdict'] == 'logged out', status['health'])
    print("✓ a check that never reached Telegram is no recovery")

    events = Events()
    t = tg(events)
    primary = scripted_client(t, [rpc(401, 'AUTH_KEY_UNREGISTERED') for _ in range(4)])   # 4 separate answers
    other = scripted_client(t, [rpc(401, 'SESSION_REVOKED'), rpc(401, 'SESSION_REVOKED')])
    for c in (primary, other):
        c.is_connected = lambda: True
    t.connection_engine._primary_client = primary
    t.connection_engine._pool = ConnectionPool(2)
    t.connection_engine._pool.connections = [primary, other]   # the pool holds the primary too
    status = await t.health_check()
    check([entry['healthy'] for entry in status['pool_connections']] == [False, False], status['pool_connections'])
    check(len(status['errors']) == 3, status['errors'])
    check([e['error'] for e in events.list] == ['AUTH_KEY_UNREGISTERED', 'SESSION_REVOKED'], events.list)
    print("✓ with a pool: every connection checked; the primary reported once, not twice")
    return True


async def test_concurrent_answer():
    print("\nTEST 19: a call answered before a logout, and finishing after it, is no recovery...")
    events = Events()
    t = tg(events)
    t.connection_engine.session = yielding(scripted_client(t, {SearchRequest: [found()]}))
    search = asyncio.create_task(t.search_groups("rooms", pace=0.3))     # answered at once, then paces
    await asyncio.sleep(0.1)
    t.message_engine.get_message_count = raising(rpc(401, 'AUTH_KEY_UNREGISTERED'))
    await caught(t.get_message_count(1))                                   # the logout, while the search paces
    await search
    check(events.verdicts() == ['logged out'], events.verdicts())
    check(t._health.snapshot()['verdict'] == 'logged out', "a call answered before the logout recovered it")
    t.message_engine.get_message_count = answered(t, 2)
    await t.get_message_count(1)                                           # answered after the logout
    check(events.verdicts() == ['logged out', 'ok'], events.verdicts())
    print("✓ no ok from the search answered before the logout; ok from a call answered after it")
    return True


async def test_no_request_call():
    print("\nTEST 20: a call that sends no request recovers nothing...")
    events = Events()
    t = tg(events)
    for error in (rpc(400, 'CHANNEL_PRIVATE'), rpc(401, 'AUTH_KEY_UNREGISTERED')):
        t.message_engine.get_message_count = raising(error)
        await caught(t.get_message_count(123))
    check(await t.download_media_by_id(123, []) == {}, "the empty download changed")    # the real method
    check(t.connection_engine._primary_client is None, "a client was built")
    check(events.verdicts() == ['no access', 'logged out'], events.verdicts())
    summary = t._health.snapshot()
    check(summary['verdict'] == 'logged out' and '123' in summary['no_access'], summary)
    print("✓ download_media_by_id(123, []) sent nothing and recovered neither the account nor group 123")
    return True


async def test_callback_reentry():
    print("\nTEST 21: a callback that calls tgdata is not called back for its own calls' events...")
    attempts, runs = [], []
    t = None

    async def recheck(event):
        runs.append(event['verdict'])
        if event['verdict'] == 'logged out':
            await t.validate_connection()                  # "double-check before pausing the account"

    t = tg(recheck)

    async def logged_out_client():
        attempts.append(1)
        raise rpc(401, 'AUTH_KEY_UNREGISTERED')

    t.connection_engine.get_client = logged_out_client
    check(await t.validate_connection() is False, "validate_connection() changed")
    check(len(attempts) == 2 and runs == ['logged out'], (len(attempts), runs))
    check(t._health.snapshot()['events'] == 2, "the nested call's event was not recorded")
    print("✓ one nested call and one callback run; the nested event recorded, not delivered back")

    delivered, done = [], asyncio.Event()
    t = None

    async def on_wait(event):                              # scheduled: delivered from Telethon's sleep
        delivered.append((event['verdict'], event['call']))
        if event['verdict'] == 'waiting' and len(delivered) == 1:
            await t.get_message_count(2)                   # whose own request waits too
            done.set()

    t = tg(on_wait)
    clients = {1: scripted_client(t, [wait(1), state()]), 2: scripted_client(t, [wait(1), state()])}

    async def count(group_id):
        await clients[group_id](GetStateRequest())         # Telethon sleeps 1 s silently
        return group_id

    t.message_engine.get_message_count = count
    await t.get_message_count(1)
    await asyncio.wait_for(done.wait(), timeout=10)
    check([d for d in delivered if d[0] == 'waiting'] == [('waiting', 'get_message_count')], delivered)
    check(t._health.snapshot()['waits'] == 2, t._health.snapshot()['waits'])
    print("✓ the scheduled path too: the callback's own call slept, was counted, and was not delivered back")
    return True


async def main():
    print("Account Health Event Tests")
    print("=" * 60)
    logging.getLogger('tgdata').addHandler(logging.NullHandler())   # keep the expected warnings off stderr
    tests = [test_classifier, test_boundary, test_delivery, test_silent_sleeps, test_two_accounts,
             test_counted_once, test_recovery, test_summary, test_log_mirror, test_polling,
             test_validate_connection, test_real_time, test_no_callback, test_fail_safe,
             test_owner_task, test_no_self_recovery, test_per_item_group, test_health_check,
             test_concurrent_answer, test_no_request_call, test_callback_reentry]
    results = []
    try:
        for test in tests:
            try:
                results.append(await asyncio.wait_for(test(), timeout=60))
            except Exception as e:  # noqa: BLE001
                print(f"✗ {type(e).__name__}: {e}")
                results.append(False)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("\nSummary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
