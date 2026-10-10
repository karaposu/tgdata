---
model: gpt-6-astra
effort: max
---
# #7 Stage 2 handoff

**Stage2 merged into dev via PR22 at `30ba706`; merged-code verification passed.**
Product `c6451bb`, branch `feat/7-account-health-ownership`, base dev/merged Stage1
`53306df`. Worktree: `/private/tmp/tgdata-7-stage2-health-ownership`.
[PR22](https://github.com/karaposu/tgdata/pull/22) is **merged**, confirmed by GitHub
at `2026-10-10T12:23:14Z`. The feature branch is retained as the archive.

## Current implementation

The existing fixed-owner monitor, private `_account_health_operation` and local
`get_account_health(account_id)` are retained. Events/state belong to the verified
numeric account; legacy health stays separate. The rework defines precise evidence:

- Owned successes and raw RPC/MultiError failures use one namespaced logical request
  key through known SDK envelopes; legacy names stay unchanged.
- Immutable keys are captured before awaiting and bound to the observation/client.
  Mutable batch containers cannot invent a successful action. Unknown/lazy input
  supplies no recovery evidence; individual private request objects stay stable.
- Restriction recovery needs the refused action, along with the existing method,
  owner, ordering, no-self-recovery and valid-handle guards. Identity-only success
  cannot clear a history-read restriction.
- Neutral attribution travels with the originating exception/explicit causes/SDK
  RPC members across task hops. Independent new RPCs are not hidden by old implicit
  context. Diagnostic classification and polling remain unchanged.
- Notifications remain isolated tasks after source cleanup; arrival may reorder
  when cleanup durations differ. No FIFO/durability expansion.

Rework scope: three runtime files, suite33 and three product documents. No Stage1,
budget or facade interface changes, no new sender layer or global ownership system.
Verification: **445 actual offline passes, 3 live skips**, 3 offline demo executions,
63-file compilation/Python3.7 grammar checks on Telethon1.45.0. Suite33 has62 cases,
21 added in this rework. No final failing-test runtime correction. See verification.md.

## Pipeline and preserved evidence

Original pipeline: triage `ea988e9`, inquiry `f19ca2a`, desc `8350f39`, initial plan
`587b060`, prompt `19ab9a1`, critic `f1aa84b`, experiment PASS `46866c3`, revision2
`a1accf6`, initial product `3d59455`, initial verification `a2b9755`.

Round1: merge fidelity PASS `1625e09`, fresh PR prompt `7711e56`, PR critic
`b9a8a5d` **REJECTED: 0 High, 3 Medium, 0 Low**. The findings were wrapped-request
key mismatch, identity-only restriction recovery and overbroad exception exclusion.
That review and its probes remain unchanged in archive/round-1/pr-critic.md and
archive/round-1/pr_probes.py.
Their probes characterize the old defects, not current acceptance. There is only
**one distinct Stage2 rejecting PR round**; old whole-issue PR16 is separate.

Revision3: archive/evidence `2509a1f`, re-plan `530ea36`, additional namespaced SDK
and child-task/exception evidence in replan-evidence.md and replan_inputs_probe.py.
The user then authorized fresh plan critic, fold and implementation together.

Revision4 cycle: fresh prompt `4f562a7`, critic `d9eefbe` (one Medium on mutable
success evidence; robust snapshot selected), required real-SDK exception-carrier
experiment PASS `d2dd499`, folded plan `aee7211`, product **`c6451bb`**. No blockers,
no re-critique of the fold. Eight pre-change regressions failed as expected; the
final product passes the complete verification set.

Round1 plan/critic/prompt/merge-check and original verification are preserved
byte-for-byte under archive/round-1, with checked SHA-256s. Active root plan is
revision4; active plan critic is the revision3 critique with its completed experiment.
Do not resume archived plans or mistake initial fidelity PASS for renewed approval.

## Renewed review and next step

Merge fidelity PASS `fd655a5`, posted on PR22 at issuecomment-6097100536. Fresh
critic prompt `da777fe`; fresh review/probes committed and pushed in `9e0b4e5`,
posted at [issuecomment-6097169418](https://github.com/karaposu/tgdata/pull/22#issuecomment-6097169418).
Root pr-critic.md records the second review: **ACCEPTED, 0 High, 0 Medium, 0 Low**. Seven additional offline probe groups passed, including
nested resolution, namespace restrictions, local/cancelled failure after successful
requests, crossed account cleanup and forwarded failure followed by fresh legacy RPC.
The final probe runner exits0. No product code changed during either review gate.

The user authorized the merge with “go”. It was prepared from dev53306df and
approved headb74e9b3, with work documents excluded and dev archaeology preserved.
The exact merge commit30ba706 passed **445 actual offline tests, 3 live skips,
3 demos and63-file syntax/grammar checks** before its normal push to dev. One
verification-launcher issue in test18 was corrected by using its normal python -m
entry point; no product/test changes. See merge-verification.md for the full record.

Next scope is **Stage3: group lookup and access checks**. Stage4 join allowance and
Stage5 joining follow later. Whole #7 remains open; no next-stage work has started.
The merged prerequisites and accepted review now supersede the old broad attempt.
§9 provenance remains the retained same-session Astra/max record, with its original
timestamp preserved rather than presented as a new selector reading.

The original checkout and old broad PR16/revision3 are preserved. Do not merge
unmerged #17 into this prerequisite. Do not commit duncan, the stray guide, or the
original checkout's untracked HANDOFF.md/todo.md. No live Telegram work, additional
accounts, login codes or membership changes were needed in this stage.
