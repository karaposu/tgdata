---
model: gpt-6-astra
effort: max
---

# #7 — implementation record

Implemented the seven-step folded plan on 2026-10-05.
Runtime/public-doc/test commit: **8e245f8f1d001c30ecd561e173e8742302cc313d**.
Base: dev at **45bab7172621f576fa5e4b3265f87ec20da04fd5**.
Branch: `feat/7-group-operations` (native issue #7 link).

## What exists

- `group_operations.py`: safe target parser; immutable portable metadata,
  lookup/access/join values; shared resolution, bounded history and join outcomes.
- `join_budget.py`: independent rolling24h SQLite attempt ledger with explicit
  per-account policy, atomic claims, status, clock floor and local error types.
- `join_client.py`: actual-send guard for both supported join requests, SDK retries,
  wrappers/batches and fresh account authority. The existing factory carries it.
- `TgData`: lookup_group, check_group_access, join_group and get_join_budget,
  each using one existing ephemeral client when work is required.
- `health.py`: default-preserving group-proof control and opt-in task-local account
  identity. Fresh read/join identity helpers update only opted-in calls.
- `test_20_group_operations.py`: 25 offline behavioral groups. Public docs explain
  the contracts, allowance, errors and limits. Package dependency declarations
  now require Telethon>=1.45.0,<2.0; actual verification used exactly1.45.0.

## Selected critic mitigations

Risk1 robust: acknowledged status survives missing update metadata, actual nested
SQLiteSession cache failure, and even a failing warning handler. Auxiliary errors
never become Telegram health; no post-ack network request is made.

Risk2 robust: parsing/cache/conversion failures have local provenance; access only
turns an actual outer Telegram group-access error into denied. Native local/transport
errors at the new facade preserve their exception object/traceback and explicit
cause while suppressing incidental context from the caller's unrelated RPC handler.

Risk3 robust: ephemeral calls start with unknown event account identity, acquire
fresh self identity and carry it in their own task context. Each admitted send
refreshes identity; concurrent calls and callback reentry do not share an override.

## Verification corrections and implementation clarifications

These preserve the plan's contract and architecture; no failure was hidden by
weakening an expected result.

1. The first test20 run passed21/24. Two failures shared one implementation bug:
   `session.get_input_entity(PeerChat(id))` can construct an input peer without a
   stored row. Add an exact marked `get_entity_rows_by_id` check first. Missing
   and ambiguous numeric IDs now fail locally before group lookup. This is a
   corrected SDK helper use within the already-planned known-cache boundary.
2. The third failure was a fixture mistake: a status check opened default test
   account111 while only account222 was configured. Supply Sender(222) for that
   check; the expected fresh-account status remains unchanged. The rerun passed24/24.
3. Empty peer responses can make SDK get_entity raise native KeyError. Include
   that missing-result case in local resolution translation and test it.
4. Test a transport error raised inside an unrelated RPC handler. The new facade
   suppresses only implicit context for non-RPC exceptions, retaining explicit
   causes and the original object. This completes selected Risk2 without changing
   the existing global health classifier.
5. Set the exclusively owned ephemeral client's flood threshold to zero after
   authorization. This makes nested SDK identity/entity calls honor the planned
   immediate-wait behavior while leaving authorization's existing behavior intact.
6. Protect optional post-ack warning emission from caller logging-handler errors.
   Add a fault-injection check; acknowledgment and retained allowance survive.
   Final new-suite size25 groups, all passed.
7. Raise package/requirements SDK minimum to1.45.0 because the imported wrapped
   join result types are used at runtime. This is a dependency declaration fix
   for the user's selected SDK, with no old-version compatibility work. The
   existing <2.0 major-version boundary remains. Update plan step6 accordingly.

## Scope and state

No live Telegram calls or joins. No duncan files in the implementation commit.
No old-SDK work, proxy issue #3 testing, worker, account-login or payment/webview
execution. GroupInfo/discovery behavior and read-budget schema remain unchanged.
All supported offline suites pass; see verification.md for exact counts and skips.

Implementation/pipeline step5 is complete. Merge check, PR creation and fresh PR
critic (CONTRIBUTING steps6–7) have not run for #7. Merge remains separately
user-authorized. Exact active model/effort were not exposed: artifacts record
unknown and the later merge check must flag CONTRIBUTING §9 honestly.
