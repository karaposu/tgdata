# Backfill run lifecycle — issue #19

**Stages 1–2 are built; Stage 2 is verified offline. Gate A is BLOCKED and unrun.**
Stage 2 adds durable run identity, strict state, start/retry/reopen/status and the
opt-in Gate A instrument. Stages 3–8 remain pending. Source preparation, acknowledgment,
completion, controls, recovery and the public facade are not implemented for this lifecycle.

This branch starts from dev `45bab71` and incorporates #18 through `e9b5154` in
feature-only merge `5d0789e`. This does not merge or approve #18 into dev. Stage 2
product code/tests/public docs are committed in `1425fd7`.

- [Contract](contract.md): operations, identity, retry/conflict/durability and state rules.
- [Assumptions](assumptions.md): what is selected, observed or still unverified.
- [Acceptance matrix](acceptance-matrix.md): 44 cases with scoped Stage 2 local evidence.
- [Live validation](live-validation.md): existing group, read-only, mandatory Gates A–D.
- [Staged plan](staged-plan.md): the whole feature's eight stages and four gates.
- [Stage 1 implementation](stage-1-contract/implementation.md) and
  [verification](stage-1-contract/verification.md): scoped pipeline and test receipts.
- [Stage 2 implementation](stage-2-state/implementation.md) and
  [verification](stage-2-state/verification.md): 198 offline test groups, 3 explicit
  live skips and 9 offline instrument checks.
- [Stage 2 usage](../../../docs/backfill_state.md) and
  [probe usage](stage-2-state/probe-usage.md).
- [Gate A report](validation/gate-a.md): missing inputs, evidence limits and resumption.

[Issue #19](https://github.com/karaposu/tgdata/issues/19) tracks this lifecycle slice of
#18. Next: qualify the selected existing account/group, independent oracle and bounded
source allowance, then execute/review Gate A. Stage 3 cannot start until Gate A passes.
No real account/config was accessed and no Telegram traffic occurred in Stage 2 verification.
