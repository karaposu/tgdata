# Dynamic critic — fixed-window plan revision 1

Review fixed-window/plan.md against its desc/triage and the actual facade, batch
reader/value/files, sync engine/store, budget adapter and tests. Run in this warmed
session. Read full relevant files; behavior findings require a line or runnable
probe. Evaluate the smallest correct extension to the existing collection contract.

Compute a Premise Inventory first, ranked by waste if false: premise, first
dependent step, waste, scheduled test, cheapest earlier test/cost and actual
coverage. Distinguish real SDK/SQLite behavior from synthetic server replies.
An affordable unrun premise test scheduled after its dependent build requires
REORDER. The real SDK date/ID/budget probe already ran; examine what it does and
what it does not prove. Live Telegram behavior remains explicitly untested.

Attack these boundaries:
- Do inclusive start/exclusive end survive SDK-exclusive second-resolution offsets,
  fractional timestamps, timezone conversion, ties, gaps and ID resumption?
- Can excluded lower-bound records consume a full requested page and fabricate
  end/empty? Can any out-of-window message trigger media preparation or advance ack?
- Does budget exhaustion retain a valid in-window prefix while still raising?
- Does repeated relative enrollment read the clock or move saved dates? Are
  explicit/relative input identity, absent state, conflicts and uncertain commits clear?
- Can a v1 daily row or pending batch change merely by loading new code? Can corrupt
  v2 windows or pending dates silently enter replay? Are custom stores still opaque?
- Does separating collections preserve daily progress? Has this slice quietly
  introduced a scheduler, job registry, completion promise or #7 health redesign?
- Are status, public docs, SDK limits, local-error provenance and old API behavior
  specified enough to test? Is any complex step under-specified (Medium if so)?

Create critic.md here, with model/effort frontmatter, a verdict immediately below,
then falsifier/affordability lines, high-level summary, inventory and findings.
Choose IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN, REORDER — TEST BEFORE
BUILD, or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant if applicable).
A falsifier is the cheapest observation that would invalidate the shape. For REORDER
specify the real-component experiment, cost, first dependent step, pass and fail.
For DO NOT IMPLEMENT follow the skill's plan-deprecation/desc-blocker procedure.

Include Restart and Inherited Lessons checks: retained window versus moving clock,
filtered-page versus exhausted range, local failures versus Telegram health, and
permanent archive versus pending observation. Do not claim this fixes ScrapeOps'
whole-walk completion, which is outside the chosen slice.

For each real finding, write two Risk paragraphs (plain consequence, then exact
symbols/trigger), Severity, Category, Impact, NoobEng and Affected areas. High/Medium
require quick/robust/long-term proposals, robust/long-term rationale, unticked
selected/elegant/last_resort boxes and initially empty Why chosen/For future notes.
Do not pad findings. Phase 3 only selects proposals and fills notes, using actual
class instances, reach/extent, size and prerequisite gates. Do not rewrite risks.
Report inherited execution blockers separately, without risk severity.
