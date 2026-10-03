"""
Smoke test for the fixed device identity.

  1. no identity keys: every client presents Telethon's machine defaults,      (no network)
     exactly as before
  2. pinned keys are presented as written — spaces kept, quotes and inline     (no network)
     comments stripped; lang_code alone sets system_lang_code too
  3. the real connection paths carry it: the use-and-close client and the      (no network)
     persistent client (driven with a stand-in that refuses to connect), and
     each pool connection
  4. device_identity(): what is presented now, and config lines that pin it    (no network)
     — pasting them back reproduces the same identity
  5. health_check reports the presented identity                               (no network)
  6. Telegram accepts a connection presenting a pinned identity                (Telegram, throwaway session)

Item 6 reads only api_id / api_hash from the config and uses a throwaway session
in a temp folder: no account is logged in, and the account's own session is never
opened. Whether Telegram's active-sessions list SHOWS the pinned values is not
checked here — that needs a logged-in account (pending a real test).
"""
# To run: python -m tgdata.smoke_tests.test_13_device_identity [config.ini]

import asyncio
import configparser
import os
import shutil
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from telethon import TelegramClient
from telethon.sessions import StringSession

import tgdata.connection_engine as ce
from tgdata import TgData, AuthRequiredError
from tgdata.connection_engine import ConnectionEngine, IDENTITY_KEYS

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "config.ini"
TMP = tempfile.mkdtemp(prefix="tgdata_identity_test_")

PINNED = {'device_model': 'PC 64bit', 'system_version': 'Windows 11', 'app_version': '4.16.8 x64',
          'lang_code': 'ru', 'system_lang_code': 'ru'}
PINNED_INI = ("device_model = 'PC 64bit'   ; the account's laptop\n"
              "system_version = Windows 11 # pinned 2026-10-03\n"
              "app_version = \"4.16.8 x64\"\n"
              "lang_code = ru\n")


def write_ini(name: str, body: str) -> str:
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write("[Telegram]\napi_id = 12345\napi_hash = 0123456789abcdef0123456789abcdef\n"
                f"session_file = {os.path.join(TMP, 'throwaway_' + name)}\n" + body)
    return path


def sent(client) -> dict:
    """The identity a client would send to Telegram (Telethon's InitConnection)."""
    return {key: getattr(client._init_request, key) for key in IDENTITY_KEYS}


def telethon_defaults() -> dict:
    return sent(TelegramClient(StringSession(), 12345, "0123456789abcdef0123456789abcdef"))


# ------------------------------------------------------------ no network --

async def test_defaults():
    print("TEST 1: no identity keys — Telethon's machine defaults, as before...")
    try:
        eng = ConnectionEngine(write_ini("plain.ini", ""))
        presented = sent(eng._new_client())
        assert presented == telethon_defaults(), presented
        assert eng.device_identity()['pinned'] == []
        print(f"✓ Unpinned: {presented}")
        return True
    except Exception as e:
        print(f"✗ Defaults test failed: {e}")
        return False


async def test_pinned():
    print("\nTEST 2: pinned keys are presented as written...")
    try:
        eng = ConnectionEngine(write_ini("pinned.ini", PINNED_INI))
        presented = sent(eng._new_client())
        assert presented == PINNED, presented
        print("✓ Spaces kept, quotes and inline comments stripped; lang_code alone set system_lang_code")

        eng = ConnectionEngine(write_ini("langs.ini", "lang_code = ru\nsystem_lang_code = en\n"))
        p = sent(eng._new_client())
        assert (p['lang_code'], p['system_lang_code']) == ('ru', 'en'), p
        assert p['device_model'] == telethon_defaults()['device_model']
        print("✓ An explicit system_lang_code wins; unpinned fields keep the machine defaults")

        eng = ConnectionEngine(write_ini("empty.ini", "device_model =\napp_version = ''\n"))
        assert sent(eng._new_client()) == telethon_defaults()
        print("✓ Empty values count as not pinned")
        return True
    except Exception as e:
        print(f"✗ Pinned test failed: {e}")
        return False


async def test_connection_paths():
    print("\nTEST 3: the real connection paths carry the identity...")
    created = []

    class StandIn(ce.TelegramClient):
        """Records what each path builds, and refuses to open a connection."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created.append(sent(self))

        async def connect(self):
            raise ConnectionError("stand-in: no network in this test")

    original = ce.TelegramClient
    ce.TelegramClient = StandIn
    try:
        eng = ConnectionEngine(write_ini("paths.ini", PINNED_INI), pool_size=3)
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
        assert len(created) == 3, len(created)
        assert all(c == PINNED for c in created), created
        print(f"✓ Use-and-close, persistent and pool clients all present the pinned identity ({len(created)} built)")
        return True
    except Exception as e:
        print(f"✗ Connection-path test failed: {type(e).__name__}: {e}")
        return False
    finally:
        ce.TelegramClient = original


async def test_pin_round_trip():
    print("\nTEST 4: device_identity() and pinning what is presented now...")
    try:
        before = TgData(write_ini("unpinned.ini", "")).device_identity()
        assert before['pinned'] == [] and before['presented'] == telethon_defaults()
        print("  presented now:\n    " + before['config_lines'].replace("\n", "\n    "))
        after = TgData(write_ini("repinned.ini", before['config_lines'] + "\n")).device_identity()
        assert after['presented'] == before['presented'], (after, before)
        assert after['pinned'] == list(IDENTITY_KEYS), after['pinned']
        print("✓ Pasting config_lines back pins exactly the same identity, all five fields")
        return True
    except Exception as e:
        print(f"✗ Round-trip test failed: {e}")
        return False


async def test_health():
    print("\nTEST 5: health_check reports the presented identity...")
    try:
        eng = ConnectionEngine(write_ini("health.ini", PINNED_INI))
        eng._load_config()
        health = await eng.health_check()
        assert health['device_identity'] == PINNED, health['device_identity']
        print("✓ health_check()['device_identity'] matches the pinned values")
        return True
    except Exception as e:
        print(f"✗ Health test failed: {e}")
        return False


# ------------------------------------------------------------- Telegram --

async def test_telegram_accepts():
    print("\nTEST 6: Telegram accepts a connection presenting a pinned identity (throwaway session)...")
    if not os.path.exists(CONFIG):
        print(f"! skipped — {CONFIG} not found (only its api_id / api_hash are read)")
        return True
    try:
        cp = configparser.ConfigParser()
        cp.read(CONFIG)
        sec = next(s for s in cp.sections() if s.lower() == 'telegram')
        path = os.path.join(TMP, "live.ini")
        with open(path, "w") as f:
            f.write(f"[Telegram]\napi_id = {cp[sec]['api_id'].strip()}\napi_hash = {cp[sec]['api_hash'].strip()}\n"
                    f"session_file = {os.path.join(TMP, 'fresh_live')}\n" + PINNED_INI)
        eng = ConnectionEngine(path)
        try:
            async with eng.ephemeral_client():
                raise AssertionError("a throwaway session claims to be authorized")
        except AuthRequiredError:
            pass       # connected, Telegram took the InitConnection, answered "not logged in"
        print("✓ Connected with the pinned identity; Telegram answered 'not authorized' (a throwaway session)")
        return True
    except Exception as e:
        print(f"✗ Telegram test failed: {type(e).__name__}: {e}")
        return False


async def main():
    print("Device Identity Tests")
    print("=" * 60)
    print(f"config (item 6): {CONFIG}\n")
    tests = [test_defaults, test_pinned, test_connection_paths, test_pin_round_trip,
             test_health, test_telegram_accepts]
    results = []
    try:
        for test in tests:
            results.append(await asyncio.wait_for(test(), timeout=90))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("\nSummary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
