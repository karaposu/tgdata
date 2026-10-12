---
model: gpt-6-astra
effort: max
revision: 3
---
# Triage — #17 operation boundary re-plan

**Weight:** feature-heavy continuation. **Branch:** feat/17-account-pool.
**Product baseline:**71502e5 (product4854464). **Current dev:**2ddb852.
**Preparation base:**ebbaaac, completed foundation inquiry now carried onto the
existing issue-linked branch. Original triage is preserved as `triage_r1.md`.

## Scope and reach

Use the [new finding](../../inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md)
and first rejected [PR critique](pr-critic.md) to regenerate the plan. The source
result/observer/control boundary changes; selection, durable account permissions,
quotas and group delivery remain their existing responsibilities. No new issue is
needed for a separate supervisor or general health redesign.

[Surfacing](surfacing_r3.md) covers the source/controller/health/batch/state/progress
interfaces, actual SDK/SQLite test fixtures, public contract/example and current-dev
difference. A small private observation module is a proposed new home; it is not an
existing module claimed read. Planned product reach: pool_source.py, account_pool.py,
pool_state.py, new pool_observation.py, test31, docs/account_pool.md, pool example,
README/smoke README; current-dev integration also touches the existing batch seam.

Why heavy: raw, daily and backfill consumers share failure and cancellation paths;
misclassification can silently discard a prefix or grant work after uncertainty.
A callback/API change and shutdown behavior cross multiple concepts even if the
runtime delta is small. Watch for a new abstraction merely moving the wait cycle.

## Current-dev integration

A non-mutating merge-tree preview reports one conflict: tgdata/batch_engine.py.
Both branches added the same private resolver; the pool also added the opt-in
cancellation-prefix parameter. The intended union retains both, with the pool-only
option default False. Diffing the pool file against dev shows only that opt-in
cancellation support. Worker connection/account-operation cleanup receipts must also
remain. The prebuild uses an isolated export of this integration; no runtime merge
is made on the working branch during the requested preparation run.

## Session warmth and preparation

Same warmed session as the full #17 foundation traverse. At ancestor ebbaaac,
account_pool, pool_source, health, pool_state, progress_facade, batch_engine, test31,
public account-pool docs and example were read fully; relevant connection/budget/
progress implementations and actual SDK boundaries were consumed during the prior
inquiry. Current-dev differences are inspected explicitly. No second architecture-
skill run or archaeology refresh is claimed. Hooks exist and are executable.
PROJECT_SPECIFICS.md is absent; no process-file change is made. Commands are obtained
from actual suite runners. Current turn metadata confirms GPT-6 Astra/max.

All issue titles were read. #7 and #10 are closed/merged; #18/#19 supply existing
progress contracts. #3 and #8 are independent pending features. #17 has exactly one
rejected PR artifact, no PARKED block, and the requested foundation traverse is
complete. This is formal re-planning, not a fourth rejected design.

## Authorized endpoint and gates

This run ends at revised description/plan, fresh in-session critic, selected fold
and the combined real-component prebuild. Full runtime implementation, renewed PR
review, live tests and merge remain later work. Keep existing-access routing; no
joining, login, new account inventory, budget reset or scheduler is introduced.
Two-account live resources remain an execution-only prerequisite for that later
gate. Only synthetic credentials, owned temporary SQLite files and blocked sockets
are used in the present prebuild. Main checkout, duncan and other worktrees stay
untouched.
