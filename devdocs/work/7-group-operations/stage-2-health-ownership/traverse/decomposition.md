---
model: gpt-6-astra
effort: max
---
# Decomposition: Stage 2

## User Input

_branch.md and sensemaking.md: fixed-owner health for verified operations, explicit
local query, owned evidence/recovery, notifications separated from client lifetime.

## 1. Coupling map

| Piece | Strong internal coupling | Crossing interface |
|---|---|---|
| P1 Owner/state/query | fixed account identity, monitor ledger, selected snapshot | one monitor per verified ID; independent plain snapshot |
| P2 Observation/evidence/recovery | actual client/task, RPC provenance, outcome, group confirmation and wait generation | owned call bound to Stage1 handle; notification records |
| P3 Lifetime/delivery composition | setup/proof isolation, body, close, notification dispatch, observer task lifetime | verified handle in; immutable event data out after close |

P1/P2 moderate: state mutations use one monitor, but source evidence belongs to the
temporary call. P2/P3 strong at call close: state must settle before callbacks and
the source client must be retired before notifications. P1/P3 weak: local queries
need no client or callback completion. Legacy monitor is a compatibility boundary,
not a fourth independent account-ownership model to migrate in this stage.

## 2. Top-down boundaries

Reuse the existing ledger as the owner-state unit; do not split its account/wait/
group fields into several stores. Keep source qualification and recovery together
because both consume the same observed client/task evidence. Put callback scheduling
outside the source lifetime, using existing event data and delivery guards.

## 3. Bottom-up validation

Atoms: Stage1 numeric owner, one bound client, one active task, one real RPC response
or exception, one wait observation generation, one explicit group-access assertion,
one ledger snapshot, one queued notification, one settled close attempt. None needs
a global registry. Parent ContextVars and exception propagation cross boundaries
and therefore appear explicitly in P2/P3 rather than remaining ambient assumptions.
Top-down/bottom-up agree: HIGH on all three pieces. No further independent split
is useful; P2's evidence subquestions below stay coupled.

## 4. Question tree and verification criteria

Root: how do new owned observations stay truthful without a broad health rewrite?

- **P1: What state can a named-account query return?** Fixed ID/session/label for
  its monitor; separate legacy state; None for unobserved account; defensive plain
  snapshots; no config/store/network access or recovery while querying.
- **P2: What may change or recover an owned condition?**
  - **P2a source:** bind an active verified handle/client and creator task; actual
    SDK hooks identify successful answers and raw RPC errors from that client;
    unrelated local or foreign-client exception chains cannot acquire that owner.
  - **P2b meaning/time:** initial fresh identity can support account evidence;
    group-access confirmation is explicit and cannot be inferred from self/metadata;
    evidence older than a condition cannot recover it.
  - **P2c concurrency:** only the handled wait generation can recover; another
    owner's or task's parent context cannot share reported/recovery flags.
  - **P2d failure:** no self-recovery from a condition the same call reported;
    invalidated/cancelled operations supply no successful group recovery.
- **P3: When can notifications act without changing work?** Setup/teardown isolated
  from outer observation; pre-proof failure not attributed; record before outcome;
  Stage1 close settles before callback invocation; sync/async observer failure and
  observer cancellation cannot replace result/error/caller cancellation; callback
  re-entry suppressed and its task exceptions retrieved. Define cooperative cleanup
  for outstanding notification tasks, including close invoked from an observer.

Tests cover each criterion through actual SDK/health/SQLite composition, including
pending futures for real overlap. They are evidence, not a separate runtime subsystem.

## 5. Interface map and assumptions

| Source → consumer | Flow | Required assumption/qualification |
|---|---|---|
| Stage1 → P3/P2 | verified account handle and client | before proof no account is known; after refusal handle stays closed |
| TgData → P1 | explicit account ID and configured label/session | no cached self identity, no implicit last-owner selection |
| SDK wrapper → P2 | client, actual answer/RPC failure | owning task and exact bound source; a native local error is not RPC provenance |
| internal operation → P2 | explicit same-group access confirmation | trusted Stage3 result interpretation, only after real owned evidence; no generic inference |
| P2 → P1 | classified condition/recovery and timing | same fixed-owner monitor, correct condition generation |
| P2 → P3 | detached event dictionaries | recorded state does not depend on callback completion or mutation |
| P3 → callback | notifications after source close | own delivery task, recursion guard, exceptions/cancellation contained |
| caller → P1 | get_account_health(account_id) | reads only owned state; legacy health_check remains separately documented |

Source provenance is short-lived call data, not an error archive or credential
fingerprint map. Explicit group confirmation is an internal semantic assertion;
Stage2 cannot prove future group business logic that Stage3 has not built yet.

## 6. Dependency order

Define P1's fixed ownership/query and P2's bound-call interfaces first. P2 and P3
can then be reasoned about against those contracts; the facade composes all three.
Real composition/probe evidence must precede runtime implementation that depends
on it. Final regressions exercise legacy and new paths together. No dependency on
unmerged #17, Stage3 or live Telegram. Work proceeds sequentially in this session.

## 7. Self-evaluation

Independence PASS via interfaces; completeness PASS across event/state/query/
recovery/delivery; reassembly PASS, including runtime determination of verified
owner and actual source; tractability PASS (P2 has focused coupled subquestions);
interface clarity PASS; balance PASS; confidence PASS (both directions agree).
Checked all seven failure modes: no premature split, hidden ambient authority,
missing query/delivery piece, over-decomposition or circular ordering.
**Verdict: PROCEED** to innovation.
