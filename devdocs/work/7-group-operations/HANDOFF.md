# #7 paused — resume only when the user asks

Saved locally on 2026-10-06. This handoff is not a new pipeline step, an
approved design, or permission to continue implementation.

The user stopped the work: “okay lets stop that since it is not working
properly , we will get back so make sure u save that progress somewhere”.
Do not automatically resume from the issue's first unchecked box.

## Saved state

- Repository: `karaposu/tgdata`.
- Branch: `feat/7-group-operations`.
- Last committed and pushed checkpoint before this handoff:
  `8a43d23d7b1b967d82d9a9696db9ccc6b0955606` — revision 3 re-plan.
- Runtime implementation: `8e245f8f1d001c30ecd561e173e8742302cc313d`.
  It still has the defects found by the first PR review.
- Base: `dev` at `45bab7172621f576fa5e4b3265f87ec20da04fd5`.
- [Issue #7](https://github.com/karaposu/tgdata/issues/7) is open.
- Its GitHub pipeline block still describes the pre-pause resume point. This
  local pause record takes precedence; no handoff was published during the pause.
- [PR #16](https://github.com/karaposu/tgdata/pull/16) is open and draft.
  Nothing from #7 has been merged.
- Working tree was clean before writing this handoff. No runtime corrections
  were made during re-planning or the pause.

Revision 3 is a saved proposal, not an accepted fix. It has not received its
new plan critique, been folded into revision 4, or been implemented. The user
has paused the approach; reconsider it with the user when work resumes.

## Why the PR was rejected

The fresh review in [pr-critic.md](pr-critic.md), committed in `87d15b4` and
[posted on the PR](https://github.com/karaposu/tgdata/pull/16#issuecomment-6001567085),
reproduced two Medium findings and one Low:

1. Exhausted temporary Telegram failures can become invalid-reference or
   generic errors because of the SDK retry policy and broad resolution catches.
2. Health events can use a freshly verified account while the public summary
   attributes the same denial to a stale cached account ID.
3. The concurrency regression does not force requests to overlap. A separate
   review probe did force overlap and passed, but the product test needs it.

## Where the evidence is

- [plan.md](plan.md): revision 3, checkpoint `8a43d23`.
- [desc.md](desc.md): current task contract and context record.
- [replan-context.md](replan-context.md) and
  [replan-r3-probes.py](replan-r3-probes.py): checkpoint `4daf873`.
- [pr-critic-probes.py](pr-critic-probes.py): reproduced review findings.
- [implementation.md](implementation.md), [verification.md](verification.md),
  [merge-check.md](merge-check.md), and [publication.md](publication.md):
  implementation, validation and publication history.
- [model-verification.md](model-verification.md): recorded §9 evidence.
- `archive/round-1/`: preserved first plan, plan critic, review and related
  records. The old `critic.md` and `dynamic_critic_prompt.md` were deliberately
  moved there; do not reuse them as the critique of revision 3.
- `traverse/`: completed original design exploration and conclusion.

Historical validation: 151 offline test groups passed and 3 live checks were
skipped across suites 12–20 on Telethon 1.45.0 / Python 3.11.10. These results
preceded the rejecting PR probes; they do not establish acceptance. The
revision 3 experiments produced six passes and one observation about the SDK
error policy and existing self lookup. They do not validate the proposed
health ownership design. Durable scripts and reports are on the branch;
temporary logs under `/private/tmp/` must not be the only evidence relied on.

## Only after the user asks to resume

1. Read this handoff and any intervening changes, then confirm which approach
   the user wants to pursue. Read `CONTRIBUTING.md`, the task documents, and
   the actual branch/issue/PR state before proceeding.
2. If continuing revision 3, the saved procedural next step is a fresh
   `critic-d` plan review, followed by a selected fold to revision 4 before
   runtime edits. The proposed ownership refactor is not yet approved by review.
3. Implement and verify the accepted plan, then refresh the merge check and
   run a fresh PR critique on the same PR #16.
4. Under CONTRIBUTING §7.4, a second rejected PR review returns to description
   and traverse. Merging requires a separate user go-ahead.

Keep Telethon at 1.45.0; use `.venv/bin/python`. Do not commit `duncan/`.
Do not perform live Telegram joins or account tests without authorization.
Keep work-folder/warming records on the feature archive branch when merging
eventually. #3 live proxy testing remains deferred.

Two newly requested ideas were filed separately as parked P3 backlog items:

- [#17 — account routing and automatic recovery](https://github.com/karaposu/tgdata/issues/17).
- [#18 — group synchronization with shared, acknowledged progress](https://github.com/karaposu/tgdata/issues/18).

Capturing them does not resume or expand #7. No implementation was started
for either future task.
