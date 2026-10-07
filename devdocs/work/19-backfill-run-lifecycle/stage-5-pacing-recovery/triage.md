---
model: gpt-6-astra
effort: max
---
# #19 Stage 5 triage

**Weight:** feature-heavy.
**Surfaced:** saved pacing/deadline; observed UTC/monotonic time; source-attempt
admission/end/cancellation; exact recovery identity and caller-proven quiescence;
CAS/lost replies; current/prior command recognition; original error/budget hints;
actual verified-account budget guard; receipt/pending/terminal invariants.
**Why heavy:** an early retry or wrong-attempt recovery can permit another read while
its predecessor is unresolved; an ack-triggered timer silently changes scheduling.
**Watch for:** conflating source failure observations with global account readiness,
UTC-only early waits, portable monotonic timestamps, refreshed retry deadlines,
recovery while a local prepare is active, blind context rebasing and false health.

## Warmth and adopted meaning

Warm at 246a187: same-session Stage 4/Gate B implementation and actual source/store/
receiver evidence retained; complete engine/values/state, budget adapter/ledger and
health paths refreshed. The SQLite/media/batch architecture is unchanged; archaeology
summaries need no refresh. Current session metadata confirms GPT 6 Astra / max.
Existing guard/hook and native #19 branch link remain. Full issue title list refreshed;
#19 is the existing scoped task, #18 its integrated foundation; no new issue needed.
Priority remains P2. Adopt the completed lifecycle traverse/Stage 1 contract; this is
implementation within that settled structure, not another architecture pass.

## Boundaries

Gate B PASS is the entry gate. Add internal pacing and recovery, preserving one opaque
aggregate and existing raw-reader ownership. Status/replay/ack remain local; saved
source failures retain actual provenance and never authorize fresh account spending.
Actual send-time verification stays in BudgetClientMixin/ReadBudget, not a new health
or account subsystem. No public facade or controls; Stage 6 and Gate C remain pending.
No live account reads or ledger changes are needed for this scoped build. Any copied
Gate B fixture remains offline and cannot clear the original unresolved evidence.
