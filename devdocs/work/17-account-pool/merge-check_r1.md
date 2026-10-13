---
model: gpt-6-astra
effort: max
status: PASS_OFFLINE_SCOPE_PR_CRITIC_PENDING
---
# Merge check — #17 existing-access account pool

**PASS for PR publication of the selected offline delivery.** Reviewed product
`4854464`, evidence head `67ffb2c`, against dev `68f6bbd`, confirmed unchanged on
the remote on 2026-10-11. This is the fidelity check; the PR critic and user merge
decision remain separate. Two-account live qualification is pending, as expressly
allowed by the original plan's E1/Step 9 and the user's offline-first selection.

The subject is the full 14-file product diff, not just the latest cleanup patch,
read with the parent description, triage, revision-2
`step_by_step_impl_plan.md`, selected `critic.md`, and the scoped
`retirement-rework/{triage,desc,plan,critic,verification}.md`. Current public
documentation, all new pool modules, the shared facade/batch changes, the full
1,038-line pool test suite, the example and adjacent budget/delivery boundaries
were examined. Same warmed session; no delegated review.

## 0 — Warmth, weight and model

The original description records same-session warmth at `95ed4c7`, an ancestor of
this branch. Original triage `03d02c7` weighs feature-heavy; GitHub labels are
`enhancement` and `heavy`. The original two-iteration traverse was completed at
`d1daa84`. The scoped triage `bacde95` retains that structure and records the actual
SDK retirement reproduction and current-dev integration assessment. Its decision
not to repeat traverse is explicit and appropriate for the established violation.

The retained probe verifies 19 named artifact/base commits are ancestors. Current
session metadata at `2026-10-11T11:02:04.423Z` confirms `gpt-6-astra`, effort `max`;
this satisfies CONTRIBUTING §9's feature-path Astra/xhigh minimum. No inferred
model selection or switch is claimed. Both implementation and review artifacts
record their provenance.

## 0b — Surface and scope

The 14 product paths are README, `docs/account_pool.md`, the daily/backfill guide
amendments, `examples/account_pool.py`, package exports, `account_pool.py`,
`pool_source.py`, `pool_state.py`, `progress_facade.py`, `batch_engine.py`,
`tgdata.py`, test31 and the smoke-test README. All belong to the ownership,
selection, budget, source, persistence and delivery interfaces surfaced by triage
and refined in the plan. No newly discovered product region requires reweighing;
feature-heavy was and remains appropriate.

Current #7 factory, account operations, health ownership, group operations and join
allowance/client code are byte-identical to dev, as are the read-budget and progress
engines. The first-parent integration commit contains incoming #7 files, but those
are not additions in this PR's product diff against dev. Original checkout,
untracked todo/handoff, duncan and unrelated work are outside this diff.

Work records stay on the feature archive. The later integrator must exclude
`devdocs/work` and branch archaeology changes under §7.6 while retaining dev's
existing copies. Publishing this branch does not authorize merging those records.

## 1 — Fidelity and deviations

Parent Steps 1–8 are implemented: strict values/errors and opaque CAS state;
owned SDK source with fixed expected identity and actual-send budget admission;
deterministic drain/spread and bounded attempts; scoped restrictions and explicit
unknown-attempt recovery; credential reload/cleanup; shared daily/backfill facade;
actual-composition tests; public documentation/example and verification.
Parent Step 9 is deliberately pending, not silently marked complete.

All five scoped rework steps are implemented: merge current dev, settle cleanup
and source children before releasing ownership, actual-SDK lifetime regressions,
current contract/handoff, and separate product/work commits with verification.

Explicit differences from the original blueprint:

- The obsolete base `_client_options()` hook is replaced by current dev's
  `_new_client(..., **client_options)` seam. This is specified by the scoped plan,
  keeps ordinary clients unchanged and gives controlled pool policy precedence.
- `asyncio.wait_for` is replaced by non-cancelling timeout observation plus retained
  cancel-and-join. The scoped critic reproduced the missed repeated-cancellation
  case; revision 2 names this change. The original outcome holder remains intact.
- Async context exit now distinguishes caller cancellation from ordinary secondary
  cleanup failure. This is an explicit scoped contract clarification, with real
  cleanup tests, rather than accidental swallowing of cancellation.
- Shared pool exceptions are defined with the state codec and re-exported through
  `account_pool`/the package. The public taxonomy stays as planned; colocating the
  definitions avoids a source/controller import cycle.
- Python 3.7 was checked at the grammar level on Python 3.11.10, not claimed as an
  executed native runtime. Telethon 1.45.0 is the opt-in pool's exact qualification.

No unplanned public API, new quota authority, progress protocol, automatic joining
or distributed ownership was introduced. AST comparison confirms all 10 public
progress delegators and all 36 retained TgData methods have unchanged executable
bodies. `_backfill_for` differs only by its planned factory extraction; TgData
retains its module-local factory. Constructor order includes current dev's trailing
`join_budget=None`.

## 2 — Does the plan still hold?

Yes for the selected boundary. Separate persisted source permission and existing
group delivery state preserve different responsibilities. Source-free replay/ack
does not require a healthy pool or live credentials. Unknown source attempts remain
blocked until explicit quiescent recovery; completed prefixes prevent failover.
The shared ledger remains the accounting authority. Cleanup needed a stronger
local lifetime boundary, not a replacement router or generic health framework.

The plan does not promise equal history across accounts, a scheduler, automatic
login/repair/joining, multiple competing owners or a hard shutdown deadline. Those
limits appear in the public contract. Historical text saying #7 was paused remains
historical; the current handoff and issue block state that #7 is now merged.

## 3 — Were all critic findings answered?

**Original High, completed result hidden by observer timeout:**
`pool_source.py:_OwnedSource.run` captures the original batch/error before awaited
health reporting and retrieves it after actual child settlement. The targeted
check preserves the exact FloodWait7200 plus 100-message prefix and a completed
successful batch when a callback outlasts the internal timer. No second source.

**Original Medium, repaired stored login ignored:**
`recheck_account` retires the owned client before fresh preflight and a durable
identity-only attempt. Successful retirement clears client/config/identity inside
the retained worker. Actual StoredSession replacement tests preserve the new key,
including cancellation during native disconnect; group restrictions remain.

**Scoped Medium, repeated cancellation releases a live child:**
the retained cancel-and-join holds `self.task` and the operation guard until the
real child ends. Retirement and shutdown use the same private waiting primitive
with their own outcome policies. Held-source and native-disconnect checks prove
no concurrent source/replacement, correct failure refusal/retry and cancellation
precedence. The mandatory six-group prebuild experiment preceded runtime changes.

Neither plan critic left a Low finding. Broader shared credential rotation and
generic source-observer supervision were consciously deferred, not half-built.

## 4 — Issue status and evidence

The current #17 rework block truthfully checks triage through implementation,
linking committed artifacts (`bacde95` through `67ffb2c`). It leaves merge-check/PR
and PR critique unchecked until those artifacts/publication exist. Its historical
first-delivery block is clearly labeled. Original umbrella intent is preserved;
current selected scope excludes automatic joining even though #7 now exists.

After this file commits and the PR is published, update step 6 with both links.
Leave step 7 pending until the fresh critique is committed and posted. Keep E1
pending, #17 open and the product unmerged. The PR body must say `Closes #17` as
required by §6.6, while plainly naming the scoped delivery and deferred live/joining
work; this does not itself close the issue on dev or settle those follow-ups.

Implementation evidence at `67ffb2c`: **619 actual offline checks across 23 suites,
three explicit live skips excluded**; pool46/46, four demo runs, 76 compile/grammar
checks and an export excluding work records passing pool46/46/demo. No product
change has occurred since that run, so a redundant full sweep was not substituted
for review.

Additional fidelity check run now:

```text
static_fidelity: 19 artifact ancestors; 10 unchanged dev foundations;
10 identical public progress methods; 36 retained TgData methods;
only the permitted backfill factory substitution.
original_critic_completed_outcomes: 2 passed
original_critic_credential_reload: 2 passed
rework_retirement: 2 passed
rework_source_and_shutdown: 3 passed
identity_at_admission: 1 passed
restriction_and_recovery: 2 passed
source_free_progress: 2 passed
PASS: static fidelity plus 7 behavioral groups (14 existing composition cases).
```

Runner: `merge-check-probes.py`; exact output: `merge-check-probes.txt`.
These selected existing composition cases substantiate fidelity; they are not the
fresh PR critic probes. Network sockets were forbidden and all data synthetic.

**Next:** publish the PR and run critic-d fresh against this full product diff and
both plans. This PASS is not merge approval or evidence of live failover.
