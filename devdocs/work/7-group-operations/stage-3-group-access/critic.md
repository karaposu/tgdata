---
model: gpt-6-astra
effort: max
---
# IMPLEMENT AFTER FOLDING THESE IN

Falsifier: live Telegram can return an ordinary successful uncached concrete group
history reply without establishing even this account's momentary history-read access.
Affordable now: no — requires an authorized live test account/group and server
interaction outside this explicitly offline delivery. This is a later qualification,
not a claim that the synthetic source tests establish live permission semantics.

## High-level summary

The stateless domain layer fits the merged ownership foundations. One Medium finding:
representability in signed64 does not make Telegram's marked peer IDs unambiguous.
A boundary probe reproduces a channel row being mistaken for a basic-chat candidate.
Fold a namespace round-trip check into the existing numeric/projection step. No new
engine, persistence, health redesign or live action is needed. No High/Low findings.
The declared source-cache limitation remains explicit and does not imply success on
all SDK backends. No open planning/execution blocker was discovered.

Review basis: plan revision1 `8407314`, description `382c911`, inquiry `f174e90`,
merged dev `30ba706`, actual Telethon1.45.0/layer229. Sequential in-session review;
not a PR critic and not a rejection of the earlier stages. Provenance is retained
session model/effort evidence; no fresh selector verification is claimed.

## Premise Inventory

### 1. Successful history is bounded momentary read evidence

**Premise:** a successful uncached concrete GetHistory result establishes that this
account could read that target at that instant; metadata/membership do not.
**First dependent step:** domain/access steps2–3.
**Waste if false:** access semantics and health assertion need redesign (steps3–5).
**Test scheduled at:** no live qualification in this task; offline shape validation in5.
**Cheapest earlier test:** designated live group/account with authorization. Not available
within this read-only offline implementation scope. Official GetHistory contract is
consistent, but reading it is not a live behavioral experiment.
**Coverage:** contract_probe executes actual SDK/budget/source ownership with synthetic
server replies. Its manual confirmation is NON-COVERING for the eventual public semantic
validation. New suite34 must call the public API without supplying that confirmation.
No promise of future access, membership or comprehensive history is made.

### 2. Merged hooks compose without changing their ownership/lifetime semantics

**Premise:** source replies/errors, metadata versus charged reads, identity admission,
post-body cleanup and deferred notifications remain usable by the new domain layer.
**First dependent step:** test scaffolding1 and wiring4.
**Waste if false:** boundary integration would expand beyond this stage.
**Test scheduled at:** already executed before plan; full public cases in5.
**Cheapest earlier test:** actual composed SDK/factory/budget/owned monitor; already run
in contract_probe.py. Stages1/2 have existing direct composition tests32/33.
**Coverage:** real1.45 SDK TL decoding, caches, constructor policy, real budget SQLite,
owner222 with stale111, metadata cost0, limit1 cost1, refusal before send, actual sender
RPC identity after mandatory SDK backoff and settled cleanup. Synthetic network data
is disclosed. Remaining public methods are unimplemented code to verify, not an assumed
external capability. No build-before-component-test ordering gap.

### 3. Result schemas and exact numeric cache rows support the proposed projection

**Premise:** known invite/entity families expose the necessary optional facts and peers.
**First dependent step:**2.
**Waste if false:** projection details/routing change, not the task's architecture.
**Test scheduled at:** actual installed constructors/TL round trips and session probes
already executed before plan. Numeric boundary probe executed during this review.
**Cheapest earlier test:** the same SDK/session experiment, no credentials/network.
**Coverage:** full/plain/Already/Peek, optional expiry/hash, min refusal and zero hash
were run. File/store hashless-community divergence was run and preserved as a source
error. New boundary experiment below disproves only the plan's sufficiency of signed64
validation; M1 repairs it inside the existing step, rather than introducing a premise.

## Restart Check

| Observed failure | Established mechanism | Design element addressing it |
|---|---|---|
| Verified B event, cached A summary | Legacy monitor ownership read mutable cached identity | Already-merged Stage2 fixed-owner monitor consumed by step4; no new monitor |
| Local/native failures translated as bad references | Broad catch around SDK helpers obscured original failure | Direct requests and only local conversion catches in2; narrow source RPC conversion in3 |
| Metadata could clear group denial | A successful request alone supplied recovery without semantic read proof | Step3 validates history, step4 confirms only complete readable result; step5 public regressions |
| Cleanup/cancellation could replace result/failure | Temporary lifetime and notification ordering crossed the owning task | Already-merged Stage1/2 boundary reused in4, composed cleanup tests in5 |

## Inherited Lessons

| Lesson | Ordering that satisfies it |
|---|---|
| Repeated patches did not settle ownership | Ownership foundations merged before Stage3 planning; new code consumes them |
| More metadata is not stronger proof of access | Reference/projection and history validation specified separately before facade confirmation |
| A simulated desired result does not test SDK composition | Executed pre-plan component probes and step1 real-source fixture precede domain bulk |
| Unavailable details are not false facts | Qualified nullable values/peer derivation in2 precede access outcomes in3 |
| Do not expand this stage into joining/routing | Stateless module in2, no service object/schema/factory edits; later stages explicitly excluded |

## M1 — Canonical numeric identity needs a namespace check

**Risk**

A very large bare group number can accidentally select a cached record for a different
kind of group. The library would then query the wrong kind of Telegram object, even
though all numbers fit the advertised integer range. Likewise an unusual basic-group
reply could be exposed with an identifier that callers would later interpret as a
channel. The promised deterministic identity would not hold at those boundaries.

In plan.md's Numeric routing and Resolution rules, signed64 representability alone does
not ensure typed identity. Telethon utils.resolve_id treats -1000000000007 as channel7,
while utils.get_peer_id(PeerChat(1000000000007)) produces that identical value. Looking
up a bare1000000000007's nominal basic row finds a cached channel7 row. Both MemorySession
and SQLiteSession reproduced `(-1000000000007, 123)` on get_entity_rows_by_id(-raw,exact=True).
No production code has been written; fix the specification before its implementation.

**Severity:** Medium
**Category:** API contract / stale cache / namespace collision
**Impact:** wrong request namespace and non-round-trippable result IDs at numeric bounds.
**NoobEng:** Telegram stores a peer's type inside the sign/range of the cache key. Integer
size validation checks storage capacity, not whether encoding preserves the original type.
**Affected areas:** new group_operations numeric routes, entity/peer validation, suite34.

#### Mitigation — Quick
Reject every large positive input without changing reply validation.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Centralize a local typed-peer validator in group_operations: positive source ID, signed64
marked ID, and `utils.resolve_id(marked) == (source_id, original_peer_type)`. Use it for
reply projection, matching/message peers and numeric candidate construction. Skip an
impossible basic namespace candidate for large bare IDs, while retaining a representable
channel candidate. Invalid source identity is GroupResponseError; no usable numeric
candidate is GroupReferenceError. Test the boundary (10**12), first non-basic ID, cached
channel collision, and signed64 extremes through the public path.
**Why this is robust:** rejects the actual collision at every new domain use of the
encoding while allowing legitimate large channel IDs and retaining explicit errors.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Selected after the separate phase3 comparison: permanent closure in one already-planned module and its tests. Other identity consumers exist, but their contracts differ; a common mechanism has not been established, so the class-wide rewrite has no demonstrated additional reach.
*For future:* —

#### Mitigation — Long-term
Introduce a shared typed identity abstraction and migrate legacy discovery, GroupInfo,
message-batch and sync identifier paths to it.
**Why this is long term effective:** consistent namespace checks could cover those other
numeric surfaces if a focused audit establishes they share this exact semantic contract.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Audit legacy discovery_engine.py, models.GroupInfo, message_batch.py and sync identifiers separately before proposing shared identity semantics. Any later abstraction can retain this validator; it is not a prerequisite.

## Experiment record

Executed before implementation with the project venv, actual Telethon1.45 utilities,
MemorySession and temporary SQLiteSession. No sockets/account/config. Outputs:

```
PeerChat(1000000000000) -> -1000000000000 -> PeerChat(1000000000000)
PeerChat(1000000000007) -> -1000000000007 -> PeerChannel(7)
PeerChannel(7) -> -1000000000007 -> PeerChannel(7)
MemorySession: bare 1000000000007 nominal basic row (-1000000000007,123)
SQLiteSession: bare 1000000000007 nominal basic row (-1000000000007,123)
```

This is an actual deterministic SDK/cache observation, not a supplied routing result.
It changes one local validation rule; it does not falsify the public API shape. No
REORDER experiment remains required before step1. The documented known SQLite cache
error is neither suppressed nor counted as a new finding.
