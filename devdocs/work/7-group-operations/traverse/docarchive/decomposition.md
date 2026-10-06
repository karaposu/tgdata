---
model: gpt-6-astra
effort: max
---

# Decomposition — the group-operation boundary

## User Input and whole

Use G1 and the committed SV6 from `sensemaking.md`: three explicit ephemeral
operations with honest metadata/membership/readability/join outcomes and durable
admission for join attempts. The whole must preserve existing account controls,
legacy APIs and the B1–B4 boundaries. This is a question decomposition, not an
implementation sequence or a selection of a storage/API design.

## 1 — Coupling map

| Elements | Coupling | Consequence for partitioning |
|---|---|---|
| Reference grammar, sensitive invite material, safe target labels | Strong | Parse and label from one interpretation; do not normalize secrets independently. |
| Metadata completeness, membership evidence, result serialization | Strong | The value contract must retain absent/unknown fields and their proof level together. |
| Allowance unit, clock/window, atomic claim, concurrent persistence | Strong | One durable admission-policy piece owns the whole accounting rule. |
| Verified account, SDK request classification, retry/send timing | Strong | One send-boundary piece owns who/what is billed and exactly when. |
| Policy storage and SDK transport | Moderate | A small committed-claim interface separates them; no transaction crosses an await. |
| Resolution, invite variants, a bounded history probe | Strong/moderate | Shared resolver supplies evidence; the history probe adds read evidence rather than relabeling metadata. |
| Join preflight, actual response/error, join result state | Strong | Keep mutation and its outcome interpretation together; no mandatory fallible enrichment after acknowledgment. |
| Ephemeral lifecycle and engine operation logic | Moderate | Caller supplies one owned client for the operation, not nested public calls opening more clients. |
| Operation claim, health identity, recovery/error reporting | Strong | The façade's observation scope must match the operation's evidence and token rules. |
| Existing read allowance and new join allowance | Weak data, shared transport | Different units/policies; same factory and actual request flow. |
| Future worker/UI and SDK objects | Weak through public result contract | New values carry the observations; worker/payment/web-view execution stays outside. |

Topological peaks are target/result meaning, durable admission, send authority,
read observation, mutation outcome, and public lifecycle/diagnostics. Tests cross
these interfaces but do not create another owner of their state.

## 2 — Top-down boundaries

Separate pure input/output meaning from Telegram I/O; separate persistent quota
state from an ephemeral connection; separate “may send now” from “what the
reply proves”; separate metadata/read observations from explicit mutation; and
keep public lifecycle/health ownership around, not inside, those operations.
Do not split the clock from quota claims, invite parsing from redaction, or
result classification from its observed SDK response.

## 3 — Bottom-up validation

Irreducible atoms: one parsed reference with original case-sensitive invite
material; one metadata snapshot; one read request/reply; one current self
identity; one committed attempt claim; one join enqueue/reply; one close attempt;
one operation health scope. Each atom fits a proposed cluster without being
split. Clock/cap/claim stay together; send authority and reply projection have
different ownership despite sharing the client. High-confidence agreement on
these boundaries. No extra piece is needed for each small validation helper.

## 4 — Question tree

### Q1 — What explicit target and result data make the operations unambiguous?

Verification criteria:
- [ ] Accepted ID/handle/invite grammar and safe rejection are explicit.
- [ ] Invite hashes preserve case and never become default diagnostic labels.
- [ ] Resolved metadata, unjoined preview and temporary peek can be represented
  without invented IDs; membership and read evidence are distinct.
- [ ] Join acknowledgment/already/requested/interaction outcomes have portable
  representations, with sensitive interaction details treated deliberately.
- [ ] Legacy GroupInfo semantics remain unchanged.

The question can be answered from the user/SDK contract without a database or
network implementation. It provides data contracts to the other pieces.

### Q2 — How is one account's join-attempt allowance durable and atomic?

Verification criteria:
- [ ] Unit, time window, configuration, zero/unconfigured policy and coordination
  domain are explicit; no invented “safe” numeric default.
- [ ] Clients/processes cannot spend the same remaining capacity.
- [ ] Clock rollback, restarts and policy updates do not erase current usage.
- [ ] A committed attempt survives uncertain/failed/cancelled outcomes; no
  network transaction or target/session credential is required in storage.
- [ ] Local validation/storage errors remain local and explain denial.

This question uses account IDs and time/claim data, not Telegram entities.

### Q3 — Where does a join acquire authoritative permission to be sent?

Verification criteria:
- [ ] Actual authenticated identity is determined, not guessed from a name or
  restored self cache.
- [ ] The mutating request is classified after relevant resolution and every
  SDK retry is covered; supported wrappers/batches have explicit treatment.
- [ ] Admission commits before enqueue with no unaccounted yield between them.
- [ ] Metadata/read requests remain in their own policies, and a local denial
  is neither sent nor misreported as a Telegram account failure.
- [ ] Missing configuration cannot permit an unbounded join through the new API.

This piece consumes Q2's claim contract and the existing real SDK/factory seam.
It does not interpret the final group result or own the connection lifetime.

### Q4 — How do lookup and access checking gather only the evidence they claim?

Verification criteria:
- [ ] One resolver explicitly handles the relevant invite variants and ordinary
  group references, rejects nongroups and preserves known incompleteness.
- [ ] Lookup sends no membership-changing request and no unnecessary history read.
- [ ] Access uses a bounded real history request when possible, through the read
  guard; missing peer/denial/error outcomes do not become false positives.
- [ ] Temporary Peek expiry and numeric-ID cache/dialog behavior are explicit.
- [ ] Metadata reads alone cannot establish history access.

The resolver/probe receives an already owned SDK client; it need not construct
a façade, quota store or independent session.

### Q5 — How does an explicit join report exactly the observed mutation outcome?

Verification criteria:
- [ ] Known already-present targets can avoid an unnecessary mutation request.
- [ ] Only the selected handle/invite join RPCs can be sent, through Q3.
- [ ] Installed 1.45.0 Ok/WebView wrappers, requested/already-member signals,
  ordinary failures and uncertain completion are treated explicitly.
- [ ] Missing result metadata does not convert an acknowledged mutation into
  a failed operation requiring blind retry.
- [ ] Nested group updates/cache persistence and incomplete/paid/interactive
  outcomes do not leak raw SDK objects or trigger an unrequested workflow.

This piece consumes resolution evidence, admission and the result contract.
It does not redefine the quota clock or silently prove read access.

### Q6 — Who owns each public call's client and diagnostic meaning?

Verification criteria:
- [ ] Each operation opens/closes one existing ephemeral client, without login
  prompts, a persistent/pool replacement or a current_group mutation.
- [ ] Public constructors/exports and optional policy wiring fit existing callers.
- [ ] Health labels conceal private invite material; recovery reflects the
  operation's actual claim; local versus Telegram errors remain distinct.
- [ ] Failure/cancellation and disconnect paths preserve the meaningful outcome.
- [ ] The façade composes engine functions on one client rather than invoking
  another public operation and accidentally creating a second lifecycle.

This is the composition owner, not a second source of group or quota state.

### Q7 — What evidence and documentation establish this whole contract?

Verification criteria:
- [ ] Real SDK/SQLite/filesystem seams are probed before relying on their behavior;
  supplied replies are not represented as live-server proof.
- [ ] Offline tests cover identity, retries, quota races, result variants,
  access/read-budget interaction, cleanup and diagnostic privacy/recovery.
- [ ] Required old suites pass and actual passes/skips are distinguished.
- [ ] Caller examples explain configuration, non-success outcomes and limitations.
- [ ] User exclusions and pipeline checkpoint/commit rules are preserved.

Q7 verifies interfaces and observable behavior; it does not decide them through
fixtures that supply the very behavior under test.

## 5 — Interface map and assumptions

| Source → consumer | Flow | Direction / assumptions |
|---|---|---|
| Q1 → Q4/Q5/Q6 | Parsed target and safe operation identity | One-way; sensitive hash only to resolver/SDK, never implicitly to logs. |
| Q4 → Q1/Q5/Q6 | Metadata/membership/peek evidence and, when present, a client-scoped peer | One-way; absence is not an ID, metadata is not read proof. |
| Q4 → Q1/Q6 | History-read observation | One-way; “not queried” differs from negative server evidence; read budget still applies. |
| SDK self authority → Q3 | Current account identity | One-way; stale session rows/config labels are not authority. |
| Q3 → Q2 → Q3 | Account/attempt admission request, committed permission or local denial | Request/reply; no network lock, no automatic uncertainty refund. |
| Q3 → SDK | Admitted mutating request | One-way; timing is part of the interface, including retries/wrappers. |
| SDK → Q5 → Q1/Q6 | Actual reply/error and projected join outcome | One-way; normal return is not automatically joined, and an acknowledgment is not invalidated by optional metadata. |
| Existing factory → Q6 → Q4/Q5 | Owned authenticated ephemeral client | Resource flow; one call owns one lifecycle, engines do not reopen it. |
| Q6 → existing health | Safe identity, actual error or recovery evidence | One-way; metadata completion alone cannot recover a read-denied group. |
| Q1–Q6 → Q7 | Public contracts, seams, invariants | Verification flow; fixture faults remain distinct from observed component behavior. |

No hidden shared target credentials enter Q2; no hidden successful-membership
assumption enters Q3; no implicit global quota across independent stores/hosts
is promised. Q6's client is an input interface to Q4/Q5, so runtime resource
ordering is not an import cycle. Optional peer metadata cannot be a hidden
post-success dependency of Q5.

## 6 — Dependency order

Define Q1 and Q2's contracts first; neither needs the other implementation.
Observe the existing SDK/factory seam before committing Q3's integration.
Q3 then depends on Q2; Q4 depends on Q1 and an existing client interface; Q5
depends on Q1/Q3/Q4. Q6 composes those interfaces with existing lifetime/health
ownership. Q7 defines behavioral evidence alongside each contract and verifies
the completed composition last. Although some contracts are independent, this
traverse and its later implementation follow their required sequential workflow.

## 7 — Self-evaluation

All seven dimensions pass. **Independence:** Q1/Q2 are pure contract/state
questions; Q3/Q4/Q5 receive explicit interfaces; Q6 composes them. **Completeness:**
all three operations, limits, lifecycle and caller evidence are represented.
**Reassembly:** supplied targets plus actual observations, admitted sends and
owned lifecycle reconstruct G1 without unstated behavior. **Tractability:** each
question fits a focused pass; Q3 and Q5 carry the delicate SDK seams explicitly.
**Interface clarity:** data, timing, resources and assumptions are named.
**Balance:** no catch-all piece hides most of the problem; Q7's cross-cutting
tests verify rather than implement the other pieces. **Confidence:** top-down
boundaries match the irreducible atoms.

Determination-mechanism check passes: Q4 determines peer/preview/read evidence;
Q3 determines current identity and whether the exact request is admissible;
Q5 determines outcome from actual types/errors; Q6 determines diagnostic scope.
None is assumed to have happened elsewhere. Further splitting would fragment
coherent questions, so DV1 is sufficient. All seven failure modes checked;
**PROCEED** to Innovation with Q1–Q7 and their interfaces.
