---
model: gpt-6-astra
effort: max
---
# Decomposition — Stage3 observation boundary

## User Input and clarified whole

_branch.md I1 and saved sensemaking.md SV6. The paired feature supplies fresh group
metadata and a separate bounded history-access observation for the expected account.
Unknown evidence stays unknown, group RPC denial stays scoped, operational errors
survive, and only valid history can assert group recovery. Joining remains outside.

## 1. Coupling map

| Elements | Coupling | Why a change propagates |
|---|---|---|
| Reference syntax, target kind and public/health label | Strong | Changing interpretation or label can select another peer or expose an invite token |
| Response identity, entity kind, metadata, member and input peer | Strong | All come from the same matched reply; splitting them could combine different groups or different evidence strengths |
| History request, budget refusal, raw RPC classification and group assertion | Strong | The same request outcome must drive both public result and health without an invented success |
| Expected account, temporary lifetime, return/raise and notification timing | Strong, already supplied | The merged boundary owns the client and account; a parallel lifecycle would break attribution/cleanup |
| Domain observation and portable public result | Moderate | A small explicit data contract crosses this boundary; SDK objects stay inside the source lifetime |
| Legacy discovery models and new observation values | Weak | Existing GroupInfo can remain unchanged while the new feature represents uncertainty |
| New source logic and joining/routing | Weak, future only | Later work can consume facts, but no allowance/mutation/state flows back into this stage |
| Implementation and SDK/admission/health test fixture | Moderate | Tests must observe the real boundary rather than synthesize its promised outputs |

## 2. Top-down boundaries

B1 separates local reference interpretation from authenticated source observation.
B2 keeps matched source metadata, membership and possible input peer together.
B3 separates “which group facts exist” from “what did the history attempt establish”.
B4 separates the already-built lifetime/health mechanics from Stage3 domain meaning
and public projection. B5 separates evidence collection from tests that challenge it.
These are conceptual boundaries, not a demand for five modules or service objects.

## 3. Bottom-up validation

The irreducible atoms are a parsed group reference; one verified operation handle;
one matched TL response; an optional safely constructible peer; one bounded request;
its result/exception; one explicit access assertion; one portable output. Group ID
and input hash must not be selected independently from different reply entities.
Likewise, access status and recovery must consume the same validated result.

The atoms align with B1–B5. No new atom requires a connection manager, budget store,
health registry or result lifecycle. Holding the SDK entity only within the operation
is a real lifetime constraint, not a reason for another stateful engine. Confidence
is HIGH for these boundaries. Field names and module arrangement remain for Innovation.

## 4. Question tree and verification criteria

### Q1 — Which explicit group reference does the caller mean?

- [ ] Accepted handle/link/invite/numeric forms are finite and documented; user/self/
  phone/other URL forms cannot silently become group lookups.
- [ ] A numeric peer's namespace is deterministic; absent/ambiguous local evidence
  does not trigger a dialog sweep or arbitrary cache selection.
- [ ] The correlation/health label is stable and does not expose an invite token.
- [ ] Bad syntax is distinguished from source failure without network-type guessing.

### Q2 — What fresh group observation can the source actually supply?

- [ ] Responses match the requested peer; users, missing/duplicate matches and
  unsupported/malformed shapes have explicit outcomes.
- [ ] Full Chat/Channel/Community and forbidden/min/invite forms preserve their
  available metadata, unknown identity and membership qualifications.
- [ ] The determination of an input peer is explicit: required ID/hash/kind,
  min status and absence are checked; zero is not confused with missing.
- [ ] Preview expiry/approval/payment hints remain observations; none invokes joining.

### Q3 — What does the history attempt establish, and what stays an error?

- [ ] A bounded request through the existing client consumes normal read admission;
  budget/auth/wait/server/local failure is not a group-read denial.
- [ ] Only a valid history response supports readable, including a valid empty reply;
  malformed or cache-only response shapes cannot invent a positive result.
- [ ] Classified group RPC failure supports denied with the original reason;
  no peer supports unprobed without sending history.
- [ ] The same validated positive result alone authorizes the existing explicit
  group assertion; metadata/unprobed/cancelled/failed work does not recover denial.

### Q4 — How do callers receive the observation under the correct account?

- [ ] Two public async methods require the expected account and use the existing
  owned-health operation once per call, without legacy _reported wrapping.
- [ ] Results retain the verified owner and portable, independent values after
  source cleanup; no raw client/entity/hash or invite secret escapes as a result.
- [ ] Original errors/cancellation and cleanup/notification rules remain unchanged.
- [ ] Existing GroupInfo/discovery/persistent-client behavior is unaffected; the
  verified1.45 version contract and result qualifications are documented.

### Q5 — Which actual mechanisms must tests observe?

- [ ] Tests run real SDK request resolution/serialization, sender error construction,
  the actual facade/Stage1/Stage2, session storage and budget admission.
- [ ] Synthetic server replies are labeled non-covering for live permissions; fixtures
  never precompute the intended owner, access verdict or recovery decision.
- [ ] Forced overlap, cancelled/failed reads, cold/cache collisions, unknown metadata
  and old rejection cases are exercised with explicit negative expectations.
- [ ] Supported offline regressions and examples verify compatibility; no live action
  or changed expectation is used to manufacture acceptance.

These criteria define answered pieces; they are not an ordered coding task list.
The existing contract_probe.py supports prerequisite mechanisms, not yet the absent
Stage3 public methods. Full method acceptance remains owed by implementation.

## 5. Interface map — data and assumptions

| Source → consumer | Flow | Assumptions that must cross explicitly |
|---|---|---|
| Q1 → Q2/Q3 | Target kind/value and safe label | Value is only a reference; it is not an authenticated peer or access proof |
| Merged lifetime → Q2/Q3/Q4 | Verified handle, numeric owner, exact client/opening task | No detached work or credential replacement; no generic persistent client substitution |
| Q2 → Q3 | Fresh metadata/member qualifications plus optional private input peer | A missing peer is a normal evidence limitation only for recognized shapes; malformed data is an error |
| Q2/Q3 → Q4 | Owner-bound observation and outcome | A domain result is not inferred from arbitrary error text; datetimes/unknowns remain representable |
| Q3 → merged budget | One concrete bounded history request | The existing hook owns reservation/settlement; local refusal precedes send; errors keep their normal charge |
| Q3 → merged health | Actual raw failures automatically; explicit confirmed access after validation | No ambient custom report, no recovery on metadata, no alias-wide rekeying or counter bypass |
| Q4 → caller | Portable values or original operational exception | Point-in-time readability, not future permission, full-history completeness or a join authorization |
| Q1–Q4 → Q5 | Public contracts and actual source boundaries | Assertions must inspect real path effects, not helper-supplied outcomes |

All runtime flows are one-way through the already-owned call. Policy/admission may
make a nested self RPC through that same bound client; this is an existing prerequisite,
not reverse domain control. Reference labels remain the current health grouping;
canonical group identity is returned separately, without an implicit alias registry.

## 6. Dependency order

First establish Q4's external owner/result/error contract and Q1's target contract;
they constrain Q2's observations. Q2's available evidence then constrains Q3's history
attempt and assertion. Q5 defines falsifiers at those interfaces before dependent
implementation and verifies the composed public path afterward. Q1's pure parser
cases and Q4's value projection can be reasoned about independently once their shared
label/shape contract exists. No circular dependency or need for parallel agents.
The final code plan chooses execution steps only after Innovation/Critique finish.

## 7. Self-evaluation and stopping

| Dimension | Result | Evidence |
|---|---|---|
| Independence | PASS | Each question is answerable using named contracts, not sibling private internals |
| Completeness | PASS | Both I1 operations, reference forms, owner, unknown/denied/error, admission, cleanup, compatibility and verification are covered |
| Reassembly | PASS | Parsed target + verified source + matched observation + optional bounded read + projection reconstruct both methods |
| Tractability | PASS | Five coherent questions; no single question contains the entire existing health/lifetime system |
| Interface clarity | PASS | Target is not proof; metadata is not a peer/permission; budget and assertion assumptions are explicit |
| Balance | PASS | Q2/Q3 are the central domain work; the other questions are meaningful boundaries rather than trivial fragments |
| Confidence | PASS | Top-down cuts preserve the bottom-up source/result atoms |

Determination-mechanism check: Q1 owns numeric identity determination; Q2 owns peer
availability and matching; Q3 owns positive/negative/error evidence; Q4 obtains actual
owner from the merged boundary. None assumes a magical earlier classifier.
Checked all seven decomposition failure modes. No missing prerequisite or need for
DV2 found. Stop here: each piece is tractable and directly verifiable; further splitting
would create fragments rather than independent problems.
