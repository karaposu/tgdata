---
model: gpt-6-astra
effort: max
---
# #19 Stage 3 triage

**Weight:** feature-heavy.
**Surfaced:** immutable intent and PrepareContext, durable attempt admission,
owned pending MessageBatch, scoped DeliveryRef, media verification, atomic receipt
settlement, backend uncertainty, cancellation/error causality and source accounting.
**Why heavy:** a source read, local artifact custody and external receiver acceptance
are distinct boundaries; a mistaken retry can skip or replace data without a visible error.
**Watch for:** reading before a confirmed admission, stale control/cursor reuse,
returning an uncommitted prefix, losing it on a CAS race, bare-hash cross-run ack,
media-dependent acknowledgment, disguised local health verdicts and unimplemented
pacing silently authorizing more source work.

## Warmth and adopted meaning

Warm at `8023adf`: retained same-session architecture/full facade/SDK context and
completed live Gate A, plus refreshed complete lifecycle, CAS, raw batch/media,
health, budget and state-test source. The archive summaries need no structural refresh.
Current GPT 6 Astra / max was verified in session metadata. The settled lifecycle
traverse and reviewed Stage 1 contract are adopted; implementation within that shape
does not need another traverse unless critique exposes a new meaning gap.

## Scope and sequencing

Add internal prepare/replay/ack on the existing opaque CAS aggregate, not another
persistence format or a wrapper around sync_group. Keep MessageBatch v1 unchanged.
The codec already requires end evidence/pacing alongside final pending work and a
terminal fact when exhaustion is fulfilled; honor that minimal invariant closure here.
Stage 4 still owns its dedicated completion/uncertain-write review and fault matrix.
Stage 5 still owns positive timing eligibility and explicit recovery: fail closed for
another positive-pause source turn after settlement, while retaining local replay/ack.
Repeated zero-pause turns remain bounded by the existing actual-send budget adapter.

Gate A is the completed entry barrier. Gate B remains after Stage 4 and cannot be
passed from this stage's offline suite. New tests use real SQLite and real SDK/batch/
media components with deliberately synthetic transport; no claim of new live coverage.
No public facade, controls, scheduler, account routing, #7/duncan, PR or protected merge.
