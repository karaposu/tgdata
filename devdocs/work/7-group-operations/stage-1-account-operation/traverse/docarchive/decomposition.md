# Decomposition: Stage 1

## User Input

_branch.md, surfacing.md, sensemaking.md: a small internal owned-operation boundary.

## 1. Coupling map

| Cluster | Strong internal coupling | Crossing interface |
|---|---|---|
| P1 Construction/policy | session, proxy, pinned device, retries before connect | one freshly configured client |
| P2 Ownership/admission | expected ID, fresh self proof, active lifetime, later budget check | verified numeric owner or explicit refusal |
| P3 Close/outcome | owned client, completed disconnect attempt, primary outcome, caller cancellation | asynchronous close completion and sanitized diagnostic |

P1↔P2 moderate: proof needs P1's bounded request policy. P2↔P3 strong at one lifetime
transition (close admission before cleanup) but no shared health or database state.
P1↔P3 weak: construction errors before a client exists require no disconnect;
once construction returns, every exit attempts it. Tests span all three contracts.

## 2. Top-down boundaries

Keep connect/auth proof in a single context rather than independent wrappers whose
exit ordering can drift. Place the cancellation helper outside proof logic; it
must also close clients when proof fails. Reuse the existing factory instead of
duplicating proxy/session/device selection. Retain budget reservation/settlement in
its existing component; only its identity provider changes when explicitly owned.

## 3. Bottom-up validation

Atoms: validated positive ID, actual SDK self response, constructor kwargs,
one yield, active→closed transition, one disconnect future, original exception,
before-send quota reservation. No atom straddles a split without a named interface.
The context orchestrates all three pieces; it is not a fourth generic framework.
Top-down/bottom-up agree: HIGH on all three boundaries.

## 4. Question tree

Root: how can one temporary operation be owned and closed without implicit identity?

- **P1: How is the client ready before its first authenticated request?** Verify:
  inherited session/proxy/device/read-budget configuration, unchanged ordinary
  defaults, no flood sleeps, finite retries, original last RPC error, no start/login.
- **P2: How is ownership determined and kept at admission?** Verify: reject bool,
  noninteger and nonpositive expectation before construction; self proof comes from
  the client's actual GetUsers(InputUserSelf) response; both user acceptance cases;
  later proof disagreement precedes reserve/send; handles do not mix on overlap;
  using a closed handle cannot admit work; auth absence has explicit error.
- **P3: How does every exit finish its cleanup attempt without changing the work?**
  Verify: success/error/auth failure/cancel all close; repeated caller cancellation
  waits for closure and propagates; cleanup exception/internal cancel logged by
  type only; logger failure cannot mask primary outcome; no detached close task.

Each piece is answerable from the interfaces below. Tests are completion criteria,
not a separate product architecture. Stop decomposition here: all are tractable.

## 5. Interface map and assumptions

| From → to | Flow | Assumption made explicit |
|---|---|---|
| caller → P2 | positive expected account ID | not inferred from a session or health cache |
| P1 → P2 | exclusive fresh client | policy set before connect; no caller login/rebinding |
| P2 → body | client + read-only verified ID + verification method | internal lexical use, not a public raw SDK sandbox |
| P2 → budget | same client's fresh verified ID | compare before durable claim; no fallback to another owner |
| context → P3 | same client and exit | run even on connect/proof failure; mark handle closed first |
| P3 → caller | settled close attempt, preserved outcome | no wall-clock guarantee; caller cancellation takes precedence over cleanup error |

The raw client is not permission to detach work; future internal call sites must
stay in the context and use the verified handle at admission. Health observations
are not an ownership source or a deliverable here. Session storage remains caller-
configured and uses existing StoredSession stale-write protection.

## 6. Dependency order

Define P2's identity/lifetime interface, then P1 construction and the orchestrating
context; P3 is independently testable against a real SDK disconnect. Integrate the
budget identity provider after P2 exists. Finally exercise the whole composition.
No cycle: the budget consumes verification but verification is an unmetered self
RPC. Actual workflow remains sequential; no agent delegation.

## 7. Self-evaluation

Independence PASS (named interfaces); completeness PASS (five user steps map to
P1–P3); reassembly PASS (construction→proof→body→close and later admission cover
the complete lifecycle); determination mechanism PASS (fresh self RPC plus numeric
comparison, not a presupposed owner); tractability PASS; interface clarity PASS;
balance PASS (three substantial but small questions); confidence PASS (both
directions agree). Failure check: no premature/over-decomposition, hidden state,
missing identity mechanism or unordered dependency. **Verdict: PROCEED.**
