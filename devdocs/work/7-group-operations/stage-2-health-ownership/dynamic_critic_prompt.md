# Dynamic critic prompt — #7 Stage 2

Read desc.md, plan.md revision 1, triage.md, traverse/finding.md and its five
executed baseline probes. Read the real health ledger/call/source hooks, facade,
Stage 1 lifetime and budget composition, test16/test32, and installed Telethon
1.45.0 code. Review in this session, sequentially, without delegation.

Question the boundary, not only implementation details:
- Is numeric ownership fixed in both event and retained snapshot? Are legacy
  observations kept separate rather than promoted from an uncertain cache?
- Can pre-proof or cleanup failures escape into an enclosing legacy call?
- Are source-time failures visible when caught, nested through budget identity
  checks, or returned in a partially failed SDK request batch?
- Can a caught identity/authentication failure leave enough old success evidence
  to recover state despite Stage 1 permanently invalidating the handle?
- Can another client, inherited child task or inactive context change state?
- Can older work, self verification, metadata, another request type, or another
  operation method falsely clear a newer or unrelated condition?
- Do sync/async callbacks begin only after disconnect settles, contain cancellation,
  retrieve task failures, suppress recursion, and close without self-await?
- Does the public query have clear unknown/no-I/O/copy semantics? Does close retain
  its cooperative scope? Are original errors and Stage 1 policies preserved?
- Reject unnecessary registries, global migration, routing or a permission engine.
  Identify concrete compatibility, performance, security, API, import and schema
  risks; flag underspecified delicate steps as Medium. Do not pad speculative lows.

Create critic.md beside the plan. Open with model/effort frontmatter from session
context (unknown if not derivable), then verdict, falsifier and high-level summary.
Choose IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN, REORDER — TEST BEFORE
BUILD, or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER if cited failures are unaddressed).
Verdict is about shape/sequence, not severity count. An affordable unexecuted
falsifier means REORDER. Name real composition experiment, cost, first dependent
step, exact passing and disqualifying results. No fake helper can supply the premise.

Compute Premise Inventory before risks, ranked by waste-if-false: premise, first
dependent step, waste, scheduled test, cheapest earlier test/cost and coverage.
Include vendor/async behavior even if not hedged. Distinguish real SDK/asyncio
coverage from synthetic network replies; no claim to prove Telegram server policy.
Carry known execution blockers unchanged; an open planning blocker stops the plan.
Include Restart Check rows (observed failure / established mechanism / addressing
design element) and Inherited Lessons rows (lesson / step ordering that satisfies it).

Write risks as sections, not a risk table. Each has two Risk paragraphs: plain,
self-contained user consequence first; precise symbols, files and conditions
second. Include Severity, Category, Impact, NoobEng and Affected areas.
For every Medium/High give Quick, Robust (why this is robust), and Long-term
(why this is long term effective) proposals. Initially each carries:
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

Phase 3 only selects/annotates existing proposals. Name genuine other instances
before selecting a class-wide fix; one mechanism must fit without special cases.
Compare reach/extent, apply size and delicacy gates; robust wins over speculative
generalization. Quick requires named external pressure. Record deferred alternatives.
DO NOT IMPLEMENT deprecates the plan and records the blocker in desc.md, then stops.
REORDER keeps the plan alive and specifies the experiment; fold only selected
mitigations after it passes. Never critique a later folded plan in this run.

