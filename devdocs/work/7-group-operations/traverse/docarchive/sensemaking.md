---
model: unknown
effort: unknown
---

# Sensemaking — what the three group operations can prove

## User Input

G1 from `_branch.md`, preserving A1–A4: implement issue #7's ephemeral lookup,
account access check and limited joining. Inputs are the committed articulation
and surfacing outputs, current source and the warmed #5/#9/#6 context.

## SV1 — Baseline

The initial reading is three convenience wrappers: resolve a group, ask whether
an account can use it, then join if needed. A join counter seems like a small
extra parameter. That reading leaves “use”, “joined” and the counter's unit
undefined and therefore cannot yet support the issue's “ready” decision.

## Phase 1 — Cognitive anchors

### Constraints

- **C1:** all three operations use the existing use-and-close client, without
  prompting or replacing the persistent/pool lifecycle (surfacing 5/6).
- **C2:** lookup/read checking must not silently perform a join; joining is an
  explicit membership-changing request (7–11/19).
- **C3:** target 1.45.0 and its actual types, preserve account controls and
  exclude duncan; live membership changes are not this implementation test (1/2).
- **C4:** #7 requires an account join limit; the amount/window/default are not
  specified by the issue (1/15/16/26).

### Key insights

- **K1:** entity metadata, account membership and a successful history request
  are different observations. A public room can be readable without membership.
- **K2:** an unjoined invite preview has no group ID in the SDK constructor;
  Peek has a chat plus expiry; Already has an existing chat (10).
- **K3:** installed joins return Ok-with-updates or WebView-with-bot/query data;
  an unqualified truthy-response → joined rule is not a protocol (8–12).
- **K4:** SDK retries sit below a public helper. Counting completed helper calls
  does not bound requests after errors or cancellations (12/16).
- **K5:** fresh get_me().id and restored _self_id are not interchangeable billing
  authorities; the existing read guard already accounts for that distinction.
- **K6:** generic group normalization preserves a private invite's text, and
  generic successful-call recovery can treat metadata as access evidence (17).

### Structural points

The existing factory owns proxy/device/session/budget composition. The short-lived
context owns connection/auth/disconnect. GroupInfo owns legacy known-group metadata.
Health observes operation context and real errors. ReadBudget owns a distinct
message-read allowance. A result contract and join admission are missing surfaces.
SDK entity caching sees direct chat/users collections, not nested join updates.

### Foundational principles

No mutation without explicit intent and configured admission. No stronger claim
than the observed response supports. Uncertain remote completion is not proof
that nothing happened. Local policy/configuration failures must not inherit a
Telegram verdict. Existing well-tested shared controls are constraints, not a
reason to pretend a new resource has the same unit as message reads.

### Meaning nodes

**Target**, **metadata**, **membership**, **readability**, **join acknowledgment**,
**join attempt**, **verified account**, **allowance**, **operation outcome**.
These name existing user/protocol concerns; they are not implementation modules.

## SV2 — Anchor-informed understanding

The feature exposes observations and one admitted state-changing operation.
Its main work is defining proof boundaries, not adding three method names.
The same account/client lifecycle can support all three, but metadata must not
stand in for readability and a join response may describe unfinished interaction.

H4/H5 inspection: “access” and “join count” cannot inherit a convenient meaning
from an existing type name. The supplied ready/private-group examples are cases
of the general account/target relation, not an exhaustive outcome list.

## Phase 2 — Perspective checking

- **Technical/logical:** the installed return wrappers and incomplete invite
  metadata introduce distinct states. New anchor: result completeness must be
  representable without inventing an ID or assuming every reply carries chats.
- **Human/user:** a ready/not-ready decision needs an explanation. New anchor:
  pending approval or required interaction cannot be presented as completed
  membership or collapsed into a generic false result.
- **Strategic:** #10 will relay these operations across a process boundary.
  New anchor: portable data and stable distinctions help without adding the
  worker, queue or a receiving service now.
- **Risk/failure:** a failed response can follow an applied remote mutation.
  New anchor: quota must be admitted before a send and uncertainty must remain
  charged; success-only accounting can lose the very attempts it must limit.
- **Resource/feasibility:** short-lived clients do not provide persistent quota
  memory. New anchor: a coordination domain must be explicit across clients and
  restarts, with no database transaction held over network I/O.
- **Ethical/systemic:** automatic lookup must not subscribe an account or pay
  for access. Invite material also grants entry. New anchor: explicit actions,
  deliberate incomplete outcomes and operation labels that do not reveal tokens.
- **Definitional/internal consistency:** “can read”, “is a member”, “join accepted”
  and “join requested” are not synonyms. GroupInfo's required ID cannot represent
  every invite preview without inventing data.
- **Phase/calibration:** no safe numeric join rate is calibrated in this project.
  New anchor: caller-supplied policy is meaningful; an invented default advertised
  as account safety is not. The limiter is local admission, not a Telegram ban
  prevention guarantee.

### Frame-exit completeness

The inherited multi-value term **access** now appears with distinct meanings.
Existence enumeration: authenticated account access, metadata visibility,
membership, history readability, posting/admin rights, paid or web-view-gated
entry. All but posting/admin capability participate as current or incomplete
operation evidence. Posting rights are not needed to read; joining does not
promise them. Paid/web-view execution belongs to an external interaction layer,
but its observed requirement remains in the result layer rather than being ignored.

Counter to that boundary: “one-call join” could require completing every external
interaction. The concrete protocol supplies an unfinished web-view outcome rather
than an acknowledged join; completing it adds a distinct interactive capability
absent from this library/request. Reporting it honestly preserves the operation's
coherence. Residual case: temporary Peek is neither durable membership nor a
timeless access grant, so its expiry remains explicit. No further referent changes
the boundary after this pass.

## SV3 — Multi-perspective understanding

A useful group operation reports exactly what was observed for a verified
account and explicit target. A limited join is an admission-controlled mutation
attempt, not a counter increment only after a happy response. Client lifetime,
result truth, quota state and operational diagnostics must remain separate.

H1/H2/H3/H7 inspection: A1's simplicity remains desirable, but A2/A4 expose
requirements it cannot erase. No calibrated numeric default or global multi-host
coordination may be assumed from the phrase “per account”.

## Phase 3 — Ambiguity collapse

### W1 — Does lookup require an addressable full group?

**Strongest counter:** return GroupInfo only, rejecting unjoined invite previews
because existing metadata always has an ID. **Structural test:** ChatInvite
contains usable title/type/count but no chat ID; requiring an ID defeats the
issue's private-group “needs to join” workflow before it can explain the target.
**Confidence:** HIGH. **Resolution:** lookup can represent a preview separately
from a resolved peer. **Fixed:** absent IDs remain absent. **Excluded:** invented
IDs or declaring a preview a full peer. **Dependencies:** result shape and access
check. **Model change:** metadata availability has more than one completeness level.

### W2 — Is access just membership?

**Strongest counter:** checking left/member flags is cheaper and avoids a history
read. **Structural test:** public history and temporary invite peeks can be read
without durable membership; a membership flag does not observe the requested
history operation. **Confidence:** HIGH. **Resolution:** distinguish membership
from read-capability evidence; prove readable history with a bounded real request
when a peer is available. **Fixed:** a quota/transport failure is not a negative
access answer; inability to form a peer is explicitly unprobed. **Excluded:**
metadata-only “can read” claims. **Dependencies:** statuses, read-budget cost and
health recovery. **Model change:** readiness derives from operation evidence.

### W3 — Does a successful join call always mean membership?

**Strongest counter:** Telegram returned normally, so report joined and simplify
callers. **Structural test:** the SDK's WebView result carries bot/query data,
while Ok wraps updates; the documented INVITE_REQUEST_SENT case also describes
a request rather than completed membership. **Confidence:** HIGH for preserving
distinct outcomes; live server timing remains unobserved. **Resolution:** report
already-present, acknowledged join, approval request and interaction-required
outcomes distinctly; ordinary failure remains an error. **Fixed:** no post-response
metadata enrichment is required to turn an acknowledged mutation into success.
**Excluded:** guessing joined from truthiness or missing metadata. **Dependencies:**
join result mapping and retry behavior. **Model change:** one call need not finish
the platform's whole membership workflow.

### W4 — What does the join limit count?

**Strongest counter:** count only confirmed new memberships, so rejected/already-
member requests do not consume allowance. **Structural test:** after a timeout
or cancellation the remote effect may already exist; success-only accounting
refunds unobserved effects, and hidden SDK retries add sends below the method.
**Confidence:** HIGH for conservative before-send admission; exact window remains
a design choice. **Resolution:** bound admitted mutating join attempts for the
verified account, including retries and uncertain outcomes. An observed already-
member shortcut that sends no join has no attempt to count. **Fixed:** no automatic
refund based on lack of a success reply. **Excluded:** claiming a bound on all
Telegram clients or on administrators' later approval timing. **Dependencies:**
policy persistence, send boundary and tests. **Model change:** the counter's unit
is observable and enforceable rather than inferred remote state.

### W5 — Must “familiar result” mean unchanged GroupInfo everywhere?

**Strongest counter:** reuse its row dictionary for all results. **Structural
test:** preview/unknown IDs, membership evidence and pending/interaction states
have no fields in that shape; fake defaults lose information. **Confidence:**
HIGH. **Resolution:** retain legacy GroupInfo behavior but expose explicit portable
operation results for the missing states. **Fixed:** no arbitrary SDK objects as
the public contract. **Excluded:** changing legacy metadata semantics for this
feature. **Dependencies:** result projection and docs. **Model change:** familiar
metadata can participate without pretending to describe all operation outcomes.

### Verified account and persistence — property or external default?

**Strongest counter:** session name/cache ID and an in-memory counter are enough
because the client is temporary. **Structural test:** the same account can have
multiple names/clients, restored self IDs can be stale, and temporary lifetime
resets a memory counter. **Confidence:** HIGH. **Resolution:** establish actual
authenticated identity and define a shared durable admission domain. **Fixed:**
identity comes from current server evidence; quota survives client lifetime.
**Excluded:** silent per-client reset. **Dependencies:** limiter/client composition.
**Model change:** ephemeral describes connection ownership, not policy lifetime.

### Diagnostics — are metadata replies enough to recover a group?

**Strongest counter:** reuse the default public health wrapper unchanged.
**Structural test:** it treats any answered request as recovery evidence, while
lookup/self-identity replies may succeed without history access; its group
normalizer also retains invite strings. **Confidence:** HIGH. **Resolution:**
use a token-safe operation identity and recovery tied to the evidence the
operation supplies. **Fixed:** local policy/input errors stay local; real Telegram
verdicts retain their meaning. **Excluded:** false group recovery and invite-token
logging. **Dependencies:** façade observation scope. **Model change:** observation
must match the operation's claim, not merely its successful return.

### B4 — What belongs to a join interaction?

**Strongest counter:** add payment/browser/bot verification completion so every
join request can finish automatically. **Structural test:** those require
additional user interaction/payment capabilities and approvals not present in
this request or library. Ignoring their existence is equally wrong because
the selected SDK can report them. **Confidence:** HIGH for describing rather
than executing them here. **Resolution:** return/raise an explicit unsupported
or interaction-required outcome as appropriate, without following it automatically.
**Fixed:** no implicit payments, browser flow or worker/login implementation.
**Excluded:** presenting such a result as joined. **Dependencies:** result mapping,
documentation and acceptance tests. **Model change:** incomplete states are valid
information, not implementation success claims.

H4/H5/H9 inspection: the load-bearing terms are backed by distinct observable
mechanisms, not renamed proxies. These resolutions address the broader pattern
of observation, mutation and admission; the two example groups are not the whole
problem. Exact public type names, limit window and storage mechanism remain open.

## SV4 — Clarified understanding

The feature has three explicit operations over a common account/target: metadata
observation, bounded read-access observation and admitted join mutation. Results
retain membership, readability, incomplete interaction and metadata completeness
as distinct information. Join allowance measures sends that can have effects.

## Phase 4 — Degrees of freedom

Fixed: existing ephemeral factory/auth/cleanup; selected SDK version; no automatic
join from lookup/check; no fabricated peer/read proof; before-send account
admission; conservative uncertainty; durable coordination; explicit outcome and
safe health scope; separate read/join units. No default “safe” numeric quota.

Eliminated: unbounded joining when policy is absent, in-memory-only allowance,
success-only refunds, returning true for every join reply, treating metadata as
read access, raw invite labels and unrelated interactive/payment/worker work.

Still viable for subsequent design: result class/API layout, accepted reference
grammar, configured window/backend shape, admission integration point and state
projection/cache details. A1's ergonomics, A2's read proof and A4's operation
boundary survive; A3 contributes membership states but not success-only counting.

## SV5 — Constrained understanding

Reuse the account lifecycle, not its incidental metadata as proof of everything.
Bind each operation to an explicit claim and bind each mutation attempt to one
authoritative allowance before it can be sent. The remaining work is choosing
the smallest components that preserve these boundaries.

## Phase 5 / SV6 — Stabilized model

#7 is an account-operation boundary with three useful calls, honest result states
and a durable join-attempt allowance. It adds no independent account transport,
implicit membership action or external interaction workflow. Read success remains
metered by the existing read budget; join admission is a different resource.
Failures carry their actual meaning, and resource ownership ends with the
short-lived call without erasing policy state.

Accommodation check: new perspectives produced refinements to one coherent
observation/mutation/admission model, not repeated exceptions needed to rescue
the “three wrappers” model. That initial model was replaced at SV3. No upstream
framing restart is indicated. Remaining API/storage choices belong to downstream
decomposition/innovation, not an unresolved meaning gap.

## Telemetry and quality

SV1–SV6 complete; all five anchor types and eight lateral/structural perspectives
used. Eight high-impact ambiguity pairs tested strongest counters. The final
perspectives confirm already established boundary types; exact implementation
choices remain explicitly open. Checked status-quo bias, premature stabilization,
anchor dominance, perspective blindness, clean-resolution trap and self-reference.
No pipeline terminology serves as evidence for application behavior. **PROCEED.**
