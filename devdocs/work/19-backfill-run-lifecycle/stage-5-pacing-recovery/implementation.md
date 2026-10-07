---
model: gpt-6-astra
effort: max
status: implemented-offline-verified
---
# Stage 5 implementation

**Complete and verified offline.** Product `a180151` implements per-run pacing and
exact-attempt recovery on the existing internal engine and opaque v1 record. Next is
Stage 6 operator controls, then mandatory live Gate C. No Gate C or public API is
claimed by this stage.

## Pipeline

Same warmed primary session, GPT 6 Astra/max. Intake `784f20b`, desc `81a207a`, plan
revision 1 `9f0b47e`, critic `03c1836`, prebuild PASS/fold revision 2 `8944336`, product
`a180151`. The five required real-primitive checks passed before product changes.
No content mitigation or architectural re-plan was required; no planning/execution
blocker remained. Existing lifecycle traverse/contract and Gate B were the foundation.

## Implementation against the six steps

1. Added immutable recovery results, positive local wait on BackfillTurn and content-
   free projection of existing pacing/recovery fields. No wire-state schema change or
   package-root/public TgData export.
2. Added lazy UTC/monotonic-nanosecond pairs, exact elapsed arithmetic and bounded
   per-group anchors. Early preparation returns without source, sleep, state mutation
   or media-directory work. Actual end is remembered before publication; cancellation
   observes it best-effort without replacing cancellation or awaiting persistence.
3. Added recover with required true quiescence, exact run/attempt/command/control
   identity, local-busy refusal, retained recognition and one conservative unknown-end
   interval. Known local ends/stronger restrictions are preserved. Actual CAS/read-back
   handles uncertain replies; no recovery advances data, creates EOF or touches quota.
4. Preserved direct SDK wait hints, without cause traversal or cached account inference.
   Source/budget observations remain historical; current account/allowance are checked
   by the unchanged real adapter on an intentional eligible source turn.
5. Added 32 temporal/fault groups, including actual recovery commit/process boundaries,
   independent clocks, real elapsed local time, original errors, stale/control/attempt
   races, fresh account changes and retained cancelled budget claims. Existing staged
   assertions changed only for now-implemented recover/pacing behavior.
6. Updated public usage and test index; supported offline sweep passed 287 actual
   groups, three explicit legacy live skips, ten guard checks and the daily demo.
   Compile/3.7 grammar passed; actual runtime remains Python 3.11.10/Telethon 1.45.0.

## Corrections and limits

Initial new-suite result was 31/32. One test passed a missing required keyword call
to an asynchronous exception helper, but Python raises that signature TypeError at
call construction. The local test invocation was changed to the synchronous refusal
helper, with the expected TypeError unchanged. Final new-suite result: 32/32. No runtime
fix or design deviation was required; both initial and final receipts are retained.

Recovery's timestamp is the trusted observation after quiescence, accepted atomically
with the state. It is not the backend's physical commit timestamp. Delayed CAS time
counts as quiet time and does not refresh the deadline on reply. Monotonic evidence
protects an engine lifetime; after losing that context, UTC must be trusted. Arbitrary
undetectable clock jumps, cross-process leases and account-wide rest remain outside
this contract. Source hints are not a second cached admission gate.

Controls remain absent. Seeded control fixtures prove preservation only. Gate B's
historical reports remain intact; raw reader, batch/media, actual budget and receiver
contracts were unchanged and their regressions passed. Their prior evidence does not
prove the new live timing/recovery/control composition; Gate C must do that after 6.

## Real-state copy check and handoff

Both Gate B unresolved records were recovered and retried through the actual new
method on disposable copies, with sockets blocked and ReadBudget construction forbidden.
Each kept cursor 0, no pending/EOF/terminal result; identical retry was a no-op. Original
file hashes and the original budget file stayed unchanged. This is LOCAL verification
using LIVE-origin state, not a Gate C PASS. See [copy receipt](gate-b-copies-results.json).

Original `empty_uncommitted` and `unknown_source` records remain unresolved under
`/private/tmp/tgdata19-gate-b-live-20261007`. Their workers' actual exits are recorded
in Gate B. Reuse the existing Gate A ledger for later live validation; its last Gate B
usage was 2202/5000 and this stage performed no Telegram reads or policy changes.

Next: Stage 6 pause/resume/cancel/abandon and concurrent settlement, then Gate C. No
PR/merge was requested or performed. Paused #7/duncan and the separate #18 checkout
remain untouched. #19's body is near its size limit; future status uses concise fields
and linked completion comments, preserving the original user request/history.
