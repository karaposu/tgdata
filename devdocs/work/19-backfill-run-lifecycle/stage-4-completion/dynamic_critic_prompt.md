# Stage 4 dynamic critic prompt

Review Stage 4's plan against the full engine, state codec, SQLite store, delivery
tests and lifecycle contract. Start with premises, ranked by work wasted if false.
Distinguish existing live evidence, synthetic transport tests and behavior not yet built.

Challenge whether exact canonical read-back proves the attempted effect without
proving rollback when it differs. Check full run identity, revisions, concurrent
controls, retained receipts, missing/corrupt state and backend outages. Verify that
admission uncertainty never permits a source send, cancellation is preserved, and
source failures retain their separate provenance.

Check completion independently from pending delivery: empty end, nonempty final,
full limit, interrupted prefix, imported origin, prior cancellation and completed
reopen. Check actual SQLite commit-boundary tests and the receiver's acceptance/
deduplication boundary. Reuse existing closure rather than building a second path.

Challenge Gate B's independent oracle, source drift checks, permitted groups, shared
budget, request caps, media custody, process-exit evidence and privacy. A synthetic
result cannot prove Telegram behavior; a receiver callback cannot substitute for a
real durable transaction. No later-stage control/recovery shortcut is permitted.

Create `critic.md` in this directory with model/effort frontmatter, then a document-
level verdict, falsifier/affordability line, high-level summary, premise inventory,
restart check and inherited lessons. Allowed verdicts: IMPLEMENT AS WRITTEN;
IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD; DO NOT IMPLEMENT —
MEANING GAP (or WRONG LAYER). The verdict judges shape/order, not the risk count.
An affordable untested premise scheduled after dependent work requires REORDER with
an actual-component experiment, cost, first dependent step, disqualifying and passing
results. Inventory fields: premise, first dependency, waste, scheduled test, cheapest
earlier test/cost and covering/non-covering evidence. A wrong shape follows the
critic-d deprecation/blocker procedure, not mitigation tiers.

Report only evidenced risks. Each Medium/High needs two Risk paragraphs (plain and
self-contained first; exact paths/symbols/triggers second), severity, category, impact,
NoobEng explanation and affected areas. Give quick/robust/long-term proposals, robust
and long-term rationales, with initially empty selected/elegant/last_resort boxes and
Why chosen / For future notes. Phase 3 selects by reach versus extent; name actual
other instances before claiming a class-wide mechanism. Keep size/blocker/delicacy
gates explicit, no quick fix chosen merely for convenience. Do not manufacture
findings or a general framework. Carry execution blockers separately from risks.

Run in the warmed primary session. Behavioral claims require observations of actual
components; seeded state fixtures cover preservation only. Gate A is source evidence,
not a live test of the new Stage 3 delivery composition. Gate B cannot pass offline.
