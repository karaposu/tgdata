---
model: gpt-6-astra
effort: max
status: PASS
gate: B
---
# Gate B — delivery, completion and restart

**Verdict: PASS — Stage 5 may begin.** All Gate B requirements in the staged plan
and live-validation §6 have evidence. This does not implement Stage 5 or authorize
PR/merge. The full feature remains in progress; controls/recovery and Gates C/D are pending.

## Revision, environment and evidence

- Product: `b1f6495099f72fb9a49d56d3cc5acef62e8ae82e`, imported from
  `/private/tmp/tgdata-19-backfill-run-lifecycle`. No uncommitted product edits.
- Date: 2026-10-07, actual Gate B RPC interval 10:26:20.970769–10:29:29.316992 UTC.
  Python 3.11.10; Telethon **1.45.0** only. Python 3.7 grammar was checked separately,
  not executed as a supported-runtime claim.
- Same user-approved account/config/session and unchanged 5,000-read authoritative
  budget as Gate A. Each live worker verified the actual self identity. Credentials,
  session files and account identifiers are excluded from the published evidence.
- Existing read-only sources: `arenda_stambul1` (`-1004478311025`) and
  `programlama_sohbet` (`-1001139574198`), selected by the user in this session.
- [Structured observations](gate-b-evidence/observations.json), [evidence guide](gate-b-evidence/README.md),
  [driver](../stage-4-completion/gate_b_probe.py), [prebuild probe](../stage-4-completion/prebuild_probe.py).
  Reports include actual worker PIDs/exit codes, RPC/SDK page traces, content-free state,
  canonical pending hashes, independent ID/date manifests and receiver counts.

## Independent fixture and boundaries

The small source was enumerated directly in descending order to an explicit empty
second page during the prebuild experiment, before tested scans. It contains 46
visible records, IDs 1 and 7–51. Its selected photo (ID 14, 2026-10-03T21:18:22Z)
was independently downloaded via SDK bytes and hashed. A separate post-gate direct
enumeration matched every expected ID/date. No fixture was derived from `prepare`.

The larger closed interval `[2026-09-14T17:25:09Z, 2026-10-06T11:28:33Z)` was
re-enumerated with four direct descending 100-slot requests, through an older-than-start
witness. The selected 350 IDs/dates matched the earlier independent Gate A manifest
before the new engine read them. The observed ID/date ordering was checked; the later
prepared/accepted set also matched. The independent path shares Telethon's transport
and TL decoder but not the tested raw-reader selection/traversal logic.

The photo hash remains
`ee515f404f8e760679cfa72d55d832a599309fc0ca1035d9acf7c719b7b6c984`, 173,837 bytes.
No bodies, sender metadata, raw RPC error text or media bytes are published.

## Actual composition and bounds

The internal BackfillEngine invokes the real guarded `TgData.get_message_batch`, with
isolated actual SQLiteSyncStore files. The test receiver uses SQLite FULL-synchronous
transactions, a unique full-delivery receipt and unique group/message record keys.
Download bytes are copied, flushed, fsynced and hash/size-verified before its receipt
transaction commits. That commit precedes acknowledgment; replay can be accepted again
without another record effect. This tests this local receiver, not ScrapeOps deployment.

Workers were sequential; no two source readers overlapped. The harness waited for each
owned process's actual exit before restarting. Local replay/ack/status workers blocked
socket connections and constructed only the state engine. Real reads were externally
spaced by at least five seconds; per-case time/request caps remained active. The unchanged
Gate A guard denied writes, joins, unrelated groups and account-wide update reads; its
pinned startup hook uses actual self/update-state metadata. No server response was faked.
This does not certify Telethon's normal passive update behavior without the diagnostic hook.

Gate B made **29 history requests, 1,198 requested message slots**, and 393,216 requested
media bytes. All history requests answered. Including the separate prebuild experiment,
Stage 4 used **1,400 of the 1,500-slot cap**. Account usage was 1,118 before Stage 4,
1,166 after the prebuild and **2,202 after Gate B**, leaving 2,798. Policy/charges were
never reset or increased; conservative charges on controlled failures remain intact.
The complete RPC type inventory and individual limits are in the evidence.

## Required cases and observations

| Case | Evidence | Actual result |
|---|---|---|
| Fresh small scope and overlapping imported collection | LIVE source + actual store/receiver | 46 records in 17/17/12 deliveries, then 38 overlapping records in 20/18 deliveries; receiver remains 46 unique group/message records; both complete at ID 51; imported origin remains imported |
| Exact full final batch | LIVE | 9 records return `limit`; ack does not complete. Subsequent empty end completes at ID 14 |
| Full batch then refused follow-up | LIVE + INJECTED local guard failure | Same 9 records accepted; blocked next send leaves no exhaustion/terminal result, cursor 14. Real equal payload hashes in separate collections cannot authorize the foreign receipt |
| Publication crash | LIVE photo + INJECTED actual post-commit process exit | Exit 73 immediately after pending commit; fresh-process replay matches the committed canonical payload hash and original delivery context |
| Receiver commit, lost reply | INJECTED real receiver transaction with LIVE payload | Exit 74 after commit before ack; repeated acceptance yields one receipt and one photo record |
| Media custody and context refusal | LIVE media + local filesystem faults | Relocated bytes replay exactly; corrupt/missing disposable copies refuse; wrong run/collection/destination refuses without mutation; receiver retains correct hash |
| Final ack before/after commit | INJECTED real SQLite process boundaries | Exit 71 before commit leaves photo owed/incomplete; exit 72 after commit leaves cursor 14/completed. All source-side media copies were removed before ack; receiver bytes remain |
| Empty completion before/after commit | LIVE empty query + INJECTED real SQLite exits | Before-commit run retains an unresolved attempt; independent after-commit run reopens completed with no fake delivery |
| Crash after actual source answer | LIVE + INJECTED process exit 76 | Saved admitted attempt remains unresolved; offline preparation raises RecoveryRequired, no second reader and no reset |
| Larger SDK/caller pagination | LIVE | 350 expected records accepted in 120/120/110 batches; six real SDK requests include second pages; complete at ID 253277 |
| Useful interrupted prefix | LIVE + INJECTED second-send guard refusal | First actual 100 records persist as `interrupted`, replay and are acknowledged at ID 252989; no exhaustion or terminal result. Real budget adapter retains the attempted-send charge |
| Duplicate/stale operations | LIVE payload + local operations | Latest ack leaves newer pending intact; older unrecognized receipt refuses; delayed prepare after progress conflicts; completed reopen is local |
| Source drift check | LIVE independent re-enumeration | Small source still matches all 46 expected IDs/dates after all cases; larger selected set matched its newly frozen independent oracle |

All **20 worker actions** exited with their exact expected normal/crash code. A separate
read-only audit loaded each actual SQLite state and receiver after the run, checking
46 + 350 reference records, one separately accepted photo, completion/unknown states
and the 1,198-slot RPC sum. Driver success alone was not used as the gate decision.

## Coverage and limits

This closes the Gate B portions of C12–C17, C21, C23–C26, C29–C31, C35 and C40–C42.
C17's *specific live quota-exhaustion/wait integration* remains for Gate C: Gate B used
its explicitly permitted controlled-failure alternative, with real budget accounting;
actual budget refusal/prefix behavior also passed the offline suites. No actual quota
increase, expiry, ban, flood or unapproved server failure was induced or claimed.

Cases spanning controls/recovery/public facade retain their later-stage portions.
Seeded pause/cancel/abandonment fixtures are only local preservation evidence. No new
pacing, recovery, control, distributed-reader, permanent archive or power-loss guarantee
is claimed. Receiver acceptance remains the caller's assertion in the library API.

## Decision and preserved state

No required Gate B assertion was skipped or inconclusive. Gate A's source assumptions
remain intact: raw reader/window/media implementation and the live guard were unchanged,
the independent comparisons still agree, and all ten guard checks passed again.
Supported offline verification passed 255 actual groups with three explicit legacy live
skips; see [Stage 4 verification](../stage-4-completion/verification.md).

**Advance to Stage 5 when requested.** Private test records remain under
`/private/tmp/tgdata19-gate-b-live-20261007`; the unresolved `empty_uncommitted` and
`unknown_source` runs were not cleared or replaced. The prefix and failed-follow-up
runs remain incomplete as required. The original shared budget remains under
`/private/tmp/tgdata19-gate-a-live-20261007/account-read-budget.sqlite3` and must be reused.
