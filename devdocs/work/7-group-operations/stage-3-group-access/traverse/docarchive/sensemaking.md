---
model: gpt-6-astra
effort: max
---
# Sensemaking — what Stage3 can observe

## User Input

_branch.md I1: “Resolve a group’s details and check whether the account can access
it.” Consume the three saved readings (metadata availability, membership eligibility,
observed history access), the inquiry surface map and the current merged foundations.

## SV1 — Baseline understanding

This is a paired public lookup/readiness feature on short-lived clients. Its apparent
simplicity is misleading: “details” and “access” can stand for different facts, and
the prior combined implementation already confused error origin and observation owner.
The open question is which claims the two results can legitimately expose, not whether
to rebuild authentication, health or joining.

## Phase1 — Cognitive anchors

- **C1, constraint:** the user selected read-only Stage3; allowance/joining remain
  later stages. The merged operation takes an expected numeric account and has a
  fixed verified client/task lifetime. Source: account_operation.py and stage context.
- **C2, constraint:** read attempts obey the existing shared budget; an exhausted
  budget is not evidence that a group is inaccessible. Source: budget_client.py.
- **K1, insight:** metadata and membership cannot substitute for a read observation.
  An ordinary invite preview has no group ID/peer; a peek carries a temporary access
  expiry. Source: actual1.45 serialized constructors and official invite semantics.
- **K2, insight:** the SDK's current Chat union includes Community variants as well
  as Chat/Channel; a CommunityForbidden may omit its hash. Source: generated layer229.
  Reusing the old four-class allowlist without considering this would hide a domain edge.
- **S1, structural point:** one private facade boundary already binds actual request
  evidence and final group assertions to an owner, and isolates pre-proof/local failures.
  The new feature supplies domain meaning to that existing boundary.
- **S2, structural point:** username/invite/numeric references have different ways to
  become input peers. Session cache rows are typed by marked ID; a bare group number
  can collide across basic-group and channel namespaces. Source: MemorySession and utils.
- **P1, principle:** a result states evidence observed for this account, not a promise
  of later access or all historical messages. Group metadata is useful even when
  access cannot be tested; operational failure must stay distinguishable.
- **P2, principle:** SDK policy/error preservation is a prerequisite already built.
  A native exception class alone does not establish that the input was wrong.
- **M1, meaning node:** group identity; **M2:** membership observation;
  **M3:** readable history now; **M4:** verified account; **M5:** unprobed access.

### SV2 — Anchor-informed understanding

The feature needs separate evidence-bearing outputs: metadata lookup and current
history access, with optional membership as another observation. Input identity and
missing peer evidence are first-class constraints; an account-level operational
failure must not be rephrased as a negative group result. H4/H5 check: these names
refer to existing SDK/library facts, not new workflow abstractions or just PR16 examples.

## Phase2 — Perspective checking

| Perspective | New or challenging anchor | Consequence for understanding |
|---|---|---|
| Technical/logical | Valid invite previews omit identity; min entities and missing hashes cannot make a general-purpose input peer | Lack of a probe target is not a successful or denied read |
| Human/caller | A scraper needs to distinguish “try later/repair account” from “group rejected this request” | Preserve errors and attach verified account to results |
| Strategic/later stages | Joining may consume membership/preview facts, but those facts do not grant a join allowance | Expose useful observations without adding mutation/lifecycle state |
| Risk/failure | Metadata can succeed while read admission fails; group errors can occur during resolution, before history | “readable” requires actual history evidence; a domain denial may carry incomplete metadata |
| Resource/feasibility | One bounded history request is enough to ask the intended question; broad dialog sweeps multiply unrelated work | Keep resolution bounded and cache requirements explicit |
| Data exposure/systemic | Invite secrets and channel hashes are transport inputs, not needed in readiness outputs or health labels | Use a non-secret correlation label and portable projections |
| Internal consistency | Old GroupInfo requires an ID and supplies discovery columns; unknown preview identity does not fit that existing contract | Preserve legacy GroupInfo and allow a separate qualified result |
| Phase/calibration | New local tests can establish SDK composition but not all live server permissions | Test real local seams and document point-in-time evidence, not permanent readiness |

### Frame-exit completeness

The inherited term “access” spans distinct propositions in this inquiry, so this
perspective fires. **Existence enumeration:** metadata visibility, membership,
history readability, permission to post, eligibility to join, local budget permission,
and session authentication. **Role assessment:** authentication and budget are
preconditions supplied by merged components; metadata/membership/history are this
stage's observations; joining and posting rights are other domains. The operation
would be incoherent if budget/auth were ignored, so they remain enforced preconditions,
not converted to group statuses. **Verdict rigor:** the strongest argument for including
join/posting capability is a future caller wanting one readiness matrix. That requires
additional mutation/permission policy and does not follow from a read reply; it is
neither needed to observe history access nor supplied by this request. **Residual:**
history completeness, edits, deleted messages and later revocation are also not proved
by a bounded successful read; explicitly preserve that limit rather than widening.

H1/H2/H3/H7: the three readings are not equivalent implementations; they have different
evidence strength. The request is about the full paired feature, not repairing only
old examples. No calibrated safety limit or real-account success rate is invented.

### Executed grounding

Ran `../contract_probe.py` on installed Telethon1.45.0 with sockets forbidden. It
uses actual TL serialization/deserialization, memory cache, the real factory/SDK/
Stage1/Stage2 composition and real SQLite budget admission. Server results are synthetic;
the probe cannot establish actual membership or server permission behavior.

```json
{"schema_cache":{"plain":"ChatInvite","plain_has_id":false,"plain_has_chat":false,"approval_hint":true,"peek":"ChatInvitePeek","peek_expiry":"2026-01-01T00:00:00+00:00","already":"ChatInviteAlready","zero_hash":0,"ambiguous_group_rows":[[-7,0],[-1000000000007,0]],"min_refused":true,"community_peer":-1000000000009,"community_forbidden_hash":null}}
{"budget_health":{"owner":222,"cached":111,"metadata_cost":0,"history_cost":1,"metadata_kept_denial":true,"explicit_read_assertion_recovers":true,"budget_refused_before_history":true}}
{"numeric_failure":{"same_final_rpc":true,"group_sends":1,"sdk_backoff":[2],"closed":true,"false_health_events":0}}
```

Exit0. Initial cache setup passed a standalone entity to process_entities, which
expects a result/container; its assertion failed. Correcting the probe to pass a
list (the actual cache interface) preserved the predicate and passed. This is a
probe-arrangement correction, not a runtime defect or a weakened feature test.
The explicit group assertion in this probe is deliberately supplied by the probe:
it establishes the existing hook's behavior, not correctness of future Stage3 logic.

Semantic references, read2026-10-10:
[checkChatInvite](https://core.telegram.org/method/messages.checkChatInvite),
[getHistory](https://core.telegram.org/method/messages.getHistory), and
[chatInvitePeek](https://core.telegram.org/constructor/chatInvitePeek).
The last documents temporary reading without joining. Installed schema is layer229;
web pages identify an older layer, so they do not override current constructor shapes.

### SV3 — Multi-perspective understanding

“Ready” cannot be one Boolean inferred from metadata or membership. A result must
carry the account, available group facts and the strength of the access observation.
A current history reply is the positive boundary. Missing evidence, denial, operational
failure and future mutation are separate. New SDK entity forms and zero-versus-missing
hashes widen the cases that must be covered, without creating a new ownership system.

## Phase3 — Ambiguity collapse

### A1 — What does “can access” mean?

**Strongest counter-interpretation:** fresh metadata or membership is a cheaper proxy
and is sufficient for onboarding. **Structural test:** a plain invite has no peer;
a peek expressly permits reading without joining; a history request can separately
fail with account/group errors. Those are separate protocol operations and observations.
**Confidence: HIGH. Resolution:** metadata availability satisfies lookup; successful
bounded history satisfies access. **Fixed:** current read evidence, not membership.
**Disallowed:** a metadata-only positive access claim. **Depends:** result statuses,
budget cost and explicit health recovery. **Model change:** two observations, not one
collapsed readiness flag. The first two articulation variants survive as metadata
properties, but not as complete access-check semantics.

### A2 — Unknown versus denied versus failed

**Strongest counter-interpretation:** all inability to read should return false.
**Structural test:** missing input peer sends no history request, whereas budget,
identity, network and server errors prevent or interrupt an observation for different
reasons. A false value erases this distinction. **Confidence: HIGH. Resolution:**
valid but unprobeable metadata yields unprobed; a classified group-access RPC yields
denied; other operational failures remain exceptions. **Fixed:** denial requires
actual group failure evidence. **Disallowed:** catch-all false/unknown on arbitrary
exceptions. **Depends:** result/error API and callers' retry decisions. **Model change:**
unavailability of evidence is distinct from evidence of denial. Malformed response
shapes are errors, not ordinary unknown observations.

### A3 — Who owns the observation?

**Strongest counter-interpretation:** the configured session or restored self ID is
enough; adding an expected account parameter burdens a simple lookup. **Structural
test:** the executed composition proves222 while cache says111; sessions are labels,
and the caller's intended account cannot be inferred safely from that stale cache.
**Confidence: HIGH. Resolution:** require the expected numeric account and return
the verified owner with each observation, using the merged boundary. **Fixed:** one
owner/client/lifetime per call. **Disallowed:** cached-owner fallback or a second
health ledger. **Depends:** all public outcomes and health. **Model change:** results
remain attributable after the temporary client is closed.

### A4 — What group facts must be representable?

**Strongest counter-interpretation:** reuse GroupInfo and require every result to have
an ID; exclude unfamiliar entity forms. **Structural test:** TL roundtrip proves a
valid preview has no ID, while the current Chat union contains Community forms using
normal channel peers and a legal missing-hash variant. Existing GroupInfo's discovery
columns cannot represent these qualifications without changing its contract.
**Confidence: HIGH. Resolution:** a small separate portable projection can retain
unknown IDs/membership and explicit current group kinds, including Community, without
changing GroupInfo. **Fixed:** no fabricated IDs or leaked input hashes. **Disallowed:**
calling a user a group, inventing complete metadata, or declaring an unsupported shape
readable. **Depends:** public values and response validation. **Model change:** type
coverage follows the pinned schema, with unknown evidence left unknown; no special
community control or joining behavior is implied.

### A5 — What work may resolving a reference perform?

**Strongest counter-interpretation:** reuse broad SDK/legacy resolution with dialog
synchronization so any convenient input eventually works. **Structural test:** those
helpers accept non-group aliases and can enumerate unrelated dialogs; positive IDs
can represent more than one cached group namespace. That conflicts with a bounded,
explicit group operation. **Confidence: HIGH. Resolution:** explicit supported handles,
Telegram links/invites and deterministically resolved numeric group peers; no implicit
join or dialog sweep. **Fixed:** bounded, typed target identity. **Disallowed:** random
cache collision selection or user/phone/self aliases as groups. **Depends:** resolution
policy and docs. **Model change:** convenience does not imply an unbounded resolver.
Whether a fully marked basic-group ID needs a cache row remains a bounded design choice,
not a permission or ownership premise.

### A6 — Are the old errors just exceptional cases to patch?

**Strongest counter-interpretation:** Stage1 now preserves final RPC errors, so the old
broad native-exception catch is harmless. **Structural test:** native exceptions can
still originate from local storage, malformed response processing or SDK helpers;
the old failure is an instance of origin being inferred from a type, not the whole
problem. The direct SDK probe retains the same final RPC with one send. **Confidence:
HIGH. Resolution:** distinguish explicit validation/absent evidence from actual request
failure; never relabel arbitrary native errors after an awaited RPC. **Fixed:** preserve
operational errors and account-owned source health. **Disallowed:** broad ValueError →
invalid-reference or blanket RPC → group-denied conversions. **Depends:** retry semantics
and test scenarios. **Model change:** enforce the boundary structurally, not by adding
error-name patches or a global exception redesign.

### A7 — What can successful lookup clear in health?

**Strongest counter-interpretation:** any fresh group reply disproves an old denial,
and canonical-ID alias merging would make summaries simpler. **Structural test:**
metadata success retained denial in the actual merged boundary; only the supplied
history assertion cleared it. Canonical alias migration would require rekeying earlier
unresolved observations and ordering, a different ownership/state task. **Confidence:
HIGH. Resolution:** lookup/unprobed results do not assert access; a validated history
result may explicitly confirm the current operation's normalized target. **Fixed:**
Stage2's owner/time/scope guards and caller-reference grouping. **Disallowed:** clearing
all aliases or overriding failed/inactive observations. **Depends:** integration and
docs. **Model change:** a local health summary is observation history, not a global
permission catalog. A caller may correlate the returned canonical peer ID separately.

### SV4 — Clarified understanding

The viable paired contract is fresh metadata plus a separate, budget-aware observation
of history access under an expected account. Metadata/membership remain useful facts,
not access proxies. Unknown peers and genuine group denials are representable without
swallowing unrelated failures. Local validation and current schema projection are
where the new feature lives; merged lifetime and health mechanics remain unchanged.

## Phase4 — Degrees of freedom

Fixed: expected owner; temporary operation; bounded references and one bounded access
read; separate membership/read facts; optional metadata; raw operational errors;
explicit group recovery only on valid history; no joins, sweeps or legacy migrations.
Eliminated: membership/metadata Boolean readiness, universal permission matrix,
automatic repair/routing, reused old event-identity overrides and duplicate budgets.
Viable design choices: public result field names, minimal module/function arrangement,
exact supported URL grammar, conservative numeric-cache convenience, and explicit
handling of inactive/migrated basic groups. These do not require changing the meaning
of the evidence or the merged architecture and belong to Decomposition/Innovation.

### SV5 — Constrained understanding

The work is a small domain adapter at the existing verified boundary: input/reference
validation, typed fresh metadata, optional budgeted history, result projection and the
appropriate semantic assertion. It has no independent connection lifecycle, admission
store or health subsystem. The only success claim is what this call observed.

## Phase5 / SV6 — Stabilized model

Build lookup as an account-owned metadata observation and access checking as an
account-owned, bounded history observation. Preserve membership, incompleteness and
expiry as qualifications. Missing peer evidence yields unprobed, classified group
RPC failure yields denied, and operational failure stays an error. A positive access
result alone permits the existing group recovery assertion. A separate public value
shape protects legacy discovery and excludes transport-only data.

SV1's apparent paired wrapper becomes an explicit evidence contract. Seven ambiguities
were resolved on structural grounds; one low-level numeric convenience remains for
later design, not as an external blocker. H4/H5 load-bearing concepts were tested by
A1–A7; H6 shows refinement rather than expanding ownership exceptions. H8 does not
fire: this is software behavior, not an evaluation of the cognitive discipline itself.
H9 vocabulary stays close to lookup, member, readable, denied and unprobed. No invented
readiness engine or general permission taxonomy is needed. Technical, caller, resource
and schema perspectives contributed distinct anchors; later frame/calibration checks
added limits rather than destabilizing the model. No premature/precedent-only closure.
