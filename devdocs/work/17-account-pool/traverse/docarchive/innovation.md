# Innovation — attempt mechanisms, iteration 2

## User Input / seed

`_branch.md`, saved current Sensemaking and Q1–Q3 Decomposition. Preserve assembly
A's scope while resolving its two critical boundary defects. Inherited methodology:
Standard default, production-task. Alternative: Contrarian-rethink would remove
durability and require externally retained shutdown state; that narrows reliability
and remains a tested alternative. Run the inherited mode with all seven mechanisms.

## Generate before testing

All Q1–Q3 are meta-decision pieces (state/outcome criteria). Each gets G/F/C.

| ID | Mechanism | Variation |
|---|---|---|
| Q1G | Domain transfer, native write-ahead journal | Separate document per account, with admitted token and scoped restrictions; CAS each independently. |
| Q1F | Combination, constraint ADD | One opaque pool document with account rows, unique admitted tokens and exact CAS; require explicit initialization and serialize pool operations. |
| Q1C | Inversion, constraint REMOVE | Reverse durable permission: let an expiring lease clear itself after a timeout, without proving the old reader stopped. |
| Q2G | Lens shifting | Regard timeout as whole-call cancellation and never recover to another account. |
| Q2F | Absence recognition, combination | Add an opt-in cancellation-prefix seam to actual BatchEngine and transfer it from wait_for's cancelled child into a typed pool timeout. Await child termination. |
| Q2C | Inversion | Reverse prefix ownership: discard complete records on timeout and retry the full range; system-level result is an at-least-once attempt, not an owed observation. |
| Q3G | Domain transfer, distinct accounting obligations | Treat restriction persistence and downstream acceptance as separate obligations; fail locally with the completed interrupted batch if settlement cannot be confirmed. |
| Q3F | Combination, extrapolation | Keep Q3G, preserve original source error separately, retain an active token until exact settlement, and expose explicit recovery/status so later callers can act without guessing. |
| Q3C | Inversion, constraint REMOVE | Reverse conservative errors: return success even when restriction settlement failed, relying on the next call to rediscover state. |

Both constraint directions fired. Absence patch-level: cancellation is omitted
from the exception tuple. Redesign-level: durable permission is absent, while the
existing backfill admission pattern already expresses it for a different owner.
Reverse absence: no new quota, receipt or cursor subsystem is missing. Native-domain
source is exact CAS admission; distinct-domain bookkeeping separates obligations.
Extrapolation extends a one-call store failure into restart/late-response histories.
Inversion reaches system permission, not just renaming a method; existence-axis
zero durable token is Q1C, identity-axis no owed prefix is Q2C.

## Inherited frame audit

Central frame “attempt permission must be durable” challenged by Q1C;
“complete prefix is owed” by Q2C; “settlement uncertainty is visible” by Q3C.
Every meta-decision has G/F/C and inversion; no unchallenged inherited commitment
or override. User exclusions are unchanged.

## Five tests

| Candidate | Novelty | Strongest scrutiny / outcome | Fertility | Actionability | Independence / disposition |
|---|---|---|---|---|---|
| Q1G | new here | survives, but per-account CAS needs more aggregate-operation bookkeeping | yes | existing primitive | CAS evidence + owner topology; ACTIONABLE alternative |
| Q1F | new here | survives with single-owner contract; conflicts stop rather than retrying writes into permission | yes | one schema and exact CAS | actual CAS plus independent serialization need; ACTIONABLE |
| Q1C | new here | FAIL: elapsed time cannot prove a stalled old task ended | — | — | killed; uncertain work must remain blocked |
| Q2G | new here | survives but timeout never recovers even with zero completed messages | limited | actual wait_for | valid alternative, weaker automatic recovery |
| Q2F | new here | survives: actual prototype retained100 records, cancelled future, real progress replay made0 reads | yes | one opt-in exception seam | empirical SDK/progress evidence; ACTIONABLE |
| Q2C | new here | FAIL: changing account visibility can lose completed observations | — | — | killed; preserve then acknowledge |
| Q3G | new here | survives if the durable token remains and error context stays local | yes | existing partial_result contract | accounting distinction + actual SyncEngine handling; ACTIONABLE |
| Q3F | new here | survives; must not make recovery an implicit reset | yes | exact token, quiescence assertion, explicit deadline | real CAS rejection plus source/receipt distinction; ACTIONABLE |
| Q3C | new here | FAIL: successful-looking operation hides unresolved eligibility | — | — | killed; expose the second obligation |

Shared-input check: Q1F/Q3F both inherit conservative ownership, so their agreement
alone is not evidence. Independent anchor: real SQLite stale-CAS refusal and actual
SDK/prefix behavior. Artifact grounding matches current _admit, SyncEngine.prepare
and wait_for; no test claims a pool implementation already exists.

## Assembly A2 — concrete refinements to assembly A

Choose Q1F+Q2F+Q3F within the original owned-reader assembly. One async opaque store
per logical pool: `load() -> str|None`, `compare_and_swap(expected, data) -> bool`.
`SQLiteAccountPoolStore` composes the existing SQLite CAS primitive in a dedicated
file/slot, with a pool document discriminator so accidental progress-state sharing
refuses. No network connection or credentials in stored state.

Explicit `initialize()` provisions missing state/adds new declared account rows;
it never clears existing restrictions or tokens. Ordinary reads/status/recovery
refuse absent state; known-state reopen uses create=False. Saved rows retain numeric
account IDs, observed time, active token (ID, group/kind, admitted time), account
repair flag, account deadline, per-group deadlines/reasons and latest recovery
recognition. Removed inventory entries remain stored; re-adding an ID cannot reset
its restrictions. Config paths, usernames and session credentials stay outside.

Before a source attempt: validate current state, choose eligible account, CAS a new
unique token, require a definite True response, then start the bounded source.
Ambiguous admission never authorizes traffic, even if later readback shows its
token. A next call sees that unresolved token and cannot select that account.
Settle only the exact token after the child ends; clear active and add the outcome's
restriction in one CAS. Stale/failed settlement stops and exposes complete data as
an interrupted prefix. No compensating write or silent success.

`recover_account(account_id, attempt_id, previous_reader_stopped=True,
retry_not_before=<explicit aware UTC>)` retires only that token, retains all stronger
known prohibitions and records bounded retry recognition. An operator must actually
stop the previous reader; the chosen retry bound handles unknown outcome policy,
not a fabricated Telegram readiness claim. A separate deliberate recheck can test
repaired authentication/identity after waits expire; it does not clear group denials
or grants quota. Both operations preserve latest-command idempotence where declared.

Pool cancellation propagates and leaves the token unresolved. Internal timeout
awaits child cancellation, transfers any completed prefix to PoolTimeoutError and
records the cooldown if settlement succeeds. A nonempty prefix stops failover.
State failures carry a completed interrupted batch and separate read_error, with
suppressed incidental context. Raw success still uses the original MessageBatch;
optional read metadata lives outside its canonical hash.

Reject duplicate expected IDs and duplicate configured session identities/known
auth-key fingerprints at source preflight; fresh ID validation remains authoritative
for different login keys belonging to the same actual account. Before verification,
health reports user_id=None, never a cached/expected ID asserted as authenticated.
Wrong identity is a configuration/repair stop, not a Telegram ban.

## Assembly check and telemetry

Strongest objection: nested account/group attempt records duplicate recovery.
Defense: account admission applies across groups and raw reads; group attempt/pending
protects one delivery stream. Their distinct owners and recovery scopes are explicit;
neither record can authorize or acknowledge the other. Unknown state intentionally
costs availability. Trusted UTC and exclusive caller ownership remain explicit
deployment assumptions, not guarantees invented by the store adapter.

Axes: storage granularity Q1G/F; authority Q1C; timeout ownership Q2G/F/C;
uncertainty reporting Q3G/F/C. All rows have mechanism traces. No remaining critical
semantic gap; actual pool composition still needs the implementation plan's tests.
Full coverage7/7, generators4/4, framers3/3; G/F/C3/3; each Q is meta-decision with
inversion satisfied. Per-piece: Q1 domain+combination+ADD+inversion/authority;
Q2 lens+absence+combination+inversion/output; Q3 domain+combination+extrapolation+
REMOVE+inversion/uncertainty. No named intervention-shape commitment, so property(v)
does not fire. Six survivors tested6/6; three kills retained; prior broad alternatives
remain in innovation_iter1.md. Convergence is externally grounded. No six innovation
failure signatures detected. **Overall: PROCEED** to Critique.
