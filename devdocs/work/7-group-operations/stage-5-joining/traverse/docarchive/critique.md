---
model: gpt-6-astra
effort: max
---
# Critique — qualify the mutation, not just a success-like name

## User Input

Evaluate all17 innovation candidates plus their assembly against _branch.md and
sensemaking.md. The user wants Stage5 implemented over merged prerequisites and
previously challenged #7's overengineering. Contract critique runs here; the later
formal implementation-plan critic-d is still required.

## Phase 0 — Dimensions and weights

| Dimension | Weight | Passing substance / external anchor |
|---|---|---|
| D1 Owner and lifetime |25, critical | actual authenticated expected account owns proof/claim/send; changed identity probe cannot send or bill |
| D2 Honest source outcome |20, critical | classify the response/error of the actual mutation, not a metadata/proof RPC; validate payload family; no false membership |
| D3 Admission and uncertainty |20, critical | one committed claim per new SDK attempt; no uncharged retry/refund; ledger and actual enqueue observations |
| D4 Coherence and scope |15, critical | consume merged structures without new unqualified ownership or post-ack guarantee; existing source/API contracts |
| D5 Feasible qualification |10, critical | real selected SDK/SQLite tests are available; no live acceptance claim from a synthetic server |
| D6 Minimum adequate implementation |8 | avoid unnecessary state/framework; compare reach to changed surfaces rather than line count alone |
| D7 Caller ergonomics |2 | portable outcomes and existing reference vocabulary; unknown facts stay usable as unknowns |

Purpose-fitness: D1–D5 failure prevents an honest owned join operation. D6/D7 alone
cannot kill a technically sufficient alternative; it can rank below a smaller one.
The project-specific axes are owner attribution, mutation admission and source-error
provenance, not generic code neatness. “Reliable” is tested across outcome/error/
cancellation, its broadest sensible meaning within the explicitly bounded API.

### Frame-premise prosecution

1. What if the merged handle cannot authorize a later mutation? Actual candidate
   composition re-verifies222, refuses333, and preserves the stale111 cache without
   billing it. The prerequisite is demonstrated, not protected by precedent.
2. What if an application enqueue is the wrong allowance unit? Actual bad-salt
   handling requeues the same RequestState/future, whereas the forced SDK retry
   performs two send admissions and costs2. A packet limiter is a different policy.
3. What if an Ok wrapper or a named RPC outcome alone proves completion? This
   premise needed more attack: the extra probes below refute unqualified use of
   the name/type. The assembly must validate payload and error origin. The overall
   source-outcome model survives; its runtime determination becomes explicit.

## Phase 1 — Fitness landscape

Viable: bounded expected-owner operation, local per-enqueue admission, qualified
source facts, explicit incomplete results, no mandatory post-ack enrichment.
Boundary: wider raw-client policy, generic quota infrastructure, per-call resources,
optional cache enrichment, narrower target grammar and later pool integration.
Dead: packet-count substitution, acknowledgment conditional on later network success,
reusable recovery permission, inherited test counts used as new proof, live-only
evidence replacing required local tests. Initially unexplored: numeric mutation
composition, unexpected RPC origin and malformed nested success payload.

## External counterexample probes

Ran `../contract_probe.py --extra` on actual1.45 SDK/owned operation/ledger; only
the wire response is synthetic and sockets/login are forbidden. Saved evidence:
`../evidence/critique-probe.txt`.

1. Numeric marked channel resolution returned peer9 with source access_hash0;
   the actual join request accepted that input peer and consumed1. Existing
   resolution can support this input without adding new lookup rules.
2. A deliberately unexpected INVITE_REQUEST_SENT response to fresh GetUsers proof
   becomes InviteRequestSentError in the actual SDK. Its request is GetUsersRequest;
   join sends0 and usage0. Catching only that exception class around the higher-level
   join await would fabricate a requested outcome for a join that never ran. This
   tests provenance handling, not a claim that Telegram normally sends that code
   for GetUsers.
3. Actual TL decoding accepts ChatInviteJoinResultOk whose nested value is User,
   despite the declared TypeUpdates annotation. The SDK returns that malformed
   wrapper after one charged attempt. Checking only its outer class is insufficient.

These findings refine the existing “other source errors stay original” and “validate
selected response shape” obligations in I8; they do not justify another health ledger
or transport rewrite. The later plan must carry both as concrete predicates/tests.

## Phases 2–3 — Candidate adversarial record

| Candidate | Prosecution | Defense | Collision, verdict and constructive output |
|---|---|---|---|
| I1 | Raw clients lack this operation's declared expected-owner context | Wider budget reach is useful for a real raw-client consumer | REFINE for separate scope: define and qualify that caller/owner contract first; not selected here (D1/D4) |
| I2 | Numeric inputs might send to a guessed or foreign peer | Current resolver has explicit namespaces/hash requirements; the extra actual-SDK numeric probe succeeds | SURVIVE D1–D5; prefer existing grammar with explicit refusal of unsupported direct mutation peers |
| I3 | Repeated per-call ledger selection can fragment accounting accidentally | Resource dependency is explicit and technically coherent | SURVIVE, lower D7 rank for current facade convention; retain as an alternative, not an added second API |
| I4 | Shared quota lifecycle can accidentally introduce read refunds into joins | Two real send guards might eventually benefit from extraction | REFINE: prove common mechanics without changing established lifecycles; larger qualification belongs separately, not a prerequisite now |
| I5 | A typed budget reference does not by itself prove a synchronous completed claim; scope may leak outside the owned call | Current handle and real SQLite seam already compose correctly, with no sender-object replacement | REFINE: require the qualified ledger/context, recognize supported join shapes, and admit only after _claim's synchronous None return; no broad raw-client promise |
| I6 | Charges protocol correction as extra application activity | A traffic shaper could control packet rate | KILL D3: replaces the selected policy unit. Seed: investigate transport shaping only if packet limits become an actual requirement |
| I7 | Later lookup failure can replace a real acknowledged join | Rich one-call information is convenient | KILL D2 as acknowledgment condition. Seed: explicit optional caller lookup can supply later information without rewriting the original outcome |
| I8 | Named success may originate in self proof; an Ok wrapper may contain User rather than Updates | Portable source outcomes are still the right result model | REFINE D2: bind recognized RPC outcomes to the exact mutation request, validate allowed payload family and WebView IDs, preserve other errors |
| I9 | Raw responses force SDK-specific interpretation back into callers | Maximum fidelity, minimal decoder code | REFINE D4/D7: retain original errors but put the relevant successful/incomplete facts in a portable result; this converges to I8 rather than a second raw API |
| I10 | Optional cache writes can fail or select the wrong room from an updates vector | The actual wrapper/cache gap exists and can be explicitly processed | REFINE: require a concrete cache consumer, exact correlation and secondary-error/cancellation tests; no current need makes this extra path part of the selected assembly |
| I11 | Invite success may still have no group ID in returned metadata | The acknowledgment does not contain a canonical target field, and existing lookup can fetch later metadata explicitly | SURVIVE D1–D5; document metadata as the preflight observation, with unknown IDs retained |
| I12 | Stored result cannot prove current membership or justify reusable mutation permission | A worker may later want durable reconciliation | KILL D2/D3 in this stage. Seed: define a separate workflow/custody requirement before a journal/recovery service |
| I13 | The old tests did not exercise the new owner/error composition | Historical fixtures offer useful components | KILL D5 as acceptance. Seed: reuse fixture machinery, not its verdict or test count |
| I14 | Synthetic replies cannot qualify live Telegram behavior | Actual dispatch, decoding, durable claims and failure precedence are observable offline | SURVIVE; add the three new counterexample/qualification cases to the final public suite, keep live limits explicit |
| I15 | Live-only qualification discards local failure coverage and exceeds authorization | A later controlled live test can validate server behavior | KILL D5 as a replacement gate. Seed: separately authorized live joining qualification after local implementation, never reuse earlier read-only permission |
| I16 | Adds a joining-specific rejection of inputs already supported by group operations | Narrow handles/invites surface is coherent | SURVIVE but lower D7 rank; numeric qualification favors I2 without new resolver machinery |
| I17 | An unmerged pool's caller behavior cannot be promised now | A stable public owned join operation is a useful future dependency | REFINE as a research frontier: qualify actual pool integration when that task is explicitly resumed |

The user-level challenge was “will this become another sprawling redesign?” I1/I4/
I12 were defended, not merely dismissed, but each needs scope or machinery absent
from the concrete bounded consumer. The selected alternative changes no ledger or
health storage and owns no new persistent lifecycle.

## Phase 3.5 — Assembly candidate A

**Composition:** I2 + refined I5 + refined I8 + I11 + I14.

**Prosecution:** a narrow guard could still misreport an error from fresh proof as
join success, accept malformed nested payloads, or treat an asynchronous/noncompleted
claim as permission. Numeric lookup may return a peer unsuited to direct joining.
These are determination gaps at actual interfaces, not reasons to build more layers.

**Defense:** use the existing exact operation handle; install a per-operation guard
on the SDK call's sender argument; require the real synchronous ledger contract;
construct the join request from the qualified peer/token. Recognized pending/already/
payment RPCs are outcomes only if their request unwraps to that exact join request,
not just a matching class name. Validate Ok's nested Updates family and WebView
integer fields before constructing GroupJoin. The preflight metadata remains the
preflight metadata; no new enrichment branch exists. Unknown/unusable direct peers
fail before mutation. Source failures/cancellation retain their existing meaning.

**Collision / verdict:** SURVIVE with those explicit predicates. This refines the
already proposed scope/validation interface, not the architecture. Actual source
and probes demonstrate the required distinctions are observable. Exact predicate
lists, public signatures and test enumeration belong in the formal plan next.
No unresolved critical design caveat remains for this local contract.

## Phase 4 — Accumulator and convergence

Pass1 screened all17 candidates against critical dimensions, recorded the boundary/
alternative directions, and tightened I5/I8's determination requirements using new
probes. Pass2 evaluated the surviving/qualified assembly across all7 dimensions and
rechecked the strongest “global guard”, “full metadata” and “live-only” alternatives.
The boundaries were already represented in the landscape; neither evaluation pass
introduced a new region. These are two critique evaluation passes within traverse
iteration1, not two invented full traverse runs.

Evaluation log:5 standalone SURVIVE,7 REFINE,5 KILL; assemblyA SURVIVE after explicit
validation refinements. Kill seeds and refinement directions are in the table.
Mechanism-independence status: **validated** for the selected assembly by actual
SDK/ledger probes, current source seams and public contracts; not merely agreement
between mechanisms sharing the “small is good” premise. Alternative future systems
remain qualified as such, not promoted from structural plausibility alone.

Coverage: owner, claim, request identity, response substance, metadata, health,
cleanup, input/configuration, raw-client scope and evidence all evaluated. Unexplored
live acceptance, packet control and future pool orchestration are different explicitly
bounded tasks; no adjacent unexplored region is needed to build the selected API.
Information gain decreased from the two qualification refinements in pass1 to no
further structural change in pass2. Dimensions/weights did not drift.

Signal: **TERMINATE**, ranked1:assemblyA; alternative API shapes I3/I16 remain lower
ranked, not additional implementation scope. Conditional cache and broad-client work
remain future refinements. All7 dimensions covered; adversarial strength STRONG;
landscape STABLE; clean assembly survivor exists. All9 failure-mode patterns checked,
including source-origin and payload-substance axes beyond labels. **PROCEED** to
Routelister and conclusion, then the formal task description/plan/critic pipeline.
