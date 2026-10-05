---
model: unknown
effort: unknown
---

Critique PR #14's implemented diff (`af593fc...293bfbc`, runtime `07d983a`)
together with `step_by_step_impl_plan.md` revision 2, in this codebase.
Run in the current warmed session; no subagent. Preserve the original plan
critic and its prompt. Save this review as `pr-critic.md`, as CONTRIBUTING §7.2
requires. Exact model/effort are unknown; carry the §9 qualification.

Read the description, declared blockers, triage, plan, initial critic and
implementation report, plus full relevant implementations and the diff.
Judge soundness independently of plan fidelity or the existing green suite.
Only real, evidenced risks belong in the result; do not pad it with style notes.

First compute a premise inventory, ranked by waste if false. For each premise,
record its first dependent plan step, downstream cost if false, scheduled test,
cheapest earlier decisive observation and current coverage. Distinguish actual
SQLite/SDK behavior from server behavior supplied by scripted replies. Existing
live-test exclusions are preconditions, not newly discovered risks. The
remaining live server-bound premise must stay explicitly unverified.

Probe the common guard from public client/engine entry points: supported raw
reads, nested wrappers, batches, resolution and retries. Inspect what actually
reaches the sender, not just returned rows or helper values. Test quota races,
refunds/failures, policy updates, rollback, expiry and reopening with real
SQLite. Check that request/response accounting cannot lose or invent capacity.

Exercise pagination after an interruption and after fresh capacity: forward,
reverse, filtered/empty pages and ID chunks. Check partial frames/dictionaries,
callback behavior, discovery's interrupted link mining and polling's stop.
Inspect SDK catch-all handlers around implicit message re-fetches, and ensure
local stops neither disappear nor acquire Telegram health classifications.
Check defaults, factory coverage, public exports, supported SDK/Python versions,
credentials, synchronous storage latency and README promises in the same flow.

Write and run targeted adversarial probes for behavioral claims. Quote exact
output and the responsible source locations for any Medium/High. Probes must
use temporary files and synthetic credentials, prohibit Telegram sockets, and
leave runtime code and the user's unrelated guide edit untouched. A supplied
reply verifies client handling only; do not claim it verifies live Telegram.
Reuse unchanged regression results; rerun only where a new concern justifies it.

Create `pr-critic.md` with model/effort frontmatter, then one critic-d verdict:
IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE
BUILD; or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant when warranted).
Add the falsifier and whether it is affordable now, a high-level summary, the
premise inventory, a restart check and inherited lessons where applicable.
Run affordable decisive experiments now; do not defer them behind approval.
Apply the skill's meaning-gap/reorder procedures if their conditions arise.

State a separate PR gate result: any High or Medium rejects under §7.3 even
if the plan's shape survives. Each risk has two paragraphs: a self-contained
plain explanation of what fails for a user, then precise paths/symbols/trigger.
Include Severity, Category, Impact, NoobEng and Affected areas. Medium/High
risks get Quick, Robust and Long-term mitigations, with the robust/long-term
explanations and initially empty selected/elegant/last_resort boxes and notes.
Keep findings as sections, not a risk table.

Then run Phase 3 separately: tick boxes and notes only. Select by reach versus
extent, enumerate real other instances before inventing a class-wide mechanism,
and apply the size/blocker/delicacy gates. Do not silently patch runtime code.
A rejected PR requires a new plan under CONTRIBUTING §7.4; selection is input
to that re-plan, not permission to bypass it. Commit the review and probes,
post the review on PR #14, and update #9's actual status. No merge in this run.
