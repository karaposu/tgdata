---
model: gpt-6-astra
effort: max
---

# Dynamic critic prompt — #18 daily continuation

Subject: plan.md revision1 plus desc.md, traverse/finding.md and actual merged
source at45bab71. This is an implementation-plan review in the same warmed session.
Read the plan and relevant modules in full. Do not substitute the design critique
for this pass. No runtime code is implemented yet.

Ultrathink about the complete ready → prepare → persist pending → deliver →
acknowledge → ready path, including every error, cancellation and crash boundary.
Test the plan's shape, not just whether its future functions sound plausible.

First read declared blockers and compute a Premise Inventory ranked by wasted work
if false: premise; first dependent step; waste; scheduled test; cheapest earlier
test/cost; covering evidence. Real SDK/SQLite behavior must be observed, not supplied
by a fake implementation. The pre-plan probe uses actual components; distinguish
that from validation of the not-yet-written runtime or a deployed destination.
An affordable unrun premise tested after dependent work requires REORDER.

Require a Restart Check for claims inherited from earlier failures: only identify
mechanisms with code/probe evidence. Prior #6/#7 lessons are local-error provenance,
exception precedence, authoritative identity, and actual overlapping tests. Determine
which are relevant to this daily layer; do not import a health redesign by analogy.

Questions derived from this repository:

1. Can first-use/repeated enrollment silently move progress or reinterpret a
   positive/aliased group ID? Does the returned batch's chat_id/start/mode bind to
   the loaded state before publication?
2. Does a pending batch replay byte-for-byte without a Telegram request, including
   after an interrupted prefix or process restart? Is media required and verified
   independently from manifest validity?
3. Does acknowledgment derive its next position from saved bytes, match the exact
   pending ID and atomically clear it? Can a duplicate latest/older/wrong ack clear
   newer work? Can one pending state recur and fool an expected-value comparison?
4. Does each store operation distinguish absent, corrupt, unsupported and unavailable
   state? Could constructor/schema initialization overwrite evidence or recreate a
   missing DB during use? Is CAS really atomic and durable in the real backend?
5. What if a custom async store commits and then raises or is cancelled? Does any
   code infer rollback or acknowledge a result it cannot establish?
6. Does a quota-limited prefix become usable without hiding the read failure? If
   saving it fails, are both errors preserved with a truthful durability claim?
7. Can rollback/close/logging failures mask the chosen primary outcome? Could a local
   error raised inside an old RPC handler become a Telegram health verdict?
8. Are replay/status/ack free of _reported contexts and network recovery claims?
   Is the real reader still subject to proxy/session/budget/health behavior?
9. Is the single-reader boundary explicit and adequate without distributed leases?
   Do overlap regressions actually hold both operations pending?
10. Do signatures, Python3.7 syntax, imports/exports, batch v1 and existing callers
    remain compatible? Does any planned implementation step omit details required
    by its failure-sensitive boundary?
11. Does the receiver example commit effects and batch/message deduplication before
    acknowledgment, bound daily work and avoid claiming a deployed guarantee?
12. Does the implementation stay within daily continuation, leaving backfill tracked
    and excluding edits/deletions permanently, with #7/duncan untouched?

Create critic.md in this directory with model/effort frontmatter, then one exact
verdict: IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST
BEFORE BUILD; DO NOT IMPLEMENT — MEANING GAP (or WRONG LAYER). Include a falsifier
and affordable-now line, high-level summary, premise inventory, restart/inherited
lessons check and coverage. Cite actual code or probe evidence for findings.

Each finding has two Risk paragraphs (plain consequence, then precise paths and
triggers), Severity Low/Medium/High, Category, Impact, NoobEng and affected areas.
For every Medium/High, supply Quick/Robust/Long-term proposals, explaining why the
latter two close their respective scope. Initially leave all selected/elegant/
last_resort boxes unchecked and Why chosen/For future notes empty. Do not use a
table to compress risk paragraphs. Phase3 only selects/annotates those existing
proposals, using reach/extent and the real-class/size gates; it cannot rewrite risk
severity or content. No quick fix is selected without named external pressure.

If a meaning gap kills the plan, deprecate it and record the blocker as the skill
requires. Otherwise run any affordable falsifying observations before claiming
acceptance. Do not manufacture findings to make the review look adversarial.
