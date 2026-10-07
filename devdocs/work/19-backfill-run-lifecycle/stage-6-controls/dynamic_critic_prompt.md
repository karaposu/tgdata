---
model: gpt-6-astra
effort: max
---
# Dynamic critique — Stage 6 and Gate C

Review `step_by_step_impl_plan.md` at `0e8ab65` with its description, triage,
contract OP-CONTROL/RECOVER, staged-plan Stage 6/Gate C and inherited A/B evidence.
Stay in this warmed session. Inspect actual values, strict aggregate, CAS/settlement,
recovery, source budget adapter, raw reader and live guard/receiver interfaces.
No subagent and no implementation during the critique.

Question the meaning and ownership, not just the proposed code. Who has authority
to pause, acknowledge, retire, replace or recover? Does a matching retry recognize
an old decision without granting a fresh one? Can ordinary data progress invalidate
operator context unnecessarily, or can a retry overwrite a newer decision? Check
full run identity, bounded command history, previous-generation reporting, recovery
ID collisions, terminal/no-change outcomes and explicit abandonment after cancel.

Trace pause/cancel during admission, source, publication and ack; both terminal
orders; two controls with the same expected revision; stale resume; failed writes
before/after commit and delayed successful replies. Ensure no source-spanning lock,
refetch, quota refund, implicit worker-death assumption or fabricated end observation.
Check revision headroom for both publication and ack, not only integer overflow.
Does the existing codec admit every proposed state without relaxing an invariant?

Check abandonment's quiescence, cursor and blob custody, local busy guard during
new succession, equal payload hashes in distinct runs, old accepted versus retired
receipts and pruning. Test whether adding result/status fields breaks internal or
public assumptions. Keep public facade, schema migrations, health ownership and
distributed scheduling outside this stage. Examine failure/performance/privacy
effects of extra CAS loops, retained payload and live fixtures.

For Gate C, inspect every consumer of the test budget wrapper, including its return
objects. Verify the stricter of two real ledgers is enforced at actual SDK send/page
boundaries, without resetting the shared policy or charges. Compare observed attempt
times with actual RPC traces; distinguish local barriers, retries, real waits and
natural quota expiry. Require a confirmed owned-process exit, durable recovery reply
loss and stable deadline after reopen. Can the stated total source ceiling really
bind multiple workers, crashes and reruns? Preserve prior A/B raw evidence. No new
Telegram writes, joins, login-code request or deliberate flood/ban generation.

Compute the Premise Inventory before deciding the verdict. For each premise state
its first dependent step, waste if false, scheduled test, cheapest earlier real
test/cost and current coverage. Rank by wasted work, not disclosure. A fake supplying
the desired provider result is non-covering. Any affordable earlier falsifier makes
the verdict REORDER, even if the content has no risk findings. Carry known execution
conditions unchanged; do not rediscover them as severity-rated risks.

Create `critic.md` here. First record model/effort frontmatter from session metadata
(unknown if not derivable), then exactly one verdict: IMPLEMENT AS WRITTEN;
IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD; DO NOT IMPLEMENT —
MEANING GAP (or WRONG LAYER). Immediately give the cheapest falsifier and whether
affordable. For REORDER specify real experiment, cost, first dependent step, exact
passing and disqualifying observations. No content implementation before it runs.

Follow with a high-level summary, ranked Premise Inventory, Restart Check (observed
failure, demonstrated mechanism, design element) and Inherited Lessons (lesson and
the step whose ordering satisfies it). Do not claim the paused #7 redesign is the
cause of an unrelated lifecycle problem. If most actual restart mechanisms lack a
design answer, reject as WRONG LAYER. An unestablished meaning cannot be mitigated.

For each real risk use sections, not a risk table. Write two Risk paragraphs: first
plain and self-contained, describing the user-visible consequence without paths or
symbols; second precise with file/symbol/trigger. Include Severity, Category, Impact,
NoobEng (engineer unfamiliar with this system), Affected areas. Flag insufficient
detail as Medium when it leaves a delicate behavior undecided; do not pad findings.

For every Medium/High risk write three actionable proposals, Quick, Robust and
Long-term. Include `Why this is robust` and `Why this is long term effective` where
appropriate. Under each emit initially empty `selected`, `elegant`, `last_resort`
checkboxes and empty Note/Why chosen/For future sections. In a separate third pass
only fill selections/notes. Compare reach per extent; enumerate actual other instances
before claiming a class. If no common mechanism serves another instance, long-term
collapses to robust. Never select quick on merit, or silently force a larger class
redesign into this delicate stage. Name prerequisites/future improvements if needed.

A meaning-gap verdict follows critic-d deprecation/blocker procedure and stops.
REORDER retains the plan, specifies the experiment and still selects proposals.
Otherwise hand the selected mitigations to task-impl to fold, without re-critique.
