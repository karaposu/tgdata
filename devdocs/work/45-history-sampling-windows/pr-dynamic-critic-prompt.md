---
model: gpt-6-astra
effort: xhigh
---
# Fresh PR critic — #45 / PR #49

Subject: the published product diff from dev77f2f53 to PR head559638a, together
with revision2 step_by_step_impl_plan.md, against current dev. Read desc.md,
triage.md, prior plan critic, prebuild evidence and actual surrounding code.
This is a fresh soundness review in the same warmed session, not a subagent.
Preserve the plan critic and its prompt; write findings to pr-critic.md.

Ultrathink. Challenge the contract, not only implementation fidelity. A passing
test suite and merge check are evidence, not a verdict. Read relevant files in
full and run fresh work-folder probes through real Telethon1.45 dispatch/TL,
StoredSession, SQLite admission and cleanup where behavior matters. Synthetic
source packets do not qualify the live Telegram server. Do not change product
code or patch findings during this review.

Compute the Premise Inventory first, ranked by waste if false: premise, first
dependent step, waste, scheduled test, cheapest earlier test/cost and coverage.
Mark tests non-covering when they supply the behavior they claim to establish.
Carry declared execution limits unchanged: live sampling requires qualified
exclusive session/authoritative allowance; native3.7 execution remains untested.
Inspect the prior combined prebuild's placement before product work. If an
affordable still-unrun premise test exists, run/specify it before claiming PASS.

Restart Check: the motivating599/300 newest-prefix bug and source-cap omission of
older days need an established mechanism and a design element addressing each.
Inherited Lessons: distinguish captured input from fresh queries, source work
from selected count, source gaps from omissions, raw members from complete albums,
and retained values from cursor/ack authority. Identify the step/testing order
that actually satisfies each lesson.

Attack these boundaries:
1. Acquisition: day opportunity under scarce calls/slots; empty and busy mixtures,
   partial first/last days, ties, short slices, unknown rows, first-probe policy,
   cap exhaustion, final-request end evidence and exact per-day completeness.
2. Values/replay: public loader and constructor, malformed/rehashed contradictory
   evidence, finite date partition, canonical hashes/types/ordering, count
   consistency, immutable getters, byte policy and native large-content behavior.
3. Selection: an independent quota/rank oracle, sparse redistribution, zero/full
   cases, normalized eligibility, excluded services, known album omissions and
   deterministic output. No implicit progress or topic callback execution.
4. Composition: cached versus authenticated identity, admission failures and
   storage errors, original RPC/local errors, cancellation during source/cleanup,
   health ownership/recovery, heartbeat failure isolation and no fake liveness.
5. Compatibility: compare activity page behavior to the original base validator,
   including exception text and atomicity. Check import/package integration and
   public docs against actual behavior. Assess CPU/memory with concrete bounds,
   not speculative optimization or a new generalized architecture.

Write frontmatter with verified model/effort, then one skill verdict: IMPLEMENT
AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN, REORDER — TEST BEFORE BUILD, or
DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER if supported). Also state the PR
threshold verdict: any High/Medium rejects; only Lows/none can pass. Follow with
a falsifier line and its affordability/result, high-level summary, Premise
Inventory, Restart Check, Inherited Lessons and evidence.

For each real finding use two Risk paragraphs: first plain and self-contained,
then precise with paths/lines/trigger. Include Severity, Category, Impact,
NoobEng and affected areas. Medium/High findings require quick/robust/long-term
mitigation proposals, the robust/long-term justification, and initially empty
selected/elegant/last_resort checkboxes and Why chosen/For future notes.
Do not pad with speculative Lows. A Medium must rest on code or reproduced output.

Commit Phase2 before Phase3. Unless a meaning gap stops the skill, Phase3 only
selects proposals and writes notes using reach/extent, the real-class check,
size gate and delicacy. It does not patch product code or rewrite findings.
Any rejected PR returns to CONTRIBUTING§7.4 revision3 re-planning later.
Record concrete probe commands/output, exact reviewed head/base, what remains
unqualified, and the in-session execution. Post the committed critique to PR49.
