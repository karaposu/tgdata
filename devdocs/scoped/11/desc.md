# Issue 11 — One door to Telegram: optional per-account proxy

**Status:** ✅ IMPLEMENTED (2026-10-03, part of 0.0.8). Tracked as GitHub issue #1 ("Route every Telegram connection through the account's proxy"). Verified locally with `tgdata/smoke_tests/test_12_proxy.py`, 7/7, including a full round trip to Telegram through a local SOCKS5 relay with user/password auth. **Pending: a test through a real remote proxy**, which needs one supplied by the user (item 7 of the smoke test runs it automatically once the config has a `proxy` key).

**How it landed.** Committed directly to `main` on 2026-10-03, outside the CONTRIBUTING.md pipeline (no issue branch, plan, critic or merge gate): the code was written before issue #1 existed, and the maintainer approved the direct commit as an exception for this issue. This file and the smoke test are its whole written record.

**The default, decided.** Issue #1's text asks to refuse when an account has no proxy. The maintainer's instruction (2026-10-03) was "use the current default, and the proxy when one is added", so no `proxy` key still means a direct connection; `require_proxy = true` gives the refusal #1 describes, per account.

## What it is

- An optional `proxy` key in the `[Telegram]` section: `socks5://[user:pass@]host:port`, `socks4://…`, `http://…`. Absent, or `none`, means a direct connection, unchanged from before.
- An optional `require_proxy = true` that refuses to connect when no proxy is configured.
- One factory, `ConnectionEngine._new_client()`, now builds every `TelegramClient`: the persistent client, each pool client, and the use-and-close `ephemeral_client`. It was three separate constructor calls. `grep "TelegramClient(" tgdata/` finds only the factory.

## The rules it enforces

- **No silent fallback.** Config problems raise `ProxyConfigError` while the config is read, before any socket opens: a malformed URL, an unsupported kind (MTProto, https, no scheme), no proxy library installed, or `require_proxy` without a proxy. A dead or refusing proxy fails the connection with `ConnectionError`; the client never retries directly. Telethon's own reconnects reuse the same client, so they carry the proxy too.
- **The password never leaks.** `ConnectionConfig.proxy` is excluded from `repr`; logs and `health_check()['proxy']` show `proxy_display`, with the password masked.
- **Config parsing pitfalls handled.** The proxy keys are read raw, so the `%` of a percent-encoded password is not taken for ConfigParser interpolation. The first whitespace token is taken before quotes are stripped, so a quoted value followed by an inline `; comment` parses. Both bugs were caught by the smoke test before shipping.

## Files

`tgdata/connection_engine.py` (`ProxyConfigError`, `parse_proxy_url`, `_new_client`, `_load_config`, `health_check`), `tgdata/models.py` (`ConnectionConfig.proxy`, `proxy_display`, `require_proxy`), `tgdata/__init__.py` (export), `setup.py` (`extras_require['proxy'] = python-socks[asyncio]>=2.0`), `README.md`, `tgdata/smoke_tests/test_12_proxy.py`.

## Not in scope

MTProto proxies; per-call proxy overrides; consumers that build their own Telethon clients (they do not pass through this door).
