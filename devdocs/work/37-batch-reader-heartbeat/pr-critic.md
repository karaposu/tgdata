---
model: gpt-6-astra
effort: xhigh
---
**IMPLEMENT AS WRITTEN**

Falsifier: on the actual published code, a heartbeat changes request/wait/budget outcomes, turns a genuine stall into false liveness, leaks into another operation or alters original failure/capture/pending-data authority.
Affordable now: yes — executed before verdict against the published product checkout. All12 fresh histories passed; no remaining affordable untested foundational premise was identified.

**PR gate: PASS — zero High, zero Medium, zero Low findings.**

## High-level summary

The heartbeat remains an observer of work already being performed. Chunk and request activity let the caller retain a slow active read, while silence still lets it cancel a stuck one. The source's original messages, retries, budget charges, errors and acknowledgment obligations stay authoritative.

Fresh combinations beyond suite44 passed: a pool download produces two chunks and then stalls; the watchdog cancels it, retains the completed earlier message in the capture, charges the existing budget and does not fail over. A daily download failure with a callback that itself raises an RPC error preserves the original source exception and exact saved prefix. Premium/server retries and budget accounting are identical with no callback, a working callback and a callback raising cancellation. No product change or re-plan is requested.

## Subject and review execution

Explicit subject: [PR38](https://github.com/karaposu/tgdata/pull/38), base38dee0bbde3259cd2d34a91206afe483132eca59 → head15241bf9a91883137cf154700f6e26fbd64ed085, together with folded revision2 step_by_step_impl_plan.md, plan.md pointer and desc.md. Current dev contains the already merged photo-trail feature. All12 heartbeat product paths and98 Python sources equal the implementation/prebuild manifests. GitHub's actual diff matches the local diff after normalizing hunk-context labels only.

Same warmed session, no subagent. Read all changed files and the actual Telethon1.45 request loop, budget sender, original source/progress/pool and cleanup contracts. Tailored prompt fe007c9 was saved before execution. Current turn metadata2026-10-15T07:50:19.128Z verifies GPT6 Astra/xhigh. This is fresh soundness review, not the fidelity check repeated. Preimplementation critic.md is preserved.

The fresh probe script imports existing valid SDK/wire fixtures, not a mock that simply emits the desired heartbeat. It runs actual published source paths, SDK loops and SQLite. Twelve newly specified histories use explicit expected values. All sockets are blocked. The direct late-Future helper check is supplemental; actual public pool/continuation/concurrent request cases establish the composed behavior.

## Premise inventory

### P1 — Observing an awaitable does not change request authority

First dependent step1; waste if false spans the helper, forwarding and recovery tests. Scheduled qualification was the complete candidate before adoption, which passed. Cheapest falsifier: real SDK retries/budget coroutine plus original-Future/list behavior and cancellation. Fresh premium/server retry comparison preserves sleep list `[1,2]`, three history requests, budget used3/reserved2 and threshold60 for absent, working and failing callbacks. Actual batched SDK MultiError retains the original second exception and first result. Concurrent budgeted cancellation leaves the second read successful, both attempts charged and no late callback on the cancelled scope. No extra task or pre-enqueue await was introduced.

### P2 — Signals distinguish intentional activity from silence

First dependent step1/2; waste if false is the watchdog contract and observer design. Complete prebuild covers a slow full download and a first-chunk stall. Fresh pool history produces two real SDK chunks, then leaves the third request unanswered. It is cancelled after silence, with temporary media removed, completed prefix101 retained, budget used2 and no second-account read. Real ConnectionEngine connection recovery waits1s with the normal handled-error path, emits49 wait ticks under a scaled slice, then succeeds on its second connect call despite a shorter watchdog. SDK sleeps themselves remain unchanged; no universal heartbeat-interval premise is asserted.

### P3 — Scope/lifetime survives pool children and delayed completions

First dependent step1/2; waste if false includes public callback isolation and capture ownership. Complete candidate tested task/background separation and all pool interfaces. Fresh nested scopes restore exact outer/inner observers; a deferred Future completed after scope exit produces zero callbacks and remains the same Future. A callback object that repeatedly fails is collectable after completion. During a deliberately held daily publication, source scope is already closed; another actual client request cannot revive its heartbeat. Cancelling that publication retains completed data on the exception, saves no invented pending receipt and emits no further source beats. Actual pool child cancellation remains quiescent with original captures.

### P4 — Callback errors are not source/data/health decisions

First dependent step2; waste if false is the source-integration contract. The actual prebuild/full tests qualify callback and logger exceptions, hashes, health, cancellation and replay. Fresh daily media failure followed by a callback RPC error preserves the exact original RuntimeError and pending prefix, and replay performs no new read. A broken callback during an actual pool access error preserves that original error,100 completed messages, failed capture and200 charged reads without failover. Invalid async callbacks refuse all four public pool entry points before any state admission or source request. No new durable field or receipt hash input exists.

No OPEN planning/execution blocker. Full candidate qualification preceded adoption; existing914-check evidence is tied to exact bytes. The new falsifiers above ran before this verdict. Synthetic transport cannot establish Telegram availability or deployed consumer timing, neither of which is claimed by this local callback contract.

## Restart check

| Observed failure | Established mechanism | Actual response |
|---|---|---|
| Healthy large batch download triggers consumer silence timeout | Batch APIs lacked heartbeat and writer omitted SDK progress callback | Public forwarding and per-chunk `media`; suite44 slow-download control and fresh progress-then-stall pool history |
| Multiple SDK waits accumulate into a silent read | Internal retries were invisible at the batch boundary | Task-scoped request/flood-result observation; actual repeated/cached tests and fresh premium/server retry parity |

The implementation addresses the established source of silence, not an unrelated scheduler or progress database. Its documentation states that a watchdog must exceed a single allowed SDK sleep plus ordinary latency. It does not promise automatic ticks during an unanswered RPC, local synchronous I/O or arbitrary storage work.

## Inherited lessons

#6 established that local failures must not masquerade as Telegram account health and cleanup must preserve the primary failure. Callback failures are consumed locally with type-only warnings; original SDK errors and blob cleanup remain unchanged, including the fresh simultaneous source/callback-error cases. #17 established that source/capture completion and durable publication have separate lifetimes. Fresh stalled pool capture and cancelled daily publication exercise those boundaries directly. No application coroutine is awaited as a heartbeat and no extra owned task is introduced. None forwarding remains absent for legacy injected readers. Full composition qualification preceded product adoption.

## Fresh evidence

Run:

```bash
/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python \
  devdocs/work/37-batch-reader-heartbeat/pr-review-probes.py \
  /private/tmp/tgdata-30-photo-trail-pr \
  devdocs/work/37-batch-reader-heartbeat/pr-review-probes.json
```

The executable, JSON and full stdout are retained beside this review. Selected exact output:

```text
daily media error preserves prefix and original exception: PASS
pool progresses then genuinely stalls: PASS
premium and server retry parity under failing callback: PASS
one concurrent budgeted read cancels independently: PASS
cancelled publication cannot retain source heartbeat: PASS
actual connection recovery wait stays alive: PASS
All 12 fresh PR review histories passed.
```

No probe failed, expectation was weakened, fixture repaired or product patched during this review. The helper hash remains3c361434a87dfb804653cb88d645a85b323279b7904d9808a4eb0bed404b9ee5. Earlier full verification remains914 executed offline checks across31 suites and7 demos,3 explicit live skips excluded. The complete merge candidate will receive its own full verification before publication; unchanged cherry-pick transport does not require another duplicate full run here.

## Findings and Phase3

No findings; no mitigation proposals or selections. No revision3 re-plan/deprecation is triggered. The helper is private and narrowly scoped; it does not create a shared retry framework, change client thresholds, parse logs or intercept global sleeps. Existing source-state/account-policy modules remain separate authorities.

Limits: tests use real local SDK/SQLite components with synthetic wire responses and scaled watchdog timing. They do not establish native Python3.7 execution, live-account availability, deployed ScrapeOps adoption, a maximum RPC duration or physical power-loss durability. Those limits are explicit in the public guide.

Both review gates pass for the named head. The maintainer already authorized merge; after posting this critique and passing the merged-tree suite, proceed without another permission question. Preserve the existing branches, exclude work notes, and do not release or deploy.
