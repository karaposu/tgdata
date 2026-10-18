---
model: gpt-6-astra
effort: xhigh
---
# Opt-in concurrent message-media downloads

> Same session warmed at archive `c3950c6` (product equals dev `d8232d1`),
> 2026-10-18. Refreshed reader, SDK, budget, file, heartbeat, health, pool and
> delivery paths listed in triage `d06021a`. Traverse completed at `159f642`.
> GPT 6 Astra / xhigh verified from current thread. No subagent or new branch.

## Problem Statement
Both readers await each message's media before preparing the next message. Small
files can spend much of that time waiting for network responses. The user requests
an optional concurrency parameter, defaulting to one, and rate-aware backoff.
The reported 2–3× speedup is an estimate, not a measured target or safety guarantee.

Concurrency affects more than throughput: later completed files must not advance
saved progress past a failed earlier message, and child work must settle on stop.
A native Telethon 1.45 probe also showed that cancelling an exported download did
not return its borrowed sender. The new optional owner must account for SDK resources.

## User Value Proposition
Callers can request a few simultaneous message-attachment downloads through tgdata,
including daily continuation, backfill and account-pool reads. Existing callers keep
the same behavior. Applications retain their current batch, receipt and upload logic.

## Success Criteria
1. Add `download_concurrency=1` to `get_messages`, `get_message_batch` and the
   corresponding daily/backfill/pool entry points. Accept integer values 1–16;
   reject bool, nonintegers and out-of-range values before source or storage work.
   Default one follows the current inline path; omitted/default options do not
   become new keywords passed to existing injected readers.
2. Above one, prepare bounded windows of at most N message records. Metadata and
   history pagination remain sequential. Only message-attachment downloads overlap;
   disk and in-memory media are supported. At most N media workers and N unaccepted
   records belong to a window. No refill until it settles; callback boundaries cap
   windows so later media work cannot continue across a callback stop or pacing pause.
3. Return records in source order. A failure retains only the fully prepared prefix
   before the first unfinished/failed position, never the greatest completed ID.
   Preserve batch wire format/hash, acknowledgment, album/photo-trail consumers,
   partial-prefix capture and replay behavior. Completed later files may remain but
   grant no progress. Default legacy best-effort errors remain; opt-in media failures
   propagate with the prepared DataFrame prefix rather than being swallowed.
4. A ConnectionEngine admits one opt-in media operation at a time, shared by its
   managed clients. A second opt-in media operation fails before source work. Default
   sequential calls and independent engines are outside this local bound; callers
   must coordinate simultaneous use of the same account. No global account claim.
5. Owned source requests share a monotonic wait observation. Gate admission before
   actual enqueue, including retries, and observe SDK-handled and cached waits.
   Keep configured thresholds and bounded SDK retry behavior; do not mutate a shared
   client's policy or add worker retry loops. Pool clients still propagate waits.
   Already-sent requests may finish; new affected work respects the observed wait.
6. Cancel and join owned workers once, preserving repeated caller cancellation and
   the primary result/error. Account for exported download iterators and SDK-created
   CDN helpers. Failed cleanup cannot replace a primary error; a successful download
   with failed cleanup is not advertised as a successful owned operation. No late
   writes or observer callbacks after return. New opt-in disk writes publish only
   complete files; local I/O failures never become Telegram health verdicts.
7. Only explicitly registered library children share health/heartbeat attribution;
   inherited SDK/background tasks remain excluded. Real progress and deliberate
   waits beat; bounded windows eventually go silent when remaining downloads stall.
   Existing budget charging, including message refreshes, stays at actual admission.
8. Complete real-component prebuild with Telethon 1.45, native files, controlled
   transport and public consumer paths passes before adoption; affected and full
   offline suites pass after adoption. A bounded opt-in benchmark is documented,
   but no live performance claim or production enablement follows from offline tests.

## Scope Boundaries
No new branch, default increase, account routing/identity redesign, global account
registry, distributed coordination, per-file chunk parallelism, adaptive tuning,
dependency upgrade, durable schema or receipt change. Profile photo enrichment stays
serial. `download_media_by_id`, search media behavior and worker job schemas remain
unchanged. Runtime tuning is not persisted and valid changes do not alter pending
replay. No live account use or ScrapeOps deployment in this implementation run.

## Priority Level
Medium / P2: daily media throughput matters, but correct progress and cancellation
are prerequisites to enabling the option. Classification remains feature-heavy.

## Known Blockers

### Ownership before an exported sender is returned — CLOSED: premise disproved
**Question tested:** do tracked download iterators and owned CDN helpers cover all
resources created during an opted-in download? **Answer:** no. The native public-path
probe in prebuild/export_creation_probe.py cancelled while ExportAuthorization was
pending, after a real MTProtoSender had connected to the controlled transport and
started its actual SDK loops. The public read and authorization request cancelled,
but the sender/transport and both loops remained active. The sender was not cached.

**Why the plan changes:** the next design must own an exported sender from creation,
before asynchronous connect/authorization and before SDK cache handoff. Iterator-only
finalization cannot find this resource. Step1's ownership boundary and its proof must
be re-planned; direct ImportAuthorization sender admission also needs examination.
**Source:** post-adoption native verification on2026-10-18, recorded as a failed
prebuild premise. All candidate product changes withdrawn; plan deprecated.
**Who closes the next design:** task-plan/critic-d using this measured fact, followed
by a new complete real-component prebuild. No user/account secret is needed to study it.

The earlier suite pass was insufficient coverage, not evidence that the leak is
acceptable. Do not resume from the folded plan. No live tests, merge or release took
place. Live throughput remains a separately authorized future measurement.
