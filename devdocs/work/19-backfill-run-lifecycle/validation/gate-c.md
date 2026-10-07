---
model: gpt-6-astra
effort: max
status: PASS
gate: C
---
# Gate C — pacing, recovery and operator intent

**Verdict: PASS — Stage 7 may begin when requested.** All critical Gate C requirements
in the staged plan, live-validation §7 and its acceptance-matrix cases have scoped
evidence. No required case was skipped. This does not implement the public facade,
pass Gate D or authorize PR/merge. The complete feature remains in progress.

## Revision and composition

- Product: `0d6bb26`, from `/private/tmp/tgdata-19-backfill-run-lifecycle`; no product
  edits during or after these tests. Telethon **1.45.0**, Python **3.11.10**.
- Date: 2026-10-07. Stage 6 RPC interval including the prebuild experiment:
  **13:44:04.516791–14:14:19.751230 UTC**. These are recorded actual times.
- Same user-approved account/session/config and unchanged authoritative 5,000/day
  ledger used by Gates A/B. Every network worker verified actual self identity.
- Read-only existing source: `arenda_stambul1`, `-1004478311025`. No messages, edits,
  joins, membership changes, account settings or deliberate floods/bans were performed.
- Actual internal BackfillEngine → TgData raw reader → guarded SDK, actual SQLite
  state, real SQLite FULL receiver transactions and hash-verified durable media.
  Receiver receipt commits precede library acknowledgment. This qualifies this local
  receiver/backend, not a future ScrapeOps or server deployment.

[Structured observations](gate-c-evidence/observations.json) retain source turn/RPC
times, command outcomes, content-free saved state, receiver counts, owned process
exits, fixed launch allocations, oracle and driver hashes. [Evidence guide](gate-c-evidence/README.md).
Drivers: [core](../stage-6-controls/gate_c_probe.py),
[matrix supplement](../stage-6-controls/gate_c_matrix.py),
[read-only audit](../stage-6-controls/audit_gate_c.py).

## Independent fixture and traffic accounting

Before product implementation, direct descending history through an explicit empty
page independently enumerated 46 records (IDs 1 and 7–51). Before Gate C, the same
independent path matched all IDs/dates again. Expected sets were not derived from
the tested forward batch reader. Every measured prefix/final result matched this
oracle. The selected photo ID 14 at `2026-10-03T21:18:22Z` was independently downloaded
and hashed: 173,837 bytes,
`ee515f404f8e760679cfa72d55d832a599309fc0ca1035d9acf7c719b7b6c984`.
Subsequent downloaded copies and receiver bytes matched it.

The whole stage, including prebuild and the matrix supplement, made **23 history
requests / 442 requested slots / 130 guarded RPCs**. Every history request answered.
Fixed launch reservations total **790**, below the **1,000-slot stage ceiling**.
Reservations were saved before launch and never refunded after an uncertain exit.
Each worker's guard enforced its own cap and persisted send admission before waiting
for a reply. The unchanged allowlist/startup diagnostic hook forbids source writes,
unrelated groups and account-wide update reads. It does not certify ordinary SDK
passive-update behavior without that hook. SDK retries were disabled for these
bounded diagnostics; no natural FloodWait was observed or manufactured.

Authoritative account usage progressed **2,202 → 2,254** during prebuild, then to
**2,334 after all Gate C cases**, leaving 2,666. The original policy and charges were
never reset or increased. A test-only intersection with a second real ledger used
cap 3, then an explicit test-cap increase to 6 while retaining all charges. Both
ledgers remained enforced at actual SDK send/page boundaries. This is **not natural
rolling expiry**; expiry/warm-up/clock-edge behavior is separately deterministic
offline evidence. No production composite-budget API was introduced.

There were **13 Gate C worker actions**, plus the separate prebuild process. Network
workers ran sequentially. The parent waited for actual owned process exits; local
restart/recovery workers blocked sockets. Case timeouts and source/media caps remained
active. The final matrix supplement stayed within the same persisted launch ceiling.

## Required observations

| Boundary / cases | Evidence | Observation |
|---|---|---|
| Restrictive quota, paused pending and wait — C17/C22 | LIVE source/budget, INJECTED local pause | Two exact 3-record interrupted prefixes persisted and reached the real receiver. Pause during the error return preserved the original exception and data. Replay/ack worked while paused and exhausted; resume retained the deadline. Early call sent nothing; next source entry was 8.0413 seconds after prior raw return for an 8-second policy. |
| Known wait across actual process restart — C19 | LIVE measured timing | Fresh-process early waits decreased from 7.456876 to 7.456499 seconds without writes/source. Next source entered 8.7682 seconds after prior raw return and after the saved UTC deadline. |
| Late acknowledgment — C19 | LIVE source/receiver/time | A receiver ack after the deadline did not start another wait. Next read was immediately eligible; successive raw turns were separated by 8.0437 seconds for the 8-second policy. |
| Settled zero-prefix failure — C24/C38 | Actual verified account/ledger; no disallowed history RPC | Exhausted test allowance produced no pending/end/progress. Early retry made no RPC. After 5.0366 seconds a distinct admitted attempt rechecked actual allowance, remained refused and sent no history request. |
| Source worker dies before publication — C18/C26 | LIVE source + INJECTED owned exit 81 | Actual source answered, then the worker exited with durable attempt still unresolved. Parent wait confirmed exit; another prepare refused without reading. |
| Recovery commits but reply is lost — C39 | Actual SQLite commit + INJECTED exit 82 | Full unknown-end 8-second interval committed. Fresh-process identical recovery retries used forbidden clocks, wrote nothing and retained the exact deadline. Early prepare waited 7.5162 seconds; later real read followed recovery by 8.7282 seconds. Accepted position was unchanged until actual receiver ack. |
| Still-active worker — C28 | INJECTED hold around actual result/error return | Recovery and abandonment refused while local preparation remained active, even with a claimed stopped flag. No timeout was treated as proof of death. |
| Late source result — C27/C32 | LIVE result + INJECTED local await barrier | Pause/cancel committed before publication. The same admitted result remained owed with newer intent. Cancelled in-flight abandonment/succession refused; after settlement explicit abandonment preserved cancelled outcome and cursor. |
| Delayed responses and opposing controls — C06–C08 | Actual CAS/load/reply barriers with LIVE-origin state | One of two conflicting commands was accepted. Both delayed pause and the specified delayed-resume-after-newer-pause ordering preserved the newer stored decision. Old resume and prepare contexts refused, without auto-rebase or extra RPC. |
| Terminal ordering — C09–C11 | LIVE final/empty source and actual receiver | Completion-before-cancel stayed completed; cancel-before-final-ack stayed cancelled. Cancel before real empty-end publication stayed cancelled. Final replay/receiver/ack while paused completed without resuming or source traffic. |
| Abandonment and equal-hash successors — C30/C32 | LIVE photo + actual store/receiver | Explicit withdrawal left accepted cursor unchanged and source files intact. Equal bytes in a successor had a distinct full receipt. Retired receipt refused; retained accepted predecessor receipt left current pending untouched. Receiver kept two scoped receipts but one unique photo. |
| Retention and pending protection — C03/C04/C16 | Actual produced histories with LIVE pending data | Current/prior creation retries recognized; pruned old retry/new attempts refused. Active pending survived local replay and could not be replaced by a new run. |
| Lost control reply — C21 | Actual post-commit SQLite close failure with LIVE pending | Exact read-back confirmed the committed pause. Same-command retry had no second effect or new clock/RPC; offline tests additionally killed actual control-commit processes before and after commit. |

The audit checked every guarded RPC after the first source entry against actual
reader-entry/return intervals. No RPC was attributable to the intervening local
control/receiver/ack/status operations. Source turns and actual SDK requests remain
separate evidence; a turn is not asserted to contain one RPC or to have bounded duration.

## Audit, corrections and limits

Core driver assertions passed first run. Its automatic summary covers those cases
only. A subsequent matrix audit identified exact orderings that still needed execution;
the supplemental run passed C03/04/06/11/16/21/32/36/38 without changing expectations.
The formal verdict above includes both drivers and the independent saved-record audit.

The audit validated all **11 specified state containers**, every receiver's actual
receipt/message rows and relevant media digest, all request sums and owned exit
proofs. Its first run had a bookkeeping typo, expecting 12 containers; several workers
reopen one file. Replacing that manual total with the exact expected filename set
corrected only the inventory assertion. All state/receiver/traffic conditions were
retained. [Initial record](../stage-6-controls/audit-initial.txt),
[final result](../stage-6-controls/audit-results.txt). No product correction was needed.

Supported offline verification: **319 actual passes**, three explicit legacy live
skips, ten existing guard checks; new controls 32/32 initially and in the full run.
Seven prebuild component/instrument checks and three durable launch/trace checks passed.
Python 3.7 grammar passed; runtime was 3.11.10, not a 3.7 runtime claim. Live timing
used explicit 5/8-second run policies; independent offline cases exercise 240 seconds,
clock faults, sub-microsecond rounding, indefinite/expired hints and real SDK budgets.
Host time was not changed. Same-host monotonic comparisons were separately measured
with a parent/child bracket; portable run state still stores only UTC evidence.

These are existing account/view/window observations, not a universal immutable archive,
distributed ownership guarantee, power-loss test or exactly-once external transaction.
The caller still owns one source reader per group, real worker quiescence, trusted UTC
after local evidence loss, account selection and durable receiver acceptance.

## Decision and preserved history

Stages 5–6 satisfy Gate C for this revision/composition. Raw reader, MessageBatch v1,
state schema, source budget adapter and health code were unchanged. Regression suites
and independent source comparisons still agree, so Gates A/B need not reopen.
The two original Gate B unknown-state files remain byte-identical to their Stage 5
recorded hashes; no original uncertain run was recovered or overwritten.

Private data remains under `/private/tmp/tgdata19-gate-c-live-20261007`. Credentials,
session strings, account identifiers, message bodies, sender metadata and media bytes
are excluded from published evidence. Continue using the original Gate A account ledger.
**Stage 7 is the next work; Stage 8, Gate D and whole-feature review remain pending.**
