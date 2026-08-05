# Trace 5 — Authentication & Session Persistence Boundary

**Category:** Integration boundary
**One-liner:** How credentials flow from `config.ini` into a live, authenticated Telegram session and how that session is persisted across runs.

---

## Entry Point

`_load_config()` reading `config.ini` (`connection_engine.py:102`), triggered on the first `get_client()`. The outbound boundary crossing is `client.start(phone=...)` in `_connect_with_retry` (`connection_engine.py:204`). Terminal state is an authenticated client backed by a `<username>.session` SQLite file on disk.

## Execution Path

1. **Parse config.** `configparser` reads the file; the section lookup is case-insensitive, scanning for `telegram`/`Telegram` (`connection_engine.py:110-118`) — a nice robustness touch.
2. **Build `ConnectionConfig`.** `api_id`, `api_hash` are required; `session_file` defaults to `'telegram_session'`; `phone`, `username` optional (`connection_engine.py:120-129`). The result is memoized.
3. **Construct client.** Session name resolved (username-or-session_file), `TelegramClient(session_name, api_id, api_hash)` (`connection_engine.py:163`).
4. **Authenticate.** `client.start(phone=config.phone)`:
   - If the `.session` file has valid auth → silent resume (no network prompt).
   - If not → Telethon sends a login code and **blocks on stdin** for it, then persists the new auth to the `.session` file.
5. **Persist.** Telethon writes/updates the SQLite `.session` file automatically; subsequent runs skip the code step.

## Resource Management

- **Durable credential artifact:** the `.session` file — effectively a bearer token for the account. It outlives the process and is Telethon-managed.
- `api_id`/`api_hash`/`phone` live in `config.ini` in plaintext.
- The config is read once and cached (`self._config`), so a mid-run edit to `config.ini` has no effect.

## Error Path

- Missing `[telegram]` section → `ValueError` (`connection_engine.py:118`).
- Missing `api_id`/`api_hash` keys → `KeyError` from the dict access (`connection_engine.py:121-122`) — not a friendly message.
- `FloodWaitError` during `start()` → slept and retried once inline (`connection_engine.py:207-216`).
- Any other connect exception → wrapped as `ConnectionError` (`connection_engine.py:220`).

## Performance Characteristics

- Config parse: negligible, once.
- `start()`: one auth round-trip when resuming; a multi-step interactive flow on first login. Because of the per-op reconnect (trace 1), the resume round-trip recurs on every operation.

## Observable Effects

- Creation/update of the `.session` SQLite file.
- On first login: an SMS/Telegram code prompt on stdin.
- Log line "Successfully connected and authenticated!" (`connection_engine.py:205`).

## Why This Design

Config-file + Telethon-session is the standard, low-friction MTProto pattern: put your API creds in a file, authenticate once interactively, and ride the persisted session forever after. The case-insensitive section handling shows deliberate care for real-world config variance. For a single-user data-extraction library this is a reasonable, conventional boundary.

---

## What feels incomplete

**The issue.** Only one auth method (phone) is implemented, despite `expansion_auth_features.md` cataloguing session-string and bot-token approaches. There's no non-interactive auth path, no `is_user_authorized()` pre-check, and no timeout — so headless first-runs hang rather than fail (cross-ref trace 1).

**ELI15.** There's exactly one way to log in, and it needs a human to type a code. The manual describes other, keyboard-free ways to log in, but none of them are built yet — so a robot running this on a server can get stuck at the login screen forever.

**Impact.** Blocks clean server/cron deployment; the only safe deploy today is "copy a pre-authorized `.session` file," which is exactly the risky practice visible in this repo (a live `.session` is committed).

**Robust Fixes / Best Practices.** Implement `StringSession` auth (portable, env-var friendly); add an `is_user_authorized()` guard that raises in non-interactive mode; add a connect timeout. Keep the phone flow for first-time setup only.

**Architectural Fix.** An `AuthProvider` strategy interface with `PhoneAuth` / `StringSessionAuth` / `BotAuth` implementations selected by config. *Reasonable given the documented intent*, though a single `session_string` config key would deliver 80% of the value with far less machinery.

**Speculative defence.** The author only ever needed their own phone login, done once, with the session cached — so the single method covered 100% of real usage. The expansion doc is a "someday" design, not a built feature.

**Is this worth fixing?** Yes if headless use is intended (the ETL framing suggests it is); the `is_user_authorized()` guard is a must regardless.

## What feels vulnerable

**The issue.** Secrets handling is unsafe by construction: `api_id`/`api_hash`/`phone` sit in plaintext `config.ini`, and the bearer-token `.session` file is written next to the code. In this repo both the filled-in `config.ini` and `.session` files are committed (see `small_summary.md`). Anyone with the repo can log in as the account.

**ELI15.** Your house key and your address are taped to the front of the notebook you handed out copies of. The design encourages keeping the key right next to the door, and in this project the key actually got photocopied and shared.

**Impact.** Full account takeover risk from a leaked repo/backup. This is the single highest-severity issue in the codebase, though it's an *operational/hygiene* problem more than a code-logic one.

**Robust Fixes / Best Practices.** Load secrets from environment variables (or a secrets manager) with `config.ini` as a non-committed fallback; ship a `config.ini.example` with placeholders; add `config.ini`, `*.session` to `.gitignore`; **rotate the exposed `api_hash` and re-authenticate** since they're already public in history.

**Architectural Fix.** A small config layer that reads env first, file second, and never logs secrets. *Not overkill* — it's table stakes for anything touching credentials.

**Speculative defence.** On a personal machine, plaintext-next-to-code is the path of least resistance and Telethon's own docs do exactly this. The committing of secrets is almost certainly an accident of `git add .` rather than intent — the `.gitignore` simply didn't cover them.

**Is this worth fixing?** Yes — highest priority for anything shared; the exposed creds should be rotated now.

## What feels like bad design

**The issue.** Required credentials are accessed as raw dict subscripts (`config[section]['api_id']`, `connection_engine.py:121`) so a missing key throws a bare `KeyError` with no guidance, while optional keys use `.get()`. Config validation is ad hoc and split.

**ELI15.** If you forget to fill in one required box, the program crashes with a cryptic error instead of saying "hey, you forgot your API ID." Some boxes are handled gently; others explode.

**Impact.** Poor first-run experience; users hit unfriendly stack traces instead of actionable messages. Low severity, pure ergonomics.

**Robust Fixes / Best Practices.** Validate all required keys up front with clear messages ("Missing 'api_id' in [telegram] section of config.ini — get it from https://my.telegram.org/apps"). One of the smoke tests already prints exactly this guidance; centralize it in `_load_config`.

**Architectural Fix.** A typed config loader (`pydantic`/`dataclass` + validation). *Mild overkill*; a handful of explicit `if key not in section: raise ValueError(...)` checks suffice.

**Speculative defence.** The happy path (author's own filled-in config) never triggers the missing-key branch, so the rough edge was never felt. The friendly guidance lives in the smoke test because that's where the author debugged setup, not in the library.

**Is this worth fixing?** Low priority — a nice onboarding polish.
