---
model: gpt-6-astra
effort: max
---
# Fresh dynamic critic prompt — #8 revision 1
Review devdocs/work/8-stepwise-login/plan.md against desc.md, traverse evidence and current code. Read the actual SDK and repository interfaces; challenge the design's premises as well as its implementation details.

Check deliberate code delivery, challenge/key/DC continuity, fresh identity, native connection setup, cancellation and physical cleanup, configuration binding, secret-free diagnostics, explicit session publication, and compatibility with existing readers. Distinguish local SDK evidence from live Telegram acceptance.

Create critic.md in the same directory, with model/effort frontmatter as its first content, a document verdict immediately after, falsifier, high-level summary and Premise Inventory before risks, ranked by waste-if-false. For each premise name first dependent step, scheduled test, cheapest earlier test/cost and coverage. Behavioral tests supplying rather than observing the claimed behavior are non-covering. Inspect plan hedges as well as implicit vendor premises.

Use exactly one verdict: IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD; DO NOT IMPLEMENT — MEANING GAP (or its WRONG LAYER variant). Verdict concerns shape/order, not risk count. Falsifier: cheapest observation that would make the plan invalid. Affordable now: yes/no with time, money/access. An affordable untested falsifier requires REORDER. Specify Experiment, Cost, Must precede, Disqualifying result and Passing result. Full combined candidate, not a selection of old probes, must pass before production. Live service behavior cannot be qualified by controlled wire replies.

Map each cited prior failure to its established mechanism and planned remedy (Restart Check). Missing mechanisms/remedies are findings; mostly wrong layer means DO NOT IMPLEMENT. Check inherited #7/#17 ownership lessons at their actual completion boundaries, including native SDK work. Carry execution blockers unchanged without mitigation tiers. Discuss existing behavior, API/schema effects, privacy, latency/memory and architectural scope; insufficient detail on a delicate section is Medium.

Each risk uses sections, not a table: Risk paragraph1 plain/self-contained consequences with introduced concepts, paragraph2 precise paths/symbols/triggers; Severity Low/Medium/High; Category; Impact; NoobEng; Affected areas. Medium/High require Quick, Robust and Long-term proposals, robust's 'why this is robust:' and long-term's 'why this is long term effective:'. EACH starts with unticked selected/elegant/last_resort and Note containing empty Why chosen / For future fields. Phase3 only selects/annotates; it never rewrites the risks/proposals. Select by reach/extent: name genuine other instances before generalizing, compare one mechanism without per-case branches, and keep large class fixes separate. A small complete instance fix beats a speculative framework.

DO NOT IMPLEMENT follows critic-d2.5 (record gap, deprecate plan, record blocker, stop). REORDER specifies experiment but leaves plan sequencing/folding to task-impl. Report actual observations and explicit limits, no manufactured passing evidence.
