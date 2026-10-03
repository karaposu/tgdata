"""Offline probe for issue #4's open mechanics, on the installed Telethon (1.45.0).

Drives Telethon's REAL request path (TelegramClient._call / __call__) with a fake
sender, so the flood-wait sleep, its log record and its logger are Telethon's own.
No network, no session on disk, no login.

Questions settled:
  S1  is a <=60 s wait invisible under a plain logging.basicConfig()?
  S2  candidate C2: a FILTER on telethon.client.users + a sentinel level + context
      variables -- captures the sleep, leaks no INFO, keeps Telethon warnings
  S3  a user who sets telethon.client.users to INFO after tgdata still sees lines
  S4  a user who sets the 'telethon' parent to INFO still sees lines
  S5  candidate per-client base_logger: where the client's warnings land
  S6  two accounts sleeping concurrently are attributed correctly
  S7  Telethon's background tasks inherit context at creation: stale call hazard + fix
  S8  dictConfig(disable_existing_loggers=True) after install
  S9  async callback from the synchronous filter; asyncio.run cancels pending tasks
  S10 client(request, flood_sleep_threshold=0) -- does the per-call threshold work?
  S11 a wait above the client threshold raises and logs no sleep record (no double count)
"""
import asyncio, contextvars, datetime, io, logging, logging.config, signal, sys

signal.alarm(120)

import telethon
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl import types
from telethon.tl.functions.updates import GetStateRequest
from telethon.tl.functions.messages import GetHistoryRequest

INFO = logging.INFO
SENTINEL = INFO - 1           # 19: a level no user sets by name
SLEEP_MSG = 'Sleeping%s for %ds (%s) on %s flood wait'
_account = contextvars.ContextVar('tgdata_health_account', default=None)
_call = contextvars.ContextVar('tgdata_health_call', default=None)


class SleepCapture(logging.Filter):
    """Candidate C2: sees every record logged on telethon.client.users, captures the
    sleep records it can attribute, and lets through only what the user's own levels
    would have let through."""
    def __init__(self):
        super().__init__()
        self.user_level = logging.NOTSET     # what the user set on this logger, if anything
        self.user_disabled = False
        self.captured = []
        self.on_capture = None

    def threshold(self, logger):
        if self.user_disabled:
            return logging.CRITICAL + 1
        if self.user_level != logging.NOTSET:
            return self.user_level
        return logger.parent.getEffectiveLevel()

    def filter(self, record):
        if record.msg == SLEEP_MSG and isinstance(record.args, tuple) and len(record.args) == 4:
            account = _account.get()
            if account is not None:
                early, seconds, _td, request = record.args
                event = dict(account=account, call=_call.get(), request=request,
                             seconds=seconds, early=bool(early.strip()))
                self.captured.append(event)
                if self.on_capture:
                    self.on_capture(event)
        return record.levelno >= self.threshold(logging.getLogger(record.name))


def install():
    lg = logging.getLogger('telethon.client.users')
    cap = SleepCapture()
    cap.user_level = lg.level
    lg.addFilter(cap)
    lg.setLevel(SENTINEL)
    return lg, cap


def ensure(lg, cap):
    """Run at every public-call boundary: notice user changes, keep capture alive."""
    if lg.level != SENTINEL:
        cap.user_level = lg.level
        lg.setLevel(SENTINEL)
    if lg.disabled:
        cap.user_disabled = True
        lg.disabled = False


class FakeSender:
    def __init__(self, plan):
        self.plan = list(plan)

    def send(self, request, ordered=False):
        item = self.plan.pop(0)
        fut = asyncio.get_running_loop().create_future()
        if isinstance(item, BaseException):
            fut.set_exception(item)
        else:
            fut.set_result(item)
        return fut


def state():
    return types.updates.State(pts=1, qts=1, date=datetime.datetime.now(), seq=1, unread_count=0)


def new_client(**kw):
    return TelegramClient(StringSession(), 12345, '0123456789abcdef0123456789abcdef', **kw)


def reset_logging():
    for name in [None, 'telethon', 'telethon.client', 'telethon.client.users', 'telethon.network',
                 'tgdata', 'tgdata.acct', 'tgdata.acct.A', 'tgdata.acct.A.client',
                 'tgdata.acct.A.client.users']:
        lg = logging.getLogger(name)
        for h in list(lg.handlers):
            lg.removeHandler(h)
        for f in list(lg.filters):
            lg.removeFilter(f)
        lg.setLevel(logging.NOTSET if name else logging.WARNING)
        lg.propagate = True
        lg.disabled = False
    logging.disable(logging.NOTSET)


def stream_handler(target):
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    h.setFormatter(logging.Formatter('%(levelname)s %(name)s: %(message)s'))
    logging.getLogger(target).addHandler(h)
    return buf


async def one_wait(client, request=None, seconds=1):
    client._sender = FakeSender([errors.FloodWaitError(request=None, capture=seconds), state()])
    return await client._call(client._sender, request or GetStateRequest())


def lines(buf):
    return [l for l in buf.getvalue().splitlines() if l.strip()]


def show(title, ok, detail=''):
    print(f"[{'PASS' if ok else 'FAIL'}] {title}" + (f"\n       {detail}" if detail else ''))


async def main():
    print(f"telethon {telethon.__version__}, python {sys.version.split()[0]}\n")

    # S1 -- baseline: the user ran logging.basicConfig(); tgdata captures nothing
    reset_logging(); root = stream_handler(None)
    c = new_client()
    await one_wait(c)
    show("S1 a 1 s Telethon sleep is invisible under basicConfig (root WARNING)",
         lines(root) == [], f"root saw {lines(root)}")

    # S2 -- C2 installed; user config = basicConfig + a handler on 'telethon' + one on 'telethon.network'
    reset_logging(); root = stream_handler(None); tel = stream_handler('telethon'); net = stream_handler('telethon.network')
    lg, cap = install()
    c = new_client()
    tok_a, tok_c = _account.set('A'), _call.set('get_messages#1')
    ensure(lg, cap)
    await one_wait(c, GetHistoryRequest(peer=types.InputPeerEmpty(), offset_id=0, offset_date=None,
                                        add_offset=0, limit=1, max_id=0, min_id=0, hash=0))
    c._log['telethon.client.users'].warning('Telegram is having internal issues %s: %s', 'RpcCallFailError', 'x')
    c._log['telethon.network.mtprotosender'].warning('network trouble (synthetic)')
    _call.reset(tok_c); _account.reset(tok_a)
    ev = cap.captured
    show("S2a sleep captured with account, call, request type and seconds",
         ev == [dict(account='A', call='get_messages#1', request='GetHistoryRequest', seconds=1, early=False)], f"captured={ev}")
    show("S2b no INFO line reaches the root console handler",
         not any(l.startswith('INFO') for l in lines(root)), f"root saw {lines(root)}")
    show("S2c Telethon WARNINGs still reach root and the user's 'telethon' handler",
         sum('WARNING' in l for l in lines(root)) == 2 and sum('WARNING' in l for l in lines(tel)) == 2,
         f"telethon handler saw {lines(tel)}")
    show("S2d a user's handler on 'telethon.network' still matches that client's network logs",
         lines(net) == ['WARNING telethon.network.mtprotosender: network trouble (synthetic)'], f"net saw {lines(net)}")

    # S3 -- user sets telethon.client.users to INFO AFTER tgdata installed (find_rooms.py style)
    reset_logging(); root = stream_handler(None)
    lg, cap = install()
    logging.getLogger('telethon.client.users').setLevel(INFO)          # the user's line
    c = new_client(); tok = _account.set('A'); ensure(lg, cap)
    await one_wait(c); _account.reset(tok)
    show("S3 user's own INFO on telethon.client.users still prints the sleep, and tgdata captures it",
         any('Sleeping for 1s' in l for l in lines(root)) and len(cap.captured) == 1, f"root saw {lines(root)}")

    # S4 -- user sets the 'telethon' parent to INFO
    reset_logging(); root = stream_handler(None)
    lg, cap = install(); logging.getLogger('telethon').setLevel(INFO)
    c = new_client(); tok = _account.set('A'); ensure(lg, cap)
    await one_wait(c); _account.reset(tok)
    show("S4 user's INFO on 'telethon' still prints the sleep, and tgdata captures it",
         any('Sleeping for 1s' in l for l in lines(root)) and len(cap.captured) == 1, f"root saw {lines(root)}")

    # S5 -- the per-client base_logger alternative
    reset_logging(); root = stream_handler(None); tel = stream_handler('telethon')
    c = new_client(base_logger='tgdata.acct.A')
    c._log['telethon.client.users'].warning('Telegram is having internal issues (synthetic)')
    renamed = c._log['telethon.client.users'].name
    show("S5a with base_logger the client's warnings bypass the user's 'telethon' handler",
         lines(tel) == [] and any('tgdata.acct.A.client.users' in l for l in lines(root)),
         f"logger name={renamed}; telethon handler saw {lines(tel)}; root saw {lines(root)}")
    logging.getLogger('tgdata.acct.A.client.users').setLevel(INFO)     # what capture would need
    await one_wait(c)
    show("S5b enabling INFO on the per-client logger leaks the sleep line to root",
         any(l.startswith('INFO tgdata.acct.A.client.users') for l in lines(root)), f"root saw {lines(root)[-1:]}")

    # S6 -- two accounts sleeping at the same time
    reset_logging(); root = stream_handler(None)
    lg, cap = install()
    async def account_call(name, seconds):
        _account.set(name); _call.set(f'{name}:fetch'); ensure(lg, cap)
        await one_wait(new_client(), seconds=seconds)
    await asyncio.gather(asyncio.create_task(account_call('A', 1)), asyncio.create_task(account_call('B', 2)))
    got = sorted((e['account'], e['call'], e['seconds']) for e in cap.captured)
    show("S6 concurrent sleeps on two accounts are attributed to the right account and call",
         got == [('A', 'A:fetch', 1), ('B', 'B:fetch', 2)], f"captured={got}")

    # S7 -- Telethon creates its updates task inside connect(), i.e. inside the caller's context
    reset_logging(); lg, cap = install()
    later = asyncio.Event()
    async def background_loop(client):            # stands in for Telethon's _update_loop
        await later.wait()
        await one_wait(client)                     # a GetDifference-style sleep, long after the call
    async def public_call(clear_call_around_connect):
        _account.set('A'); _call.set('get_messages#7'); ensure(lg, cap)
        client = new_client()
        if clear_call_around_connect:
            tok = _call.set(None)
            task = asyncio.get_running_loop().create_task(background_loop(client))
            _call.reset(tok)
        else:
            task = asyncio.get_running_loop().create_task(background_loop(client))
        return task
    t = await asyncio.create_task(public_call(False)); later.set(); await t; later.clear()
    stale = cap.captured[-1]
    t = await asyncio.create_task(public_call(True)); later.set(); await t
    fixed = cap.captured[-1]
    show("S7a hazard: a background task created during a call keeps that call's context after it ends",
         stale['call'] == 'get_messages#7', f"background sleep attributed to call={stale['call']!r}")
    show("S7b fix: clearing the call variable around connect() keeps the account, drops the stale call",
         fixed['account'] == 'A' and fixed['call'] is None, f"background sleep -> {fixed}")

    # S8 -- dictConfig with disable_existing_loggers=True after tgdata installed
    reset_logging(); lg, cap = install()
    logging.config.dictConfig({'version': 1, 'handlers': {'h': {'class': 'logging.StreamHandler', 'stream': 'ext://sys.stderr'}},
                               'root': {'handlers': ['h'], 'level': 'WARNING'}})
    disabled_after_dictconfig = lg.disabled
    c = new_client(); tok = _account.set('A')
    await one_wait(c); before = len(cap.captured)
    ensure(lg, cap); await one_wait(c); after = len(cap.captured); _account.reset(tok)
    show("S8 dictConfig disables the logger (capture dies); the boundary check restores capture",
         disabled_after_dictconfig and before == 0 and after == 1,
         f"disabled={disabled_after_dictconfig}, captured before ensure={before}, after={after}")

    # S9 -- async callback from the synchronous filter
    reset_logging(); lg, cap = install()
    delivered, errors_logged, keep = [], [], set()
    async def async_cb(event):
        delivered.append(event)
        raise RuntimeError('monitor bug')
    def schedule(event):
        task = asyncio.get_running_loop().create_task(async_cb(event))
        keep.add(task)
        def done(t):
            keep.discard(t)
            if not t.cancelled() and t.exception():
                errors_logged.append(repr(t.exception()))
        task.add_done_callback(done)
    cap.on_capture = schedule
    c = new_client(); tok = _account.set('A'); ensure(lg, cap)
    await one_wait(c, seconds=1); _account.reset(tok)
    await asyncio.sleep(0)
    show("S9a an async callback scheduled from the filter runs during Telethon's own sleep; its error is contained",
         len(delivered) == 1 and errors_logged == ["RuntimeError('monitor bug')"],
         f"delivered={len(delivered)}, contained errors={errors_logged}")


def s9b():
    """asyncio.run() cancels tasks still pending when main returns."""
    ran = []
    async def cb():
        await asyncio.sleep(0)
        ran.append(True)
    async def main_returning_right_after_scheduling():
        asyncio.get_running_loop().create_task(cb())     # scheduled, never awaited
        raise_after = True
        return raise_after
    asyncio.run(main_returning_right_after_scheduling())
    show("S9b a callback scheduled just before the program ends is cancelled by asyncio.run (lost)",
         ran == [], f"callback ran: {bool(ran)}")


async def thresholds():
    reset_logging(); lg, cap = install(); tok = _account.set('A'); ensure(lg, cap)
    # S10 -- per-call threshold through the public __call__
    c = new_client()
    c._sender = FakeSender([errors.FloodWaitError(request=None, capture=1), state()])
    raised = False
    try:
        await c(GetStateRequest(), flood_sleep_threshold=0)
    except errors.FloodWaitError:
        raised = True
    show("S10 client(request, flood_sleep_threshold=0) still sleeps instead of raising (per-call threshold ignored)",
         not raised and len(cap.captured) == 1, f"raised={raised}, sleep records captured={len(cap.captured)}")
    # S11 -- a wait above the CLIENT threshold raises and logs nothing
    c = new_client(); c.flood_sleep_threshold = 0
    c._sender = FakeSender([errors.FloodWaitError(request=None, capture=1), state()])
    n = len(cap.captured); raised = False
    try:
        await c._call(c._sender, GetStateRequest())
    except errors.FloodWaitError:
        raised = True
    show("S11 a wait above the client threshold raises and writes no sleep record (no double count)",
         raised and len(cap.captured) == n, f"raised={raised}, new sleep records={len(cap.captured) - n}")
    _account.reset(tok)


asyncio.run(main())
s9b()
asyncio.run(thresholds())
