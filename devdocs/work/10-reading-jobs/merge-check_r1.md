---
model: gpt-6-astra
effort: max
---
# Merge check — #10 reading worker

**Fidelity gate: PASS — proceed to PR and fresh PR critique.**
2026-10-12. Reviewed product `6ee146c`, branch snapshot `77734d7`, against freshly
fetched dev `68f6bbda33aeb1963b96b3c719d8f23938fa4449`. Dev has not moved.
This is the plan/diff check required by CONTRIBUTING7.1, not a soundness verdict
or merge authorization. The user now explicitly requested PR publication/review.

## Warmth, weight and model

Same session as implementation and #17 review. Re-read the full changed product
files, revision2 plan, desc, triage, selected planning findings and retained
verification; refreshed relevant factory/owned operation/health/batch interfaces.
The warmed base and all10 checked pipeline checkpoints are branch ancestors.
No subagent review. Feature-heavy triage matches issue labels enhancement/heavy.

**§9 checked:** current turn metadata at `2026-10-12T05:32:12.915Z` records
`gpt-6-astra`, effort `max`; this meets the feature gate's Astra/xhigh requirement.
This is observed metadata, not a guessed model name or an unresolved user question.

## Diff against the surfaced work

Exactly13 product files changed. `worker_protocol.py`, `worker_engine.py` and
`worker.py` implement the protocol/inventory/source/process surfaces. Three existing
files carry narrow private seams: account_operation, connection_engine and
batch_engine. Setup adds a console entry point. Two smoke suites, their README,
public README/docs/worker and the caller example complete the product.

All lie in triage's process/source/ownership/packaging/test/docs territory. No
unrelated product path, duncan, session file, policy database or original checkout
edit is included. Eleven existing facade/health/group/allowance/session/batch/progress
modules are byte-identical to dev. No code from #17's unmerged pool is present.
Product paths are unchanged since implementation commit `6ee146c`.

## Plan fidelity and deviations

1. **Protocol:** four allowlisted verbs, finite versioned frames, canonical IDs,
   fixed parameter validation, increasing consumed IDs and sanitized errors exist.
   Batch documents remain unchanged; health/group/error identifiers are projected.
2. **Source:** existing expected-account/health contexts wrap reads and group APIs.
   The new optional BatchEngine resolver is worker-specific. Private cleanup
   failure receipt is recorded before logging/caller cancellation and stops admission.
3. **Process:** one loop/job/output writer; source-free ready; existing ledger
   policy checks; raw stdout; EOF/error/signal handling; module/console entry points.
4. **Qualification:** actual SDK/SQLite and subprocess test groups implement the
   planned histories. Existing smoke tests remain intact. Coverage is evidence for
   the cases exercised, not proof that the subsequent critic can find no gap.
5. **Public docs/example:** manifest and four request forms, exact IDs, partial
   batches, uncertain completion, stores, limits and exit behavior are documented.
6. **Verification:** retained24-suite result612 actual passes/3 live skips,
   compile/3.7 grammar and isolated installed module/console/demo qualification.
7. **Commits:** product6ee146c is separate from work/evidence6c60832 and archived
   whitespace77734d7. Issue status is backed by those committed artifacts.

Named implementation refinements: 8 KiB per collected health event; count all
discarded unpublished events on encoding failure; cancel/gather remaining owned-loop
tasks after failed native disconnect. All are disclosed in the product commit and
implementation.md and complete the plan's existing bounds/teardown responsibilities.
The offline caller demo deliberately uses no accounts and proves ready/refusal/EOF;
source proof is in the SDK tests. Reference-only media was already the selected scope.

One small unrecorded signature drift: the dataclass WorkerAccount accepts optional
session_store/label positionally, whereas the plan sketched them keyword-only.
The documented keyword calls work and validation/ownership semantics are unchanged;
this broadens the trusted constructor's accepted calling form. Record it here rather
than silently claiming an exact signature match. It is not a reason to introduce a
new constructor solely for formatting fidelity in this review pass.

The plan's architecture still describes the implementation: explicit accounts,
temporary verified clients, existing policies and caller-owned scheduling/delivery.
No structural deviation or unclosed planning blocker found by this fidelity pass.

## Every planning finding

- **Risk1 / Medium — unbounded legacy resolution:** worker `_read` uses merged
  group parsing/resolution and a checked InputPeer, refusing absent peers without
  scanning dialogs. BatchEngine's default get_entity/dialog-fallback AST is identical
  to dev. Original prebuild7 source histories and current test37 cover bounded worker
  reads/refusals, wrong ownership, partial wait and canonical ID matching.
- **Risk2 / Medium — buffered output survives stop:** CLI unwraps raw output and
  uses write-all without teardown flush. Actual test38 exercises broken-reader exit3
  and SIGINT/SIGTERM under backpressure without draining the still-open output pipe.
- No High or Low planning findings remain to account for. Both selected robust
  remedies were folded after the required prebuild passed, before runtime edits.

## Evidence reviewed and refreshed

`probes/merge_fidelity.py` records13 product paths,10 ancestry checks,11 unchanged
foundations and an unchanged default BatchEngine resolution AST. A probe-only wrong
module name was corrected from group_join to the actual join_client; its initial
failure is retained in merge_fidelity-fixture.txt. No product or expectation changed.

Fresh runs: **test37 25/25; test38 14/14**, under the same Python3.11.10/Telethon1.45.0
runtime. Logs: probes/merge_test37.txt and merge_test38.txt. The prior full612-pass
record remains applicable to identical product code/current dev; it was inspected,
not represented as rerun today. Full branch whitespace passes. No Telegram sockets,
login, live joins or budget changes outside owned synthetic test directories.

## Issue truth and publication

Issue10 is open. T/0/1/2/3/4/5 are checked with committed evidence;6/7 were correctly
pending at entry. Implementation's old “no PR in this run” boundary describes that
completed run; today's user instruction authorizes these review/publication steps.
Update6 only after this committed check and PR publication, and7 only from the fresh
critique's actual result. Keep live qualification separate from offline success.

PR must target dev and say Closes #10. Per7.6, the eventual approved merge must
exclude devdocs/work/10-reading-jobs; those documents stay on the archived branch.
Keep #17's draft rejection/re-plan independent. No merge in this task.
