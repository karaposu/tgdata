---
model: gpt-6-astra
effort: max
---
# Stage 7 — public backfill API and caller example

> Session warmed at `5b51cc3` (2026-10-07); same-session lifecycle/source/health model
> and Gate C evidence retained, facade/store/example/interfaces refreshed. See
> [triage](triage.md). Model/effort verified gpt-6-astra/max.

## Problem Statement

The lifecycle is implemented and Gate C qualified it through internal engine imports,
but normal TgData users cannot configure it or call its operations through the public
class. Applications also need a concrete receiver/restart example that preserves
identity and acknowledgments instead of mistaking a successful source read for saved
output. An incorrect wrapper can discard local timing/activity evidence or emit false
Telegram health recovery for a purely local success.

## User Value Proposition

Callers can explicitly start, inspect, prepare/replay, acknowledge, control and recover
historical runs using the normal library surface and portable typed values. They retain
account/scheduling/worker/destination ownership. A repeatable offline example shows
durable receipt handling and independently stored daily/history progress in one logical
database, making the boundary usable on a laptop or with a custom online store.

## Success Criteria

1. Optional backfill_store and the six reviewed facade operations are additive and
   preserve existing constructor arguments, daily/window APIs and MessageBatch v1.
   Disabled/misconfigured lifecycle use refuses locally; no fallback to the daily store.
2. Public calls retain the internal engine's same-instance in-flight and pacing evidence.
   Exact request/run/context/receipt/command semantics, result/error types and bounded
   recognition are preserved without hidden retries, automatic rebase or source work.
3. Package-root imports expose the reviewed immutable values and local errors. Status
   remains stored, content-free and attributable, with separate intent/pending/end/
   terminal/wait/failure facts. Local queries do not refresh account identity or secrets.
4. Only actual raw source reads carry Telegram health context. Local create/status/
   replay/ack/control/recovery and storage/media errors neither create source events
   nor clear a previously observed problem; ordinary source errors remain attributable.
5. Public documentation explains store namespaces, caller-owned durable acceptance,
   retained identities, recovery/quiescence, pacing/budget limits and explicit abandonment.
   README and smoke-test discovery point to the contract and runnable example.
6. The offline example uses actual durable SQLite state/receiver transactions, retains
   its intent/reference, reopens after a chosen lost-ack interruption, deduplicates
   replay, and completes only after acceptance. It shows pause/cancel and sequential
   daily/backfill turns with separate namespaces in one database, without pretending
   synthetic source observations validate Telegram or a real deployment.
7. New public-surface tests, the example and supported full offline regressions pass
   on Telethon 1.45.0. Preserve gate provenance and leave Stage 8/Gate D pending.

## Scope Boundaries

Use the existing lifecycle contract/state machine and async opaque-text load/CAS store
protocol. Collection identity is not automatic physical backend namespacing; callers
configure isolated namespaces, which can share an application database. Do not build
a production namespace framework, scheduler, account routing, distributed readers,
edits/deletions, permanent message archive or media garbage collection.

The example is a bounded application demonstration, not a general worker service or
an automatic recovery daemon. Public status does not promise account readiness or
exactly-once external effects. No new Telegram reads, Stage 8/Gate D, package release,
PR/protected merge, duncan changes or paused #7 work is included.

## Priority Level

**Medium (existing P2).** This is the next reviewed dependency for the public lifecycle;
it should preserve the already tested ownership rules rather than introduce new ones.

## Known Blockers

None identified. Gate C passed at product `0d6bb26`. The namespace/receiver example's
real local SQLite composition is cheaply testable before depending on it. Existing
public daily behavior, raw-reader health context and package interfaces are accessible.
No account/login input is needed for this stage.

## Inherited lessons

Local work is not Telegram evidence. A wrapper must not discard source activity or
monotonic evidence. Collection identity is not a database namespace. Source end is
not receiver acceptance; a hash is not run authority; error is not rollback. Retain
requests before submission and never turn missing known state into fresh enrollment.
Examples must execute their claimed durability boundary, not supply it with a fake.
