---
model: claude-opus-5-5[1m]
effort: unknown
---

# Merge-check — #67 WebSocket transport (CONTRIBUTING §7.1)

**What was read together:**
- `desc.md`;
- `plan.md` (revision 2, `ef9a9a5`);
- `critic.md` (verdict REORDER; the experiment PASSED, `002fd9c`);
- the actual diff against `dev`: `git diff origin/dev...HEAD -- . ':!devdocs'`.

**The diff:** 10 files, +1603 / −8, in four code commits — `2ee82df`, `9039067`, `2133d7e`, `d22c73e`. These are what the PR carries. No `devdocs/` path is in any of them.

**The session** was warmed at `240a208` and stayed warm throughout: traverse, desc, plan, critic and implementation all ran in it.

---

## 0. Was the work done warm, and was it weighed?

**Yes.**
- **The warming record.** `desc.md`'s first line is "Session warmed at `240a208` (2026-11-26) — /arch-small-summary + /arch-intro", and `git merge-base --is-ancestor 240a208 HEAD` succeeds.
- **The weight.** `triage.md` exists (`e13c444`), with **Weight: feature-heavy**, and the issue carries the `heavy` label. They match.

## 0b. Did the diff stay inside what triage surfaced?

**Yes, with two small additions that do not change the weight.**

**Inside what triage surfaced:**
- `tgdata/connection_engine.py` — `_load_config`, `_new_client`, the connect wrappers, `health_check`, and the "remote DNS is moot" comment;
- `tgdata/models.py` — `ConnectionConfig`;
- `tgdata/login.py` — the binding;
- `README.md` — next to the proxy section;
- the smoke tests (test_12's relay pattern, test_13's stand-in, test_14's canary convention).

**New files the design called for:** `tgdata/ws_stream.py`, `tgdata/websocket_transport.py`, `tgdata/smoke_tests/test_50_websocket_transport.py`.

**Not named in triage:**
- `tgdata/__init__.py` — exporting the new error class, next to `ProxyConfigError`;
- `docs/stepwise_login.md` — the traverse named it, and `desc.md` criterion 12 lists it;
- `tgdata/smoke_tests/README.md` — the test's entry.

**The weight was right.** The blast radius proved to be exactly the single client factory, as triage predicted: no consumer module changed. The consumers that turned out to read configuration errors by class — polling (`tgdata.py`) and the worker (`worker_protocol.py`) — are covered by the class hierarchy, not by edits.

## 1. Does the implementation match the plan?

**Yes.** Step by step, against revision 2:

| Step | Implemented as planned | Evidence |
|---|---|---|
| 1 baseline first | yes — captured on unchanged code; re-capture after every later step is identical | test_50 `BASELINE`, item 9 |
| 2 `ws_stream.py` | yes — standard library only; no `Origin`; IP host → `ValueError`; certificate error propagated; `ConnectionError` / `IncompleteReadError` only after the handshake | `ws_stream.py`; items 1, 2, 11 |
| 3 `websocket_transport.py` | yes — `super().__init__(host_for(dc_id), 443, dc_id, **kwargs)`; `_proxy_connect` reused; certificate → `TransportConfigError`; socket and writer closed on a failed connect (Low risk 4 too) | items 3–6 |
| 4 config key, error class | yes — `TransportConfigError(ProxyConfigError)` in `connection_engine.py`; `ConnectionConfig.transport` appended last; exported | items 7, 9 |
| 5 factory, wrappers, route line, `health_check` | yes — lazy import inside the `websocket` branch; `except ProxyConfigError: raise` in both wrappers | items 7, 9, 10 |
| 6 binding | yes — only when not `tcp` | items 9, 10 |
| 7–10 tests | yes — 71 checks, folded harness mechanics | `verify.md` |
| 11 docs | yes | `2133d7e`, `d22c73e` |
| 12 regression | yes — test_50 plus 14 offline suites green | `verify.md` |
| 13 live check written | yes — not run | `live_check.py`, `live_check.md` |
| 14 live run | **not run — waived by the maintainer before the merge** (2026-11-26; see `plan.md` E1) | — |

**Deviations, each with its reason:**
- **The reconnect item runs over SOCKS5 only.** Plan step 8 said both runs, main connect and reconnect, would be done over SOCKS5 and over HTTP CONNECT; main connect runs over both. Reconnect reuses the same connection object and the same `_proxy_connect` path, so the proxy kind adds nothing to what the item proves.
- **The pool sources were built with `AccountPool` plus `source.preflight()`,** not with `pool_storage_cases.py`'s builders, which the fold named. `preflight()` is the pool's own offline client builder; the cases module builds synthetic wires, which this item does not need.
- **`live_check.py` downloads with the client tgdata built** (`tg.connection_engine.get_client()`), where plan step 13 said "through tgdata's public API". `TgData` has no public download call. The connection, reads and `health_check` do go through `TgData`.
- **Four test-only fixes during verification,** listed in `verify.md`. Production code was not changed to make a test pass.
- **`models.py`'s last line** lost trailing spaces and gained its missing final newline. This is whitespace only.

## 2. Does the plan still make sense against what the code turned out to be?

**Yes. One premise was corrected by evidence, and the plan's reasoning was updated in place, not left false.**
- **The keep-alive premise was false.** The traverse and the plan reasoned that Telethon's 60 s keep-alive keeps connections inside the relay's idle cut. The pre-build account check showed connections cut within minutes *despite* the pings, and Telethon's reconnect, by name, recovering them. The decision — no transport-level pings — is unchanged, since pings would not help. The rationale is corrected in `desc.md` (scope and risks), `traverse/finding.md` (Monitoring) and `critic.md` (the result), and the README tells operators to expect reconnects.
- **What this means for strict clients** (pool sources, owned operations, the login) is documented. They take a retryable `transport` outcome after a cut, and the pool applies a 30 s cooldown. This costs throughput, not correctness; a WebSocket-aware reconnect policy for the pool would be a separate issue.
- **Everything else the plan relied on held in the code:** the four construction sites passing `dc_id`, `_proxy_connect` dialling `_ip`, retry-by-type, and the class-level `_config` cache. The canary checks it after any Telethon upgrade.

## 3. Did the critic's findings actually get answered?

**Medium — all three, robust tier selected and folded:**
- **Risk 1** — the consumers keyed on `ProxyConfigError`. Answered by `TransportConfigError(ProxyConfigError)` (`connection_engine.py`), the standard-library errors in `ws_stream.py`, the certificate conversion in `websocket_transport.ConnectionWebSocket._connect`, and `except ProxyConfigError: raise` in `_authenticate` / `_ensure_connected`. **Proven** by test_50 item 7: polling treats it as unrecoverable, the worker reports `configuration_error`, and the pool returns `unknown`.
- **Risk 2** — the test mechanics. Answered by `FakeDoor` modes (`close_after_first`, `silent`, `drop`, `close_now`, …), `bounded()`, `restoring()` (class-level `_config` and `_ssl_context`), `collect()`, and `delay=0`. The suite finishes in about 5 s, with no hang and no state leaking between items.
- **Risk 3** — account safety. Answered in `experiment_account_check.py` (which ran live safely) and `live_check.py`: `--exclusive-confirmed` is required, a copy of the session is used, and `AUTH_KEY_DUPLICATED` is reported as INVALID RUN.

**Low:**
- **Risk 4** (a stream left open by a failed connect) — **answered.** `_connect` closes the writer on any failure after the stream opened.
- **Risk 5** (`_ssl_context` is process-wide) — **consciously left.** The class comment states that production code never sets it, and the canary does **not** assert it is `None`, because the plan never selected that addition.

**The REORDER experiment** ran before step 2 and PASSED. Its result is recorded in `critic.md`.

## 4. Is the issue's status block complete and honest?

**Yes, as of this check.** Steps T and 0–5 are ticked, and each names its committed artifact:

| Box | Artifact |
|---|---|
| T | `triage.md`, `e13c444` |
| 0 | `traverse/finding.md`, `e27b9c4` |
| 1 | `desc.md`, `54f4f04`, posted as a comment |
| 2 | `plan.md`, `4f1c2a9` |
| 3 | `critic.md`, `b3614e4`; experiment PASS `002fd9c` |
| 4 | revision 2, `ef9a9a5` |
| 5 | code and tests, `2ee82df` … `afa9354`; `verify.md` |

- **Step 5's note** says step 14 waits for the maintainer's go. It will be updated to say the step was waived when box 6 is ticked.
- **Boxes 6 and 7** — this check, and the PR critic — are ticked as their artifacts commit.

**Gate result: PASS.** The PR may be opened. §7.2, the PR critic, runs on it next.
