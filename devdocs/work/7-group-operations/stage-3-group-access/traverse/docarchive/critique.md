---
model: gpt-6-astra
effort: max
---
# Structural critique — Stage3 contract candidates

## User Input

_branch.md I1, saved sensemaking.md SV6, decomposition.md Q1–Q5 and innovation.md's
15 candidates plus focused assembly. This is the inquiry critique, not the later
implementation-plan critic-d or PR gate. Run in this session without subagents.

## Phase0 — Dimensions and weights

| Dimension | Weight | Substance / external-anchor success criterion |
|---|---|---|
| D1 observed meaning | Critical5 | Metadata/member flags alone never establish a history-read result; known missing peer is not denial; validated empty history can establish a read response |
| D2 owner and failure provenance | Critical5 | Expected/actual account agrees; raw operational failures keep identity/meaning; result and health consume the same owned source, including failed/cancelled work |
| D3 bounded source/admission | Critical5 | Explicit group reference, deterministic namespace, no dialog sweep/join/login; history uses the existing actual-send budget |
| D4 SDK/backend feasibility | Critical4 | Candidate can run through actual1.45 and existing sessions; SDK/cache failures remain explicit rather than fabricated results; no claimed universal backend success |
| D5 caller completeness | Critical4 | Both methods, qualified metadata and optional access evidence are usable after cleanup; lookup fields survive the access result |
| D6 compatibility/extent | High3 | Existing GroupInfo and legacy behavior stay intact; existing owner/lifetime/health are consumed, not silently migrated |
| D7 evidence quality | Critical5 | Canonical API/source and executed component evidence challenge claims; supplied fixture outcomes are not counted as proof of those outcomes |
| D8 parsimony | Supporting2 | Prefer fewer stateful roles and small interfaces where correctness/coverage are equivalent; style alone cannot kill a correct candidate |

These cover the failure planes in the original critiques: caller-visible error origin,
actual SDK request association, account/health ownership and evidence strength. They
also cover this stage's newly surfaced cache/peer and result-shape boundaries. No
speed-only or code-line-count criterion replaces those mechanisms. Source/user anchor:
“Resolve a group’s details and check whether the account can access it.” A candidate
must fulfill both halves, not just expose a convenient SDK object.

### Independent frame-premise prosecutions

1. **Merged foundations are sufficient.** What if domain access cannot be connected
   without rewriting the monitor? Actual contract_probe budget_health showed metadata
   kept denial and a valid explicit history assertion cleared it under222 with cache111;
   the primitive needed by this stage exists. This does not prove the new method will
   call it correctly; that remains an implementation/plan-test obligation.
2. **Metadata/membership and read access differ.** What if this is needless model
   complexity? The serialized plain invite has no peer, while the documented peek
   allows temporary reading without joining; actual history can still fail after
   metadata succeeds. Those are protocol facts, not vocabulary chosen by the inquiry.
3. **A small projection can cover the intended SDK surface.** What if the SDK cannot
   deliver some shapes through its ordinary session path? A new backend probe below
   found exactly such a limitation. It narrows the support claim to observations the
   source actually returns; source/cache failure must remain an error. It does not
   justify pretending that every legal wire reply yields a public result or quietly
   installing a new session layer in this stage.

## Phase1 — Fitness landscape

**Viable:** explicit bounded references, qualified owner-bound facts, actual history
observation and existing lifecycle/admission/health; small stateless or thin-engine
arrangement. **Dead:** metadata/membership as sufficient read proof, lost unknowns,
catch-all denial and opaque SDK output shifting the feature back to callers.
**Boundary:** broad convenience versus fixed work; universal backend success versus
honest source-error propagation; a shared legacy migration versus this staged feature.
**Unexplored/outside purpose:** permanent permission prediction, all-account routing,
live server guarantees, global session-cache repair and joining. Their exclusion is
checked against the read-only stage, not inferred from a preference for fewer files.

## Phases2–3 — Adversarial candidate evaluation and constructive outcomes

First sweep screened every candidate on critical dimensions, then compared the viable
ones on all dimensions. The following is the accumulator: prosecution, strongest
defense, collision/verdict and useful seed. External grounding is explicit in the
component results/source contracts; no mechanism-independence quarantine is needed
for the surviving local-composition claims.

| Candidate | Prosecution | Defense | Collision / verdict / constructive output |
|---|---|---|---|
| G1 | Broad helper vocabulary/sweeps violate D3 and plain invite metadata is lost | Familiar convenience and existing SDK maintenance | KILL as complete policy; preserve the seed of reusing SDK wire conversions inside explicit bounded routes |
| F1 | Cold numeric channels may be unresolvable; marked/bare collisions can select the wrong entity | Typed local rows and explicit target matching make the limitation visible; no sweep is necessary | SURVIVE D1–D8; require bounded integer checks, exact typed matches, explicit missing-cache error and no arbitrary positive-ID choice in the plan |
| C1 | Caller-supplied peers omit the requested onboarding/lookup work (D5) | Zero resolver minimizes hidden I/O | KILL; seed: retain explicit typed peers internally, without making them the only public input |
| G2 | Default IDs/Boolean membership misrepresent valid previews; rewriting GroupInfo breaks D6 | One familiar representation is easy to consume | KILL; seed: separate the new qualified observation from legacy discovery columns |
| F2 | Dropping qualifications or promising success for all SDK/backend combinations would mislead callers | Nested full lookup keeps expiry/unknown hints, and source errors can remain errors | SURVIVE D1–D8 with the baseline SDK limitation below explicitly documented/tested; the contract is a projection of available observations, not a guarantee that cache processing cannot fail |
| C2 | Caller still branches over every SDK form and sees transport-only fields (D5/D6) | Exact raw data avoids projection mistakes | KILL for this public surface; seed: retain raw objects only inside the verified call and validate the projection |
| G3 | Permission prediction from metadata/member flags is disproved by preview/history separation (D1) | Zero history cost and potentially richer UI | KILL; seed: return member/configuration hints as qualifications, not permission predictions |
| F3 | An unexpected history shape or swallowed budget error can create false readiness | Actual bounded request plus narrow classified group denial supports a clear observation | SURVIVE D1–D8; require exact response validation before assertion, preserve empty-valid versus malformed and operational-error distinctions |
| C3 | Exception-only/no-unknown output hides a normal preview and “any success” can clear false readiness | Errors remain explicit and API is small | KILL the collapsed result; seed: keep operational exceptions unchanged within F3's qualified outcomes |
| G4 | Extra object has no independent state; could drift into another lifecycle manager | Existing engine style is coherent if it consumes the verified handle | SURVIVE all critical axes; viable unselected alternative, weaker than F4 on D8 only |
| F4 | Helpers might bypass the owner boundary or obscure coupling | Two facade methods plus one cohesive domain module need no new mutable coordinator | SURVIVE D1–D8; explicit operation parameter and no constructor/lifecycle changes are acceptance conditions |
| C4 | A global migration is large, changes legacy contracts and is not necessary for this feature (D6) | Long-term uniform ownership has real value | KILL for Stage3; seed/future question: separately assess legacy migration only when an actual consumer requires it |
| G5 | Stand-in verdicts supply ownership/access behavior, hiding the known SDK failures (D7) | Cheap, focused pure-function tests remain useful | KILL as the acceptance strategy; seed: retain pure tests as supplements to real composed paths |
| F5 | Synthetic replies do not prove live permissions; a convenient fixture can still bypass cache/error processing | Actual wire construction/SDK/lifetime/admission and forced scheduling establish the local contract | SURVIVE D1–D8; test every important seam and explicitly label non-covering live assumptions |
| C5 | Live-only testing cannot deterministically provoke malformed replies, races or local failures (D7) | Real server observations qualify examples | KILL as sole gate; seed: a separate authorized live read-only gate can supplement, not replace, deterministic acceptance |

F1/F2/F3/F4/F5 form the preferred set. G4 remains a real alternative; no stylistic
objection was promoted to a fatal defect. Every KILL has a useful retained seed.
No critical REFINE remains: required precision above instantiates existing candidate
criteria rather than adding another subsystem or changing the selected meanings.

### Second sweep — concrete failure histories / source-plane checks

- **Caller changes reference form:** fully marked basic-group ID supplies its own
  kind; bare group ID needs unique local namespace; a cached user row is never a
  group. Matching response by marked peer prevents a same-number wrong-kind reply
  from producing metadata/readiness. The plan must cover range/overflow and missing
  rows, not just a friendly username example.
- **Metadata succeeds, read does not:** actual budget probe establishes normal
  admission refusal before GetHistory and preservation of the prior denial. F3 must
  raise that refusal; it cannot treat the earlier metadata success as access proof.
- **Typed but wrong history reply:** a messages wrapper alone is not enough if its
  fields/peers contradict the requested target. Validate required shape and any
  returned message peer before a semantic assertion. A proper empty history is not
  a failure. The SDK's success hook alone is not the group's semantic result.
- **Qualifications disappear after read:** full GroupLookup nested in GroupAccess
  keeps a peek expiry and unknown payment/request hints. A positive read does not
  synthesize membership or erase those qualifications. Derived convenience views
  must agree with that single value, not copy independent mutable facts.
- **Backend failure before projection:** actual added probe passes a serialized
  CommunityForbidden with no hash through the ordinary SDK/factory. The file session
  fails while caching the reply; the store-backed session returns it. Both close,
  with zero false health events. No successful future GroupLookup is inferred from
  an error, and no SDK compatibility patch is silently added to the group feature.

Executed by extending ../contract_probe.py, final exit0:

```json
{"optional_hash_backends":{"file":"IntegrityError","stored":"reply returned"}}
```

Mechanism: Telethon SQLiteSession defines `entities.hash integer not null`, while
its inherited cache projection can yield None for the current CommunityForbidden
constructor's optional hash. The failure is inside SDK session processing before
UserMethods._call returns to a domain adapter. The same source issue affects G4,
F4 and raw-SDK C2; it is not caused by the selected value projection. A file-session
workaround would change a shared SDK/session contract and is not a prerequisite for
classic-group lookup or the error-preserving Stage3 boundary.

**Binding qualification for description/plan:** do not advertise that every legal
SDK entity shape succeeds through every backend. Preserve actual session errors,
characterize this1.45 edge in the new public-path tests, document the known limitation,
and make an unprobed result only when a recognized reply actually returns without a
usable peer. No “caught IntegrityError → denied/unprobed” workaround. This caveat is
not on a critical axis because D4 demands honest source-error propagation, not repair
of all underlying vendor bugs. Core contract and user-requested classic-group behavior
still have a clean viable candidate.

## Phase3.5 — Assembly evaluation

**Assembly A:** F1+F2+F3+F4+F5, including the source-failure qualification above.
**Prosecution:** individually correct parsers, models and health hooks can still
produce a false public result if the final method disconnects too early, passes the
wrong account/target, asserts access before checking the history reply, or catches
an SDK/cache failure as a domain outcome. This is the exact integration plane where
prior attempts failed; neither small file count nor a passing helper test protects it.
**Defense:** the actual operation already binds owner/task/client and cleanup, and
the actual source hooks own budget/error evidence. A stateless adapter only adds the
domain checks and projection while that handle is active. Public-path tests can force
all these boundaries and inspect both output and ledger before/after cleanup.
**Collision:** SURVIVE. All critical dimensions can be met without another lifecycle,
registry or global migration. D8 favors A over the equivalent GroupEngine arrangement,
while A preserves the full public contract. The known SDK/cache edge is an error path,
not a false successful observation. It must be explicit in the later plan/tests.

## Phase4 — Coverage map, accumulator and convergence

The two consecutive evaluation sweeps above used the same dimensions: first the full
15-candidate landscape, then targeted consumer/failure histories and a new real SDK
backend probe. They are evaluation cycles within this critique, not invented extra
traverse iterations. Neither introduced a new solution region; the second sharpened
an already-mapped source-failure boundary rather than expanding the architecture.
The accumulator contains all15 verdicts, constructive seeds, six viable candidates
(five selected plus G4), assembly A, and the concrete qualification.

Coverage: reference breadth, source schema, owner/result coherence, budget and error
origin, unknown/denied/readable, recovery semantics, cleanup/notifications, legacy
compatibility and verification source are evaluated. No adjacent unexplored region is
needed for the requested paired API. Live server state, global migration and joining
remain explicit outside domains, not hidden dependencies.

**Signal: TERMINATE with ranked survivors:** A first; the equivalent G4 thin-engine
assembly second on parsimony; component survivors F1–F5 supply A. The question is
answered for implementation planning. No High/Medium severity or PR acceptance is
claimed by this conceptual verdict; plan critic-d still follows description/planning.

**Telemetry:** dimensions8/8 covered; prosecution STRONG at user, failure-case,
specification, substance and external-anchor planes; landscape STABLE after the two
sweeps; clean critical-dimension SURVIVE exists. Mechanism independence validated for
local claims by current source and executed artifacts, not by shared wording alone.
Nine failure modes checked, including frame-premise and actual-plane absence. The
new SDK edge prevents overclaiming but does not justify a general cache/health rewrite.
**PROCEED** to Routelister and the runner's answeredness/conclusion check.
