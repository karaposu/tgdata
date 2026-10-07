# Source input — #17

## User request

> The other big proposal you’re remembering is **#17—the account pool that handles routing and failures automatically.**
> $task-impl lets do this then

## Confirmed scope

Question: #17 includes automatic joining, but the group-access/join work in #7 is still paused. What should this first delivery cover?

Answer: Routing and failover for groups accounts can already read; keep #7 paused (recommended).

## Original GitHub request

Source: https://github.com/karaposu/tgdata/issues/17; fetched 2026-10-07 before implementation. Original parked status below is historical; the user has now selected the scoped delivery above.

Requested on 2026-10-06 for the future backlog. The user wants reusable Telegram behavior in tgdata so a web app can supply groups and accounts without rebuilding the account orchestration currently described as living in ScrapeOps.

**Request: an account pool that routes and recovers by itself.**

The caller asks tgdata to “read group X” and does not choose the account. The pool selects an account that:

- is healthy;
- can see the group;
- has read budget left;
- satisfies the configured warm-up eligibility policy.

When an account is banned, logged out or loses access to a group, the pool switches to another eligible account. When reading needs a new group member, it can join with a spare account under the configured join policy and allowance. Group membership and the accounts able to read that group remain known to the pool.

The motivating consumer currently owns drain/spread strategies, account budgets and pinning groups to accounts that joined them. The requested outcome is that accounts become an inventory — add an account and its proxy — while tgdata owns reusable routing and failover on both laptops and servers.

**Library boundary.** This is a library capability. The web UI, business workflows and downstream processing remain with the application. Selection and retries must respect the existing account budgets, health states and waits. A caller needs a clear outcome when no eligible account can proceed. These are requirements to qualify later, not an accepted design.

**Related work.** #4 already supplies health events and #9 already enforces per-account read budgets and warm-up policy; neither issue supplies this routing policy. #7 supplies group lookup/access/join primitives but is unfinished and paused, so its accepted implementation is a prerequisite for automatic joining. #5 supplies pluggable session storage. #10 is the separate worker-process proposal and can consume this library capability; its existing scope is not changed by filing this issue. The current connection pool can have multiple sessions for one account; this proposal is a pool of distinct accounts, not a request to reinterpret that setting silently.

**Questions for later qualification.** Settle selection/fairness and group affinity; warm-up eligibility versus reduced allowance; persistent ownership when several callers share the pool; retry/stop behavior; and when automatic joining is enabled. Do not start those design decisions during backlog capture.

---
## Pipeline status

**Direction:** parked — explicitly requested for later. Resume only when the maintainer schedules this task.
**Priority:** P3 — future backlog, provisional until triage.
**Path:** feature — new behavior.
**Weight:** not decided; triage has not run.
**Dependencies:** existing #4, #5 and #9 are merged into dev; automatic group joining requires #7, which is not merged.
**Branch:** none; no implementation branch created.
**Docs:** none; this issue is the backlog record.
**Session warmth (step W):** not recorded for implementation; only existing issue titles and relevant bodies/reviews were checked for backlog capture.

- [ ] **T — triage**
- [ ] **0 — traverse** — decide whether required during triage
- [ ] **1 — desc**
- [ ] **2 — plan**
- [ ] **3 — critic**
- [ ] **4 — fold**
- [ ] **5 — implement**
- [ ] **6 — merge gate**
- [ ] **7 — PR critic**

**To continue:** wait for the maintainer to select this task. Then re-read this request, related issue outcomes and CONTRIBUTING.md before beginning the normal pipeline. Filing this issue does not resume #7 or authorize implementation.
