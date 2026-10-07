# Innovation: small owned operations

## User Input / seed

_branch.md and P1–P3 from decomposition: implement a trusted operation without
reintroducing the rejected design's broad machinery. Seed types: dissatisfaction,
failure, constraint. The user's valuation is a foundation that stays small as #7
grows. Inherited mode: Standard default. Alternative: Contrarian-rethink would
primarily test whether any new abstraction is needed. Keep Standard with explicit
contrarian candidates at each piece; all seven mechanisms fire.

## Generate — before evaluation

All three pieces are meta-decisions (their contract criteria govern later code).
Each receives generic, focused and contrarian variants. No intervention vocabulary
shape is load-bearing here (property v does not fire).

| ID | Piece/type | Mechanism and axis | Candidate |
|---|---|---|---|
| C1 | P1 generic | combination: configuration | Factory accepts a full reusable policy object for any kind of temporary operation. |
| C2 | P1 focused | constraint ADD: scope | Add optional constructor options to the existing factory; private owned context supplies fixed no-wait/no-retry policy. |
| C3 | P1 contrarian | inversion: construction | Reverse “new clients are required”: use the persistent client and merely verify it at operation entry. |
| C4 | P2 generic | extrapolation: surface | A public operation SDK lets future callers supply arbitrary callbacks/clients and verified-owner tokens. |
| C5 | P2 focused | absence: contract | Add the missing internal handle carrying account_id/client and a fresh verify method; budget admission consumes it. |
| C6 | P2 contrarian | inversion + constraint REMOVE: identity | Remove explicit owner binding; trust each fresh response as a new owner whenever it changes. |
| C7 | P3 generic | domain transfer: lifetime | Treat cleanup like structured resource disposal: retain one completion and defer caller cancellation until it settles. |
| C8 | P3 focused | lens shift: success criterion | Judge work outcome and cleanup separately; log cleanup type while preserving successful work/primary error. |
| C9 | P3 contrarian | inversion: outcome | Reverse “finish close first”: fire-and-forget close or return at a short timeout, treating cancellation responsiveness as success. |
| C10 | P2 redesign | absence + combination: authority | Move account ownership into every global health/request record before building the context. |

Absence patch-level: before-reservation owner comparison is missing. Redesign-level:
an explicit owner is missing from the old feature's contract; already-present in a
different form: read-budget billing gets a fresh identity but does not compare an
expected one. C5 combines those facts without duplicating budget persistence.
Constraint REMOVE is C6; ADD is C2. Inversion depth: persistent-client reuse would
make the system share mutable policy (C3); zero expected owners permits the system
to change billing owner (C6); prompt shutdown without owned completion makes the
system return before resource disposal (C9). Existence and identity axes were both
checked, not just a component-level opposite.

## Inherited frame audit

Central belief “one owned client per operation” challenged by C3. Proof contract
challenged by C6; completed close criterion challenged by C9; internal surface
challenged by C4; separating health challenged by C10. All piece commitments have
opposite candidates before testing. Audit does not fire; no override needed.

## Five-test cycle

N = novelty within this repository's accepted dev, S = strongest scrutiny,
F = fertility, A = actionability, M = independent mechanism grounding. Each row
enters all five tests; a failure is retained as evidence, not silently omitted.

| ID | N | S | F | A | M | Disposition |
|---|---|---|---|---|---|---|
| C1 | new policy system | too many unsupported dimensions for one fixed policy | wide | buildable but disproportionate | only extrapolating future needs | KILL: new abstraction has no second consumer |
| C2 | constructor seam new | SDK connect consumes settings immediately; defaults stay intact | later temporary ops reuse | small factory change | source lifecycle + constraint narrowing | ACTIONABLE |
| C3 | new reuse condition | mutating retry policy affects simultaneous ordinary work; no exclusive close ownership | limited | cannot satisfy close contract | conflicts with user lifetime and SDK state | KILL |
| C4 | new external API | arbitrary detached/login work needs a much wider contract | high | disproportionate this stage | future demand only | DEFER: revive on actual external operation consumer request |
| C5 | new explicit agreement | raw client still isn't a sandbox; keep private, active scope and immutable owner | stages 2–5 | existing budget provider seam | fresh-self source + admission invariant | ACTIONABLE with stated private-use bounds |
| C6 | no meaningful new guarantee | expected A/actual B acceptance case fails | counterproductive | easy but wrong | contradicted by explicit user requirement | KILL |
| C7 | completed-close composition new | a hanging close can hang caller; state this limitation | any later one-shot operation | real SDK probe supports it | structured lifetime + shield probe | ACTIONABLE |
| C8 | explicit precedence new | logger failure or disconnect self-cancel must not replace outcome | safe future mutation APIs | small helper/diagnostic | actual SDK close + side-effect outcome reasoning | ACTIONABLE |
| C9 | prompt cancellation criterion new | detached cleanup violates completed close attempt, probe reproduces | poor | simple but wrong contract | only latency motive | KILL |
| C10 | broader ownership redesign | unnecessary before wrong-account request refusal; crosses Stage 2 | broad | too large now | repeats old discarded frame | KILL for Stage 1; health remains later work |

Artifact grounding: current dev factory has no option seam; budget provider already
does fresh lookup; _AnswerEvidence/HealthMonitor already exist and are not absent
features. Telethon1.45 constructor and disconnect probe supply external evidence.
Shared-input check: convergence is not counted from P1–P3 alone; the SDK lifecycle,
budget send ordering and future side-effect retry hazard are independent grounds.

## Assembly and re-test

C2+C5+C7+C8 form one small lexical context: configure, prove, yield a handle,
close admission, finish close. The handle's verify method is the shared identity
provider for later admission, eliminating a second competing proof rule. C8 re-tests
C7: use an inner close task that records cleanup exceptions (including its own
CancelledError) as cleanup status, so the outer shield loop can distinguish caller
cancellation. Caller cancellation is re-raised after settlement; logging failures
are swallowed at this diagnostic boundary.

Axis coverage: constructor policy (C1–3), public/internal surface and ownership
(C4–6/C10), shutdown timing and outcome precedence (C7–9). Every committed row has
mechanism trace. C4 is the articulation's public variant, deferred with concrete
trigger; the dispatch-supervisor variant is killed by its recursion/traffic cost
and lack of an arbitrary-SDK contract in this stage.

## Telemetry

4/4 generators, 3/3 framers; 10 candidates tested, four actionable plus one
deferred. P1: combination, constraint, inversion; P2: absence, extrapolation,
inversion, combination; P3: domain transfer, lens shift, inversion. All three
meta-decision pieces have generic/focused/contrarian sets and satisfied inversion.
Convergence: four mechanisms supported by separate source/probe grounds. No
untested survivor, early-frame lock or omitted uncomfortable candidate.
**Overall: PROCEED.**
