# Dynamic PR-critic prompt — PR #68 (#67 WebSocket transport), CONTRIBUTING §7.2

**Subject.** The implemented diff of PR #68 (`feat/67-websocket-hostname-transport-pr` → `dev`: 10 files, +1605 / −9), read **together with** `plan.md` (revision 2), and judged **fresh** against the codebase it lands in: tgdata 0.1.4, Telethon 1.45.0, Python 3.11+ only.

**Rules for this critique:**
- Read every changed file in full, and the unchanged code each change touches.
- Probe anything behavioural with the real Telethon in the venv and quote the output.
- A Medium stands only on a line of code or a probe.
- Never contact Telegram or use the real account.
- It runs in-session (§7.5).

**Ultrathink.** The plan and its critic already passed. The question here is whether the **built code** is sound — including in places the plan never looked. Ask:

1. **Does the guarantee hold in code, not in prose?** Can any code path — Telethon's connect, reconnect, exported and borrowed senders, the CDN client, `_switch_dc`, the direct case — open a socket to an IP for a `websocket` account?
2. **Are the error contracts true on every path that can raise?** That means Telethon's `_try_connect`, Telethon's **auto-reconnect loop**, tgdata's wrappers, polling, the worker, the pool and discovery. Where does a "stop immediately" error actually stop, and where is it retried or logged with a traceback?
3. **Does the default path stay byte-identical?** Check constructor arguments, log lines, the binding hash, imports, the config record, and `health_check`'s keys, including through `TgData.health_check()`.
4. **Is the WebSocket stream correct as a byte stream?** Check fragmentation, control frames between fragments, close and end-of-file, length encodings, limits, cancellation and timeouts, and cleanup on every failure branch (socket, TLS stream, writer).
5. **Do the docs and docstrings in the diff state only what the code does?** That covers the README section, the corrected comment, `TransportConfigError`'s docstring, and the base `ProxyConfigError` docstring the subclass now inherits.
6. **Does the package ship what it needs?** The new modules in the wheel; no new dependency.
7. **Do the tests observe, rather than supply,** the behaviour they claim? Do they terminate and clean up process-wide state?
8. **Does the diff deviate from `plan.md`,** and is each deviation a decision or a slip?

## Output

Write `pr-critic.md` in the plan's folder — **not** `critic.md`, which step 3 owns — with a high-level summary on top.

**Order:**
1. **The frontmatter** (`model`, `effort`).
2. **The verdict,** from the four `/critic-d` verdicts, then the falsifier line.
3. **A `Gate:` line applying §7.3:** any High or Medium → **REJECTED**; Low only → **PASS**, with the Lows recorded and consciously left.
4. **The high-level summary.**
5. **The Premise Inventory.**
6. **The risk items,** each with: a two-paragraph Risk (plain, then precise) · Severity · Category · Impact · NoobEng · Affected areas · Mitigation tiers with unticked boxes (Medium/High only).
