---
model: gpt-6-astra
effort: max
---
# Sensemaking: Stage 2 health ownership

## User Input

_branch.md, source-input.md and surfaced current code: implement health ownership
for the staged account-operation foundation without resuming the broad rewrite.

## SV1 — baseline

Giving health events a verified ID looks small. The old rejection shows that an
event label alone is insufficient: the retained state and later recovery/query
must carry the same owner.

## Phase 1 — anchors / SV2

Constraints: Stage1's one verified client/owner and cleanup rules; no new group
feature, registry across instances, persistence or live work. Legacy health remains
a compatibility surface with many existing wrappers and tests.

Insights: HealthMonitor already encapsulates a complete ledger, so fixed ownership
can reuse that unit. `_who()` currently reads mutable identity at both emission and
snapshot. `_recover()` treats any answered request as potential group evidence.

Structural points: `_AccountOperation` provides a verified handle; the factory's
`_AnswerEvidence` sees the actual client and request; HealthMonitor owns record,
recovery, callbacks and snapshots; TgData is the local composition point.

Principles: a health observation is not authority to choose an account; identity
proof is not proof of group access; observers must not change the observed work.
Meaning-nodes: fixed owner, owned observation, recovery evidence, local snapshot.

**SV2:** store each new verified account's health under fixed ownership and define
the observation boundary, not just its label. H4/H5: “owner” is numeric identity
proved by Stage1; neither a session name nor the example numbers themselves.

## Phase 2 — perspectives and actual probes / SV3

Technical: client identity is available at the request wrapper, while the current
call context alone cannot distinguish a foreign client or authentication subcall.
User: a named-account query is easier to interpret than a default summary that
silently selects among old and new accounts. Strategic: reuse one existing monitor
per verified owner instead of rewriting every ledger field into a registry.
Failure: callbacks and cleanup execute at different times from the health record.
Resources: no additional authentication RPC is needed beyond Stage1/admission.
Systemic: keep health advisory; neither callback failure nor a health query should
start account work, join or decide routing. Phase: group-access semantics belong
to Stage3, so Stage2 must require explicit access confirmation rather than guess
from metadata. Internal consistency: “observer cannot break work” is stronger than
catching ordinary Exception; cancellation is a separate failure mode.

Three baseline probes ran against real current health/facade and SDK code, with
synthetic transport and socket.connect/connect_ex forbidden:

```json
[
  {"case":"stored_owner_relabel","event":222,"snapshot":111,"denied_groups":["7"]},
  {"case":"self_proof_recovers_group","verdicts":["no access","ok"],"no_access":{}},
  {"case":"observer_changes_primary","expected":"ChannelPrivateError","actual":"CancelledError"}
]
```

The first used the public get_message_count/health_check facade with Stage1's real
temporary client inside a synthetic engine read: after the denial, changing the
primary cache relabelled its stored summary. The second ran only verify_account
inside a group health call after a prior denial. The third made an async observer
raise CancelledError while an actual health call was propagating ChannelPrivateError.
These are observations of current mechanisms, not tests supplying their conclusions.

Frame-exit enumeration: health refers to legacy per-instance observations, verified
owned operations, pre-proof diagnostics and callback delivery. Legacy identity has
no guaranteed proof and cannot be migrated into a verified ledger by renaming it.
Pre-proof errors still reach the caller but cannot honestly become a condition of
the expected account. Delivery is a notification of already-recorded facts, not
part of Telegram success. Residual review found no need for cross-instance state.

**SV3:** fixed ownership needs bounded source evidence and a separate notification
lifetime. H1/H2/H3/H7: the three initial variants differ principally in migration
extent, not the need for these safeguards. Full legacy migration is not necessary
to make the new owned boundary truthful.

## Phase 3 — ambiguity collapse / SV4

### A1 — partition a ledger or reuse fixed-owner monitors?

Strongest counter: one owner-indexed HealthMonitor makes all snapshots uniform.
Structural test: it requires rewriting every account/wait/group/counter field and
default selection behavior; existing HealthMonitor already encapsulates that state.
Resolution HIGH: reuse one fixed-owner monitor per verified account within a TgData
instance, separately from its legacy monitor. Fixed: owner never changes after
creation. Excluded: last-writer identity and cross-instance registry. Dependents:
composition/cache and snapshots. Model change: ownership is the existing ledger's
boundary, not another dimension on every stored cell.

### A2 — migrate health_check or expose an explicit owned snapshot?

Counter: extend no-argument health_check to pick the last verified account. Structural
test: concurrent accounts and legacy observations make “last” ambiguous, and a
network check of the primary can clear the wrong source. Resolution HIGH: add an
explicit local `get_account_health(account_id)` view for verified operation state;
return None when this instance has no verified state for that ID. Keep the existing
network health_check legacy behavior separate and document the distinction. Fixed:
query does no I/O, guessing or recovery. Excluded: aggregate default selection.
Dependents: facade docs/tests and future group callers. Model change: the caller
names the ownership it asks about, just as Stage1 names the expected account.

### A3 — what does a successful request prove?

Counter: a request answered while a group is named proves that group's access.
The self-only probe disproves it. Resolution HIGH: only the bound verified client's
answers in the owning task can supply account recovery evidence. Group recovery
requires the internal operation to explicitly confirm access after an actual owned
answer; metadata/self verification does not automatically confirm it. Fixed: record
the evidence time, and compare it against the condition's time. Excluded: return-
value-only recovery and foreign-client answers. Dependents: request observation,
call confirmation method and Stage3 semantics. Model change: ownership and scope
of evidence are distinct. The confirmation is a trusted internal assertion about
the operation's result, not an attempt to infer all group semantics in Stage2.

### A4 — when may account health start?

Counter: attribute failed setup to the expected ID, since the caller selected it.
Structural test: expectedA/actualB is precisely the case Stage1 must reject; before
proof there is no verified owner. Resolution HIGH: owned observation begins only
after Stage1 yields. Setup/identity-mismatch/local errors retain their caller
exceptions without creating owned health conditions. Isolate setup/teardown from
enclosing health calls so neither contributes recovery evidence to an outer owner;
an error owned by this boundary must not be reattributed by an enclosing legacy
call. Fixed: no fabricated owner for pre-proof failure. Excluded: merging unknown
diagnostics into account state. Dependents: scoped isolation and exception handling.
Model change: inability to prove identity is a caller-visible failure, not proof
that the expected account is banned/logged out.

### A5 — can exception type alone establish its owner?

Counter: the surrounding call names an account, so classify any escaping health
exception there. Structural test: a nested foreign client or a local exception
with incidental RPC context can occur inside that call. Resolution HIGH: retain
request provenance in the short-lived call: actual bound-client failures observed
by the factory wrapper, then classify only a matching exception/cause for owned
automatic reporting. Explicit engine reports remain tied to the active owned
observation, with the same source check for RPC failures. Fixed: no credential
fingerprints or cross-call error registry. Excluded: attributing another client's
error by ambient context alone. Dependents: small request hooks and call-local
references. Model change: verified account plus observed source supplies authority.

### A6 — observer delivery and work outcomes

Counter: await the existing callback in the work task, preserving old delivery
timing. The observer-cancellation probe shows it can replace the primary error;
it can also hold a temporary client open. Resolution HIGH for new owned operations:
record health synchronously, queue its notifications, finish the Stage1 close
attempt, then schedule callback delivery in isolated tasks. Observer failure and
observer cancellation are best-effort diagnostics, never caller cancellation.
Legacy delivery timing remains unchanged. Fixed: state is available before the
operation's outcome; owned callback completion is not a prerequisite for it.
Excluded: callback re-entry loops, delivery as routing permission, or an unbounded
observer delaying client closure. Dependents: deferred notification/delivery tests
and clear documentation. Model change: health state is authoritative in memory;
the callback is a notification, not part of remote success.

### A7 — nested/concurrent calls and wait recovery

Counter: sharing a monitor or inherited ContextVar is enough to share recovery.
Structural test: an older call can finish after a newer wait for the same request;
different monitors can be nested on the same task. Resolution HIGH: inherited
parent reporting stays within the same monitor/task; owned records reject stale
or foreign-task contexts; wait recovery must match the observation generation it
handled, not just the request name. Fixed: simple per-call evidence/ticks and per-
request current wait token. Excluded: whole request-history framework or health
changes from detached inherited contexts. Dependents: overlap/reentry regressions.
Model change: shared account identity permits shared state, not stale recovery.

### A8 — the old example or the general ownership pattern?

Counter: pinning user_id on snapshot fixes the demonstrated mismatch. Structural
test: sequential account changes, overlapping sources and recovery would still
operate on shared unqualified state. Resolution HIGH: test events, local snapshots
and recovery under distinct owners, same owner concurrency and legacy coexistence.
Fixed: no copying legacy conditions into owned state. Excluded: hardcoded-ID or
event-only fixes. Dependents: complete acceptance matrix. Model change: the old
example is evidence of a boundary problem, not the entire defect.

**SV4:** eight ambiguities have explicit bounded commitments. Callback timing is an
intentional new owned-path contract, not a silent change to legacy delivery.

## Phase 4 — reduction / SV5

Fixed: per-instance fixed-owner monitors reused from existing HealthMonitor;
explicit no-I/O snapshot; observation only after proof; client/task-bound evidence;
explicit group-access confirmation; wait-generation matching; notifications after
cleanup in isolated tasks; compatibility boundary for legacy calls.
Eliminated: last-owner default, broad legacy migration, registry, persistent health,
general arbitrary-client supervision and per-RPC reauthentication.
Remaining implementation latitude: private helper placement/names and reuse of
existing callback guards. No external decision or permission is required.

**SV5:** prove → observe owned work → record/recover by owned evidence → close →
notify. Query reads the chosen owner's already-recorded ledger, never the cache.

## Phase 5 — SV6 and checks

Use the existing ledger as a fixed-account unit and compose it with Stage1 rather
than redesigning the library around multi-account health. Each owned observation
has one verified client and one task; stored facts and summaries have that same
account. Recovery has explicit evidence, and callbacks occur after client cleanup
without controlling the result.

Compared with SV1, the model now includes evidence scope, pre-proof boundaries,
legacy query behavior and notification lifetime. Accommodation/H6: new perspectives
required boundaries inside one composition, not a new state registry. H8 uses
actual code/probes, not this discipline's definitions. H9 retains account/health/
operation language. Last perspectives confirm rather than expand the design.

## Telemetry

Five anchor types; eight perspectives; three executed baseline probes; 8/8
ambiguities resolved with structural counters. All SV1–SV6 and hook checks present.
Checked status-quo bias, premature stabilization, anchor dominance, perspective
blindness, clean resolution and self-reference. No unresolved planning premise is
hidden; selected composition still requires prebuild proof in the later plan critic.
**Verdict: PROCEED** to decomposition.
