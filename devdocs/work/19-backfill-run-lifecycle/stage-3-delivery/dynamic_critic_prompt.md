---
model: gpt-6-astra
effort: max
---
# Dynamic critic prompt — Stage 3 delivery

Critique `step_by_step_impl_plan.md` against its sibling description and the actual
8023adf runtime, Stage 1 contract, Stage 2 codec and Gate A receipts. Compute the
premise inventory before judging implementation details. No open planning/execution
blocker is declared; independently confirm that judgment. Gate B is after Stage 4.

Read complete relevant implementations: backfill values/codec/engine, opaque SQLite
CAS, MessageBatch, BatchEngine, batch_files, existing SyncEngine, health cause traversal,
budget errors and actual SDK/test seams. Do not confuse a scripted transport or seeded
future state with live evidence or implemented lifecycle transitions.

Audit these boundaries adversarially:

1. Complete run/cursor/control authority before admission; confirmed exact-text CAS
   before a reader call; overlap/unknown attempts; no transaction held across I/O.
2. Ownership and exact v1 payload/hash across publication/restart/replay; no callback,
   credential, budget or clock on replay; required file integrity and relocation.
3. Ordinary failures, malformed/empty/interrupted prefixes, source cancellation,
   post-commit failure and missing/invalid/regressed clocks. Preserve the real error,
   but never let local failure/cancellation inherit a Telegram verdict through a cause.
4. Same-attempt settlement after compatible controls; immutable intent comparison,
   bounded false-CAS retries without source refetch, counter headroom and stale responses.
5. Full DeliveryRef matching, equal hashes across runs/collections/destinations,
   latest/prior acknowledgment recognition, newer pending data and acknowledgment after
   media removal. Receipt acceptance is a caller assertion, not a file-presence check.
6. Stage boundaries: minimal end/terminal closure required by the existing codec is
   not a Stage 4 sign-off; stored pacing is not Stage 5 timing eligibility. The positive-
   pause restriction must fail closed while local delivery remains possible. Controls,
   recovery and public facade are not accidentally introduced.
7. Compatibility, imports, schema and resource cost: preserve old state/APIs and
   MessageBatch v1, isolate local health, bound retries and avoid retaining payload
   history or creating a general scheduler/transaction/receipt framework.

Create `critic.md` in this folder. Start with actual `model`/`effort` frontmatter,
then exactly one verdict: IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN;
REORDER — TEST BEFORE BUILD; or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER if relevant).
Place a falsifier directly beneath verdicts 1–3: the cheapest observation that would
invalidate the plan and `Affordable now: yes | no` with cost/access. Affordable unrun
falsification before a dependent build requires REORDER, not a content-only pass.

After a high-level summary, include a Premise Inventory ranked by wasted work: premise,
first dependent step, waste if false, scheduled test, cheapest earlier test/cost and
current coverage. Flag non-covering fake/state-supplied behavior explicitly. A new
implementation property is not an already observed external premise; name what can
only be tested after that implementation exists. Reading closes documentary claims,
not unobserved vendor behavior. Disclosed-but-tested-late premises remain unclosed.

Include a Restart Check mapping each cited prior failure to its established mechanism
and the step addressing it; distinguish inherited guardrails from the reason this
feature exists. Include an Inherited Lessons check tying each lesson to actual ordering.

For each real risk, use sections, not a risk table. Provide Risk as two paragraphs
(plain/self-contained first, precise paths/symbols/triggers second), Severity,
Category, Impact, NoobEng and Affected areas. Every Medium/High gets actionable quick,
robust and long-term proposals, with why-robust/why-long-term-effective fields. Each
proposal starts with unticked selected/elegant/last_resort boxes and empty Why chosen /
For future notes. Do not invent findings or treat already handled conditions as open risks.

For REORDER, name an actual-component experiment, cost, first dependent step and
explicit disqualifying/passing observations. It must run before step 1. A primitive
probe cannot be represented as the new unbuilt engine working. For DO NOT IMPLEMENT,
follow the skill's deprecation/blocker procedure, not mitigation or implementation.

After risk generation, perform Phase 3 without rewriting findings: identify actual
other instances before generalizing, compare reach against extent, reject gratuitous
frameworks, and tick only the chosen proposals. Explain selected tradeoffs; a forced
choice must retain the better rejected proposal and its blocker. No last-resort choice
without a named pressure. Do not re-critique the folded plan.
