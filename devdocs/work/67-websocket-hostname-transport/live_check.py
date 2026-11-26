#!/usr/bin/env python3
"""
Live check for tgdata #67 (plan step 14, success criterion 14): the BUILT
WebSocket transport on the real account — tgdata's own code, through its
public API, with `transport = websocket` in the account's config.

Steps, through tgdata (TgData, interactive_login=False):
  1. connect with the account's existing session — no login, no code requested;
  2. read 5 messages (TgData.get_messages);
  3. download one media file stored on another data centre (with the client
     tgdata built);
  4. stay idle for --idle seconds (default 330);
  5. read again — the connection is expected to have been cut and reconnected
     by name in between;
  6. health_check().
It prints every "Connecting to ..." line Telethon logs — each must be a
*.web.telegram.org hostname, never an IP — and any Telegram error by name.

SAFETY — read before running:
  * Nothing else may use this account's session while this runs. Telegram
    revokes a session key used from two addresses at once (AUTH_KEY_DUPLICATED),
    which logs the account out. Stop every application using the session, then
    pass --exclusive-confirmed. The script refuses to run without it.
  * It works on a COPY of the session file and of the config (in a temp folder,
    deleted at the end); the originals are never written.
  * It never logs in and never asks Telegram for a login code.
  * Downloads go to memory only.

Usage:
    python live_check.py --config /path/to/account.ini --chat some_public_channel --exclusive-confirmed

Needs: tgdata from the feature branch with the proxy extra, Telethon 1.45.0:
    pip install "tgdata[proxy] @ git+https://github.com/karaposu/tgdata@feat/67-websocket-hostname-transport"
"""

import argparse
import asyncio
import configparser
import ipaddress
import logging
import os
import shutil
import sys
import tempfile
import time

from telethon.errors import AuthKeyDuplicatedError, RPCError

from tgdata import TgData, AuthRequiredError, TransportConfigError
from tgdata.connection_engine import ConnectionEngine
from tgdata.websocket_transport import DC_HOSTS


class ConnectLines(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.lines, self.reconnects = [], 0

    def emit(self, record):
        message = record.getMessage()
        if message.startswith("Connecting to"):
            self.lines.append(message)
        elif "begin reconnect" in message:
            self.reconnects += 1


def chain(error):
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        yield error
        error = error.__cause__ or error.__context__


def duplicated(error) -> bool:
    return any(isinstance(e, AuthKeyDuplicatedError) or getattr(e, "reason", None) == "AUTH_KEY_DUPLICATED"
               for e in chain(error))


def refused(error) -> bool:
    """An account / authorization refusal anywhere in the chain."""
    for e in chain(error):
        if isinstance(e, AuthRequiredError):
            return True
        if isinstance(e, RPCError) and getattr(e, "code", None) in (401, 403, 406, 420):
            return True
    return False


def describe(error) -> str:
    for e in chain(error):
        if isinstance(e, RPCError):
            return f"{type(e).__name__} (Telegram {getattr(e, 'code', '?')}: {getattr(e, 'message', '')})"
    return f"{type(error).__name__}: {error}"


def private_copy(config_path, workdir):
    """Copy the config and its session into `workdir`; the copy's session_file
    points at the copied session. Returns the copied config's path."""
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    if not cp.read(config_path):
        raise SystemExit(f"cannot read {config_path}")
    section = next((s for s in cp.sections() if s.lower() == "telegram"), None)
    if section is None:
        raise SystemExit("no [Telegram] section")
    raw = (cp[section].get("session_file") or "").split(";")[0].split(" #")[0].strip().strip("'\"")
    if not raw:
        raise SystemExit("the config needs an explicit session_file")
    source = os.path.expanduser(raw)
    if not source.endswith(".session"):
        source += ".session"
    if not os.path.isabs(source):
        source = os.path.join(os.path.dirname(os.path.abspath(config_path)), source)
    if not os.path.exists(source):
        raise SystemExit(f"session file not found: {source}")
    shutil.copy2(source, os.path.join(workdir, "check.session"))
    cp[section]["session_file"] = os.path.join(workdir, "check")
    copy = os.path.join(workdir, "check.ini")
    fd = os.open(copy, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        cp.write(f)
    return copy


async def find_other_dc_media(client, entity, home_dc, limit):
    async for msg in client.iter_messages(entity, limit=limit):
        media = getattr(msg, "document", None) or getattr(msg, "photo", None)
        dc = getattr(media, "dc_id", None)
        if media is not None and dc and dc != home_dc and dc in DC_HOSTS:
            return msg, dc
    return None, None


async def run(args) -> int:
    workdir = tempfile.mkdtemp(prefix="tgdata67_live_")
    catcher = ConnectLines()
    tl = logging.getLogger("telethon")
    tl.setLevel(logging.INFO)
    tl.addHandler(catcher)
    results = []
    state = {"duplicated": False, "refused": False}

    def record(step, ok, detail):
        results.append((step, ok, detail))
        print(f"{'✓' if ok else ('–' if ok is None else '✗')} {step}: {detail}")

    tg = None
    try:
        config = private_copy(args.config, workdir)
        cfg = ConnectionEngine(config)._load_config()
        if cfg.transport != "websocket" or not cfg.proxy:
            raise SystemExit("the config must set transport = websocket and a proxy")
        print(f"tgdata transport = {cfg.transport}; proxy {cfg.proxy_display}; a copy of the session is used")
        tg = TgData(config_path=config, interactive_login=False)
        try:
            client = await asyncio.wait_for(tg.connection_engine.get_client(), args.timeout * 4)
            me = await asyncio.wait_for(client.get_me(), args.timeout)
            record("1 connect (existing session)", True,
                   f"logged in on DC {client.session.dc_id}; account id ends …{str(me.id)[-3:]}")
        except Exception as e:  # noqa: BLE001 — classified below
            state["duplicated"], state["refused"] = duplicated(e), refused(e)
            record("1 connect (existing session)", False, describe(e))
            raise

        entity = await client.get_entity(args.chat)
        group_id = await client.get_peer_id(entity)
        frame = await asyncio.wait_for(tg.get_messages(group_id=group_id, limit=5), args.timeout * 2)
        record("2 read (TgData.get_messages)", True, f"{len(frame)} messages")

        home = client.session.dc_id
        msg, dc = await find_other_dc_media(client, entity, home, args.search)
        if msg is None:
            record("3 other-DC download", None, f"SKIPPED — no media stored outside DC {home} in {args.chat}")
        else:
            data = await asyncio.wait_for(client.download_media(msg, file=bytes), args.timeout * 12)
            record("3 other-DC download", True, f"{len(data or b'')} bytes from DC {dc} (home DC {home})")

        print(f"… idle for {args.idle:.0f} s")
        start = time.monotonic()
        while time.monotonic() - start < args.idle:
            await asyncio.sleep(min(60, args.idle - (time.monotonic() - start)))
            print(f"   {time.monotonic() - start:.0f} s")
        frame = await asyncio.wait_for(tg.get_messages(group_id=group_id, limit=1), args.timeout * 4)
        record("4 read after idle", True, f"{len(frame)} message; reconnects seen so far: {catcher.reconnects}")

        status = await tg.health_check()
        record("5 health_check", status.get("transport") == "websocket",
               f"transport={status.get('transport')!r}, primary_connection={status.get('primary_connection')}")
    except SystemExit:
        raise
    except TransportConfigError as e:
        record("error", False, f"TransportConfigError: {e}")
    except Exception as e:  # noqa: BLE001 — classified below
        state["duplicated"] = state["duplicated"] or duplicated(e)
        state["refused"] = state["refused"] or refused(e)
        if not results or results[-1][1] is not False:
            record("error", False, describe(e))
    finally:
        if tg is not None:
            try:
                await tg.close()
            except Exception:  # noqa: BLE001
                pass
        tl.removeHandler(catcher)
        shutil.rmtree(workdir, ignore_errors=True)

    print("\nConnections Telethon opened:")
    ip_seen = False
    for line in catcher.lines:
        host = line[len("Connecting to "):].split(":")[0]
        try:
            ipaddress.ip_address(host.strip("[]"))
            ip_seen = True
            print(f"   ✗ {line}")
        except ValueError:
            print(f"   ✓ {line}")
    print(f"   reconnects: {catcher.reconnects}")

    print("\nResult")
    if state["duplicated"]:
        print("   INVALID RUN — another client was using this session (AUTH_KEY_DUPLICATED).")
        return 3
    if ip_seen:
        print("   FAIL — a connection named an IP address.")
        return 1
    if state["refused"]:
        print("   REFUSED — Telegram refused the account or its session.")
        return 1
    failed = [r for r in results if r[1] is False]
    if failed:
        print("   INCONCLUSIVE — a step failed for a reason that is not an account refusal:")
        for step, _, detail in failed:
            print(f"     {step}: {detail}")
        return 4
    skipped = [r for r in results if r[1] is None]
    print("   PASS" + (" (the other-DC download was not exercised)" if skipped else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="the account's tgdata config, with transport = websocket")
    ap.add_argument("--chat", required=True, help="a public channel the account can read (e.g. a large one)")
    ap.add_argument("--search", type=int, default=300, help="messages to search for other-DC media")
    ap.add_argument("--idle", type=float, default=330)
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--exclusive-confirmed", action="store_true",
                    help="confirm nothing else is using this account's session right now")
    args = ap.parse_args()
    if not args.exclusive_confirmed:
        print("Refusing to run: stop every application using this account's session, then pass "
              "--exclusive-confirmed. (Two simultaneous users of one session get it revoked.)")
        return 2
    logging.basicConfig(level=logging.WARNING, format="   log %(name)s %(levelname)s: %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
