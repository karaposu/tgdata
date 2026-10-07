---
model: gpt-6-astra
effort: max
---
# Stage 4 source input

Latest user request, verbatim:

> $task-impl stage 4

Interpretation: scoped Stage 4 of issue #19, then its mandatory live Gate B.
The original staged request remains in #19 and stage-1-contract/source-input.md.
Inherited requirements: existing read-only groups; one source reader per group;
Telethon 1.45.0 only; no edits/deletions or competing machines. Caller owns the
archive, scheduler, account selection and durable receiver acceptance.

Entry: feature branch feat/19-backfill-run-lifecycle at 62d5f60; Stage 3 product
3140dcd, Gate A receipt 8023adf. Stages 1–3 and Gate A are complete; Stage 4/Gate B
are pending. No PARKED block or rejected PR critic exists for this scoped folder.
Do not touch paused #7, duncan, other worktrees or protected branches.

Persistent live authorization: selected config/account from Gate A, existing groups
arenda_stambul1 and programlama_sohbet. Reuse the authoritative account ledger;
no policy reset/increase. Existing login may be reused. Receiver will be an isolated
local SQLite database with durable blob files, under the test directory.
Source reads are bounded, guarded and externally spaced; source writes remain forbidden.
