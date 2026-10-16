---
model: gpt-6-astra
effort: xhigh
---
# #45 implementation — revision 2 complete

Completed 2026-10-16 after the mandatory combined prebuild at ac51fab.
Product commit: `20c6781ae7229e36054e5c89ba5735dfb8f0f904`.
Base: dev `77f2f53eba8bdc6922127a3b9118bf17de4efabf`.

## Delivered contract

`TgData.capture_group_history` obtains reference-mode raw message content under a
freshly verified expected account. UTC-day rounds bound accepted raw slots and
logical history attempts separately, preserving empty, unvisited, incomplete and
terminal day evidence. Source errors/cancellation retain their original outcome
and attach accepted pages as a best-effort `HistoryCapture`.

`HistoryCapture.sample` is a separate pure operation. It applies normalized explicit
eligible IDs, sparse-day quota redistribution and deterministic within-day ranks.
Its selected output reports source coverage separately from intentional omissions,
including known omitted album members. Canonical captures can be retained/reloaded
for byte-identical selection replay. No selected ID has acknowledgment authority.

## Plan completion

1. Extracted `history_observation.history_page`; activity retains its projection,
   result contract and diagnostic strings. Unmodified suite46 passes35/35.
2. Added immutable `HistoryCapture`, `HistorySample`, `HistorySampleError`, strict
   canonical capture loading, bounded eligibility and finite water-filling.
3. Added day-distributed source capture with cheap initial probes when spare
   requests permit a depth pass; no-spare-call captures retain useful page sizes.
   Accepted pages are atomic, with cross-day duplicate-ID refusal.
4. Added the facade method and exports, preserving existing ownership, budget,
   heartbeat and temporary-client cleanup. No package version change.
5. Added suite47 (31 groups), `docs/history_sampling.md`, README and smoke README.
6. Targeted/full verification passed; product and work evidence are separate commits.

No plan design deviation or product correction was needed during verification.
One test-fixture construction correction is documented in verification.md.

## Scope held

Batch envelopes, progress stores, sync/backfill, album/trail assembly, connection
policy and read allowance implementations are byte-unchanged from the base.
The only existing behavior extraction is activity page validation. No new
dependency, source retry, media download, inferred trail, predicate runtime,
implicit storage, join, scheduler or distributed ownership feature was added.

Source count caps are not byte/RSS guarantees. The reload limit is an explicit
caller policy, default64MiB. Sampling is descriptive, not statistically
representative; busy days can remain partly captured. Real Telegram visibility
is not qualified by synthetic source packets.

## Next handoff

Merge check against triage/description/revision2 plan/critic and actual diff,
then product-only PR and a fresh critic-d review. No PR, merge, release or
deployment was performed by this implementation run. §9 model/effort evidence
already records gpt-6-astra/xhigh for this session.

The original checkout remains on feat/7-group-operations with only the user's
uncommitted version edit; that edit, duncan and unrelated guide changes are absent
from these commits. Continue on feat/45-history-sampling-windows, not that checkout.
