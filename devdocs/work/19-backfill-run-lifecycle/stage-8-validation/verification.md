---
model: gpt-6-astra
effort: max
status: PASS
---
# Stage 8 verification

**PASS at product `405218e`: 357 actual supported offline checks; Gate D PASS.**
Runtime remains `17fccbc`. Python 3.11.10, Telethon 1.45.0 only. The 57 product Python
files also compiled and parsed with Python 3.7 grammar; this is not a Python 3.7
execution claim. Work-folder instruments compiled separately.

| Suite | Actual passes |
|---|---:|
| 30 — combined public failures | 15 |
| 29 — public facade/example | 23 |
| 28 — controls | 32 |
| 27 — pacing/recovery | 32 |
| 26 — completion | 16 |
| 25 — delivery | 41 |
| 24 — lifecycle state | 23 |
| 23 — fixed windows | 22 |
| 22 — daily continuation | 25 |
| 19 — message batches | 33 |
| 18 — account budgets | 28 |
| 17 — session storage | 12 |
| 16 — health events | 21 |
| 15 — login checks | 11 |
| 14 — flood threshold | 11 |
| 13 — identity | 5 + one explicit live skip |
| 12 — proxy | 5 + two explicit live skips |
| 11 — two explicitly awaited offline helpers | 2 |

Additionally: ten existing Gate A guard checks, nine new Gate D receiver/guard checks,
offline help, daily example (four records, cursor 104), and public backfill example
(five records, three receipts, real owned-process restart). The full runner used at
most three parallel offline subprocesses and a 180-second per-job bound. Existing
loopback proxy checks ran with the required sandbox permission; no Telegram access
was part of the offline sweep.

New test30 passed 15/15 on its first run and again in the full regression. Its first
nine groups each execute both before/after actual commits: 18 confirmed owned process
exits. Source replies are synthetic; actual facade, SDK, SQLite, receiver and fault
boundaries execute. The other six groups combine failed publication/source provenance,
cancelled replies, late terminal ordering/successors, control races, media loss after
acceptance, and missing/malformed state with failed cleanup. No runtime repair was needed.

Actual logs: [initial test30](test30-initial-results.txt),
[full regression test30](test30-regression-results.txt), [supported sweep](offline-results.txt).
Legacy live skips are excluded from 357, not counted as successful observations.

The mandatory real prebuild passed before Step 1: 202 history slots of 250 allocated,
full independent small-group/photo qualification, actual public download, exact reopen,
paused receiver/ack and local health isolation. [Prebuild evidence](prebuild-results.json).
The final [Gate D report](../validation/gate-d.md) records all 14 owned workers and the
independent saved-record audit: 250 historical records in 120/120/10 batches plus 2 daily,
four real waits >=12 seconds, interrupted prefix, actual source/recovery/ack exits,
scoped controls/receipts and verified photo custody. Total Stage 8 allocation 1330/1500;
attempted 1082, sent 1061 in 23 history requests; shared 5,000 policy unchanged.

One small instrument correction is recorded in [audit-correction.txt](audit-correction.txt):
the audit initially applied successful-history-response expectations to normal media
DC-routing responses. It now verifies history success and separately proves the planned
file migration/answered continuation. No lifecycle expectation, runtime code or live
fixture changed, and no additional live read was needed. The corrected audit passed.

No substantive unresolved failure remains. The selected local test receiver/SQLite/
worker composition is qualified. Other deployments still need equivalent durability,
clock and single-reader guarantees. Formal merge-check/PR/fresh PR critique remain pending.
