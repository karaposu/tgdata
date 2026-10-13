---
model: gpt-6-astra
effort: max
---
# Sensemaking — #8 login state and ownership

## User Input
_branch.md I1, all considered articulations V1–V3; preceding surfacing.md and the original issue/user request in ../source-input.md.

## SV1 — Baseline
Expose the SDK's send-code, sign-in and password methods as three non-console calls, retaining whatever lets the next request continue.

## Phase 1 — Cognitive anchors
Constraints: deliberate phone/code/optional-password calls; factory proxy/device policy; the existing StoredSession text contract; ordinary scraping must retain its no-code behavior. Existing users, not account registration or a new web server.
Key insights: a credential does not contain the challenge; SDK completion is composite; a local save return may not prove publication.
Structural points: application owns the web conversation/storage; Telegram owns auth-key authorization/challenge acceptance; the SDK owns transport/DC mechanics; tgdata mediates explicit steps and returns useful observations.
Foundational principles: cancellation/timeout is not rollback; known remote success is not undone by a later local failure; persisted state does not by itself authorize concurrent consumers.
Meaning-nodes: unfinished login, auth key/DC, verification code hash, authenticated account, final session, caller checkpoint, actual client retirement.
Evidence: exact five-group SDK probe is in sdk-probes.txt/json. Installed Telethon1.45 and actual StoredSession/native migration/disconnect run; only wire replies are synthetic. No server behavior is thereby qualified.

## SV2 — Anchor-informed
The feature is a login conversation with separate facts: request/challenge progress, remote authorization, locally retained credentials and application publication. The SDK's one coroutine is not the public contract.
H4/H5 check: “session” is overloaded; do not let its familiar name conflate a transport key, authenticated account and saved store row. The historic headless-prompt incident is one motivating case, not the whole new feature.

## Phase 2 — Perspectives
- Technical: two send_code_request calls issue SendCode then ResendCode; StringSession preserves the key but loses the client challenge map. New anchor: explicit intent and challenge context must survive separately from the key.
- Human: wrong code/password should leave a usable next step, while an expired/unsupported challenge needs a clear action. New anchor: error category and allowed next action are not the same as boolean login failure.
- Operator/restart: a returned checkpoint can move between workers; an interrupted network request may already have acted. New anchor: portability is not exactly-once execution.
- Failure: sign_in can raise after Authorization because _on_login requests updates; zero-retry migration can change DC/key then raise. New anchor: preserve observed authorization and actual mutated session independently of a later exception.
- Storage: StoredSession.save logs and returns after failed persistence. New anchor: a returned finished credential is not proof that the application's chosen store committed it.
- Security/systemic: unfinished blobs also contain credentials. New anchor: only trusted application storage owns them; browser-visible status must exclude the phone/hash/key/password. OTP/password input must not be persisted as flow context.
- Compatibility: ordinary readers, worker and AccountPool intentionally never log in. New anchor: adding an explicit conversation must not relax those callers or attribute unfinished-login faults to a cached account.
- Resources/phase: SDK composition can run offline now; actual provider delivery and 2FA service acceptance need live evidence. New anchor: sandbox/test-server and production qualification are different, and a successful fake wire is not a live login.
- Strategic: user selected a general library. New anchor: a distributed auth workflow service is an optional broader owner, not a prerequisite merely because web requests are separate.

### Frame-exit completeness — “session” and “success”
Gating applies: both terms carry distinct propositions across the inquiry's state layers.
Existence enumeration: transport auth key; challenge state; authorized identity; saved credential row; application's web session; future scraping client. Success can mean remote RPC acceptance, completed SDK initialization, physical cleanup or durable publication.
Role assessment: the web application and store remain external but load-bearing. Their serialization/exclusive handoff and persistence obligations must be named; excluding a web UI does not eliminate them.
Verdict rigor: the strongest counter says separate HTTP requests require a database coordinator inside tgdata. A caller already owning those requests can store opaque state and serialize its own flow; the library can supply a bounded explicit step without owning a server. That does not establish safety for concurrent copies or an in-flight process crash.
Residual check: future scraping clients consume the finished credential and must independently establish live authorization/budgets. That consumer is covered by the existing session contract, not a new authentication receipt guaranteeing perpetual access.

## SV3 — Multi-perspective
A three-call wrapper is insufficient. The useful boundary is one explicit login conversation, with a retained secret checkpoint and redacted observation, using a known owner for each external action. Final credential publication remains a separate application action.
H1/H2/H3/H7 check: V1/V2/V3 share the same auth facts but differ in owner/durability; none may silently promise more. The question is not “how to make StoredSession do everything.” Supported stages, unsupported challenges and uncertain calls need separate interpretations.

## Phase 3 — Ambiguity collapse

### A1 — “Session” includes everything needed for the next step
Strongest counter: a portable SDK session string already contains login state.
Structural counter-test: sdk-probes credential_is_not_challenge reconstructs the auth key but the fresh client has no phone-code-hash map; StoredSession is a different opaque format too.
Confidence: HIGH.
Resolution: unfinished challenge context and the transport credential are distinct.
Fixed: next-step context explicitly includes the required challenge information.
No longer allowed: pass a StringSession as a #5 store payload or assume restoring it restores the login conversation.
Depends: serialization, code submission and final handoff.
Model change: one credential blob is not a whole workflow.

### A2 — A raised sign-in means authentication failed
Strongest counter: awaiting sign_in is the SDK's documented success boundary.
Structural counter-test: actual SDK receives Authorization, sets authorized/self ID, then GetDifference fails; its coroutine raises while the credential/self rows survive.
Confidence: HIGH.
Resolution: remote authorization is observed separately from SDK setup, disconnect and publication.
Fixed: retain an actual success before later awaits can obscure it.
No longer allowed: automatically resend/re-login just because a later operation raised.
Depends: completion status, cancellation recovery and output retention.
Model change: success is a fact with an owner, not the public task's final status.

### A3 — “Restorable” means safe retry of any interrupted call
Strongest counter: web-worker handoff is useless unless every interrupted request can be transparently replayed.
Structural counter-test: a stored previous step cannot reveal whether a subsequent SendCode reached Telegram; neither #5's load/save nor caller-owned snapshots are a durable admission/reconciliation protocol. Repeating the SDK helper demonstrably resends.
Confidence: HIGH for the distinction; LOW for first-delivery preference.
Resolution: prefer V2's restoration of retained completed-step state, with explicit uncertainty and caller ownership, rather than claim exactly-once recovery. The optional user preference was asked; absent a reply this was stated as a working default, not a user-confirmed requirement.
Fixed: documented scope distinguishes between-step restore from an interrupted external action.
No longer allowed: infer rollback from timeout/process loss, or hide another code request inside “retry.”
Depends: caller guidance and admission/status semantics.
Model change: portable data and operational authority are different. V1 remains technically viable if requested; V3 must justify a stronger guarantee and its coordinator.

### A4 — Zero SDK retries means the session cannot change on error
Strongest counter: with retries=0 the caller only observes one failed request.
Structural counter-test: actual _call invokes native _switch_dc/connect, changes DC and auth key with the proxy retained, then raises PhoneMigrateError; the probe observed one SendCode request.
Confidence: HIGH.
Resolution: preserve the actual resulting credential/DC even on exceptions, and explicitly bound any handling of a proven redirect.
Fixed: migration and service re-execution are distinct facts.
No longer allowed: restore stale pre-call key bytes over the SDK's new state, or assume any migration is an unknown success.
Depends: transient state, proxy continuity and retry contract.
Model change: a failed method can still have changed its owned connection state.

### A5 — Waiting for the caller Task proves the library is done
Strongest counter: the existing request task is the simplest completion handle.
Structural counter-test: the caller may continue application work after an auth step. Native disconnect can itself outlive a cancelled waiter; actual _disconnect_owned already retains that work. The completed pool review also distinguishes owned completion from an application task.
Confidence: HIGH.
Resolution: own the auth invocation and its temporary client; complete/retain that work before releasing its local ownership. Preserve true caller cancellation without losing known facts.
Fixed: transport/cleanup ownership is narrower than application lifetime.
No longer allowed: detached SDK work, direct propagation of component-owned CancelledError as a caller stop, or a task-wide shutdown join.
Depends: per-step execution and local overlap/cleanup policy.
Model change: lifetime and returned data need distinct, explicit owners. These are a broader pattern across connect/RPC/migration/cleanup, not only one prior pool counterexample.

### A6 — Session save is the final success receipt
Strongest counter: using the existing save hook directly gives automatic storage integration.
Structural counter-test: sdk-probes save_is_not_publication_receipt observes no exception and no stored value after a real failing backend; dump still supplies the credential. The protocol also has no atomic distributed compare/write.
Confidence: HIGH.
Resolution: distinguish a usable finished #5-compatible credential from the application successfully saving it. Do not change #5's existing save semantics to retrofit another consumer.
Fixed: explicit credential handoff and persistence responsibility.
No longer allowed: claim durable storage from the silent SDK save hook or overwrite another active account credential as incidental cleanup.
Depends: result/API/docs and any persistence convenience later selected.
Model change: library login completion need not acquire the application's credential-record ownership.

### A7 — Every auth response fits code or password
Strongest counter: the requested three steps imply every server response can be forced into them.
Structural counter-test: installed1.45 has SentCodeSuccess, SentCodePaymentRequired and AuthorizationSignUpRequired; official auth docs also describe other challenge paths. There is no code/password input that makes signup consent or a paid/unsupported flow disappear.
Confidence: HIGH.
Resolution: support the selected existing-account code/password path, and represent other required interaction explicitly without taking it.
Fixed: no signup, payment, password recovery/reset, QR or background resend as accidental fallback.
No longer allowed: call all unknown constructors “wrong code” or create an account automatically.
Depends: result classification and UI-facing status.
Model change: supported workflow steps are bounded; explicit unsupported interaction is a valid result.

### A8 — “Through proxy” proves the exit IP and the account owner
Strongest counter: using one configuration and cached identity is sufficient proof.
Structural counter-test: configuration sets the route but does not measure its exit IP (#3 remains separate); current ownership code distinguishes actual server identity from cached/session labels.
Confidence: HIGH.
Resolution: retain configured route/device continuity and bind completion to actual authorization/verified self data. Do not report an unmeasured exit IP or a pre-login cached account as verified.
Fixed: account identity is established by the login outcome; proxy status describes configured routing.
No longer allowed: reuse an old named session implicitly as the new conversation or relabel its cached account.
Depends: factory integration, restored-state binding and diagnostics.
Model change: settings, observations and authenticated ownership are separate evidence.

## SV4 — Clarified
The login conversation must carry challenge and credential state, record remote acceptance before secondary work, and expose honest next actions. Portability does not buy retry authority; final-store ownership stays explicit. Typed unsupported results protect the three-step boundary.
H4/H5 checks: each load-bearing term above has a counter-test; the source examples expose a general separation of external action, observation and persistence rather than warranting a universal auth supervisor.

## Phase 4 — Degrees of freedom
Fixed: deliberate calls; no console; no old-credential mutation during preparation; existing proxy/device factory; actual1.45 auth types/SRP; no automatic broad retries; neutral unfinished-account health; owned cleanup; distinct remote/persisted completion.
Eliminated: naive wrappers around start/sign_in; using credential-only serialization as challenge state; SDK save as a commit receipt; background UI/coordinator/network-account discovery.
Viable: V2 application-owned checkpoint and bounded local conversation; V1 reduced portability if requested; V3 only with an explicit requirement for a durable coordinator. Shape/names remain for decomposition/innovation; no production step is designed here.

## SV5 — Constrained
A library conversation mediates explicit inputs using private credentials. The application serializes one active conversation and decides when its outputs are durably stored. A restored checkpoint can continue or inspect authorization, but unknown external effects remain visible. Source and ordinary scraping consumers keep their present contracts.

## Phase 5 / SV6 — Stabilized model
Treat login as a small owned conversation, not as interactive client startup stretched across requests. Retain the transport key/DC plus challenge facts privately; expose only safe status. Observe actual authorization independently of cleanup and final storage. The caller owns persistence, exclusive use of checkpoints and the next deliberate input. The first delivery can target restorable completed steps without importing a distributed workflow service.
Compared with SV1, the main change is the success/ownership boundary, not more SDK calls. H6: evidence required distinct facts, not an expanding list of exceptions to a “raised means failed” rule; no accommodation loop was needed. H8: actual SDK/serializer probes supply an external check on the inherited ownership language.
Remaining: candidate API and interrupted-step dispositions need critique and full actual-component prebuild. Live server acceptance remains unqualified by these five probes. The optional persistence preference is not misreported as an answered question.

## Telemetry and evidence
Six sense versions; nine lateral perspectives plus frame-exit enumeration/role/counter/residual; eight collapse pairs (seven HIGH and one mixed preference); no ambiguity silently dropped. Perspective additions produced challenge-state, post-auth outcome, publication and handoff distinctions. Later strategic/compatibility checks constrained those rather than adding new structures.
Failure-mode check: status quo challenged; no early stabilization before probes; multiple anchors; uncomfortable storage/SDK/restart perspectives; counters tested; no claim of cross-cycle convergence. Structural manual check: SV1–SV6, anchor types, perspectives, eight complete collapse entries, reduced freedom, model and telemetry present. Checker absent. Next: Decomposition.
