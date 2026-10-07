# Dynamic critic prompt — #17 account routing

Evaluate `step_by_step_impl_plan.md` revision1 against `desc.md`, triage, the
completed traverse, and actual dev95 code. This is the task-impl plan critic,
in the same warmed session; do not delegate. The user authorizes existing-access
routing/failover only. #7 remains paused. E1 live resources is an execution
precondition at step9, not a finding to rediscover.

First build a premise inventory ranked by wasted downstream work: premise, first
dependent step, waste if false, scheduled test, cheapest earlier real-component
test and current coverage. Distinguish a scripted wire response from a fake
client supplying the behavior being tested. Factory/SDK/SQLite behavior must be
observed through real implementations. Existing live gates prove one-account
reads, not new multi-account deployment or equal account visibility.

Question the plan's ownership shape before its code details:

- Does expected identity remain distinct from verified identity through cached
  rows, reconnects, second-page budget admission and repair? Can two aliases turn
  the same account into separate allowance or waiting authorities?
- Does source permission exist durably before any source work? Prosecute lost
  admission replies, stale settlement, changed inventory, deleted known state,
  duplicate JSON keys and exact recovery retries after a newer attempt.
- Is a wait or repair flag ever shortened by success, initialization, status,
  repair, recovery, a backward/forward clock observation, or another group?
- What happens when source work completes but health reporting/callbacks are
  still awaited as the timer fires? Who retains the actual batch/error/prefix?
  Does a callback timeout become a fabricated transport failure or lose a flood wait?
- Does credential repair actually reload the session? A fresh get_me on an old
  in-memory auth key is not proof that a newly repaired stored login was loaded.
- Classify exact exception provenance: local media/state/format failures never
  trigger another account or inherit Telegram health from incidental context.
- Follow a100-message prefix through timeout, restriction-store failure, actual
  daily/backfill publication, replay, destination acceptance and acknowledgment.
  No second source may replace an already-complete observation.
- Verify concurrency and cleanup: real overlapping tasks, cancellation while
  committing/observing, close from a callback, blocked disconnect, no background
  source continuing after failover. A cooperative timeout is not hard preemption.
- Check canonical group resolution before reads; SDK exhaustion must not become
  invalid-reference or an unbounded dialog sweep. Respect account-specific hashes.
- Verify per-send budget authority, minimum-age gate and finite retry policy;
  known waits can block metadata too. No new accounting or automatic login/join.
- Does extracting progress methods preserve all public signatures, clock-injection
  seams, cache ownership and source-free replay/ack? Look for circular imports,
  package omissions and examples importing private work artifacts.

Inspect `tgdata/connection_engine.py`, `budget_client.py`, `read_budget.py`,
`health.py`, `batch_engine.py`, `batch_files.py`, `sync_engine.py`, `sync_store.py`,
`backfill_engine.py`, `tgdata.py`, actual Telethon1.45 and relevant test helpers.
Assess latency/storage/CPU cost of the bounded inventory and whole-document CAS.
Flag under-specified steps as Medium where their missing semantics could change code.
Do not pad with hypothetical risks unrelated to this contract.

Create `critic.md` in the same directory as the implementation plan, with a high
level summary on top. First emit model/effort YAML frontmatter from current session
(unknown if unavailable). Immediately follow it with exactly one verdict:
IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD;
or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant if failures are unaddressed).

Immediately below verdict emit:
Falsifier: cheapest observation that would require replacing the plan's shape.
Affordable now: yes|no, with time/access cost.
If affordable and not already established, use REORDER, naming Experiment, Cost,
Must precede, Disqualifying result and Passing result. Behavioral tests must run
the real component in its real composition; a supplied result does not close a premise.

After summary include Premise Inventory, then Restart Check with one row for each
observed identity, hidden-wait, error-exhaustion, post-result-state and timeout-prefix
failure. State established mechanism and the plan element that addresses it.
Include Inherited Lessons with the exact step ordering that satisfies each lesson.

For each actual risk use prose sections, not a risk table. Risk has two paragraphs:
plain self-contained explanation for an unfamiliar reader, then precise symbols,
paths and trigger. Include Severity(Low/Medium/High), Category, Impact, NoobEng,
Affected areas. Each Medium/High has quick, robust and long-term proposals;
robust includes why this is robust, long-term why this is long term effective.
Under every proposal emit initially unticked selected/elegant/last_resort boxes
and Note with Why chosen: — and For future: —. Phase3 alone selects/annotates.

If DO NOT IMPLEMENT, follow critic-d's deprecation and desc-blocker procedure,
without mitigation tiers or implementation. If REORDER, keep plan alive and give
the actual pre-build experiment. Carry E1 unchanged. Phase3 applies reach/extent,
real-class and size gates; do not pull #7 or a generalized scheduler into this task.
