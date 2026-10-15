---
model: gpt-6-astra
effort: xhigh
---
# #43 — merged into dev

Branch: `feat/43-richer-group-profiles`, based on dev `abd1f57`.
Worktree: `/private/tmp/tgdata-43-richer-group-profiles`.
Product: `b62dc03`. Public contract: `docs/group_profiles.md`.

TgData.get_group_profile(target, *, account_id, pinned_limit=0, heartbeat=None)
returns GroupProfile with basic/supergroup/channel full metadata and optional
one-response pin observations. GroupPinnedMessage retains original ID/date/text
and service/unavailable kinds. Unknown counts, exactness, coverage and failure
remain explicit. Original pin errors retain completed profile evidence where
attributes are supported. Existing verified operations own policy and cleanup.

Pipeline: qualification1ba6de5, plan6b003f2, critic19cfb80, passed prebuild/foldc85f8af,
productb62dc03. Triage feature-heavy; full traverse was unnecessary because this
is a bounded consumer of the settled #7 structure, with the SDK composition
qualified before product work. No parked description or rejected PR critic.

Verification:952 offline checks/32 suites and7 demos PASS,3 live skips;100-source
compile/Python3.7 grammar pass on3.11.10/Telethon1.45.0. See verification.md and
evidence/verified-result.json. Initial fixture corrections and sandbox loopback
refusal are preserved; no architectural deviation or product fix during tests.

Merge check PASS f7f88b6, posted on PR47. Product-only PR branch:
feat/43-richer-group-profiles-pr at72f51313214a318d59eb9fc43e652ae64bf67159.
Fresh in-session critic-d ACCEPTED:0 High/0 Medium/0 Low;13 fresh probe groups,
29 cases passed against the actual PR checkout. See pr-critic.md, pr-probes.py
and pr-probe-results.json. No product change during review. §9 verified Astra/xhigh.

The user's go-ahead was received. PR47 merged into dev at490cf5f4aaf682a1ed9fcf8c680be56f2ec14c92
on2026-10-15T19:41:00Z. Actual merged-tree verification:952 offline checks/32 suites,
7 demos PASS,3 live skips;100-source compile/grammar PASS. Published tree exactly
matches the tested local merge. See merge-verification.md and merge-parity.json.

No work-folder/archaeology files entered dev. Both branches are retained. #43 is
complete; close manually for the dev target. Main/version0.1.1 and original
checkout edits are unchanged. No release/deployment. #44/#45/#46 are separate.
