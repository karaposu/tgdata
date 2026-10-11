---
model: gpt-6-astra
effort: max
---
# #7 Stage5 — Joining through a verified account

**Session warmth:** retained Stages1–4 implementation, review and merge context at
dev `f15f1a864f07905aee1c8d679f6039fb5c898ae6`. Refreshed current group resolution,
account operation, factory/facade, owned health, read/join allowance and actual
Telethon1.45 dispatch/result/cache paths. No archaeology refresh claimed.
Triage is feature-heavy; the sequential inquiry concluded in `traverse/finding.md`.

## Problem Statement

tgdata can verify an account, look up a group and check its read access, but has
no public joining operation on dev. Callers would otherwise combine raw SDK
requests, quota admission and several possible outcomes themselves. Joining can
be acknowledged, require approval/payment/interaction, or fail with an uncertain
remote outcome. Those are different facts, not one success flag.

The old broad #7 attempt was rejected for source-error classification and account
ownership failures. Those prerequisites are now merged. Stage5 must consume them,
not revive cached identity or widen the health design again. New inquiry probes
also show that a success-like RPC error may originate in identity proof and an
Ok wrapper may contain the wrong nested payload; result classification needs both
origin and shape, not names alone.

## User Value Proposition

A caller configures a JoinBudget, names the expected account, and asks tgdata to
join a group. The library owns the temporary client's proof, admission, request
and cleanup, then returns portable account-qualified outcomes. Applications can
handle pending or external-action-required states without interpreting SDK objects
or guessing whether allowance should be refunded.

## Success Criteria

1. `TgData(..., join_budget=budget)` enables `join_group(target, *, account_id)`.
   Missing/invalid budget or missing policy fails explicitly. No automatic login,
   rate choice or ledger provisioning occurs. Existing reads retain their behavior.
2. Reuse current reference resolution, including qualified numeric peers. Existing
   membership and known payment requirements can return without a join attempt;
   unusable direct peers refuse rather than trigger guessed requests.
3. Every new SDK join enqueue re-verifies the expected account and consumes a
   synchronous committed claim immediately before sending. Changed identity,
   failed admission and cached waits do not produce an unauthorized join. Retried,
   failed, cancelled or uncertain admitted attempts are not refunded.
4. Frozen GroupJoin values distinguish joined, already_joined, requested,
   payment_required and interaction_required. The result identifies the verified
   owner/normalized target and keeps preflight metadata/unknown IDs honest.
5. Recognized RPC outcomes must belong to the exact mutation request; malformed
   payloads cannot become joined. Other source errors retain their original type
   and object. Cancellation remains cancellation.
6. No mandatory post-ack network/cache enrichment can turn acknowledgment into a
   false mutation failure. Existing teardown/notification behavior remains; joining
   alone does not assert read-access recovery.
7. Real-SDK/SQLite public-path tests cover identity, send ordering, source outcomes,
   corrupt/missing quota, cancellation, cleanup and forced overlap. Supported
   offline suites, demos and compile/grammar checks pass on Telethon1.45.0.

## Scope Boundaries

- One bounded joining consumer of merged Stages1–4. No routing, login flow,
  membership reconciliation service, generic quota framework or health rewrite.
- No automatic payment, bot/web-view interaction, bulk chat-list join or new basic
  group/community mutation method. Unsupported direct routes require an invite.
- Guarding is confined to this verified operation. Arbitrary raw SDK clients,
  private transport calls and packet-level retransmissions are outside that guard.
- Result metadata comes from preflight. Refreshed group IDs or read readiness can
  be requested through the existing lookup/access methods afterward.
- No live Telegram mutation in this implementation/verification run. Offline
  fixtures do not establish live acceptance, safe rates or every platform/runtime.
- Keep accepted Stage3/4 Lows and unrelated files outside this feature; preserve
  the original untracked files, duncan and the stray guide.
- This task-impl run ends after implementation/verification and required commits/
  issue updates. PR critique and merge are later explicit requests.

## Priority Level

**Medium (P2).** Completes the staged #7 group-operation surface and gives later
routing/worker work a qualified joining consumer without adding that work now.

## Known Blockers

None identified. Nine actual SDK/ledger probe groups established the local
composition and exposed predicates the plan must specify. Current source and
existing APIs resolve the remaining implementation choices. Live joining is a
separately authorized qualification frontier, not a hidden claim of this delivery.
