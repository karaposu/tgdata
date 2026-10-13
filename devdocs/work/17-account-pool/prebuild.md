---
model: gpt-6-astra
effort: max
status: PASS
plan_revision_tested: 6
folded_plan_revision: 7
---
# Public outcome ownership prebuild — full combined gate passed

**P0 PASS,2026-10-13.** One complete attempt passed **750 executed offline test groups**,
**three offline demos**, and the separate unchanged-product negative controls. Three
explicit legacy live skips are excluded. No watchdog fired. The candidate and probes
stayed byte-identical during execution, and branch production stayed unchanged.

The result resolves the experiment in critic.md. Its one selected Medium correction
is folded into plan revision7. Production implementation remains pending; this run
was authorized for plan/critique/prebuild only. PR26 stays draft/rejected on a63099e.

> Implementation follow-up: product007c2e4 now carries the qualified mechanism;
> [actual-branch verification](verification_outcomes.md) passed separately. This P0
> report remains the preimplementation record. Its export script checks baseline
> equality, so reproduce P0 from preparation commit9772541 in an isolated checkout;
> use probes/outcome/verify.py for the current implemented branch.

## Exact subject and representation

Source baseline: f1cae2c (production a63099e), containing dev
2ddb852d917998d003f9db863fce09a92e9c5712, verified current before P0 and unchanged afterward. The export has
no .git directory and was created under /private/tmp/tgdata17-outcome-prebuild-b_vrcnwb.
Runtime: Python3.11.10 / Telethon1.45.0; real SDK client/iterators/disconnect, ReadBudget,
SQLite account/progress stores, raw batches and daily/backfill engines.

The candidate implements the whole proposed interaction, not the prior inquiry's
exit-only capture adapter:

- Public single-use PoolReadCapture and immutable PoolReadSnapshot.
- A private invocation completion Future; the caller Task is only a stop address.
- Early retention of BatchEngine's actual validated complete-record buffer, including
  completed media before a later download blocks. Snapshots materialize locally;
  there is no whole-prefix copy per appended record.
- Required capture arguments at the four public pool data methods; one private writer
  crosses the source and progress engines without rebinding or global context storage.
- Per-attempt metadata reset from selected Risk1, verified identity attachment, stable
  finalization and bounded error type facts, without retaining exception/task graphs.

Eight candidate runtime modules change: new pool_result plus account_pool,
pool_lifecycle, pool_source, batch_engine, sync_engine, backfill_engine and exports.
The shared optional seams leave ordinary TgData/#7/#10 behavior unchanged in the
executed regressions. Three existing pool fixture files and the pool demo are migrated
to required capture inputs. Their322 existing assert statements remain structurally
identical after removing only the added capture keyword. The migration supplies input;
it does not supply result data or change expected outcomes.

No real login, Telegram traffic, joining, budget reset or product patch occurred.
Synthetic wire stimulates the actual SDK. Providers used in faults delegate actual
SQLite writes before/after controlled interruptions. Their committed state is inspected
separately from returned signals and available data. The proxy suite uses only a local
refusing relay with an explicitly nonexistent live configuration.

## Full attempt2 results

| Executed component | Result |
|---|---|
| All26 supported offline suites12–19 and22–39 | 725 executed groups PASS;3 live skips excluded |
| New explicit public ownership suite | 17 groups PASS, with parameterized histories |
| Retained fresh PR-round2 soundness controls | 8 groups PASS; old assertion oracles unchanged |
| Pool lifecycle within the26 suites | 48/48 PASS |
| Full pool feature suite within the26 | 46/46 PASS |
| Worker source/process suites within the26 | 33/33 and25/25 PASS |
| Pool, daily-continuation and backfill demos | 3/3 PASS |
| Original-product negative controls | Expected wrapper loss and app-lifetime wait reproduced; retained regression controls PASS |
| Candidate Python compilation /3.7 grammar | 87 files PASS; not native3.7 execution |
| Candidate/probe stability and branch production equality | PASS |

The new17 groups cover required binding and reuse, prestart/queued stop, concurrent
binding, four public data methods, early pagination, 32 settlement-stop combinations,
16 wrapper histories, application continuation, stale stop, progress publication after
close, paired account/group faults, exact receipt/replay, attempt provenance, monitor
finalization, early media, retention/empty results, provider refusals, local wait/paused
states and diagnostic bounds. Every case uses actual records and separately observes
signal, charge and durable facts. Group counts are not claimed to be individual RPCs
or independent architectural proofs.

The important observations are:

- A real100-record prefix is visible while a later real SDK page is pending. It survives
  genuine cancellation with charge200 and an unresolved account attempt, without a
  second-account read or a fabricated group receipt.
- Completed source data is visible before held account/progress writes finish. Before
  and after actual commits produce the correct distinct token/wait/pending facts.
- shield/gather/timeout and late/repeated waiters can replace signals without consuming
  the caller's capture. The actual Task remains cancelled where cancellation is required.
- Pool close can finish native retirement while an application catches cancellation
  and waits for that close before continuing unrelated cleanup. No whole-Task join.
- Daily/backfill publication can remain running after close; the capture stays running
  until its public call ends, and real pending delivery remains a separate store fact.
- Interrupted captured hashes cannot substitute for the actual full/end pending receipt.
  Real local replay/ack after close works with removed credentials and forbidden pool
  state/budget access. Replay's capture has no invented verified account.
- First-account failure does not contaminate the second account's batch metadata.
  Actual identity refusal produces no batch, no account label and no source read.
- An incomplete media record is excluded while a previous real downloaded blob and
  complete record remain available. Terminal captures retain only plain state and one
  immutable batch, with bounded error names and no private error messages.

## Attempts and corrections

Candidate construction initially stopped on an ambiguous text marker in __init__.py;
the export builder matched both the module comment and an indented export-list comment.
Narrowing the marker and rebuilding a fresh export was a local construction correction.
No behavioural test ran and no runtime design changed. The first builder is preserved.

Full attempt1 passed all14 then-authored new groups, prior review8, other existing suites
and demos, but the proxy suite could not bind127.0.0.1 under the filesystem/network
sandbox. Attempt1 is **FAIL**, not waived. Local-only loopback permission was obtained
through the execution sandbox and the entire combined command was rerun.

The coverage audit also added explicit recipient assertions for provider refusal,
local wait/paused results and bounded diagnostic type names. Its media stimulus was
strengthened to retain a real completed download before the next blocked download.
Candidate runtime and all prior semantic expectations stayed unchanged. Exact attempt1
probe sources and both full attempt logs/manifests remain available. Attempt2 passed
all17 new groups with all regressions in the same run; no targeted-result stitching.

## Reproduce and inspect

From this branch, with the existing Telethon1.45 environment:

```bash
python devdocs/work/17-account-pool/probes/outcome/export.py
python devdocs/work/17-account-pool/probes/outcome/build.py
python devdocs/work/17-account-pool/probes/outcome/run.py
```

The last command needs local loopback bind/connect permission for test12; live cases
remain skipped. Parent watchdogs bound child processes; killed processes cannot pass.
The runner uses fresh per-process temporary state and records every command/output.

- [Full combined report](evidence/outcome/attempt-2/summary.json)
- [New ownership histories](evidence/outcome/attempt-2/outcome_cases.txt)
- [Earlier PR controls](evidence/outcome/attempt-2/prior_review_controls.txt)
- [Baseline negative controls](evidence/outcome/attempt-2/baseline_negative_controls.txt)
- [Candidate hashes and unchanged assertion counts](evidence/outcome/candidate-manifest.json)
- [Baseline tree/hashes](evidence/outcome/export-manifest.json)
- [Readable isolated candidate diff](evidence/outcome/candidate.patch)
- [Construction/environment/coverage notes](evidence/outcome/preparation-corrections.md)

## Limits and next gate

P0 supports implementing folded plan revision7; it is not already that implementation
on the feature branch, a new PR approval, or live qualification. Promote the tested
mechanism under the plan, add permanent suite40 and public documentation, then verify
the actual branch and renew both merge gates. If the candidate or dev composition
changes materially, qualify that change before using this report. E1 remains pending
on two approved accounts/shared group/existing allowance. No native3.7 runtime claim.
