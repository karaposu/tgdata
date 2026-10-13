---
model: gpt-6-astra
effort: max
---
# Decomposition — #8 login conversation

## User Input
_branch.md I1 and V1–V3, saved surfacing.md and sensemaking.md/SV6. Partition the understood ownership problem; do not turn the partition into an implementation plan.

## 1 — Coupling Map
Strong clusters:
- Conversation phase, phone/challenge association, current credential/DC and redacted observation: changing their meaning together changes which input is valid next.
- Actual auth request, its response classification and recording that response: observation must occur at the response boundary, before later work can fail.
- Child execution, cancellation and physical retirement: completion cannot be declared by observing a cancelled waiter.
Moderate interfaces:
- Configured factory policy ↔ an owned auth client: settings and credential material cross, but ordinary reader policy need not change.
- Private checkpoint ↔ application storage: opaque state crosses; durable commit/exclusive use are external assumptions.
- Completed credential ↔ existing session consumer: the #5 format crosses; auth-conversation state does not.
Weak/no coupling: group lookup/join, history budgets, pool routing and worker job protocols do not need new login behavior. Their ordinary no-prompt paths are compatibility controls.

## 2 — Top-down boundaries
B1 separates state/observation meaning from SDK mechanics.
B2 separates request semantics from generic owned lifetime; they share one explicit synchronous observation interface, not arbitrary application callbacks.
B3 separates common connection settings from the new conversation's authentication policy.
B4 separates produced secret values from application publication.
These are conceptual boundaries, not a prescription to create one file/service per piece.

## 3 — Bottom-up validation
Atoms: a phone-bound challenge hash; an auth key plus its DC; one actual server authorization; one input invocation; a cancelled caller; native disconnect completion; an opaque store write.
A hash cannot be cut away from its phone/key context. Auth result classification cannot be deferred beyond an await that can erase it. Physical retirement cannot be reduced to cancellation of an await. Store receipt cannot be inferred from producing credential text.
Top-down and bottom-up agree on B1/B3/B4 (HIGH). B2 is HIGH only with the explicit “record actual result before secondary await” contract; treating lifetime as a transparent wrapper around a composite SDK helper would split a strong bond and is rejected.

## 4 — Question Tree
Root: how can separate deliberate login inputs yield an honest, reusable credential through the configured route?

### Q1 — What private facts and public observations represent one login conversation?
Scope: phase/challenge/credential association, input eligibility, safe status versus exportable secrets, and portable-checkpoint validation. Applicable to V1 and V2; V3 additionally needs a durable admission owner.
Verification criteria:
- [ ] Every allowed next input and local refusal has a stated source fact.
- [ ] Credential/DC and challenge context cannot silently diverge after a redirect/error.
- [ ] Public status/repr excludes sensitive values; explicit secret export has a distinct contract.
- [ ] Restoration preserves completed-step facts without inventing current authorization, rollback or cross-worker exclusivity.
Independence: meaning and schema constraints can be settled without choosing a transport or store implementation.

### Q2 — Which actual SDK/server observations permit each auth transition?
Scope: deliberate send-code, code submit, optional-password/SRP, existing authorization checks, supported/unsupported constructors, invalid input and wait/redirect/unknown outcomes.
Verification criteria:
- [ ] A repeated public action does not silently become resend or another auth mutation.
- [ ] Authorization returned by the server is retained before extra initialization/cleanup.
- [ ] Fresh self identity cannot be replaced by session naming/cached identity.
- [ ] Known wrong input, expired context, required 2FA, unsupported interaction and transport uncertainty remain distinguishable.
- [ ] Redirect handling has an explicit bounded behavior and preserves the actual session.
Independence: response-to-fact rules are testable through actual TL objects/SDK with controlled wire, given Q1's contract and Q3's lifetime interface.

### Q3 — Who owns one step's work until it actually ends?
Scope: entry/overlap, queued cancellation, component interruption, body outcome capture, cleanup, and retained local facts. This is an invocation owner, not the application's whole request lifetime.
Verification criteria:
- [ ] No new source action starts after a queued stop.
- [ ] Genuine caller cancellation stays cancellation; component interruption is not misreported as caller intent.
- [ ] Repeated stop waits for actual owned work/native disconnect.
- [ ] Cleanup cannot erase already-known auth/challenge data or permit reuse of an incompletely retired client.
- [ ] Capture/restore cannot be mistaken for permission to run concurrent copies.
Independence: lifetime can be qualified with an opaque internal body, but final qualification must compose the actual Q2 body; a stand-in body alone cannot pass the feature.

### Q4 — How does an auth client preserve connection configuration and existing consumers?
Scope: API credentials, proxy/require_proxy, effective device identity, SDK version/policy, isolated transient session, health context and current factory.
Verification criteria:
- [ ] Every connection/DC change preserves the selected route with no direct fallback.
- [ ] No existing configured session is loaded/replaced just to begin a new login.
- [ ] Restore enforces the intended API/settings binding and explicit device continuity.
- [ ] Ordinary TgData/worker/pool no-code behavior and store signatures stay unchanged.
Independence: construction/compatibility is observable before any auth mutation.

### Q5 — What can the application safely persist, publish and use afterward?
Scope: completed-step handoff, the finished #5-compatible credential, explicit target-record ownership, operational limits and qualification.
Verification criteria:
- [ ] A retained unfinished checkpoint can supply the next step without saving codes/passwords.
- [ ] Final credential actually reloads through StoredSession and current client factory.
- [ ] Local save failure is distinct from successful remote login and can be handled without requesting another code.
- [ ] Examples explain exclusive latest-state use, private server storage, uncertain requests and the application's persistence responsibility.
- [ ] Combined SDK/serializer/lifetime and full compatibility checks precede production; live evidence is separately scoped.
Independence: this piece consumes the Q1/Q2/Q3 contracts and the existing store format; it need not own the application's database or HTTP server.

## 5 — Interface Map, including assumptions
| Source → target | What flows | Assumption / timing |
|---|---|---|
| Q4 → Q2/Q3 | Configured auth client and transient credential | Correct proxy/device policy is present before connect/auth; ordinary clients are independent |
| Q1 → Q2 | Valid step, private phone/hash/key/DC and next-input constraints | One active owner; state validation precedes source work |
| Q2 → Q1 | Actual challenge/auth/known-error/redirect observations | Record synchronously at observed response, before cleanup or external persistence |
| Q3 → Q2 | Owned execution/stop/retirement boundary | No detached work; component interruption is distinguishable from caller stop |
| Q2 → Q3 | Opaque body completion plus locally retained observation | Public task status is not the body outcome or payload carrier |
| Q3 → Q1/Q5 | Running/quiescent/cleanup status | No completed-checkpoint transfer claim while prior owner still acts |
| Q1/Q2 → Q5 | Secret checkpoint or completed credential, safe status separately | Not a database commit receipt; sensitive material stays off browser/log surfaces |
| Application → Q1/Q5 | Latest retained state, serialized invocation and deliberate input | No concurrent stale copies; storage protection/durability belongs to the integrator |
| Q5 → existing session consumer | #5-compatible opaque text and authenticated account observation | Saving/loading text does not certify future authorization or account readiness |

Assumptions-not-data check: exclusivity, truthful quiescence, persistence and meaning of a restored observation are explicit interfaces. A future durable coordinator (V3) must supply them itself; they are not silently inferred from a blob. A prototype only retaining an object (V1) still owes Q2/Q3, even without serialization.

## 6 — Dependency Order
Define Q1/Q4 contracts first. Define Q3's owned-body/observation interface before composing Q2. Work Q2 and Q3 together at their strong timed boundary, then Q5's handoff. Verify the complete composition before production changes.
Q1's pure value constraints and Q4's local policy inspection are independent conceptual work, but this inquiry remains sequential and uses no subagents. The Q2↔Q3 runtime exchange is not a planning cycle: the interface is defined before either concrete side, and the final prebuild tests both together.
No extra prerequisite feature is established. A broad database-backed auth coordinator would introduce new Q1/Q5 obligations instead of making the existing task smaller; it needs a stated requirement.

## 7 — Self-Evaluation
| Dimension | Result |
|---|---|
| Independence | PASS with named interfaces; no claim that all pieces can be built independently or in parallel |
| Completeness | PASS: explicit inputs, restoration, remote outcomes, secrets, route, lifetime, handoff and qualifications mapped |
| Reassembly | PASS at contract level: configured owned step changes known conversation facts, retires client, then caller persists/uses the appropriate artifact |
| Tractability | PASS: five bounded questions; Q2 is the largest but finite response classes and no extra auth families keep it focused |
| Interface clarity | PASS: state, timing and external ownership assumptions all listed |
| Balance | PASS: no trivial per-field/file fragments; each piece owns a distinct failure boundary |
| Confidence | HIGH except product portability preference remains the explicit working default from Sensemaking, not new factual evidence |

Determination-mechanism check: Q1 determines valid next inputs from validated phase/context; Q2 establishes authorization and unsupported requirements from actual response/verified-self evidence, not a cached label; Q3 determines physical completion from owned task/disconnect completion; Q5 obtains publication truth from the application's store action. No determination is merely presumed.

Failure-mode check: Sensemaking preceded this partition; no strong phone/hash/key bond split, no hidden store/timing interface, no missing response/lifetime owner, no per-field over-decomposition, dependency order explicit, complexity bounded. Further splitting stops because each question is directly verifiable. This is DV1, with no false implementation/test completion boxes.
Manual structure PASS: seven process outputs, Q-tree with criteria, assumption-aware interfaces and seven-dimensional evaluation. Next: Innovation.
