---
model: gpt-6-astra
effort: max
status: PASS
---
# Gate D — complete public lifecycle

**PASS — 2026-10-07, product `405218e`, runtime unchanged from `17fccbc`.**
The complete TgData facade ran against actual Telegram through Telethon 1.45.0,
actual SQLiteSyncStore and a receiver that stores full scoped snapshots after
verified file custody. Python 3.11.10; Python 3.7 grammar was checked separately.

The user approved existing read-only groups `arenda_stambul1` and
`programlama_sohbet`, the selected project account and its existing budget. There
were no sends, joins, account changes, induced server restrictions or policy resets.
Independent descending raw SDK reads qualified the fixture before lifecycle reads;
they shared the SDK decoder/transport but not the tested ascending batch/window path.

## Actual observations

| Required composition | Observed result |
|---|---|
| Complete bounded history | Independently qualified 250 IDs/dates; accepted batches 120/120/10, exactly matching the set, with actual second SDK pages. Completion followed final receiver acceptance and ack. |
| Delayed delivery and restart | First receiver commit followed a deliberate two-second delay; owned worker exited 73 before ack. A fresh socket/config-blocked process replayed exactly, deduplicated, paused, acknowledged and resumed. Original deadline retained; 9.476 seconds still remained. |
| Daily turn between historical turns | Two independently expected daily records delivered/acked while history was waiting. Both saved rows were compared before/after; each operation left the other collection unchanged. Receiver held 252 unique messages in four complete snapshots. |
| Real pacing | Next historical preparations began 12.036 and 12.041 seconds after preceding source ends. The daily read occurred inside the second interval. No library sleep or account-wide rest claim. |
| Controls and authority | A real source result held before publication preserved a newer pause. Busy recovery/abandon refused; paused final ack completed. Both cancel/completion orders, delayed resume after newer pause, opposing CAS controls, stale contexts, explicit cancellation/abandonment and four equal-hash generations behaved as specified. Retired/pruned receipts could not settle newer pending data. |
| Usable interrupted prefix | Local test guard refused the second SDK send after a real 100-record page. Exact prefix replay/receiver/ack succeeded; failure remained visible, source not exhausted. The denied 20-slot claim stayed reserved. This was an INJECTED local refusal, not a Telegram denial. |
| Unknown source / lost recovery reply | Owned worker exited 81 after actual raw return but before publication. Parent confirmed exit. Local prepare refused unresolved work. Recovery exited 82 after actual commit; original retry kept the exact deadline and observed 11.548 seconds remaining. Real re-read began 12.040 seconds after recovery and only its receiver ack advanced progress. |
| Photo custody / lost ack reply | Independently hashed photo: 173,837 bytes, SHA-256 `ee515f404f8e760679cfa72d55d832a599309fc0ca1035d9acf7c719b7b6c984`. Full one-record batch did not establish end. Exact reopen/replay, corrupt disposable-copy refusal and missing-source refusal passed. Verified receiver bytes and full snapshot preceded actual ack commit/exit 84; duplicate ack needed no source copy. |
| Full batch then failure / actual end | After ack the photo run stayed incomplete. A locally refused follow-up did not invent completion. After 12.035 seconds, an actual source end completed it without another receiver delivery. Its denied one-slot claim stayed reserved. |
| Public local health boundary | Clearly labeled INJECTED prior no-access fixtures remained unchanged through local operations. Local workers blocked sockets/config; SDK traces attributed all source/metadata/file calls to actual source or explicit qualification, not local replay/ack/control/recovery. No real denial/ban was manufactured. |

Fourteen owned workers ran sequentially and were explicitly waited for. The five
intentional exits were 73, 81, 82, 83 and 84. Same-host monotonic timestamps were
bracketed by parent launch/exit observations; persistent state remains UTC. Independent
source cases had at least five seconds external spacing. Per-worker deadline 180 s;
parent deadline 195 s. No timeout or live retry was needed.

## Limits and accounting

Including the required prebuild: **1,330 slots allocated of a 1,500 ceiling; 1,082
attempted, 1,061 sent in 23 history requests.** Failed allocations were not reclaimed.
Media requests totaled 1,179,648 requested bytes, below each worker's 4 MiB bound.
The independent source search still contained the same 350 records as earlier gates;
a 250-record closed prefix was frozen before tested reads. The small fixture remained
46 records. No expected set was weakened after testing.

The authoritative account policy remained 5,000/day. Stored charged use moved from
2,334 to 3,262; outstanding conservative reservations from 19 to 40. The 21 added
reservations are the two deliberately blocked sends. Recovery/replay/ack refunded
nothing and created no source traffic. Requested slots, returned charges and allocation
ceilings are different quantities; they are reported separately.
The 928-slot charged increase equals 907 actual returned SDK message slots plus the
21 uncertain blocked claims, both in total and independently for each source worker.

## Independent audit and corrections

[audit_gate_d.py](../stage-8-validation/audit_gate_d.py) read actual saved SQL rows,
complete receiver snapshots, first-observation indices, blobs, immutable requests,
owned-process records and actual SDK traces. It independently matched all expected
sets, exact scoped snapshots, terminal/incomplete states, pacing and slot totals.
It also verified both preserved unresolved Gate B database hashes, unchanged.

One local audit filter was corrected: it initially demanded an answered success from
every SDK call, including three legitimate GetFileRequest/FileMigrateError routing
responses. Telethon 1.45.0 follows these to the file DC. The corrected audit requires
successful history responses and separately proves each file migration has an answered
same-operation continuation plus verified bytes. This is the already planned file/DC
transport, not a relaxed lifecycle expectation. Initial observation and correction:
[audit-correction.txt](../stage-8-validation/audit-correction.txt). No runtime fix or
additional live run was required. The independent audit then passed.

Evidence: [sanitized observations](gate-d-evidence/observations.json),
[evidence scope](gate-d-evidence/README.md), [case map](../stage-8-validation/coverage-map.md).
Raw messages, state, receiver SQL/files and source oracles remain private under
`/private/tmp/tgdata19-gate-d-live-20261007`. No credentials, account identity or raw
message/sender data is published.

## Decision and remaining scope

Every required Gate D case ran. No behavioral disqualifier, unresolved source drift
or untested critical case remains in this selected composition. Runtime source/window,
storage and pacing semantics did not change during Stage 8, so A/B/C remain valid.
The intentionally incomplete prefix test state is retained privately; no worker remains
active. Other test runs are completed or explicitly cancelled/abandoned.

This gate certifies the selected test composition. The operational application must
still provide durable receiver acceptance, appropriate backend guarantees, reliable
UTC after restart, and actual single-reader ownership. No power-loss simulation,
distributed leases, account routing, edit/deletion reconciliation or other SDK version
is claimed. Formal merge-check, PR publication, fresh PR critique and merge remain pending.
