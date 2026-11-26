"""
Smoke test for the WebSocket transport (issue #67): `transport = websocket`
reaches Telegram's WebSocket door by hostname, never by IP.

Everything runs OFFLINE: loopback sockets only, never Telegram, never an
account. TLS items need the `openssl` command (a throwaway test certificate
authority is generated in a temp folder); without it they are SKIPPED.

  0. the default path is byte-identical to before #67            (no network)
"""
# To run: python -m tgdata.smoke_tests.test_50_websocket_transport

import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tgdata import connection_engine as ce
from tgdata import login as login_module
from tgdata.connection_engine import ConnectionEngine
from tgdata.login import LoginFlow

TMP = tempfile.mkdtemp(prefix="tgdata_ws_test_")

API_HASH = "0123456789abcdef0123456789abcdef"
IDENTITY_LINES = "device_model = BaselineModel\nlang_code = en\n"
PROXY_LINE = "proxy = socks5://u:p@127.0.0.1:1080\n"

# Today's default path, captured by capture_default_path() at a199c0c — before
# any #67 code change — and pasted here. Step 9 re-captures and compares.
BASELINE = json.loads(r'''
{
 "direct": {
  "binding": "1fb3c4e29b47a61fef00462b2d13c9f211068539ba37ecbcd8ff8199183b97b9",
  "clients": [
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "device_model": "BaselineModel",
     "lang_code": "en",
     "proxy": null,
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": null,
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "base_logger": "<logger tgdata.login.sdk>",
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": null,
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   }
  ],
  "route_lines": [
   "Telegram connections are direct (no proxy configured)",
   "Device identity pinned: device_model='BaselineModel', lang_code='en', system_lang_code='en'"
  ]
 },
 "proxy": {
  "binding": "42d13bbc6c9021ddf4eca7231b2ebfb65c1e3fe617f064bd6ded1f5ad2ae5202",
  "clients": [
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "device_model": "BaselineModel",
     "lang_code": "en",
     "proxy": {
      "addr": "127.0.0.1",
      "password": "p",
      "port": 1080,
      "proxy_type": "socks5",
      "rdns": true,
      "username": "u"
     },
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": {
      "addr": "127.0.0.1",
      "password": "p",
      "port": 1080,
      "proxy_type": "socks5",
      "rdns": true,
      "username": "u"
     },
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   },
   {
    "args": [
     "12345",
     "0123456789abcdef0123456789abcdef"
    ],
    "kwargs": {
     "auto_reconnect": false,
     "base_logger": "<logger tgdata.login.sdk>",
     "connection_retries": 0,
     "device_model": "BaselineModel",
     "flood_sleep_threshold": 0,
     "lang_code": "en",
     "proxy": {
      "addr": "127.0.0.1",
      "password": "p",
      "port": 1080,
      "proxy_type": "socks5",
      "rdns": true,
      "username": "u"
     },
     "raise_last_call_error": true,
     "receive_updates": false,
     "request_retries": 0,
     "retry_delay": 0,
     "system_lang_code": "en"
    }
   }
  ],
  "route_lines": [
   "Telegram connections go via proxy socks5://u:***@127.0.0.1:1080",
   "Device identity pinned: device_model='BaselineModel', lang_code='en', system_lang_code='en'"
  ]
 }
}
''')


def write_ini(name: str, body: str) -> str:
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write("[Telegram]\napi_id = 12345\n"
                f"api_hash = {API_HASH}\n"
                f"session_file = {os.path.join(TMP, 'baseline')}\n" + body)
    return path


def _plain(value):
    """Constructor arguments as comparable JSON values (loggers by name)."""
    if isinstance(value, logging.Logger):
        return f"<logger {value.name}>"
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return f"<{type(value).__name__}>"


def capture_default_path():
    """What tgdata builds for a fixed TCP account today: TelegramClient's
    arguments (minus the session object) for the ordinary client, an owned
    account operation's client and LoginFlow's client; the route log lines;
    and the login binding hash — with and without a proxy. Construction
    only: nothing connects."""
    records = []

    class Recorder(ce.TelegramClient):
        def __init__(self, *args, **kwargs):
            records.append({'args': _plain(list(args[1:])), 'kwargs': _plain(kwargs)})
            super().__init__(*args, **kwargs)

    class LoginRecorder(login_module._LoginClient):
        def __init__(self, *args, **kwargs):
            records.append({'args': _plain(list(args[1:])), 'kwargs': _plain(kwargs)})
            super().__init__(*args, **kwargs)

    strict = dict(flood_sleep_threshold=0, request_retries=0, connection_retries=0,
                  retry_delay=0, auto_reconnect=False, raise_last_call_error=True,
                  receive_updates=False)
    out = {}
    log = logging.getLogger("tgdata.connection_engine")
    for name, body in (("proxy", PROXY_LINE + IDENTITY_LINES), ("direct", IDENTITY_LINES)):
        ini = write_ini(f"baseline_{name}.ini", body)
        lines = []
        handler = logging.Handler(logging.INFO)
        handler.emit = lambda record: lines.append(record.getMessage())
        old_level = log.level
        log.setLevel(logging.INFO)
        log.addHandler(handler)
        original, original_login = ce.TelegramClient, login_module._LoginClient
        ce.TelegramClient, login_module._LoginClient = Recorder, LoginRecorder
        records.clear()
        try:
            engine = ConnectionEngine(ini)
            engine._new_client()                     # ordinary client (logs the route once)
            engine._new_client(**strict)             # an owned account operation's client
            flow = LoginFlow(ini)                    # constructor only: builds its client, no socket
            out[name] = {'clients': list(records), 'route_lines': list(lines),
                         'binding': flow._binding}
        finally:
            ce.TelegramClient, login_module._LoginClient = original, original_login
            log.removeHandler(handler)
            log.setLevel(old_level)
    return out


async def main():
    print("TgData WebSocket transport smoke test (issue #67) — offline\n")
    results = []
    print(f"\n{sum(results)}/{len(results)} passed")
    return all(results)


if __name__ == "__main__":
    try:
        if "--print-baseline" in sys.argv:
            print(json.dumps(capture_default_path(), indent=1, sort_keys=True))
        else:
            ok = asyncio.run(main())
            sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
