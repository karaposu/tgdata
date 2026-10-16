---
model: unknown
effort: unknown
---
# #50 revision7 handoff

The user-requested oversized-input contract and replacement plan are complete.
Finding:e2f5ab6 in devdocs/inquiries/2026-10-16_20-49__bounded-terminal-input/.
Description:79c7327. Current plan:step_by_step_impl_plan.md,revision7.

The new contract observes input bytes, keeps at most128 value bytes, permanently
invalidates an oversized line and discards it while hidden through its delimiter,
EOF or stop. It clears prequeued input before inviting a prompt. Exact restoration
includes the native canonical/PENDIN transition before restoring echo. Existing
LoginFlow and native session publication stay intact.

Evidence:46 native input cases plus7 selected real-component handoffs passed expected
outcomes, including500,000 bytes plus newline and paced input. Three deliberately
persistent cleanup faults correctly report failure with no value and dirty modes;
the harness repairs its own terminals afterwards. Prototype source snapshots retain
its initial PENDIN failure, marker correction and pre-prompt queue refinement.
This is premise evidence, not the full next candidate prebuild.

The next action is fresh critic-d on revision7, then fold revision8 and run the FULL
combined prebuild before product edits. The canonical critic.md/prompt are absent
intentionally; historical failed gate is critic_r6_prebuild.md, prior selected plan
critic is critic_r5.md. Do not apply either old verdict to the replacement plan.
Revision6 remains deprecated and unchanged except its existing failure marker.

Product PR51 remains34907d4, draft, rejected and unmerged. No product source, version,
dependency, real account, configured session or running reader changed. Current-turn
§9 model/effort verification remains pending; do not reuse an earlier session stamp.
The original checkout's version edit remains untouched.
