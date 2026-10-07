# Sensemaking: Stage 1

## User Input

_branch.md and surfacing.md: determine the smallest truthful ownership/lifetime
boundary spanning the three considered articulations.

## SV1 — baseline

A temporary authenticated client and an expected ID appear sufficient. That leaves
the meaning of fresh identity, late admission and completed cleanup implicit.

## Phase 1 — anchors / SV2

- Constraint C1: the user's five steps and two acceptance cases; health is Stage 2.
- Insight K1: Telethon 1.45 get_me(input_peer=False) returns a fresh User but leaves
  nonempty _self_id unchanged. The returned ID and cache are different authorities.
- Structural S1: _new_client owns proxy, identity and session configuration;
  BudgetClientMixin._read_budget_account is the existing before-reservation seam.
- Principle P1: proof is from the authenticated client; filenames and old health
  identity cannot authorize another account's operation.
- Meaning M1: an operation owns a newly constructed client for one lexical lifetime.
- Insight K2: connect itself can fetch self/GetState; policy must precede connect.
- Constraint C2: SDK retry exhaustion defaults to ValueError, so preserve its last
  RPC error deliberately. No indefinite request retries or flood sleeps here.

**SV2:** bind expectation, proof, admission and cleanup to the same client instance.
H4/H5: “owner” means the numeric authenticated account, not a session label or a
task-context event override. The two example IDs illustrate a general authority
rule, not the whole input space.

## Phase 2 — perspectives / SV3

| Perspective | New anchor or challenge |
|---|---|
| Technical | Actual get_me source hides UnauthorizedError; direct self RPC preserves it. |
| User | Stage 1 must be usable by later stages without publishing an arbitrary SDK extension API now. |
| Strategic | Explicit identity per operation avoids the old plan's multi-owner health ledgers. |
| Failure | SDK disconnect shields an internal task; outer cancellation can return before closure. |
| Resource | A proof before each metadata request doubles traffic and introduces recursive proof plumbing. |
| Systemic | Successful Telegram side effects must not look failed merely because teardown failed. |
| Internal consistency | “Reliable close” cannot honestly mean guaranteed closure if the transport itself raises or hangs. |
| Phase | This is an internal foundation; health and group APIs are deliberately not calibrated/implemented yet. |

Frame-exit review: account identity occurs as expected, fresh, cached and billing
identity. Expected/fresh control admission; cache remains SDK optimization; billing
must agree; health is not made correct by this context alone. The strongest contrary
argument is that deferring health makes ownership useless: it fails because the
request gate can prevent wrong-account work independently, while health remains an
explicit later consumer rather than an implicit promise. No excluded account role
is required to execute the Stage 1 boundary.

**Actual component probe (offline, 2026-10-08):** real TelegramClient.disconnect and
_disconnect_coro with only sender.disconnect gated by an asyncio.Event. Direct
await: after caller cancellation, caller_done=True/disconnect_done=False. Holding
its completion and awaiting it through fresh shields: caller_done=False while
blocked, including a second cancellation; after release, disconnect_finished=True
and the caller raises CancelledError. No socket/Telegram request occurred. A test
must preserve this real composition rather than replace disconnect with a stub.

**SV3:** ownership is a scoped, explicit fact; teardown is a separate outcome with
cancellation deferred until the SDK's close attempt settles. H1/H2/H3/H7: internal
and public contexts share mechanics but differ in obligations; a universal dispatch
supervisor is not required by the examples or the stage boundary.

## Phase 3 — ambiguity collapse / SV4

### A1 — internal foundation or public raw-client API?

Counter: a public context would let the user employ Stage 1 immediately. Structural
test: arbitrary client users can log in, retain clients or spawn detached work;
enforcing that contract needs machinery unrelated to later tgdata consumers.
**Resolution / confidence:** internal operation context, HIGH for this staged task.
Fixed: later tgdata implementations consume a handle. Excluded: new TgData facade
and a promise to sandbox arbitrary SDK use. Dependents: Stage 2/3 call sites and
documentation. Change: a useful implementation seam rather than a new product API.

### A2 — initial proof or constant reauthentication?

Counter: authenticating before every SDK request is strongest. Structural test:
self verification is itself an SDK request; recursion avoidance and extra traffic
would be needed, while one private client never calls login/start in this context.
**Resolution / confidence:** fresh proof before yielding, explicit fresh verification
at later admission, HIGH. Fixed: expected ID is immutable and admission returns
only that ID or raises. Excluded: silent rebinding, cache authority and proof from
a different client. Dependents: budget seam and future join admission. Change:
identity is passed as data, not inferred from logging/task context. Runtime method
for discovery: direct GetUsers(InputUserSelf) response; no credential fingerprint.

### A3 — how far does closure guarantee extend?

Counter: timeout shutdown and return promptly. Structural test: Telethon's shielded
task can outlive the timeout, so prompt return does not prove resource closure.
**Resolution / confidence:** await one retained close attempt to settle, HIGH for
completion semantics; no wall-clock shutdown guarantee. Fixed: caller cancellation
is remembered and re-raised after close, including repeated cancellation. Excluded:
detached cleanup, retrying the whole operation on cleanup failure. Dependents: close
helper and cancellation tests. Change: distinguish completed close attempt from
guaranteed successful transport closure; a hanging SDK close still hangs.

### A4 — cleanup exception versus primary outcome?

Counter: raise a cleanup-only failure to make it visible. Structural test: an
already successful future join could then be retried by its caller. **Resolution /
confidence:** preserve success or primary error; log only cleanup error type, HIGH.
Caller cancellation arriving during cleanup remains CancelledError. An internally
cancelled disconnect is a cleanup failure, not proof the caller cancelled. Fixed:
logging is best effort and cannot mask outcomes. Excluded: exception text/session
credential leakage. Dependents: outcome matrix and sanitized diagnostics. Change:
failure reporting and work outcome have separate precedence.

### A5 — two ID examples or a general lifecycle invariant?

Counter: only fix stale cached identity. Structural test: admission can freshly
observe a different user later, and invalid/bool IDs can alias integers. **Resolution /
confidence:** positive integer expectation plus fresh comparisons at admission,
HIGH. Fixed: real overlap uses distinct handles/clients; closed handle cannot admit
new work. Excluded: relabeling a different principal. Dependents: lifetime and
interleaving tests. Change: pattern covers stale cache, mismatch, logout and drift.

**SV4:** all five ambiguities have concrete commitments; no appeal to the old
revision's architecture is needed. Motives are jointly served: safety, small later
features, and reduced patch accumulation.

## Phase 4 — reduced freedom / SV5

Fixed: internal handle, one fresh SDK client, numeric expected owner, fresh self RPC,
constructor-time zero flood threshold and finite retries with original RPC errors,
noninteractive auth, admission comparison, retained cleanup completion. Factory
defaults for ordinary clients remain unchanged. Eliminated: public raw SDK API,
per-dispatch reauthentication, timeout-as-success, health ledger and new persistence.
Still variable for implementation design: exact private names and small helper
placement; no unresolved semantic gate.

**SV5:** create → connect → prove → yield owner/client → close admission → settle
disconnect. Budget admission re-proves on that same client before reservation.

## Phase 5 — SV6

Build an internal, scoped account operation that explicitly owns its client and
verified numeric identity. Proof and quota admission agree; constructor policy
already governs authentication; teardown attempts complete without replacing the
work outcome. This differs from SV1 by giving authority, lifetime and cancellation
precise meanings. It does not promise global health attribution or arbitrary SDK
supervision.

Accommodation/H6: added perspectives refined the single-client model instead of
requiring new owner registries. H8: external SDK source/probe grounds the conclusion.
H9: “expected account” and “verified account” retain the user's terms. Failure-mode
check: no status-quo defense, forced clean resolution, one-anchor dominance or
unchecked friendly perspective. Shutdown hangs remain explicit, not explained away.

## Telemetry

Five anchor types; eight perspectives, four materially new anchors; 5/5 ambiguities
resolved; SV1→SV6 changes authority, API boundary and cleanup semantics. Last two
perspectives confirmed structure. All six SVs and required counter-interpretations
present. **Verdict: PROCEED** to decomposition.
