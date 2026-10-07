---
model: gpt-6-astra
effort: max
---
# Stage 7 source input

User request: `$task-impl **Stage 7**`, with the full task-impl skill supplied.

Authoritative scope: [staged plan, Stage 7](../staged-plan.md#stage-7--expose-the-lifecycle-through-a-small-public-api),
the [contract](../contract.md), and [Gate C PASS](../validation/gate-c.md).
Baseline `5b51cc3`, product `0d6bb26`; existing issue #19 and branch
`feat/19-backfill-run-lifecycle`. The six operations have already been specified.

Deliver additive TgData wiring/exports with optional backfill_store, honest stored
status, public documentation and an offline durable-receiver/restart example. Keep
daily/backfill namespaces separate, even when an application uses one database.
Only actual raw message reads carry source health context. Local operations must
neither create source health evidence nor clear a prior problem.

Existing instructions persist: Telethon 1.45.0 only; one source reader per group;
no edits/deletions or distributed reader/routing design; duncan and paused #7 stay
untouched. Formal pipeline commits and required GitHub updates are authorized.
No PR, protected merge, deployment or Stage 8/Gate D execution is requested here.
No new Telegram traffic is required for this stage; Gate D remains after Stage 8.

The orchestrator passes this explicit folder to the delegated description/plan/
critic skills; the target is unambiguous and no folder-selection confirmation is
needed. No PARKED block or rejected PR-critic history exists for this new stage.
