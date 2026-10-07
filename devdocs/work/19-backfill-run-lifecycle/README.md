# Backfill run lifecycle — issue #19

**Stages 1–5 are built; Gates A/B passed and Stage 5 is verified offline.**
The internal engine supports durable delivery, qualified completion, exact write
confirmation, per-run pacing and explicit interrupted-attempt recovery. Stage 5
product is `a180151`: 287 actual offline groups passed, with three explicit legacy
live skips. **Next: Stage 6 controls, then mandatory live Gate C.** The public facade
and Gates C/D remain pending.

This branch starts from dev `45bab71` and incorporates #18 through `e9b5154` in
feature-only merge `5d0789e`. This does not merge or approve #18 into dev. Stage 2
product code/tests/public docs are committed in `1425fd7`; Stage 3 adds `3140dcd`; Stage 4 adds `b1f6495`; Stage 5 adds `a180151`.

- [Contract](contract.md): operations, identity, retry/conflict/durability and state rules.
- [Assumptions](assumptions.md): what is selected, observed or still unverified.
- [Acceptance matrix](acceptance-matrix.md): 44 cases with scoped Stage 2/Gate A/Stage 3 evidence.
- [Live validation](live-validation.md): existing group, read-only, mandatory Gates A–D.
- [Staged plan](staged-plan.md): the whole feature's eight stages and four gates.
- [Stage 1 implementation](stage-1-contract/implementation.md) and
  [verification](stage-1-contract/verification.md): scoped pipeline and test receipts.
- [Stage 2 implementation](stage-2-state/implementation.md) and
  [verification](stage-2-state/verification.md): 198 offline test groups, 3 explicit
  live skips and 9 initial offline instrument checks; later live evidence is separate.
- [Stage 3 implementation](stage-3-delivery/implementation.md) and
  [verification](stage-3-delivery/verification.md): 41 delivery groups, 239 total actual
  offline passes, 3 live skips and 10 instrument checks.
- [Stage 4 implementation](stage-4-completion/implementation.md) and
  [verification](stage-4-completion/verification.md): exact read-back, 16 new completion
  groups, 255 total actual offline passes, 3 live skips and a passing real prebuild probe.
- [Gate B report](validation/gate-b.md): 20 sequential worker actions, 46/350-record
  independent source comparisons, actual receiver/media custody and final commit crashes.
- [Stage 5 implementation](stage-5-pacing-recovery/implementation.md) and
  [verification](stage-5-pacing-recovery/verification.md): 32 pacing/recovery groups,
  287 total actual offline passes, three live skips and actual recovery on disposable
  copies of Gate B state. This is not a live Gate C result.
- [Available staged usage](../../../docs/backfill_state.md) and
  [probe usage](stage-2-state/probe-usage.md).
- [Gate A report](validation/gate-a.md): seven live comparisons, two controlled
  interruptions, 23 repeated state tests and 10 instrument checks; all passed.

[Issue #19](https://github.com/karaposu/tgdata/issues/19) tracks this lifecycle slice of
#18. **Next: Stage 6 — pause/resume/cancel, concurrent settlement, abandonment and
successors**, then mandatory Gate C. No PR or merge is implied. Private Gate B records
remain under `/private/tmp/tgdata19-gate-b-live-20261007`; both original unknown attempts
remain unresolved. Stage 5 tested only disposable copies and made no Telegram calls.
Reuse the existing Gate A ledger for later live work; its last Gate B usage was 2202/5000.
