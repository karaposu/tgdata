---
model: gpt-6-astra
effort: max
---
# Fresh critic-d prompt — PR #26 / #17

Ultrathink. Review the complete implemented product diff `68f6bbd...cdcfd63`
in PR #26, together with the original revision-2 `step_by_step_impl_plan.md`
and scoped revision-2 `retirement-rework/plan.md`. Preserve their existing
critic files. Run in this warmed session, not a subagent. Fidelity already passed;
judge soundness independently, including the retained original pool code.

Read full relevant implementations and contract boundaries. Source faults must
be demonstrated on actual Telethon 1.45, SQLite, pool and delivery composition;
replace transport or inject a specifically labeled boundary failure, not the
behavior under examination. Block network sockets. No live account access.

Challenge these invariants:

- Actual identity at each charged send owns budget, data and health. Test a
  change after a completed page, pre-proof authentication failure and stale cache.
- Eligibility is distinct from admission; uncertain remote CAS/cancellation never
  grants source permission. Settlement cannot erase newer restrictions, or turn
  a known long wait into a short local retry. Probe delayed/lost write replies.
- Retained children and native disconnects really end before ownership is released.
  Combine close with cancelled recheck/read, internal cleanup failure and repeated
  cancellation. Check task and session lifetime, not just a returned exception.
- Completed source outcomes survive observers and local storage/media errors.
  Exercise observer behavior beyond an ordinary timeout, including hostile or
  inherited errors; prove a local fault cannot invent Telegram restrictions.
- Known state never resets during inventory changes/restart/recovery. Strict
  encoding, exact token/CAS and conditional retry semantics must agree.
- Daily/backfill pending data remains replayable and acknowledgeable with all
  source/config/pool-state access unavailable; new source errors preserve prefixes.
- Shared facade/factory changes retain current dev APIs and ordinary TgData behavior.
  Packaging and docs must expose the actual scope and cleanup limits.

Write `pr-critic.md` beside the original plan, frontmatter first (`model`, `effort`
from current metadata; use `unknown` if unavailable), then exactly one plan verdict:
IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD;
or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant where applicable). State the
separate PR decision: any High or Medium means REJECTED; Low-only/none means ACCEPTED.
Do not repair runtime code during this gate. Rejection returns to revision-3 planning
under CONTRIBUTING §7.4; do not silently overwrite or deprecate the existing evidence.

Directly below the verdict name the cheapest disqualifying observation and its
affordability. Execute affordable falsifiers before an accepting verdict. Then give
a high-level summary and a ranked Premise Inventory before risk items: premise,
first dependent step, waste if false, scheduled test, cheapest earlier test/cost,
and actual coverage. Label synthetic wire/finalizer boundaries honestly; fabricated
desired outcomes are non-covering. Carry declared live E1 unchanged as an execution
precondition, not a new defect or an offline claim of live qualification.

Include Restart Check rows (observed failure, established mechanism, addressing
design) and Inherited Lessons with concrete ordering/evidence. Cite executed probe
output and exact source lines; zero findings is permissible only after attempted
falsification. Separate inherited dev limitations from newly introduced defects.

For every risk write two paragraphs: plain self-contained consequence first, then
precise path/symbol/trigger. Include Severity, Category, Impact, NoobEng and affected
areas. Each Medium/High needs quick, robust and long-term proposals, with robust/
long-term rationale and initially empty selected/elegant/last_resort boxes plus
Why chosen/For future notes. Commit the Phase-2 critique before selection. Phase 3
only ticks boxes and fills notes: prefer reach per extent; a shared mechanism needs
another real instance and must not invent coupling or expand this task. A meaning
gap stops rather than offering patches to a dead premise. Only real findings;
no speculative severity inflation or padding.
