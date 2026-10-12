# Fresh critic prompt — #17 restart

Review desc.md and step_by_step_impl_plan.md from scratch against actual pool/source,
health, store, daily/backfill and batch implementations, plus current-dev worker.
Use all archived failures as counterexamples. Do not treat r3's 36 passing groups
as proof of the replacement. Review in this warmed session, never a subagent.

First read declared blockers: distinguish factual CLOSED failures from behavioral
qualification and E1 execution access. Compute premises before risks, ranked by waste
if false. For each: premise, first dependent step, waste, scheduled test, cheapest
earlier real-component test/cost, existing coverage and non-covering stand-ins.

Challenge these specific boundaries:
- Can the caller and a component cancel independently, concurrently, before start,
  during source finalization, or during a store's late actual commit? Does repeated
  cancellation retain the actual child and busy ownership without cancelling cleanup?
- Does a provider task get cancellation meaning at every invocation, including
  attribute lookup/call, load/CAS, pool/daily/backfill and synchronous session loading?
- Does a failed admission refuse traffic even if committed? Does non-admission
  backfill reconciliation still use exact real state? Are retries, quotas, tokens,
  progress and receipts unchanged? No canceled reply proves rollback.
- Can a complete source batch be retrieved after pool settlement or progress save
  fails? Are invalid batches excluded? Is an error prefix distinguishable from
  durable pending data, end evidence and an acknowledgment receipt?
- Which operations can a same-pool provider reenter, particularly state-only reads
  with no active source task? Test lifecycle mutations as well as close. Can guards
  survive task hops and then expire without blocking legitimate external control?
- Does passive reporting eliminate user callbacks/tasks/log-mirror dependencies,
  bound count/encoded bytes/types/loss, and drain during close without I/O?
- Does source outcome survive every secondary completion path? Does unexpected
  source cancellation remain unresolved? Does native failed retirement quarantine?
- Does the common helper serve real repeated instances without becoming a global
  supervisor or changing ordinary TgData/#7/#10 cancellation? Preserve Python3.7 API
  compatibility and Telethon1.45, current worker resolver and cleanup receipts.

Create critic.md beside the plan. Frontmatter: actual model/effort (unknown if not
available). Then verdict: IMPLEMENT AS WRITTEN / IMPLEMENT AFTER FOLDING THESE IN /
REORDER — TEST BEFORE BUILD / DO NOT IMPLEMENT — MEANING GAP (or WRONG LAYER).
Immediately give Falsifier and Affordable now (cost/access). Affordable falsifier
means REORDER. Specify full real-component experiment, cost, first dependent step,
passing/disqualifying observations; no targeted probe substitutes for combined P0.

Then high-level summary, Premise Inventory, Restart Check (each observed failure,
established mechanism, addressing design element), and Inherited Lessons (lesson,
step/order that satisfies it). Empty addressing cells are findings; most empty
means WRONG LAYER. Execution blockers are preconditions, not severity-rated risks.

For each real risk use sections, not a risks table: two-paragraph Risk (plain,
self-contained consequence first; precise paths/symbols/triggers second), Severity,
Category, Impact, NoobEng and Affected areas. For Medium/High supply quick/robust/
long-term mitigations, robust justification and long-term justification. Every
proposal has empty selected/elegant/last_resort boxes and Note with Why chosen/For
future blank. Do not pad risk counts. Phase3 only selects/annotates, using actual
other instances, one-mechanism validity and reach/extent, never tier prestige.
