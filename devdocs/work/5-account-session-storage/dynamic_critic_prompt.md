# Plan critique prompt — issue #5, revision 3

Review the regenerated plan at `cc665f4` against the description and the
rejected PR critique `a6deab7`. Run in this warmed session, without delegation.
Read the adapter, real Telethon logout/disconnect, constructor paths and tests.

Focus on the shared credential-ownership rule: compare the current stored
login with the key last synchronized before either a changed save or delete.
Check ordinary deletion, stale deletion, first login, external removal, read
failure, corrupt current data, failed deletion, marker updates and warning
counts. Does the refactor preserve unchanged-save elision, optional delete,
credential-free logs, default files and the current format? Does it need a
new public contract or atomic store operations beyond the agreed scope?

Use the archived lifecycle probe and a clearly labelled ephemeral prototype
where useful; do not mistake a supplied guard for verification of the future
production implementation. No sockets or live Telegram. The previous live
restoration and non-atomic cross-process boundaries remain explicit.

Write `critic.md`, preserving earlier critiques in git history. Include model
and effort frontmatter (unknown if not exposed), the four-way critic verdict,
falsifier/affordability, high-level summary, ranked premise inventory, restart
check, inherited lessons, probes and real risks. Each risk uses plain and
precise paragraphs, severity, category, impact, NoobEng and affected areas.
Medium/High risks receive quick/robust/long-term proposals with why robust and
long-term work, initially blank selection/elegant/last-resort boxes and notes.
Run Phase 3 to select by reach/extent. Do not invent findings to fill a list.
This judges the new plan, not permission to merge PR #13. Carry the maintainer's
merge go-ahead and §9 disposition as execution preconditions.
