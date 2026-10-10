# Dynamic critic — #7 Stage 4 allowance

Review the committed revision1 `plan.md` with `desc.md`, triage, inquiry finding,
actual contract-probe evidence, current ReadBudget/SQLiteSyncStore, public exports,
health classifier, packaging and offline test conventions. Read relevant code;
do not inherit a verdict from the old broad #7 implementation. Execute in this
session, no delegated agent. Stage4 only; Stage5 joins/guards remain outside.

First read declared blockers. Confirm an OPEN planning blocker without re-rating
it; carry execution preconditions unchanged. Compute a Premise Inventory before
risks, ranked by wasted work if false. For each: premise, first dependent step,
waste, scheduled test, cheapest earlier real-component test/cost, and present
coverage. Label stand-ins that supply the desired behavior non-covering. Prior
SQLite probes qualify only the composition they actually exercised. In particular,
does simultaneous use with the real read ledger preserve both accounting domains?

Question the approach as well as details. Does the local unit mean admitted
attempts consistently through status, reconfiguration, cancellation and a lost
return? Does a reusable grant/refund requirement actually exist? Is one dedicated
ledger smaller and safer than extending read reservations? Confirm the Stage5
identity/send seam is described without falsely implementing a guard now.

Trace explicit provision versus existing-state reopen, absent/partial schema,
types/PK/FK/index metadata, orphan owners, and record validation before time
advance/pruning. Distinguish detectable corruption from arbitrary valid-looking
external edits. Trace rolling boundaries, lowered-cap next availability, per-account
clock persistence and denied-claim commit ordering. Check integer/clock bounds,
UTC formatting, immutable snapshots, path normalization and sanitized errors.

Trace the transaction under normal return, insert/commit failure, commit followed
by error, rollback/close failure, cancellation and logging failure. No grant may
escape after uncertainty; original failures must survive secondary cleanup. Check
all advertised Python versions, not just syntax parsing/current interpreter.
Check local-error context does not create a Telegram health finding. Evaluate
storage/CPU/lock costs concretely without inventing a generic quota project.

Require actual SQLite, forced process overlaps and exits, wrappers that delegate
real work before injected failure, export/no-.git tests and all supported offline
regressions. Distinguish process exits from power-loss evidence. Flag insufficient
detail as Medium when a complex path cannot be implemented without inventing a
contract. Do not pad findings with hypothetical adversarial file editing.

Create `critic.md` here, frontmatter model/effort from actual session (unknown if
unavailable), then verdict: IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN,
REORDER — TEST BEFORE BUILD, or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant
when failures are not addressed). Include a falsifier and whether its cheapest
test is affordable now. An affordable untested premise whose build precedes its
test requires REORDER: name experiment, cost, first dependent step, disqualifying
and passing results. Wrong premises require deprecation/blocker procedure, not
mitigation tiers. High-level summary follows the verdict, then Premise Inventory.

Require Restart Check rows for historical partial-table reset, invalid timestamps,
and broad #7 owner/source failures: established mechanism and design response.
Require Inherited Lessons rows with the actual step ordering that honors each.

Each real risk gets two paragraphs: first explain the user-visible problem in
plain self-contained terms without symbols/paths; second give exact symbols,
paths, triggers and flow. Then Severity Low/Medium/High, Category, Impact,
NoobEng (engineer unfamiliar with this system) and Affected areas. Use subsections,
not a risk table. Medium/High each get Quick, Robust and Long-term mitigations;
include 'why this is robust' / 'why this is long term effective'. Under EACH put:

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

Phase2 writes unticked proposals. Phase3 only selects/annotates: enumerate real
other instances before calling something a class; prove one mechanism fits before
generalizing; compare reach/extent; use the size gate and separate future work
when broader changes do not belong here. Quick only under explicit pressure,
never by convenience. No severity/risk reshaping in selection. Do not edit the
plan during critique. The orchestrator folds selected mitigations after any
required experiment passes, then implements without another plan critique.
