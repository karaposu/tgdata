---
model: gpt-6-astra
effort: max
---

# Fresh critic-d prompt — #7 implemented diff plus folded plan

Subject: the actual `origin/dev...feat/7-group-operations` product diff and
`devdocs/work/7-group-operations/plan.md`, in the current codebase. This is the
CONTRIBUTING §7.2 PR soundness gate, not a repeat of the fidelity judgment.
Read desc/triage/plan/initial critic/merge-check as context, not proof of correctness.
Preserve critic.md and dynamic_critic_prompt.md. Write pr-critic.md beside the plan
and retain executable probes in this work folder. Same warmed session, no delegation.

Challenge the strongest promises independently:

1. Does a group's cached identifier resolve only the group requested? Check bare
   versus marked IDs, deleted/migrated/min/forbidden entities and mismatched replies.
   Does every reported membership/readable/joined state have the stated evidence?
2. Distinguish local bad input, missing cache rows, transient SDK/server failure,
   auth failure and unknown outcome. Inspect how get_entity and _call actually
   finish after retry exhaustion. Ensure exception translation preserves category,
   object/cause and health provenance instead of changing remote failure to bad input.
3. Follow quota claims through resolution, cached flood waits, retry, reconnect,
   cancellation and wrapper/batch variants. A claim must precede each supported
   join enqueue, under the account actually authenticated for that request.
   Challenge clock rollback, policy lowering, corrupt/missing rows and cleanup.
4. Follow state beyond one happy call: same and different accounts, concurrent
   ephemeral contexts, health callback reentry and the health snapshot consumers
   read. Does fresh event identity agree with the account a summary describes?
5. Inspect post-ack behavior beyond the existing regression cases: optional
   metadata/cache/warning/close failures, unexpected/empty/ambiguous updates and
   incomplete approval/payment/webview results. Can a fallible local step erase
   or mislabel a remote outcome? Can raw invite material appear in diagnostics?
6. Verify cold-account/no-store/default/file-store paths, shared proxy/device
   controls, ordinary read/discovery/batch compatibility, dependency versions and
   Python support. Check the real SDK/session methods, not only test fixtures.
7. Test the test apparatus: supplied transport is non-covering for Telegram server
   acceptance; immediate futures may fail to create claimed concurrency; stand-in
   disconnect may omit actual cleanup behavior. Use real composition/fault probes
   where a conclusion depends on it. Avoid re-running unchanged broad suites just
   to generate more green output; target newly identified concerns.
8. Question the architecture for the requested library/future worker boundary.
   Preserve explicit local coordination and offline scope; do not invent an
   unrequested distributed store, login workflow or live joining experiment.

Compute the Premise Inventory before choosing a verdict, ranked by waste if false:
premise, first dependent step, waste, planned test, cheapest earlier observation,
and actual covering/non-covering evidence. Carry declared live-test bounds as
preconditions, not fresh findings. Include a falsifier and affordability. Run an
available real-component falsifier before accepting; name any unavailable required
experiment. Check prior incidents/lessons against concrete mechanisms and ordering.

Create pr-critic.md with model/effort frontmatter, document-level skill disposition,
PR verdict (ACCEPTED/REJECTED), falsifier, high-level summary, Premise Inventory,
Restart/Inherited Lessons checks, risk sections and validation/limits. For each
actual risk include two Risk paragraphs (plain consequence first, exact path/
symbol/trigger second), severity/category/impact/NoobEng/affected areas. For every
Medium/High, write Quick/Robust/Long-term proposals, with robustness/class-wide
rationale and initially empty selected/elegant/last_resort boxes and notes.

Run Phase3 separately: change only selections/notes; name actual other instances,
reject fake generalization, compare reach/extent, apply the size/blocked/delicate
checks. A selection here informs the required re-plan; it does not authorize a
post-review patch. One Medium or High rejects the PR under §7.3. On rejection,
keep it draft, commit and post the review, mark the issue honestly, and point to
§7.4 revision3 re-planning. Do not overwrite the earlier plan-critic evidence.
A wrong/unestablished architectural premise invokes critic-d's deprecation/blocker
procedure; ordinary implementation findings instead follow the PR re-plan rule.
Low-only findings may be consciously left, recorded explicitly. Do not manufacture
findings to satisfy a quota, and do not accept merely because fidelity passed.
