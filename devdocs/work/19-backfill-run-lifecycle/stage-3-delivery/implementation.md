---
model: gpt-6-astra
effort: max
status: verified
date: 2026-10-07
---
# Stage 3 implementation record

**Stage 3 is complete and verified.** It adds internal durable prepare/replay/ack to
Stage 2's existing state/start/status foundation. Gate A remains passed; Stage 4 and
Gate B are next. No Stage 4/Gate B completion or later API readiness is implied.

## Pipeline

| Checkpoint | Commit |
|---|---|
| Intake, surfacing and feature-heavy triage | `8b67a11` |
| Description | `935c490` |
| Plan revision 1 | `e55e7ac` |
| Dynamic critic / REORDER experiment criteria | `987f116` |
| Five-check primitive PASS / revision 2 fold | `fa50ae2` |
| Product code, tests and public documentation | `3140dcd` |

The selected user task ran through the supplied task-impl chain. There were no open
planning or execution blockers. critic-d required the cheap real-primitive experiment
before build; it passed, with no additional severity findings or mitigation proposals.
The whole-source/retained-session warming and actual gpt-6-astra/max stamp are recorded
in the description/triage. #19's linked feature branch and #18 prerequisite ancestry
are preserved; no protected branch was merged or advanced.

## Plan completion

- [x] Step 1: immutable PrepareContext/DeliveryRef/Turn, local errors and saved size bound.
- [x] Step 2: scoped local guards, exact CAS and confirmed attempt admission before reading.
- [x] Step 3: exact publication/replay, safe same-attempt rebasing and failure/cancellation handling.
- [x] Step 4: full-context atomic acknowledgment and latest/prior receipt recognition.
- [x] Step 5: 41 new delivery groups with actual SQLite/SDK/media/receiver components.
- [x] Step 6: staged public usage, scope limits and task evidence.
- [x] Step 7: 239 offline groups, 3 explicit live skips, 10 instrument checks, daily demo,
      compilation/syntax checks and separate product/evidence checkpoints with #19 publication.

## Behavior and scope

The reader is injected as `read_batch=tg.get_message_batch`. Every new source call is
preceded by one confirmed aggregate admission; no read repairs a failed write. Pending
replay is exact and local. A receipt includes run/generation, collection/group,
destination and batch identity; only the saved next cursor advances. Valid acceptance
does not depend on local artifact survival. Local storage/media/cancellation errors
cannot inherit a source health verdict; the original ordinary read error is preserved.

The existing codec requires source end evidence and minimal terminal closure when its
last obligation settles. That closure is included, not a weakened intermediate record.
Stage 4's dedicated completion/uncertain-write audit is still pending. Positive timing
and explicit recovery remain Stage 5: first turns and zero-pause continuation work;
further timed admission fails closed, while local replay/ack are available. Seeded
control/recovery snapshots do not claim those later APIs exist. No root exports or
TgData facade changes were made.

See [verification](verification.md) for actual results, limits and every local correction,
and [available usage](../../../../docs/backfill_state.md) for the staged API.

## Next handoff

Select Stage 4 on this same branch. Reuse the minimal end/closure helper rather than
implementing a competing path; test/refine its complete empty/final/uncertain-commit
matrix. Then execute Gate B against the real new engine and a durable receiver. Retain
Gate A's user-selected source setup and existing ledger; never reset its charges.
No #7/duncan changes, new account routing, source writes, PR or merge occurred here.
