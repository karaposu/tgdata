---
model: claude-opus-5-5[1m]
effort: unknown
---

# PR critic — PR #68 (#67 WebSocket transport), CONTRIBUTING §7.2

**Verdict: IMPLEMENT AS WRITTEN** (merge). The findings below are informational Lows.

```
Falsifier: the built code, run on the real account (live_check.py), fails where the pre-build
           prototype passed — e.g. the account's session refused, or a connection naming an IP.
Affordable now: yes — about 15 min and the maintainer's go. The maintainer explicitly waived it
                before the merge on 2026-11-26 ("Live run will be … tested after the release").
```

**About that falsifier.** By `/critic-d`'s own rule, an affordable falsifier would make this verdict REORDER. That rule is not overridden silently: the maintainer took the decision knowingly, on the strength of the prototype check on the same account (PASS, `critic.md`), whose connection class has the shape the built class has. The decision is recorded in `plan.md` (E1) and `verify.md`. This critique records the residual risk and does not overrule the owner of it.

**Gate: PASS — Low only (§7.3).** No High, no Medium. Four Lows are recorded below and consciously left. The PR merges.

**How this ran.** In-session (§7.5), against `gh pr diff 68` (10 files, +1605 / −9) and `plan.md` (revision 2), on Telethon 1.45.0 and Python 3.11.10. Every claim below cites code or a probe run for this critique.

---

## High level summary

The built code does what the plan said, and the places the plan never looked hold up.

**"Never an IP" holds in code.** The class swaps the IP for the hostname in its constructor (`websocket_transport.py`, `super().__init__(host_for(dc_id), PORT, dc_id, **kwargs)`). Every construction site therefore yields a name:
- Telethon's main connect;
- reconnect, which reuses the same object;
- exported and borrowed senders;
- the CDN client, which uses the parent's class, and whose DC fails fast;
- `_switch_dc`, which goes through `connect()` and so builds a new connection with the new DC.

test_50 records only names through the real factory. The probe below shows that even a failing reconnect dials only `venus.web.telegram.org`.

**The default path is unchanged.**
- **Constructor arguments, route lines and binding hash** re-capture identical to the pre-#67 baseline.
- **The transport module** is never imported for a TCP account (a subprocess check).
- **`health_check`** gains one additive key. No test or consumer compares the exact key set (grep). `TgData.health_check()` returns the engine's dict plus `health`, so the key reaches `TgData` users.

**The error contract holds at the gates that matter:**
- Telethon's `_try_connect` (one attempt; test_50 item 7);
- `AccountPool._failure` (`unknown`);
- polling (unrecoverable);
- the worker (`configuration_error`);
- `TgData`'s wrappers (type kept).

**One path the plan did not consider** retries it: Telethon's own auto-reconnect loop (Low 1).

**The stream** handles fragmentation, control frames between fragments, close and end-of-file, every length encoding, limits, and cleanup on each failure branch. The checks are in test_50 items 1–2.

**Packaging and dependencies.** A wheel built from the PR branch contains `tgdata/ws_stream.py`, `tgdata/websocket_transport.py` and the test (`find_packages()`). There are no new dependencies.

**Deviations from the plan** are the ones `merge-check.md` names, each a decision with a reason:
- the reconnect item runs over SOCKS5 only;
- the pool is built with `preflight()`;
- the live check downloads through the engine's client;
- `models.py`'s whitespace was normalised.

---

## Premise Inventory

### P1 — the built code behaves on the real account as the prototype did
- **Kind:** behavioural — Telegram, and the relay.
- **First dependent step:** the release.
- **Waste if false:** a patch release after the fact. Nothing on the TCP path is affected (P2).
- **Test scheduled at:** after the release, in use. The maintainer waived step 14.
- **Cheapest earlier test:** `live_check.py`, about 15 min — affordable, and waived (see the verdict).
- **Coverage:**
  - **covering for the account premise:** the 2026-11-26 prototype run, which used the real component in the real composition with the same class shape;
  - **non-covering for the built code itself:** test_50 observes tgdata's behaviour against local stand-ins, which cannot show Telegram's.

### P2 — accounts without the key are unaffected
- **Kind:** documentary.
- **Status:** closed by test_50 item 9 (byte-identical re-capture; module not imported) and 14 regression suites.

### P3 — Telethon's internals stay as relied on
- **Kind:** documentary.
- **Status:** closed for 1.45.0 by the canary (item 11). It re-opens on any Telethon upgrade, and the README says to rerun the canary.

---

## Risk items

### Low 1 — Telethon's automatic reconnect retries a "stop immediately" error, logging tracebacks, before giving up

**Risk**

Paragraph 1 (plain). The new configuration error is documented as "stops at once, never retried". That holds when a connection is first opened, and on the account-pool and owned-operation paths. But an ordinary long-running client that loses its connection mid-session — which the WebSocket door makes routine, every few minutes — reconnects through the Telegram library's own background loop. That loop treats every unexpected error as worth another try. If the certificate stops verifying at exactly that moment, the client tries a few more times, writing a stack trace to the log each time, before it gives up. It still never connects to an IP address, and the next request reports the proper configuration error. The cost is a few wasted attempts and alarming log lines, and the README's "never retried" is too strong.

Paragraph 2 (precise).
- **The loop:** `MTProtoSender._reconnect` (Telethon 1.45.0) wraps `await self._connect()` in `except (IOError, asyncio.TimeoutError)` → retry, `except BufferError`, and `except Exception as e: self._log.exception('Unexpected exception reconnecting on attempt %d', …); await asyncio.sleep(self._delay)`. It does this for `retry_range(retries, force_retry=False)`, where `retries = connection_retries` (5 by default for `TgData`'s ordinary client).
- **The probe:** a sender with an auth key and `auto_reconnect=True, retries=3, delay=0`; the door drops the first connection; `_ssl_context` is then cleared, so the reconnect meets an untrusted certificate. Output: `proxy tunnels: 4 (1 = the first connect, the rest = reconnect attempts)`, `reconnect tracebacks: 3`, `exception type in the traceback: TransportConfigError`, `hosts: ['venus.web.telegram.org']`.
- **Fires when:** ordinary clients only (`auto_reconnect=True`), at a certificate failure on a reconnect. Strict clients do not reconnect: the pool sources, owned operations and `LoginFlow` all set `auto_reconnect=False`.

**Severity** — Low. Purpose-fitness: the guarantee holds (names only), the error surfaces typed on the next call (`_ensure_connected` passes it through), and the attempts are bounded.
**Category** — Documentation precision / log noise
**Impact** — up to `connection_retries` extra TLS attempts and tracebacks in the log, after a mid-session certificate change; an operator may read the tracebacks as a crash.
**NoobEng.** Telethon has two retry loops. `_try_connect`, at connect, retries only `IOError`s. `_reconnect`, after a drop, retries any `Exception`. A `ValueError` subclass therefore stops the first and not the second.
**Affected areas** — `README.md` "Failures" bullet; `TransportConfigError`'s docstring ("Never retried"); ordinary `TgData` clients.
**Left as:** recorded. A one-line README and docstring precision fix — "never retried when connecting; Telethon's own reconnect loop may try it a few times after a drop before giving up" — belongs in the next docs touch-up, or the release preparation.

### Low 2 — the base `ProxyConfigError` docstring now overstates its timing

**Risk**

Paragraph 1 (plain). The existing error type for "the configured route cannot be used" says in its description that it is always raised while the config is read, before any connection opens. The new WebSocket error is a kind of that type, and one of its cases — a certificate that does not verify — is raised while connecting. Code that catches the parent type and assumes "nothing was attempted yet" would be slightly wrong for that one case.

Paragraph 2 (precise). `connection_engine.ProxyConfigError`'s docstring says "Raised while reading the config — before any connection is opened". `TransportConfigError(ProxyConfigError)` is raised at config time (unknown value), at construction (unmapped DC), and at connect, from `ConnectionWebSocket._connect` (certificate). No tgdata code relies on the timing: the three consumers — `_polling_cannot_recover`, `worker_protocol.describe_error`, `AccountPool._failure` — read only the class (grep).

**Severity** — Low
**Category** — Documentation precision
**Impact** — none in tgdata; a minor surprise for an external catcher.
**NoobEng** — a subclass inherits its parent's documented contract. When a subclass widens when the error can occur, the parent's docstring should say so.
**Affected areas** — `ProxyConfigError` docstring.
**Left as:** recorded. Fold it into the same docs touch-up as Low 1.

### Low 3 — `_ssl_context` is a process-wide trust switch

Carried from the step-3 critic (its Risk 5), where it was consciously left.

**Risk**

Paragraph 1 (plain). For testing, the new connection type has a setting that replaces which certificate authorities it trusts. It is shared by every account in the process. Production code never sets it, but if anything did — or a test crashed before restoring it inside a long-lived process — every WebSocket account there would trust the substitute.

Paragraph 2 (precise).
- **The seam:** `websocket_transport.ConnectionWebSocket._ssl_context = None`, a class attribute passed to `open_websocket(..., ssl_context=self._ssl_context)`.
- **Who sets it:** only `test_50`, inside `restoring()`, which resets it in `finally`.
- **Documentation:** the class comment says "Test seam only … Production code never sets it".

**Severity** — Low
**Category** — Security hygiene
**Impact** — only on misuse.
**NoobEng** — a class attribute is global to every instance of the class.
**Affected areas** — `websocket_transport.py`, `test_50`.
**Left as:** recorded, as at step 3.

### Low 4 — test_50 waits on wall-clock time in places

**Risk**

Paragraph 1 (plain). A few checks in the new test wait a fixed fraction of a second, or poll for up to four seconds, for something to happen over local sockets. On a very slow or overloaded machine a check could fail without anything being wrong.

Paragraph 2 (precise). Item 2 sleeps 0.2–1 s for frames to arrive. Item 4's reconnect polls `proxy.destinations` for up to 40 × 0.1 s. Item 8 sleeps 1 s for Telethon's close handling. All of these ran green repeatedly here: about 5 s per full run, and 71/71 on the work branch and the PR branch. No CI runs the smoke tests (`.github/workflows/` holds only the PyPI publish job).

**Severity** — Low
**Category** — Test robustness
**Impact** — a rare false failure on a slow host.
**NoobEng** — event-driven waits, such as awaiting a future the door resolves, are sturdier than sleeps.
**Affected areas** — `tgdata/smoke_tests/test_50_websocket_transport.py`.
**Left as:** recorded.

---

## Checked and found sound

- **SOCKS4 gets the hostname.** python-socks with `rdns=True` sends SOCKS4a, `0.0.0.1` plus the name (`_protocols/socks4.py:49`), and does not resolve the name locally (`_connectors/socks4_async.py:33–37`).
- **`TgData.health_check()` carries `transport`.** It returns `connection_engine.health_check()`'s dict, with `health` added.
- **There is no import cycle.** `websocket_transport` imports `connection_engine` at load; `connection_engine` imports `websocket_transport` only inside `_new_client`.
- **Every failure branch cleans up.** The socket is closed on any failure in `open_websocket` (TLS included); the writer is closed on any failure after the stream opened (step-3 critic Risk 4); `wait_for` cancellation inside `_open()` closes the writer.
- **The stream's limits refuse rather than truncate:** the upgrade response is capped at 16 KiB, and a frame at 16 MiB.
- **The wheel built from the PR branch includes the new modules.**
