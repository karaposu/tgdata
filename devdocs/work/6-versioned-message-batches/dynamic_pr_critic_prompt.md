---
model: unknown
effort: unknown
---

# Dynamic PR critic prompt — #6 / PR #15

Subject: the implemented `origin/dev...81e3cfd` diff for PR #15, together with
`step_by_step_impl_plan.md` revision 1, in this codebase. This is the fresh
CONTRIBUTING §7.2 soundness check, after the PR was opened. Run in the same
warmed session without subagents. Preserve pre-build `critic.md` and
`dynamic_critic_prompt.md`; write this result to `pr-critic.md`.

Read whole relevant implementations/interfaces and the actual published diff,
not grep fragments. Treat the approved plan as a claim to test. Resolve known
blockers first; do not relabel declared live-server/deployment/receiver
boundaries as new findings. Target Telethon 1.45.0 only. Trace these contracts:

1. Portable value: exact fields/types, canonical UTF-8, signed IDs, nulls,
   immutable copies, hash verification and saved replay. Attack alternate JSON
   representations, invalid values and cross-process identity.
2. Continuation: group resolution (including basic groups), SDK filtering/pages,
   exclusive cursors, gaps, empty results, boundary IDs and failures after a
   completed prefix. Can the result claim progress beyond a required record/file?
3. Media: the actual SDK selection and stream contract, reference refresh,
   byte completeness, size mismatch, existing objects, concurrent publishers,
   local I/O failure and cancellation. Trace temporary versus public files and
   error identity on every exit; do not assume a filename proves content.
4. Shared controls: the connection factory, quota admission and health wrapper.
   Are refresh reads charged? Are successful refreshes supported? Does error
   classification identify the current failure correctly through explicit and
   incidental exception chains? Is any local storage/format problem reported as
   a Telegram account/group verdict?
5. Existing behavior and scope: legacy DataFrame/media contracts, imports,
   package discovery, sync I/O and allocation costs, Python syntax, user docs,
   future #10 integration. The guide checkpoint is an archive-only delta;
   duncan is explicitly excluded. Do not invent a receiver or claim live proof.

Write and run focused probes for unresolved behavioral questions using the real
components in composition. Script only the external transport/fault being
supplied; state what that does and does not establish. Quote actual output.
Every Medium/High must rest on precise source and/or a reproducible observation.
Do not pad findings, patch runtime code or weaken tests during the critique.

Create `pr-critic.md` beside the plan, frontmatter first (`model` and `effort`
from session context, otherwise `unknown`), then a critic-d verdict and falsifier,
an explicit PR ACCEPT/REJECT disposition, and a high-level summary. Any High or
Medium rejects under CONTRIBUTING §7.3; a rejection returns to planning rather
than silent patching. Keep §9's unavailable model metadata visible separately.

Compute the Premise Inventory before risks: premise, first dependent step,
waste-if-false, planned test point, cheapest earlier test/cost and actual
coverage. Rank by waste, not disclosure. Mark supplied vendor replies as
non-covering for live behavior. An affordable unrun decisive prerequisite test
requires REORDER; run affordable local observations now. Include Restart Check
and Inherited Lessons mapping observed failures/lessons to established mechanisms
and the design's ordering. No claim of a premise being closed by prose.

For each finding, use sections, not a risk table: Risk in two paragraphs (plain
consequence first, exact files/symbols/triggers second), Severity, Category,
Impact, NoobEng and Affected areas. Medium/High findings each need Quick,
Robust and Long-term proposals, including why robust/long-term work, with empty
selected/elegant/last_resort boxes and empty Why chosen/For future notes.

Phase 3 runs separately after Phase 2: tick and annotate without changing risks
or severities. Enumerate real other instances before claiming a class-wide fix;
compare reach against extent. If a general fix grows this task or creates fake
coupling, select the smallest robust fix and explain any future work. No quick
fix on merit alone. Meaning-gap/wrong-layer verdicts follow the skill's stop
procedure instead. Commit the final prompt/probes/critique and post the critique
on PR #15; record a rejection honestly in the issue and PR status.
