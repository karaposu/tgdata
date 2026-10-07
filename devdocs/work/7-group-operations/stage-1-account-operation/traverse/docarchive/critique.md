# Critique: Stage 1 mechanisms

## User Input

_branch.md, sensemaking.md and innovation.md: evaluate all ten candidates and their
assembly against the user's two identity cases and reliable close requirement.

## Phase 0 — dimensions and frame prosecution

| Dimension | Weight | Concrete success criterion |
|---|---|---|
| Ownership correctness | critical | B/A/B proceeds as B; A/B refuses before body; later admission never changes owner |
| SDK lifecycle truth | critical | policy precedes connect; actual SDK disconnect completion retained under cancellation |
| Outcome integrity | critical | original error/success survives cleanup failure; caller cancellation remains cancellation |
| Compatibility | critical | current persistent/pool/ordinary ephemeral defaults and quota charging preserved |
| Stage fit / parsimony | high | no new public arbitrary-client API, health registry, routing or database |
| Feasibility / evidence | high | source-backed seams and executable offline composition, not invented SDK behavior |

Weights follow purpose: a wrong account or masked mutation result invalidates the
feature. Names/line counts alone do not. Substance criteria cover exact send/claim
ordering, not just an “owned” label. Broad ownership includes admission, not only
events. No check requires the defect it is meant to detect.

Inherited premises prosecuted independently: (1) fresh self proves the active
client — if false, neither cache nor numeric comparison suffices; actual GetUsers
on the same SDK client is the available authority. (2) one client must be new — if
reuse were safe, C3 wins; mutable SDK policy/lifetime on the persistent client defeats
reuse. (3) completed cleanup matters — if prompt return were sufficient C9 wins;
the recorded real SDK probe contradicts equivalent closure. External anchor:
Telethon disconnect returns `asyncio.shield(self.loop.create_task(self._disconnect_coro()))`.

## Phases 1–3 — landscape and adversarial verdicts

| ID | Prosecution | Defense | Collision/verdict and constructive output |
|---|---|---|---|
| C1 | policy object expands unsupported configurations | reusable and explicit | KILL on stage fit: use a fixed private policy until a second policy consumer exists |
| C2 | options might override session/proxy identity | supplied only by private context; factory retains those settings | SURVIVE: narrow factory kwargs, fixed internal call site; compatibility tests required |
| C3 | one operation changes another's retry behavior and closes its transport | avoids connection setup | KILL on ownership/lifetime: reuse configuration, not the live client |
| C4 | detached/login-capable callers defeat scoped proof | useful extensibility | REFINE/defer: revive on an actual public consumer and specify its obligations first |
| C5 | late verification could complete after scope exit, or child work could inherit the handle | one owner and an existing before-reserve seam | REFINE into C5r: private handle tied to creator task, check active before and after self RPC, read-only identity/client access; no detached work |
| C6 | changes expected owner to whichever account replies | always uses fresh data | KILL: preserve the expectation; fresh data validates it instead of replacing it |
| C7 | outer cancellation cancels the awaitable; repeated cancellation can detach teardown | retained shielded completion survives both in actual SDK probe | SURVIVE with inner task retaining disconnect and recording its own failures; no timeout promise |
| C8 | diagnostic logger can throw; disconnect's own cancel can masquerade as caller cancel | work outcome remains meaningful for future joins | SURVIVE in its assembled form: cleanup records type-only status; outer cancellation captured separately; best-effort logging |
| C9 | caller returns with transport still open, as probe observed | fastest stop response | KILL on lifecycle truth: defer cancellation rather than detach cleanup |
| C10 | recreates broad revision 3 before an operation exists | could solve eventual health attribution | KILL for Stage 1: consume explicit owner in Stage 2, leave registry design there |

Viable region: fixed policy + private proof/admission + retained close + independent
diagnostic. Dead: cached/dynamic owner, persistent-client mutation, detached close.
Boundary: general public extension API. Unexplored: live network outages/hung SDK
close; neither is treated as evidence of successful shutdown.

## C5r refinement re-test

New prosecution: keeping raw client private cannot prevent a future developer from
retaining it and calling SDK methods after closure. Defense: this is an internal
contract with lexical, creator-task use, not a security wrapper. The handle and
budget admission enforce active/task checks; implementation tests exercise refusal.
Collision: SURVIVE under explicit internal-use contract; document no arbitrary
SDK/login/rebinding/detached-work support. No ContextVar, task registry or per-RPC
identity reauthentication is required. The caller still receives an account fact
instead of guessing from `_self_id`.

## Phase 3.5 — assembly A1

A1 = C2+C5r+C7+C8. Prosecution: an auth error during connect precedes the explicit
proof; or `get_me` hides UnauthorizedError; or active check accidentally blocks
cleanup. Defense: catch auth classes across connect/proof only; verify with direct
self RPC; close admission before cleanup but do not route SDK teardown through the
admission guard. Later verification maps auth failures consistently. No health call
wrap or login method is added. Collision: SURVIVE. Original auth/RPC failures and
the two acceptance cases have explicit paths. Rank A1 first, its four parts second.

## Phase 4 — accumulator, coverage and convergence

Round 1: all ten candidates screened on critical dimensions; four components
survive after C5r refinement. Changed region: lifetime misuse moved from implicit to
explicit refusal. Round 2: assembly/auth composition retested across all six axes;
same viable region. Round 3: cancel-at-close, cleanup-self-cancel and admission
after-close scenarios replayed against that assembly; same viable region, no new
mechanism proposed. Dimensions/weights unchanged. Mechanism-independence: validated
by actual SDK source and disconnect probe, not this artifact's own assertions.

Coverage: 10/10 candidates plus C5r/A1, 6/6 dimensions; external-anchor, user-case,
failure-scenario and specification-gap axes all used. Adversarial strength STRONG;
landscape STABLE across the last two review rounds. Clean A1 survivor; no adjacent
unexamined region likely to improve this stage's bounded contract. No claim of
multiple independent agents or additional complete traverse iterations.

**Signal: TERMINATE — A1, then its constituent C2/C5r/C7/C8.**
**Telemetry: PROCEED.** No rubber-stamp, irrelevant nit, silent weight drift or
external-grounding quarantine. Public arbitrary operations remain deferred; health
remains a separate stage, not an unexamined “fixed” claim.
