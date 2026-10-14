---
model: gpt-6-astra
effort: max
---
# Fresh PR critic prompt — #28 / issue8

Review PR28 product diff `c4e6eac...0a3c83d` together with plan.md revision2 in this
work folder. Product commit877d29d. Read implementation, tests, guides and relevant
SDK paths in full. Do not treat merge-check PASS or existing tests as proof of
soundness. Run in this warmed session, never a subagent (CONTRIBUTING §7.5).

Challenge the premises behind explicit auth input, retained private state, current
identity, configured route/device continuity, cancellation and actual cleanup,
safe diagnostics and #5 credential consumption. Check combinations absent from the
implementation tests: completed outcomes versus late caller stop, component stops,
body failure plus native flush failure, close retry cancellation, successive native
redirects, waits at each auth phase, real ambient health and ordinary reader reload.
Consider synchronous/async ownership and partial states, not just happy-path names.
Inspect imports/package compatibility, performance/resource retention, public API and
schema implications. No broad service/coordinator abstraction without an actual need.

Create `pr-critic.md` beside the plan, preserving `critic.md` and its original prompt.
First content: frontmatter model/effort read from session, unknown if unavailable.
Then one critic-d verdict (IMPLEMENT AS WRITTEN / IMPLEMENT AFTER FOLDING THESE IN /
REORDER — TEST BEFORE BUILD / DO NOT IMPLEMENT — MEANING GAP or WRONG LAYER variant),
Falsifier and Affordable-now lines, and a separate PR Gate PASS/REJECTED. Put the
high-level summary next, followed by Premise Inventory before findings. An affordable
unrun falsifier requires REORDER and a full experiment with cost, first dependent
step, passing/disqualifying observations; run it, not a stand-in supplying the claim.
Inventory each unproven premise: first dependent step, waste-if-false, scheduled test,
cheapest earlier test/cost and coverage/noncoverage. Rank by waste. Live Telegram
acceptance is not established by synthetic wire; retain that explicit limit.

Restart Check: each cited failure → established mechanism → actual design element.
Inherited Lessons: each lesson → observable ordering/behavior evidence. Missing
mechanisms/remedies are findings, not silently excused by acknowledgement.

For each real finding, use sections rather than a finding table: Risk paragraph1
plain/self-contained consequences, paragraph2 precise paths/symbols/triggers;
Severity High/Medium/Low; Category; Impact; NoobEng; Affected areas; exact fresh probe
output/source evidence and bounds. Medium/High require Quick, Robust, Long-term
proposals, with why-this-is-robust / why-this-is-long-term-effective. Each initially
has unticked selected/elegant/last_resort boxes and empty Why-chosen/For-future notes.
Phase3 only selects/annotates; compare actual reach/extent, name genuine other
instances before generalizing, keep large class fixes out of this change.

Quote reproducible outputs and record control cases, unchanged product hashes and
all failures/limits. Do not pad findings with speculation or style issues. At PR
gate any High or Medium REJECTS (§7.3), even if a mitigation seems small. §7.4 then
requires re-planning rather than patches. Do not alter runtime/tests or silently
weaken assertions during this review. Lows alone may pass with explicit disposition.
Commit and post the final critique; update PR/issue to the actual gate result.
