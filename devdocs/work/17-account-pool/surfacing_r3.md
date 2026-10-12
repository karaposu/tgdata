---
model: gpt-6-astra
effort: max
---
# Surfacing — #17 revision-3 preparation

## User Input

Re-plan around the completed operation/observation contract, then run a small
real-component prebuild. Scope: the existing #17 issue and branch.

## Reception

Artifact case; signal-first; bounded pool/source/state/progress/health and relevant
current-dev integration. Three traversal cycles: prior findings, complete source/
consumer implementations, current-dev difference and owned prebuild evidence.

## Traversal Trace

| # | Region | Identifier | Relevance | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | History | `devdocs/work/17-account-pool/pr-critic.md` | core | HIGH | filesystem: 2026-10-12T19:50:24.305078+00:00 |
| 2 | Design | `devdocs/inquiries/2026-10-12_19-42__17-account-pool-foundations/finding.md` | core | HIGH | filesystem: 2026-10-12T19:50:32.852159+00:00 |
| 3 | Source | `tgdata/pool_source.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.357069+00:00 |
| 4 | Controller | `tgdata/account_pool.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.347687+00:00 |
| 5 | Health | `tgdata/health.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.351936+00:00 |
| 6 | Permission | `tgdata/pool_state.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.357544+00:00 |
| 7 | Progress | `tgdata/progress_facade.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.358386+00:00 |
| 8 | Batch | `tgdata/batch_engine.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.349407+00:00 |
| 9 | SDK fixtures | `tgdata/smoke_tests/test_31_account_pool.py` | core | HIGH | filesystem: 2026-10-12T19:50:24.370022+00:00 |
| 10 | Example | `examples/account_pool.py` | sub | HIGH | filesystem: 2026-10-12T19:50:24.343130+00:00 |
| 11 | Public contract | `docs/account_pool.md` | core | HIGH | filesystem: 2026-10-12T19:50:24.334949+00:00 |
| 12 | Current-dev integration | `git:68f6bbd..2ddb852 source diff and merge-tree preview` | core | HIGH | none: null |

## State Summary

Territory/purpose: the twelve named regions, to establish re-plan reach and test
composition. Coverage: first eleven confirmed at full-file resolution; Git region
confirmed for exact changed interfaces and merge preview. Earlier inquiry's wider
history/progress evidence is retained and linked, not claimed newly re-read wholesale.
Confirmed-absent: PROJECT_SPECIFICS.md searched in tracked/workspace inventory; no
project card found. Existing README/suite runners supply actual commands.
Concept names/provenance: source outcome(3), operation ownership(4), passive health
observations(5), attempt permission(6), delivery progress(7), private batch options
(8/12). All vocabulary/structural references; no new concept coined by surfacing.
Recency distribution: one item per region; eleven filesystem timestamps (newest=
oldest per row), one no-mtime item; counts12/11/1. Mtime never filters relevance.
Workspace populated:true, all named content in context. Frontier: candidate combined
behavior is not yet proven; current-dev conflict needs the declared union resolution
inside the isolated prebuild export. No additional code territory blocks planning.

## Telemetry

Three cycles; twelve entries, core11/sub1; bounded traversal converged. Operational
and identity failure modes checked, including desync/overstep/recency bias; none.
Manual required structure10/10 PASS; structural checker absent. **PROCEED.**
