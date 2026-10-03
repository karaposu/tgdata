---
model: claude-opus-5-5[1m]
effort: unknown
---

## User Input

devdocs/work/4-account-health-events/traverse/_branch.md — SAVE the artifact as devdocs/work/4-account-health-events/traverse/surfacing.md. This is a re-invocation over the same codebase territory as devdocs/work/4-account-health-events/triage.md, which is the prior-artifact (its Traversal Trace is the exclusion filter for items whose relevance does not change). Refined purpose, from _branch.md: surface what bears on deciding the MEANING of account health events in tgdata — the state set and signal mapping, the event shape (account identity, ok-semantics), the emission sites (the broader pattern, not only the six named), callback semantics, and the persistent-path logout scope — including the consumer requirements in issues #3, #8, #9, #10, the existing callback conventions and their documentation, and any observed evidence of real account states.

---

# Surfacing — the meaning of account health events (first surface)

**Mode:** artifact · **entry point:** signal-first · **territory:** explicit-bounded (boundary discovery not fired).

**Reception.** Purpose and territory come from `_branch.md`. The prior artifact is `../triage.md`, whose 60-entry Traversal Trace serves as the exclusion filter. Every triage item keeps its tag here unless re-tagged below. The prior workspace is the same session, in which every core triage region was read in full.

**New regions:**
- the consumer issues;
- callback conventions and their documentation;
- observed evidence of real account states;
- Telethon releases newer than the installed 1.40;
- the process shape `desc.md` must take;
- the private proposal #4 came from.

## Traversal Trace

Recency is filesystem mtime in UTC, a signal only. GitHub issues and probe results have no file and carry `none`.

| # | Region | Item | Verdict | Conf. | Note | Recency |
|---|---|---|---|---|---|---|
| 1 | GitHub issues | #4 body — the event fields (time, account, group, call, wait length) and its two examples | core | HIGH | per-account aggregation ("waited 4 times, 210 s total; logged out after 9 days") and a ban seen without logs | none |
| 2 | ″ | #10 — the worker that "emits health events" and moves accounts between machines | core | HIGH | events may leave the process; the account's identity must survive a move | none |
| 3 | ″ | #8 — step-by-step login | core | HIGH | the intended replacement for the interactive `start()` — bears on scope question (5) | none |
| 4 | ″ | #3 — proxy check; an account whose check fails "pauses until someone looks" | core | HIGH | a pause driven by something that is not a Telegram verdict — the state-set boundary | none |
| 5 | ″ | #9 — per-account budget that "reports 'budget reached; next window in 6 h'" | sub | HIGH | a self-imposed wait — whether it is a health state or something else | none |
| 6 | ″ | #1 (closed) — the proxy; a dead or refusing proxy fails with `ConnectionError` | sub | MEDIUM | connectivity loss as a candidate state | none |
| 7 | ″ | #2 — device identity | side | LOW | a device, not an account; no health bearing | none |
| 8 | Docs | `README.md` — `progress_callback`, `batch_callback`, `heartbeat`, `found_callback`, `DiscoveryInterrupted` | core | HIGH | the callback conventions a health callback would sit beside | 2026-10-03T07:55:57Z |
| 9 | ″ | `devdocs/guides/group_discovery.md` §6 — the watchdog that treats silence as a hang; `found_callback` ends a run on error | sub | HIGH | precedent for an exception-safe liveness stream next to a propagating data stream | 2026-10-03T07:09:48Z |
| 10 | ″ | `devdocs/scoped/9/desc.md` — heartbeat phase labels and a watchdog consumer | sub | MEDIUM | a second, still-open proposal for an event stream; health events and heartbeat phases could meet | 2026-08-23T12:01:11Z |
| 11 | ″ | `test_08_batch_callback.py` `test_batch_callback_error_handling` — asserts a batch-callback exception reaches the caller | sub | MEDIUM | propagation is tested, documented behaviour today | 2025-08-16T21:47:22Z |
| 12 | Observed evidence | a downstream scraping service's `loop.log`, 2026-10-03 — a logged-out session on the persistent path (tgdata 0.0.3) asked for a login code 11 times between 10:29 and 11:40, every ~5 minutes, until an operator stopped the process | core | HIGH | first-hand: report-only leaves a running loop requesting codes; bears directly on scope question (5) | 2026-10-03T08:40:10Z |
| 13 | ″ | raw-Telethon check on a copy of that session, 2026-10-03 — `AuthKeyUnregisteredError` on `GetStateRequest` | core | HIGH | the actual class a real logout produced | none |
| 14 | ″ | `loop.log` history — 423 "Could not find the input entity" (`ValueError`), the most frequent Telegram-side failure | core | HIGH | the dominant real signal is access or cache-miss, not waits or bans | 2026-10-03T08:40:10Z |
| 15 | ″ | `loop.log` — 0 "Sleeping for" lines in its whole history | sub | HIGH | absence of evidence, not evidence of absence: Telethon logs those sleeps at INFO, which this consumer does not record | ″ |
| 16 | ″ | `loop.log` — 122 `TimeoutError`, 86 `ConnectionError` | sub | MEDIUM | transport failures are frequent; bears on whether connectivity is a state | ″ |
| 17 | ″ | a consumer's group finder (`find_rooms.py`) — sets `telethon.client.users` to INFO "to make Telegram's rate-limit waits visible"; a 20-minute wait "looked like a hang until checked" | core | HIGH | working precedent for observing silent sleeps through Telethon's logger | 2026-09-27T20:16:52Z |
| 18 | ″ | `find_rooms.py` — username-lookup waits of 8 h 19 min and 20 h 55 min, `flood_sleep_threshold` 24 h | sub | HIGH | real wait lengths span seconds to a day — the event must carry them | ″ |
| 19 | ″ | this session's probes — an authorized Premium account; throwaway sessions answering "not authorized" | side | MEDIUM | "never logged in" is a different situation from "logged out" | none |
| 20 | Telethon > 1.40 | 1.42, 1.44, 1.45 define `FrozenMethodInvalidError` ("a method that is not available for frozen accounts") and `FrozenParticipantMissingError`; 1.40 does not | core | HIGH | the reading-side candidate for "restricted" exists, but only in newer Telethon | none |
| 21 | ″ | `FrozenMethodInvalidError` inherits `FloodError` (the 420 family) and carries no wait length | core | HIGH | a category fallback would read a frozen account as "waiting" | none |
| 22 | Telethon 1.45 base classes | `UserDeactivatedBanError` and `SessionRevokedError` both inherit `UnauthorizedError`; `UserRestrictedError` → `ForbiddenError`; `PeerFloodError`, `ChannelPrivateError`, `FrozenParticipantMissingError` → `BadRequestError`; `AuthKeyDuplicatedError` → `AuthKeyError` | core | HIGH | a ban and a logout share a base class; specific classes must decide before any category fallback | none |
| 23 | ″ | a consumer runs Telethon 1.44 (per the proposal #4 came from) | sub | MEDIUM | the same tgdata may see the frozen errors in one place and not another | none |
| 24 | Private proposal | the private proposal, §4 (the event set and fields), §3 (pause on a failed check), §9 (budget reports), §10 (worker emits events) | sub | HIGH | the requirement origin; private — shapes the meaning, never quoted into public text | 2026-10-03T07:18:47Z |
| 25 | Process | CONTRIBUTING.md §6.1.1 — `desc.md`'s five sections (Problem Statement, User Value, Success Criteria, Scope Boundaries, Priority) | side | MEDIUM | the shape this meaning must fill | 2026-10-03T07:26:22Z |
| — | Triage trace | entries 1–60 of `../triage.md` | as tagged there | — | unchanged; re-tags under the refined purpose: Telethon `start()` (triage #55) and `_authenticate` (#3) now carry observed evidence (#12); `is_user_authorized` (#54) and the base classes (#52) gain the frozen and ban findings (#21, #22) | see triage |

## State Summary

**Territory:** the triage territory, plus consumer issues #1–#4 and #8–#10, the callback documentation (README, discovery guide, scoped/9), observed evidence (the downstream service's loop log, the raw-Telethon check, a consumer's group finder, this session's probes), Telethon 1.42–1.45 error lists, CONTRIBUTING's `desc.md` shape, and the private proposal.

**Purpose:** what bears on deciding the meaning of account health events — the state set and mapping, event shape, emission sites, callback semantics, and the persistent-path logout scope.

**Coverage map**

| Region | Coverage | Aggregate verdict |
|---|---|---|
| triage territory | confirmed (prior artifact; read in full) | core |
| consumer issues | confirmed (bodies written and read in this session) | core |
| callback docs | confirmed | core / sub |
| observed evidence | confirmed for the downstream service's log and the finder; probes recorded | core |
| Telethon 1.42–1.45 | confirmed for the error classes and their bases only | core |
| process shape | confirmed | side |
| private proposal | confirmed (read in full earlier this session) | sub |

**Confirmed-absent:**
- No observed banned, restricted or frozen account anywhere in the evidence.
- No flood-sleep line in the consumer's log, because of its log level.
- No consumer that reads tgdata's events today; none exist yet.

**Concept names**

| Name | Type | Provenance | Gloss |
|---|---|---|---|
| state-set boundary | coined-term | #4, #5, #6 | Telegram verdicts vs. connectivity, proxy and self-imposed pauses |
| category fallback | coined-term | #21, #22 | mapping by an error's base class when its specific class is unknown |
| `FrozenMethodInvalidError` | structural-reference | #20 | Telethon ≥ 1.42; a frozen account calling a method it may not use |
| login-code storm | coined-term | #12 | a headless loop re-requesting login codes after a logout |
| never-logged-in vs. logged-out | coined-term | #19 | a throwaway session vs. a revoked one |
| account moves | vocabulary | #2 | an account read from a laptop, then a server |
| silent sleep | coined-term | #15, #17 | a wait Telethon sleeps through and only logs |
| per-account aggregation | vocabulary | #1 | totals and durations per account |

**Recency distribution**

| Region | Newest | Oldest | No mtime | Items |
|---|---|---|---|---|
| GitHub issues | — | — | 7 | 7 |
| docs | 2026-10-03T07:55:57Z | 2025-08-16T21:47:22Z | 0 | 4 |
| observed evidence | 2026-10-03T08:40:10Z | 2026-09-27T20:16:52Z | 2 | 8 |
| Telethon > 1.40 | — | — | 4 | 4 |
| proposal, process | 2026-10-03T07:26:22Z | 2026-10-03T07:18:47Z | 0 | 2 |

**Workspace-populated status:** `{populated: true, populated-at: 2026-10-03T11:45, extent: every new region read or probed; triage regions carried from the same session}`.

## Telemetry

- Mode `artifact`, entry `signal-first`, boundary discovery not fired.
- Cycles: 6 new regions plus the prior trace. Items enumerated: 25 new — core 13, sub 10, side 2, umbrella 0.
- Convergence: new regions exhausted at item resolution; nothing left at uncertain relevance; no HIGH-confidence rejections needed.
- Workspace-overload trigger: not fired.
- Failure modes checked: missed-relevance (newer Telethon added after triage's frontier named it), territory-mis-binding (the proposal is private, so it is used as a requirement source only), recency-bias-filter, interpretive-overstep.
- `items_with_mtime` 12 / `items_without_mtime` 13.

## Frontier — for downstream

- **Do frozen accounts fail reads?** `FrozenMethodInvalidError` names "a method that is not available"; whether history reads are among those methods is behavioural and unobserved.
- **What a ban looks like on a read.** `UserDeactivatedBanError` exists; no banned account has been observed.
- **Where #3's pause and #9's budget belong** — inside the health state set, or as a separate signal beside it.
- **The heartbeat (scoped/9) and health events** — one stream or two.

## Self-assessment

**PROCEED.** Every new region is covered, and the prior trace carries the code territory. The frontier items are questions for Sensemaking and Critique, not gaps in this surface.
