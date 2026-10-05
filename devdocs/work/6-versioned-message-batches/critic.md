---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a live Telegram history observation shows that the SDK interface
cannot provide the ordered visible-message prefix required by the retained
batch contract. Affordable now: no — an authorized live account/server run is
outside this local cycle. The affordable new file-object and exception
protocol checks were run before implementation, as quoted below.

# Plan critique — #6 revision 3

Reviewed the complete replacement plan at `e391cd6`, `desc.md`, the original
rejection `670564e`, current source and the actual 1.45.0 SDK in the same warmed
session. No subagent. The original plan/critics remain under `history/round-1/`.

## High-level summary

The re-plan addresses the shared mechanism behind both findings: ownership of
file operations and error precedence. It identifies SDK-invoked writes/flushes
as local I/O without surrounding the SDK await with an overbroad OSError catch.
It also applies teardown policy to close, unlink and existing-file verification,
not only the unlink path in the first reproduction.

The local helper, private stream proxy and shared cleanup owner fit inside the
existing leaf module. They preserve the v1 value, reader, budget, health wrapper
and legacy API contracts. The plan specifies primary versus cleanup-only failure,
cancellation, guarded diagnostics and accurate limits on file deletion. Its
tests challenge those distinctions in the public composition.

No new High, Medium or Low finding is established against revision 3. The two
prior Mediums are explicit inputs with selected Robust responses already in
steps 2–5; they are not silently downgraded or claimed fixed before code exists.

## Premise Inventory

### 1 — The real SDK accepts the guarded file object

First dependent step: 2, then 4. Waste if false: stream boundary and publisher
composition would need a different design. Planned test: before this plan,
then implementation tests at step 5. Cheapest earlier observation: run the
actual SDK photo/document downloader with a delegated real file object; cost
under a second locally. It passed before planning. This critique added cached
photos to the same real SDK probe; all return the supplied object and write
exact bytes while leaving close to the owner. Supplied transport bytes are
**non-covering for live server content**, but output-object dispatch is observed.

### 2 — Local file provenance can be isolated from SDK transport provenance

First dependent step: 2. Waste if false: the proposed local boundary would
suppress genuine health events or retain false ones. Planned test: pre-plan
protocol probe plus step-5 actual publisher/public API tests. Cheapest earlier
observation: SDK write/flush faults under an incidental RPC context and a
transport error with an explicit RPC cause. Already run: the same local OSError
escapes with no health verdict; the same transport exception/cause still yields
the real no-access classification. This observes Python chaining, the actual
health classifier and actual SDK calls through a probe-local file adapter.
It is not a claim that the production publisher is already implemented.

### 3 — The primary outcome can survive secondary teardown failures

First dependent step: 3. Waste if false: both publishers' resource policy must
change. Planned test: Python-unwind seam before build, then real permission,
close, cancellation and logging faults through the new owner at step 5.
Cheapest earlier observation: exercise BaseException unwinding with a caught
secondary cleanup failure; already performed for RPC and cancellation identity.
The original PR probe demonstrates the real permission-denied unlink mechanism.
New owner behavior remains to be tested after construction. No vendor premise
is deferred behind its dependent work.

### 4 — Complete non-replacing files can still support the v1 contract

First dependent step: 4. Waste if false: publisher/reader integration. Planned
test: original filesystem/SDK seam checks and step-5/7 regressions. Cheapest
earlier observation: existing local hard-link/concurrency and integrity tests,
already passed before the first build. This plan retains their primitive and
checks, adds standard open/opener descriptor ownership and keeps close before
publication. Deployment filesystems and power-loss durability remain unverified;
unsupported operations raise. No live completeness claim is inferred.

### 5 — Stable replay and safe continuation remain independent of cleanup

First dependent step: 1 (retained), then 4. Waste if false: the public contract
would need redesign. Planned test: retained golden/immutability/prefix/replay
suite plus step-5 double-failure probes. Existing source and tests establish
the append-after-completion boundary, unchanged schema and caller-owned cursor.
The plan explicitly allows private leftovers and completed orphan blobs while
forbidding incomplete public artifacts. The receiver stand-in is **non-covering
for deployed receiver transactions**, which remain the caller's responsibility.

No affordable unrun prerequisite experiment forces REORDER. There are no OPEN
planning or local execution blockers; existing live/deployment/model boundaries
are carried forward without assigning them invented risk severities.

## Restart Check

Observed R1: FileExistsError under a handled, unreported ChannelPrivateError
causes a false no-access event with zero requests. Established mechanism:
native local errors bypass the custom error's context suppression and the health
classifier follows `__context__`. Steps 2/4 localize every owned file operation,
including the SDK's stream calls, while leaving the SDK await outside that
classification boundary. Step 5 tests both the false-context case and genuine
explicit-cause control.

Observed R2: unlink PermissionError replaces a primary SDK error. Established
mechanism: `_remove_temp` raises from a finally block. Steps 3/4 own both close
and removal, retain primary BaseException identity, attempt remaining cleanup
and preserve the first cleanup-only failure. Step 5 covers real permission
denial, cancellation, close/read double failures and logging failure. Step 6
states the physical best-effort deletion limit rather than promising impossible
cleanup. Neither rejection mechanism is left to a caller workaround.

## Inherited Lessons

The re-plan keeps raw records separate from presentation and saved observations
separate from fresh queries (step 1). File names still require verified bytes
(step 4), and quota spending is separate from completed application progress
(unchanged reader, steps 1/5). The new lessons are implemented in the sequence:
establish the SDK stream seam before code; define local provenance before
composition; define primary/secondary precedence before either producer uses
it; challenge those behaviors before repeating the merge gates.

## Executed observations

`probe_replan_seams.py`, actual output on Telethon 1.45.0:

```text
Re-plan seam probes — Telethon 1.45.0
PASS document: SDK returns supplied proxy, exact bytes, owner retains close
PASS photo: SDK returns supplied proxy, exact bytes, owner retains close
PASS cached photo: SDK returns supplied proxy, exact bytes, owner retains close
PASS SDK write fault: original OSError retained, incidental RPC not classified
PASS SDK flush fault: original OSError retained, incidental RPC not classified
PASS SDK failure: file proxy leaves transport exception identity and explicit RPC cause intact
PASS unwind: primary ChannelPrivateError survives caught secondary cleanup error
PASS unwind: primary CancelledError survives caught secondary cleanup error
All 8 seam observations passed; no production publisher change or live-server claim
```

The attack also checked acquisition/close ownership, guarded attribute delegation,
unlink after close failure, cleanup-only failure after completed publication,
logger exceptions, current transport causes and existing-file read/close ordering.
Each has a concrete mechanism and regression requirement in the plan, rather
than a direction to merely handle errors. No shared health/budget modification,
schema migration, package change or new service is required.

## Findings and Phase 3

**0 High / 0 Medium / 0 Low.** Phase 3 ran after analysis; there are no new
mitigation proposals to select. Prior PR R1/R2 Robust choices are already the
inputs to this replacement plan, not new findings awaiting a fold. Per task-impl,
skip Fold for IMPLEMENT AS WRITTEN and implement revision 3. Do not fabricate
a revision 4 or claim the prior defects are resolved until verification passes.

The exact active model/effort remain unavailable (`unknown`); CONTRIBUTING §9
compliance is not certified. The user authorized the complete re-plan/review
cycle, while merge still requires separate go-ahead. This is a plan verdict;
the eventual second PR critique must independently judge the implemented diff.
