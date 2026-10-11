---
model: gpt-6-astra
effort: max
---
# Implementation — #10 reading worker

2026-10-11. Product commit **`6ee146c`**, based on merged dev `68f6bbd`.
Executed the folded seven-step revision2 plan (`bee5b1f`) in the same warmed
session. The required REORDER experiment passed before runtime changes; its
7 source, 6 cleanup and 4 pipe histories are retained in `probes/prebuild.txt`.
No execution blocker or architectural verification failure arose.

## Completed steps

1. **Protocol:** strict bounded version1 lines, consumed increasing request IDs,
   fixed safe diagnostics, four parameter schemas, decimal identifier projection,
   preserved raw MessageBatch dictionaries and bounded complete-frame encoding.
2. **Execution:** explicit WorkerAccount inventory, existing read/join policies,
   fresh verified temporary operations, bounded read resolver using merged #7,
   source-owned health collector and sticky cleanup-failure receipt. Existing
   BatchEngine default resolution and ordinary owned-operation outcomes remain.
3. **Process:** manifest and trusted session-store bootstrap, one loop/job/writer,
   raw output, EOF/error/signal semantics, safe logging policy and packaged CLI.
4. **Tests:** test37 has 25 source/protocol groups; test38 has 14 actual-process
   groups. Real Telethon/SQLite execute behind synthetic transport with blocked
   sockets. These tests exercise source behavior, not fake worker implementations.
5. **Docs/example:** `docs/worker.md`, README and smoke README, and the runnable
   `examples/reading_worker.py`. The offline demo deliberately demonstrates an
   empty inventory/local refusal; full source qualification is in the tests.
6. **Verification:** 24 suites, **612 actual passes, 3 explicit live skips**;
   compile/3.7 grammar for76 files; isolated wheel/module/console invocation;
   worker and daily demos; new/restarted backfill demos. See `verification.md`.
7. **Publication:** product is committed separately from these work-folder notes.
   Push this feature branch and update issue10 step5 from the committed evidence.
   Merge-check, PR and fresh PR critique remain subsequent, unperformed gates.

## Local corrections and implementation details

- A rejected encoded reply set initially omitted collected-but-unpublished health
  frames from `health_dropped`. Include both collector drops and discarded events;
  the size-failure test requires this exact disclosure. No source outcome changed.
- The first actual process run reproduced pending Telethon update/keepalive tasks
  after failed native disconnect. The result was correct, admission already stopped,
  but loop closure printed task destruction/closed-loop diagnostics. The process
  now cancels and gathers its remaining loop tasks before shutdown_asyncgens/close.
  It does not retry disconnect/source/output or claim the failed cleanup succeeded.
  This completes the planned process teardown, not a new supervisor/lifecycle design.
- Bound each collected health event to8 KiB as well as256 per job. Oversized events
  count as dropped; source errors/partial batches survive. This concretizes the
  plan's bounded-plain-event requirement and is disclosed in ready and public docs.
- The worker retains **reference-only** media. This is the planned first protocol,
  not a claim of supporting arbitrary output/download paths.
- The example's offline mode has no configured accounts, so it proves the actual
  packaged process boundary without taking on a second synthetic SDK implementation.

No selected critic remedy was omitted: bounded resolution and raw output are both
implemented and tested. No new queue, routing, persistent socket pool, HTTP listener,
progress store, login flow or automatic retry was added. The issue17 runtime was
not copied; its rejected draft review/handoff remains untouched.

## Test-fixture and environment corrections

All failed attempts are retained under `verification/` rather than hidden:

- First core run17/19: the synthetic RPC fixture had not attached the actual join
  request to InviteRequestSentError; the merged guard correctly refused to treat
  it as successful mutation evidence. The fixture now binds errors like the SDK.
  The synthetic ChatInviteJoinResultWebView also needed its required `users` field
  under1.45.0. Neither acceptance condition was weakened. Then19/19,23/23 and
  final25/25 passed as coverage was completed.
- First process run13/14 exposed the real teardown correction above. The rerun
  and integrated suite both passed14/14 with empty stderr, including cleanup failure.
- The initial test12 run could not bind loopback under the socket sandbox. Rerun
  permitted local loopback and passed5 actual cases; missing config still skipped
  both live cases. No Telegram relay was enabled. Test13 separately skipped1 live case.
- Initial wheel build lacked the environment's `bdist_wheel` command. The existing
  base-environment wheel0.44.0/build tooling was used only for build metadata; no
  runtime dependency/requirement was changed or downloaded. Installed checks used
  the project Python3.11.10 environment and Telethon1.45.0.
- The first retained-directory backfill demo invocation omitted its required
  explicit `--new` provision flag and correctly refused absent state. The corrected
  new-then-restart commands passed, with zero source reads on completed restart.

## Scope/model record

Thirteen product files changed; all are within the surfaced source/ownership,
process, packaging, test and caller-doc boundaries of feature-heavy triage. Work
documents stay on this branch. GPT-6 Astra/max was verified from this turn's
metadata at `2026-10-11T11:02:04.423Z`; no delegated reviewer or cold-context claim.
Original checkout untracked HANDOFF/todo, duncan and other worktrees remain untouched.

There was no live Telegram read/login/join, allowance reset, deployment, PR or dev
merge. #10 remains open until its review/merge process. #17 remains independently
rejected at draft PR26 with revision3 re-planning next.
