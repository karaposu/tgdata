---
model: gpt-6-astra
effort: max
round: 3
---
# Fresh implemented-diff critic — issue17 / PR26

Subject: the ENTIRE23-file product diff dev2ddb852...007c2e4 together with folded
step_by_step_impl_plan.md revision7 and desc.md revision5. Current review head001d920
changes work evidence only. This is a new PR soundness review, not another plan critic.
Use the same warmed session without delegation (CONTRIBUTING §7.5). Keep critic.md
unchanged; create pr-critic.md beside the plan, with a high-level summary on top after
frontmatter/verdict. Preserve the second round as pr-critic_r2.md and this prompt's
predecessor as pr-dynamic-critic-prompt_r2.md.

Read the known blockers first. No planning blocker is OPEN. Carry E1 (two approved
accounts, shared readable group, existing bounded allowances) unchanged as an execution
precondition on step7, not a new risk. User authorized offline review; no live calls,
credential work, runtime fixes, re-plan or merge. Native3.7 is unqualified.

## Attack the concepts and their boundaries

Separate the actual source result, caller stop signal, owned invocation completion,
caller-retained data, permission/charge and durable progress receipt. Ask where each
becomes authoritative and whether ordinary application composition crosses that boundary.

1. Can an outer shield waiter stop while the real read remains active? Observe a real
   first page, later source reply and final capture. A wrapper stop must neither finalize
   nor cancel the inner call accidentally; its independent capture must remain useful.
2. Can preparation for one group still publish while another group/account reads? Hold
   actual progress CAS, start the other invocation, close the pool and then finish the
   publication. Probe success, ordinary error and cancellation without a shared-writer
   leak, false receipt, wrong owner, or waiting for the wrong public Task.
3. Does shutdown stop only the exact library invocation if the caller immediately starts
   unrelated work, a different pool, or its own cleanup? Include a stale stop/finished
   invocation control. No whole-Task join or cancellation-consumption assumption.
4. Can post-source clock/validation/media or publication failure still hide complete
   records? Use actual messages/downloads and stores, not a manufactured MessageBatch
   or helper that supplies the expected result. Distinguish available records from a
   valid stored receipt and from read_error_type. Media existence is checked on replay.
5. Challenge the selected attempt-provenance transition at additional boundaries:
   first-account empty failure, second attempt's admission/load/verification failure,
   held source with no prefix then actual records. Prior failure must not masquerade
   as the source of second-account data. No complete prefix permits another account.
6. Recheck the retained whole feature: deterministic selection, exact identity at send,
   real allowance and warm-up, scoped waits/denials, unknown attempts and exact recovery,
   duplicate credentials, all-state passive health draining, native retirement, provider
   roles and bounded reentry. Do not infer rollback from a cancelled/failed write.
7. Look for API, packaging, shared TgData/worker, database and performance regressions.
   Public captures are required only for the unmerged pool; optional shared parameters
   must not affect existing consumers. No universal byte bound or crash persistence is
   promised. Avoid unsupported private-object mutation as a manufactured finding.
8. Read docs/examples as consumer instructions. Could following them lose data, advance
   progress without a receipt, misinterpret shutdown, or accidentally contact Telegram?

The retained750-check run is evidence for its tested histories, not a substitute for
new falsifiers. Fresh probes must run actual Telethon1.45/SQLite/ReadBudget/engines with
synthetic wire only at the network boundary; block sockets and preserve actual I/O
effects. Use bounded processes and record exact source/probe hashes. A watchdog kill
is failure. Instrumentation may hold/fail a real boundary; it must not supply the
ownership, result, receipt or cleanup completion whose behavior is being tested.
Try to disprove the new contract and the retained router, not merely restate the plan.

## Output and decision

Begin pr-critic.md with model/effort from current session metadata (unknown if unavailable),
round3 and status. Immediately follow with one critic-d verdict:
IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD;
or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant when justified).
Then Falsifier and Affordable now. If an affordable unexecuted behavioral falsifier
exists, REORDER: describe experiment/cost/prerequisite/disqualifying/passing observations.
Here its prerequisite is PR acceptance, because the subject is implemented. Record its
actual result; never use the phrase as permission to patch the product.

Compute a Premise Inventory first, ranked by waste if false. For each premise name
first dependent step, waste, planned test point, cheapest earlier test and coverage.
Flag helpers supplying the outcome as non-covering. Include real service visibility/
proxy and native-runtime limits without pretending offline tests qualify them.

Add a Restart Check row for every demonstrated failure: retirement reuse; child release;
observer outcome loss/cycles; gated drain masking stop; provider-owned cancellation/data
loss; status-provider control; close consuming public cancellation; wrappers losing it
without close; application Task outliving invocation; progress publication outliving
source. Name the implemented mechanism and evidence or the missing cell explicitly.
Add Inherited Lessons mapped to the prebuild-before-production order and fresh probes.

For each real finding use headings (not a risk table): Risk in two paragraphs, plain
self-contained consequence first, then precise paths/symbols/trigger; Severity High/
Medium/Low; Category; Impact; NoobEng; Affected areas; concrete observed evidence.
Every Medium/High gets Quick/Robust/Long-term proposals, with why-this-is-robust and
why-this-is-long-term-effective. Under each, emit empty selected/elegant/last_resort
boxes and Why chosen/For future notes. Save phase2 before phase3 selection. Phase3
changes only boxes/notes: enumerate a real class before generalizing, select the smallest
mechanism with the best reach per extent, reject overengineering, apply size/delicacy gates.
Do not manufacture findings, downgrade real defects or rewrite the severity to pass.

PR decision is separate and explicit: any High/Medium REJECTS under §7.3; only Lows or
none PASS for the reviewed offline scope. Two previous rejected PR rounds remain history.
If this is a third rejection, record that fact and required upstream process; do not
start another design or piecemeal patch. A meaning-gap verdict follows critic-d's exact
deprecation/blocker procedure without overwriting earlier deprecated plans. If no gap,
leave plan7 intact. A passing review still cannot claim E1 complete or authorize merge.
Commit and post the full critique to PR26; update the issue, merge-check and handoff
with actual results and separate remaining gates.
