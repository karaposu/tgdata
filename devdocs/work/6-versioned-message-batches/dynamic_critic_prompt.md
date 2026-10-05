---
model: unknown
effort: unknown
---

# Dynamic plan critic — #6 revision 3

Critique `step_by_step_impl_plan.md` revision 3 (`e391cd6`) against current
code, `desc.md` and `history/round-1/pr-critic.md` R1/R2. Run in the warmed
session without subagents. This is the second-cycle plan critique, not a
rewrite of the rejected PR report. Target Telethon 1.45.0 only.

Read declared blockers first. Independently trace file ownership, exception
provenance and public continuation through the SDK, BatchEngine, file helpers,
health classification, budget guard, saved manifests and tests. Does the revised
plan address the two demonstrated mechanisms, rather than just their first
symptoms? Challenge the following specifically:

- The local-I/O guard must include SDK-invoked stream write/flush and native
  path/open/read/fsync/link/close/unlink operations. It must preserve original
  objects/types and must not classify a whole SDK await as local merely because
  a transport exception subclasses OSError. Real explicit RPC causes must work.
- Resource ownership must begin on open, avoid descriptor leaks during handoff,
  close before publishing output, preserve primary exceptions and cancellation,
  attempt remaining cleanup after a failure, and raise the first cleanup-only
  error. Existing-file verification has its own read/close double-failure case.
- Logging secondary failure must not mask the chosen result or expose error
  text/paths. Permission-denied deletion cannot be promised away; check the docs
  distinguish a private leftover from a partially published final object.
- Retaining v1/reader/API semantics must be substantive: exact schema/hash,
  safe prefixes, media selection, budgeted refresh, legacy DataFrame contracts,
  package imports and sync-I/O costs. #10 is a future consumer, not permission
  for a universal storage framework or a receiver.

Run affordable vendor/stdlib protocol probes before endorsing a dependency.
Use actual SDK/file operations; identify supplied transport/fault behavior and
never treat it as live-server evidence. Check the existing seven re-plan seam
observations and extend any non-covering local premise. Tests of newly proposed
publisher code occur after construction; do not confuse that with postponing
an affordable test of an existing prerequisite.

Create `critic.md` beside the plan, high-level summary near the top. Begin with
frontmatter `model`/`effort` from actual context, otherwise `unknown`; then one
critic-d verdict (IMPLEMENT AS WRITTEN / IMPLEMENT AFTER FOLDING THESE IN /
REORDER — TEST BEFORE BUILD / DO NOT IMPLEMENT — MEANING GAP or WRONG LAYER)
and the cheapest falsifier with affordability. An affordable unrun decisive
prerequisite check requires REORDER; specify/run it before dependent work.

Compute Premise Inventory first: premise, first dependent step, waste-if-false,
scheduled test, cheapest earlier observation/cost, actual coverage. Rank by
waste, not disclosure. Include a Restart Check for both prior failures and the
Inherited Lessons check. Name declared boundaries separately from findings.

Every real risk must have Severity, Category, Impact, NoobEng, Affected areas,
and two Risk paragraphs: a self-contained plain consequence followed by exact
files/symbols/triggers. No risk tables or padding. Medium/High proposals need
Quick/Robust/Long-term options, why the latter two work, and initially empty
selected/elegant/last_resort boxes plus Why chosen/For future notes. Execute
Phase 3 separately, ticking/annotating without revising severities or proposals;
require real other instances before a class-wide solution, compare reach/extent,
and avoid expanding the task for speculative future generality. Follow the
skill's stop/deprecation procedure only for an actual meaning-gap/wrong-layer
verdict. Do not modify runtime code during this critique.
