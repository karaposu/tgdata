---
model: gpt-6-astra
effort: max
---
# #19 Stage 2 triage

**Weight:** feature-heavy.
**Surfaced:** exact-text CAS, typed run identity, persisted query/creation input,
strict state codec, current/prior run recognition, backend uncertainty, status privacy,
SDK send/page paths, fixture provenance and the mandatory live validation barrier.
**Why heavy:** durable records and retry identity meet across process boundaries;
malformed state can silently misattribute progress. The live probe touches a real account.
**Watch for:** new/retry confusion, stale predecessor, accepting corrupt nested data,
clock reads during recognized retry, post-commit errors mistaken for rollback,
accidentally wiring future lifecycle actions, and a synthetic-only Gate A PASS.

## Warmth and adopted meaning

Same-session Stage 1 inquiry/contract context and refreshed complete storage/window/
batch interfaces, installed SDK request/iterator source and repository process.
Warm baseline is prerequisite merge `5d0789e`; product diff against #18 `e9b5154`
was empty before Stage 2. Retained earlier full facade, budgets, media and smoke-test
reads remain applicable; no redundant archaeology refresh. Active gpt-6-astra/max.
Adopt Stage 1's reviewed contract; no new traverse unless critique finds a meaning gap.

## Selected boundary

Build types/codec, storage-only start/status and opt-in Gate A instrument/tests.
No preparation/ack/control/recovery runtime or public TgData facade yet; those retain
their later stages. Slot fixtures can exercise codec/successor validation without
claiming lifecycle transitions have been built. Runtime state must remain strict.
Stage 2 implementation/offline verification can complete independently of live access.
Gate A cannot pass until its selected existing-group/read-only evidence exists, and
Stage 3 cannot start without that pass. No unrelated fixes, duncan, #7 or protected merge.
