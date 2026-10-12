---
model: gpt-6-astra
effort: max
revision: 4
---
# Triage — #17 whole-operation restart

**Weight:** feature-heavy. **Branch:** feat/17-account-pool. **Issue:** #17 / draft PR26.
**Baseline:**09e0277 (runtime71502e5/4854464); **current dev:**2ddb852.
**Surfaced:** [restart trace](surfacing_restart.md), pool controller/source/state,
sync/backfill engines and stores/facade, batch values, health, test31 and original
prebuild, docs/example, shared batch seam and merged worker. Proposed private homes:
pool_lifecycle.py and pool_observation.py. These are proposed, not existing modules.
**Why heavy:** cancellation crosses source and three durable namespaces. A lost reply
must preserve both completed data and refusal to infer permission. Shared engines
also need to retain known batches on publication errors without inventing receipts.
**Watch for:** mistaking a component's cancellation for caller stop; releasing a live
write; treating a prefix as durable delivery; replacing simple owners with a global
supervisor; silently changing ordinary TgData cancellation or worker behavior.

Session warm by other means at ancestor09e0277, 2026-10-13: carried complete foundation
traverse/source/controller/health/state/batch/progress/fixtures/docs reads, refreshed
entire account_pool, pool_source, sync_engine, backfill_engine, sync_store and
progress_facade. Current-dev union inspected. No new architecture-skill run claimed.
All issue titles refreshed; #7/#10 merged. Existing heavy label remains correct.
One rejected PR, one failed prebuild, no PARKED block. PROJECT_SPECIFICS.md absent;
use actual README and runners. Existing repository hooks remain installed.

The latest user request authorizes a fresh description/plan, in-session critic,
real-component prebuild, fold, implementation and full offline verification.
This supersedes the earlier preparation-only endpoint. E1 two-account live access
is still unavailable; it gates later live qualification only. PR publication/review
renewal and merging are later gates. Preserve main checkout, duncan, historical
artifacts and unrelated work. No automatic joining, login or budget reset.
