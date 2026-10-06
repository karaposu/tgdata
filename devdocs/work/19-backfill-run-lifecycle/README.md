# Backfill run lifecycle — issue #19

**Stage 1 is complete: the contract and validation specification.** The runtime in
Stages 2–8 is not implemented here. This branch starts from dev `45bab71`; it does not
contain #18's unmerged daily/fixed-window runtime prerequisites.

- [Contract](contract.md): operations, identity, retry/conflict/durability and state rules.
- [Assumptions](assumptions.md): what is selected, observed or still unverified.
- [Acceptance matrix](acceptance-matrix.md): 44 future runtime cases, all UNRUN.
- [Live validation](live-validation.md): existing group, read-only, mandatory Gates A–D.
- [Staged plan](staged-plan.md): the whole feature's eight stages and four gates.
- [Stage 1 implementation](stage-1-contract/implementation.md) and
  [verification](stage-1-contract/verification.md): scoped pipeline and test receipts.

[Issue #19](https://github.com/karaposu/tgdata/issues/19) tracks this lifecycle slice of
#18. Later code work needs its prerequisite base and a separately selected Stage 2.
Do not mark live gates or later stages complete from these specification documents.
