# Backfill run lifecycle — issue #19

**Stages 1–4 are built; Gates A and B passed.**
The internal engine supports durable admission, exact pending preparation/replay,
full-context acknowledgment, qualified completion and bounded exact-state confirmation
of ambiguous writes. Stage 4 product is `b1f6495`: 255 actual offline groups passed,
with three explicit legacy live skips. Gate B passed real source/receiver/crash checks.
Positive timing/recovery, controls and the public facade retain Stages 5–7; Gates C/D
remain pending.

This branch starts from dev `45bab71` and incorporates #18 through `e9b5154` in
feature-only merge `5d0789e`. This does not merge or approve #18 into dev. Stage 2
product code/tests/public docs are committed in `1425fd7`; Stage 3 adds `3140dcd`; Stage 4 adds `b1f6495`.

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
- [Available staged usage](../../../docs/backfill_state.md) and
  [probe usage](stage-2-state/probe-usage.md).
- [Gate A report](validation/gate-a.md): seven live comparisons, two controlled
  interruptions, 23 repeated state tests and 10 instrument checks; all passed.

[Issue #19](https://github.com/karaposu/tgdata/issues/19) tracks this lifecycle slice of
#18. **Next: Stage 5 — durable pacing and explicit recovery**, then Stage 6 controls and
mandatory Gate C. No PR or merge is implied. Private Gate B records remain under
`/private/tmp/tgdata19-gate-b-live-20261007`; two deliberately unresolved attempts were
preserved. Reuse the existing Gate A account ledger, now 2202/5000 used; do not reset it.
