---
model: gpt-6-astra
effort: max
---
**Verdict: IMPLEMENT AS WRITTEN.**

Falsifier: the actual SDK/budget adapter cannot preserve a date-positioned first
request followed by exclusive-ID continuation, or the existing opaque SQLite store
cannot retain the window and pending observation in one conditional durable record.
Affordable now: yes — these local component observations were run before this
verdict and passed. No affordable unrun premise test is postponed behind a dependent
build step. Synthetic transport is not evidence of live server selection.

## High-level summary

Reviewed revision1 at 0e3e4a4 against desc, triage, the complete facade, batch reader/
value/files, sync engine/store, budget adapter and the offline suites. This is an
in-session review under CONTRIBUTING §7.5, not a subagent review. No High, Medium
or Low finding was established against the specified plan. No fold is required.

The new option remains inside the existing collection/progress structure. It does
not invent a second cursor lane or job scheduler. Daily v1 records are retained as
v1, window records are distinguishable and strictly validated, and old code rejects
those rows. The plan spells out pagination/filter/limit interplay and repeated
relative initialization sufficiently to implement and test them.

## Premise Inventory — ranked by waste if false

### 1. SDK date positioning and exclusive-ID resumption compose
**First dependent step:**2. **Waste if false:** reader selection and continuation.
**Test scheduled:** probe_sdk.py before plan, then step4 regressions.
**Cheapest earlier test:** actual 1.45 iterator/request creation with a scripted
transport and tied-timestamp replies; under two seconds, no account access.
**Coverage:** first request offset_id=0, offset_date=start-1s, add_offset=-2,
limit=2; next iterator after ID102 uses offset_id=103, date=None. Both tied messages
on each page are yielded. This covers SDK construction/order, not Telegram's server.
The documented oldest-first/exclusive-date behavior is the vendor API contract:
https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.iter_messages
Live visibility/date selection is untested, consistent with the existing library's
offline verification boundary. No authorized affordable live probe exists here.

### 2. A shrunken budget page keeps the first date seek and raises on exhaustion
**First dependent step:**2. **Waste if false:** prefix selection and retry meaning.
**Test scheduled:** pre-plan probe, then step4 through actual new runtime.
**Cheapest earlier test:** real budget ledger/adapter around the real iterator.
**Coverage:** limit3 with budget2 yields IDs101/102 from a request retaining the
original date, then raises ReadBudgetExceeded; used=2. Synthetic replies do not
supply the budget decision or iterator resizing. An exhausted allowance is not end.

### 3. One conditional state record can retain both dates and pending output
**First dependent step:**3. **Waste if false:** durable freeze/replay/ack architecture.
**Test scheduled:** pre-review SQLite observation; parent suite22 already exercises
process exits during actual ack commit; new step4 uses window records.
**Cheapest earlier test:** persist opaque records with the existing backend, reopen
and reject stale replacement. **Coverage:** actual SQLite retained both independent
values unchanged and rejected a stale expected value. The backend is intentionally
schema-agnostic; the new decoder/transition behavior still needs implementation tests.

### 4. Second-resolution wire offsets have representable boundaries
**First dependent step:**1/2. **Waste if false:** advertised accepted dates.
**Test scheduled:** pre-review actual TL request serialization, step4 validations.
**Cheapest earlier test:** bytes(GetHistoryRequest(...)) at Unix0 and signed32 max.
**Coverage:** both serialize through actual1.45 code. Epoch has the SDK's unset
meaning, handled deliberately by selecting the oldest history. Microseconds remain
in the local predicate; the seek floors/pads, so it cannot be used as the predicate.

### 5. Caller acceptance and visible history remain external boundaries
**First dependent step:**consumer integration, not the library extension.
**Waste if false:** downstream completeness/duplicate claims.
**Test scheduled:** no deployed receiver/live server validation in this slice.
**Cheapest earlier test:** no available authorized production integration; examples
and existing local receiver tests cover the protocol only. **Coverage:** explicitly
non-covering for ScrapeOps deployment and live Telegram. The plan promises neither
an immutable server snapshot nor exactly-once external effects.

## Restart Check and Inherited Lessons

- A moving relative window loses the original query: step3 loads before observing
  the clock and compares stored request identity. New reads never resolve days.
  Step4 exercises later and earlier clocks, including an uncertain committed setup.
- A fully filtered page can look empty without being exhausted: step2 distinguishes
  last scanned ID, included output count and actual iterator exhaustion. Step4 has
  full pages before the inclusive boundary and same-timestamp splits.
- A budget-limited walk can be marked complete by ScrapeOps' caller: this plan does
  not fix that application. It propagates quota failures and deliberately adds no
  permanent completion state. Remaining job orchestration is explicitly deferred.
- Local errors can inherit Telegram context: the window helper uses BatchFormatError;
  sync initialization/decoding converts it to existing local Sync errors. Store/replay
  operations stay outside the reported network wrapper. No health owner changes.
- A temporary pending observation is not the archive: step3 retains existing exact
  replay, step5 makes the caller acceptance boundary and separate stores explicit.

## Boundary and compatibility audit

An explicit range intersects after_id; it never replaces the acknowledged cursor.
A zero cursor gets the efficient date seek. Arbitrary earlier nonzero cursors can
cost extra scans, and the plan says so rather than claiming a free server-side
intersection. Date checks remain after every cursor change. Filtered messages never
reach media preparation, and missing dates fail rather than acquiring guessed time.

Returning limit at an exact count does not prove more messages exist. A following
empty read may be required, including an extra budgeted request; the existing
contract already has that property. Date-crossing end describes this fixed query,
not a permanent job-completion marker. The batch v1 payload stays unchanged because
it identifies observations, not query definitions; frozen bounds live in state.

Relative request identity includes days, seed and mode; explicit identity includes
normalized bounds, seed and mode. Changing forms conflicts deliberately, preventing
an accidental reset. Input shape is validated before state access, but no clock
observation occurs when matching saved relative state exists. A commit-then-error
can be reloaded with the original dates. Window fields survive dataclass replacement
on both pending and ack transitions.

Version-specific exact keys prevent v1 records being read as window records by
accident. Window duration is validated against saved relative input; pending records
must satisfy the same range. Status adds fields only for window dictionaries, so
daily to_dict remains stable. Mixed versions can coexist in one backend across
independent group keys without changing its SQL schema. Independent collections
of the same group still require separate stores, as before.

No unselected implementation prerequisite, known planning blocker or inherited
execution blocker was found. No changes to test expectations, older SDK support,
paused #7, sessions, quotas, media publication or public MessageBatch format are
required. The new suite must establish the implementation, not merely repeat these
component probes. Combined merge-check and fresh PR critique remain later gates.

## Probe output

```text
PASS date positioning is preserved on first SDK request; resume uses exclusive ID
PASS messages sharing a timestamp survive an ID-based page boundary
PASS real budget page resizing retains date seek and raises after completed prefix
PASS supported endpoint timestamps serialize through the real SDK
PASS existing SQLite opaque-state contract preserves independent versions and stale CAS
```

## Phase3 selection

No risk item requires mitigation proposals; no selected/elegant/last_resort decision
is manufactured. Proceed directly to implementation of revision1 under task-impl.
