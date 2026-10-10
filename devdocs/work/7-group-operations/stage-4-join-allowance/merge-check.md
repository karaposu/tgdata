---
model: gpt-6-astra
effort: max
---
# #7 Stage 4 merge check

**Fidelity gate: PASS.** Reviewed product `de1f758`, preparation/evidence head
`fb1194d`, against current remote dev `1ce39d5c90df399d57b4935cef353762c77cc537`.
Remote dev was fetched at this check and remains the warm-up/base commit.
This is §7.1 fidelity, not the fresh PR soundness verdict or merge authorization.

## 0 — Warmth, weight and provenance

The description records retained same-session context from Stages1–3 at1ce39d5,
with read/storage/ownership/health refreshes. `git merge-base --is-ancestor` confirms
that commit is an ancestor. Triage exists at11dbde1, weighs this feature-heavy,
and matches #7's enhancement/heavy labels. The required contract traverse concluded
at a5305f6 before description/plan. No archaeology refresh is claimed.

**§9 verified:** the current matching session turn_context at
`2026-10-10T19:41:40.206Z` records `model=gpt-6-astra`, `effort=max` and the original
project cwd. The same thread's earlier implementation contexts also record Astra/max.
Source is the thread's actual local session JSONL, inspected through a narrow
model/effort/timestamp extraction, not an assumed config default or selector UI.
Max meets/exceeds the feature path's Astra xhigh requirement; that comparison is
explicitly the interpretation used here. Frontmatter agrees. Both review gates run
in this warmed session, never in a subagent.

## 0b — Scope against triage

Six product paths change: tgdata/join_budget.py, tgdata/__init__.py,
tgdata/smoke_tests/test_35_join_budget.py, tgdata/smoke_tests/README.md, README.md,
docs/join_budget.md. The exact new test/contract paths were fixed during planning;
triage had already surfaced the allowance, public API, testing and documentation
concepts. These additions do not reveal a new subsystem or change the heavy weight.

The rest of the diff is this stage's work folder: input, triage, full inquiry,
description, plan, critic, probes and evidence. No unrelated original-checkout file,
duncan, guide, other stage, archaeology, process document or dependency change is
present. No account/health/client/budget/group-operation runtime file changes.

## 1 — Implementation fidelity

| Planned step | Actual delivery / evidence | Assessment |
|---|---|---|
| 1 Local values/errors | Frozen JoinBudgetStatus, fresh dict, six exports, validated ints/epochs, context-suppressed errors; explicit cancellation branches | Matches |
| 2 Persistent custody | Existing-file mode except explicit provision; exact owned schema descriptors, orphan checks, IMMEDIATE transaction, FULL sync, type-only storage errors and cleanup precedence | Matches |
| 3 Policy/status/claim | Validate old state before clock/prune, monotonic per-account observation, preserved claims on configure, correct cap-reduction expiry, denial after maintenance commit, one inserted unit per successful claim | Matches |
| 4 Qualification |35 actual SQLite/process test groups, independent process barriers, before/after commit exits, real delegated faults, cancellation/health checks | Matches |
| 5 Consumer docs/exports | Standalone public ledger and contract; explicitly no TgData guard yet; future verified-account/send obligations described | Matches |
| 6 Delivery evidence | Product de1f758, separate verification/handoff fb1194d,529 offline groups/3 live skips,3 demos,67-file compile/grammar, export without .git | Matches |

No material runtime deviation. New runtime is311 lines in one standard-library
module; the test suite is595 lines. The code checks stored times against the prior
clock, not the advanced one. It never repairs a partial namespace or refunds an
uncertain attempt. Zero limit is not unlimited. Actual exception conversion omits
raw message/path text; invalid path errors use a fixed description rather than
echoing path/conversion details, consistent with the privacy intent.

The tests and public exports were completed before final verification; the final
cancellation test uses a real claim interrupted at commit. Verification records
that strengthening transparently. No failed check was made to pass by relaxing an
expectation, and no runtime change followed verification.

## 2 — Does the plan still hold?

Yes. A standalone admitted-attempt ledger is the right scope for this stage's local
contract. ReadBudget settles message reservations and has different custody behavior;
extending it would couple different policies. The actual shared-file prebuild test
passed before implementation. Existing ownership/health foundations remain the
Stage5 source of verified identity; no stale cache authority is reintroduced here.

The delivered promise is deliberately limited: same-host cooperative storage,
accurate forward clock, no arbitrary external-edit/backup rollback detection, and
no live joining or Telegram-safe-rate assertion. Uncertain commit/close may waste
capacity but cannot return permission. The schema validation is local assurance,
not a universal database corruption detector. These limits match the inquiry and
public contract rather than being discovered excuses.

## 3 — Plan critic addressed

Only **Risk1 (Medium)** was selected: cancellation on Python3.7 can inherit Exception.
`_integer`, `_epoch`, constructor path conversion and `_now` explicitly re-raise
asyncio.CancelledError before generic conversion. Sole cleanup failure checks it
explicitly; secondary cleanup failures preserve the primary. Native cancellation,
throwing index/path/float conversions and an Exception-derived compatibility fixture
exercise those boundaries. No native Python3.7 run is falsely claimed.

Required REORDER experiment: actual ReadBudget configure/reserve/settle/reopen with
the proposed join tables, PASS3e40528 before product work. Read usage2 and join usage1
coexisted with real schema descriptors/FK enforcement. No High findings or consciously
left plan-critic Lows. The wider runtime/CI audit proposal was not selected and did
not enter this stage.

## 4 — Issue state is honest

The fetched #7 body has T,0,1,2,3,4,5 checked against actual committed artifacts:
11dbde1, a5305f6, e27879b, a136033/8d5a256,34508a7/3e40528,8d5a256,de1f758/fb1194d.
Steps6/7 remain unchecked while this check is being written. Update step6 only
after this artifact is committed and the PR/comment are published; step7 only
after its separate fresh critique is committed and posted. Parent issue remains
open for Stage5. Old PR16 is historical and is not the current branch/rejection.

## Verification at this gate and next action

Full product diff, new source/test files, public docs and stage artifacts were
read together. The worktree is clean, product bytes equal the verified de1f758 tree,
and full diff whitespace checks pass. The recorded529 offline passes,3 live skips,
3 demos and export run remain applicable because neither base nor product changed.
Fresh soundness probes belong to the next gate; they are not replaced by these counts.

Publish the Stage4 PR into dev with **Refs #7**, a scoped exception to the generic
Closes wording because this is a deliberately partial delivery and Stage5 remains.
Post this check, then run fresh critic-d on the implemented diff plus revision2
plan. Any High/Medium rejects under §7.3 and requires §7.4 re-planning, not a patch.
Do not merge in this request. A later authorized merge must exclude this work folder,
preserve dev's archaeology, verify merged code and retain the feature branch.
