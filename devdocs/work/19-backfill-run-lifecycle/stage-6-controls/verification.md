---
model: gpt-6-astra
effort: max
status: PASS
---
# Stage 6 verification

**PASS: product `0d6bb26`, all 319 supported offline checks and mandatory Gate C.**
Telethon 1.45.0, Python 3.11.10; compile and Python 3.7 grammar over 54 product/test
files passed. No runtime 3.7 claim. No product change followed these runs.

[Machine results](verification-results.json), [32-group output](control-test-results.txt),
[instruments](instrument-results.txt), [Gate C report](../validation/gate-c.md).

| Suite | Actual passes | Explicit live skips |
|---|---:|---:|
| 28 controls | 32 | 0 |
| 27 pacing/recovery | 32 | 0 |
| 26 completion | 16 | 0 |
| 25 delivery | 41 | 0 |
| 24 state | 23 | 0 |
| 23 windows | 22 | 0 |
| 22 daily continuation | 25 | 0 |
| 19 message batches | 33 | 0 |
| 18 budget | 28 | 0 |
| 17 sessions | 12 | 0 |
| 16 health | 21 | 0 |
| 15 login | 11 | 0 |
| 14 flood threshold | 11 | 0 |
| 13 identity | 5 | 1 |
| 12 proxy | 5 | 2 |
| 11 explicitly awaited offline helpers | 2 | 0 |
| **Total** | **319** | **3** |

Existing guard checks: 10/10. Daily example: four stored messages, accepted through
104. New prebuild instrument/actual-codec checks: 7/7 before product edits and again
after. Durable launch/send-guard checks: 3/3. Default live-driver help and compilation
passed. Full regressions used the prior bounded parallel runner, with no real account
config/session; only loopback proxy tests needed local socket permission.

New control suite passed 32/32 on its initial run and again in the full sweep. There
were **no product corrections** and no weakened runtime assertions. Core live cases
passed first run. The acceptance-matrix audit required additional exact orderings;
the separate supplement passed unchanged C03/04/06/11/16/21/32/36/38 expectations.

## Instrument corrections, explicitly recorded

1. Before the first live experiment, corrected its planned error-prefix label to the
   existing `interrupted` wire value, and installed the restrictive test budget on
   both the existing client and engine factory. No live failure or product edit.
2. The critic required the complete composite reservation interface (`amount`) and
   durable per-launch caps. Both were implemented in the test helper and passed
   actual local SDK plus real-source checks before building controls.
3. The saved-record audit initially asserted 12 state files by manual miscount. Its
   specified cases produce 11 containers because workers reopen files. Replaced that
   bookkeeping total with the exact required filename set; all actual state, receiver,
   RPC and policy conditions were retained. Initial failure and final PASS remain in
   [audit-initial.txt](audit-initial.txt) and [audit-results.txt](audit-results.txt).

## Gate C result and limits

All required live cases passed across 13 Gate C worker actions plus the earlier
prebuild: 23 history requests, 442 requested slots, 790 reserved launch slots within
the 1,000 ceiling. Account policy stayed 5,000/day; actual usage 2,202 → 2,334. Both
original Gate B uncertain-state files retain their earlier SHA-256 hashes.

Real pacing used 5/8-second policies; 240-second and clock/rolling-expiry boundaries
remain separate deterministic tests. Test allowance 3 → 6 is explicitly a policy
increase in a separate restrictive ledger, not natural expiry or a shared-policy
increase. No server flood/ban, source write or alternative account was used. Receiver
durability is the actual local FULL SQLite/file composition; other deployment
backends/receivers need equivalent evidence. No distributed-reader or perfect-clock
guarantee is inferred. **Next: Stage 7. Stage 8, Gate D and review remain pending.**
