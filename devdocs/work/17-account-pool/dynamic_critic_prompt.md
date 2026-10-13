---
model: gpt-6-astra
effort: max
subject_plan_revision: 6
---
# Dynamic critic — #17 public read ownership

Read desc.md revision5, step_by_step_impl_plan.md revision6, the public-outcome inquiry
finding/evidence, both rejected PR critiques and the previous failed storage prebuild.
Read actual AccountPool, pool_lifecycle, pool_source, BatchEngine, MessageBatch,
SyncEngine, BackfillEngine, ProgressFacade, ReadBudget, state stores and the pool/worker
fixtures. Judge the new plan as a stranger: an earlier traverse is input, not proof.
Do this in the current session; no delegation. Product a63099e, current dev2ddb852.

Challenge these concepts together:
- Is the owned invocation's completion independent of arbitrary caller continuation,
  without releasing actual source/provider work or native retirement prematurely?
- Can direct, late, repeated, shield/gather and timeout consumers retrieve actual data
  through a capture held before invocation, even when cancellation objects differ?
- Is early data actual fully validated/media-complete source data, including pagination
  and monitor-finalization stalls? Does a borrowed record buffer remain coherent,
  bounded and detached from Task/client/error graphs? Does snapshot cost grow per read
  rather than quadratically per record?
- Are one-shot binding, failed validation, missing/wrong type, same/different-pool
  reuse, prestart cancellation, finality and immutable snapshots defined operationally?
- Does no-prefix failover keep data/account/error provenance consistent for each actual
  attempt? Can an empty later value erase a known prefix or stale metadata survive?
- Can the private engine adapter carry one already-bound writer without rebinding,
  recursive public calls, global context capture or leaking the new calling convention
  into ordinary TgData and the worker?
- Can close finish while public progress publication continues under its caller,
  without a false finalized snapshot? Do replay/ack remain source-free after close?
- Do real before/after account and group CAS, paired store failures, charges, waits,
  exact receipt hashes and recovery remain independent of available data?
- Are provider I/O-only roles, bounded passive health, native retirement quarantine,
  repeated caller stop and original error precedence retained in the complete composition?
- Are changes limited to the actual missing boundary? Name concrete existing instances
  before proposing any shared supervisor, universal result store or wider API rewrite.

Create `critic.md` in the same directory as the plan. First include model/effort
frontmatter derived from current metadata, then one document verdict: IMPLEMENT AS
WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD; or DO NOT
IMPLEMENT — MEANING GAP (WRONG LAYER if established failures are not addressed).
Immediately below, give Falsifier and Affordable now lines. An affordable unexecuted
falsifier requires REORDER; name real-component experiment/cost/first dependent step/
passing and disqualifying observations. If the proposed order already puts it first,
say so and retain that gate rather than inventing a late-test defect.

Put a high-level summary on top, then Premise Inventory before risks. For each premise,
rank waste-if-false and state first dependent step, waste, test location, cheapest
actual earlier test/cost, current coverage and non-covering simulations. Synthetic
wire may stimulate the real SDK but is not live two-account evidence. A fake result,
receipt or cleanup flag cannot close the corresponding behavioural premise.

Include Restart Check (observed failure / established mechanism / addressing design)
and Inherited Lessons mapped to the plan's ordering. Carry E1 as an execution
precondition without severity. If an open planning gap invalidates steps, use critic-d
Phase2.5: deprecate the plan, record the blocker only in desc Known Blockers, and stop.

For each real risk use subsections, not a risk table. Risk is two paragraphs: first
plain/self-contained without symbols/paths, then precise paths/call sequence/trigger.
Include Severity Low/Medium/High, Category, Impact, NoobEng and Affected areas. Medium/
High risks each get Quick, Robust and Long-term mitigation proposals. Robust includes
'Why this is robust'; Long-term includes 'Why this is long term effective'. Under
EACH proposal initially emit:

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

Do not pad findings or call known test limitations new risks. Unsupported detail in a
complex step is Medium when it would change behavior. Separate written contract,
experimental candidate feasibility and production qualification. After saving Phase2,
run Phase3 selection separately: only tick boxes and fill notes, using actual-class,
one-mechanism, reach/extent, size and delicacy gates. Do not alter findings while choosing.
