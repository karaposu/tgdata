# Issue 12 — A fixed device identity per account

**Status:** ✅ IMPLEMENTED (2026-10-03, part of 0.0.8). Verified with `tgdata/smoke_tests/test_13_device_identity.py`, 6/6, including a connection to Telegram that presented a pinned identity (throwaway session). **Pending:** a check on a logged-in account that Telegram's active-sessions list shows the pinned values.

**How it was done.** Built directly at the maintainer's request ("implement it here now without any gh issues"), outside the CONTRIBUTING.md pipeline. GitHub issue #2 ("Give each account a fixed device identity") asks for this; per that instruction it was not updated. Committed directly to `main` on 2026-10-03, at the maintainer's decision, as part of the bootstrap before the repository adopted CONTRIBUTING.md and cut `dev` — so that the first pipeline issue (#4), which changes the same connection engine, builds on top of it rather than conflicting with it later.

## Why

Every connection tells Telegram what device it is running on (Telethon's `InitConnection`: device model, system version, app version, language codes). Unpinned, Telethon derives these from the machine and from its own version — on the Mac this was written on: `arm64`, `25.6.0`, `1.40.0`. So the same account presents a different device when read from another machine, after an OS update, and after every Telethon upgrade. Telethon sends the identity on every connection, not only at login, so the drift is real today, and a pin applies to an existing session from its next connection.

## What it is

- Five optional `[Telegram]` keys: `device_model`, `system_version`, `app_version`, `lang_code`, `system_lang_code`. Absent = Telethon's defaults, exactly as before; a missing key keeps its own default.
- Read in `ConnectionEngine._load_config` (raw, so `%` is never interpolation; inline `; comment` / `# comment` and surrounding quotes stripped; spaces kept). `lang_code` alone also sets `system_lang_code`, following Telethon's documented intent rather than its constructor default.
- Applied in `ConnectionEngine._new_client`, the single client factory from #1 — so the persistent client, every pool connection and every `ephemeral_client` carry it. Logged once per engine (pinned values, or "not pinned").
- `ConnectionEngine.device_identity()` / `TgData.device_identity()`: what connections present now, which fields are pinned, and ready-to-paste `config_lines`. No network and no session: it builds a client on an in-memory `StringSession` (never connected) and reads back what Telethon would send. This is the way to pin an existing account to what it already shows, instead of inventing new values.
- `health_check()['device_identity']` reports the presented identity.

## Not in scope, and open

- Choosing identities (realistic values, one per account) is the caller's decision; tgdata only presents what it is given.
- Whether a changing identity matters to Telegram is unmeasured — the precaution is cheap, the benefit unproven.
- The probe in `device_identity()` reads Telethon's private `_init_request`; it falls back to the configured values if a future Telethon renames it.

## Files

`tgdata/connection_engine.py` (`IDENTITY_KEYS`, `_load_config`, `_identity_kwargs`, `device_identity`, `_new_client`, `health_check`), `tgdata/models.py` (five `ConnectionConfig` fields), `tgdata/tgdata.py` (`TgData.device_identity`), `README.md`, `tgdata/smoke_tests/test_13_device_identity.py` and its README entry.
