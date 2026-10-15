---
model: gpt-6-astra
effort: xhigh
---
# Implementation and verification — batch heartbeat #37

**Merged into dev7d9840f via PR38 after completed reviews and merged-tree verification.** Product commit `b789846` on the existing `feat/30-photo-trail-folding` branch. No new branch was created. PR36 retains its historical reviewed1cd001e head; the reused product branch carries heartbeat15241bf. No release or consumer deployment occurred.

## Delivered behavior

Optional synchronous heartbeat(phase) is available on TgData.get_message_batch/sync_group/prepare_backfill, the underlying BatchEngine/SyncEngine/BackfillEngine, and AccountPool.read/get_message_batch/sync_group/prepare_backfill. None stays omitted for legacy injected readers. A batch invocation binds a transient task-owned observer, including inside the pool's owned source child.

Actual progress emits message/scanning, media-chunk, resolution/dialog and request-result phases. The sender observer preserves the original Future/enqueue point and directly awaits the existing budget coroutine; it creates no additional request task and changes no retry/flood/budget policy. Concurrent/background tasks cannot acquire another read's scope; deferred notifications stop on exit. Callback errors, apparent RPC errors, directly raised cancellation and logger failures do not alter batches or health. Async/noncallable callbacks refuse before I/O, unexpected returned coroutines close, and real task cancellation remains cancellation.

Known tgdata-owned sleeps emit in at-most10-second slices. SDK internal waits are deliberately unchanged: the watchdog must exceed a single allowed SDK sleep plus ordinary latency (default60s versus consumer120s). Repeated flood responses are individually visible; there is no timer that makes an unanswered request look alive. A heartbeat reports activity, never a receipt/count or account recovery decision. Pending replay remains local and needs no beat; original media verification, data hashes, source receipts and pool captures remain authoritative.

Public guidance is docs/batch_heartbeat.md and the README/smoke README entries. Version stays0.1; no batch metadata/schema change. ScrapeOps needs a later released dependency and its own heartbeat forwarding change. Its running tree was read only.

## Process and qualification

Warming/surfacing/triage8ee0a73; description9cde140; plan1 at58548d9; tailored promptae0c695 and same-session critique69ed69d (zero findings, REORDER for actual-component qualification). Complete prebuild1f4d2fa passed472 offline checks across17 suites plus3 demos. Formal fold21d3285 followed, then exact candidate adoption and productb789846. adoption.json ties all12 product files and98 Python sources to the qualified candidate.

The explicit no-new-branch instruction supersedes only the normal fresh-branch step. Model/effort GPT6 Astra/xhigh was verified from the current turn record. No cold agent or subagent review was substituted. The initial endless synthetic-history fixture and local authoring corrections are retained in prebuild/report.md; no expected product behavior was weakened and no architectural substitute was made. No runtime correction followed adoption.

## Full actual-branch result

**PASS:914 executed offline checks across31 suites, seven demos, three explicit live skips excluded.** New suite44:31/31. All old suites12–19/22–43 pass, including health, retry threshold, budgets, source progression, pool lifetime, worker subprocesses, album assembly and photo trails. The worker-process suite ran67 controlled subprocesses. All38 jobs exited0, no verification watchdog failure.

Python3.11.10 / Telethon1.45.0. All98 package/example Python files compile and pass Python3.7 grammar checks; native3.7 execution is not claimed.89 pre-existing Python files are unchanged. Product/source hashes remained stable during both runs and are identical between candidate and actual branch. Public Markdown local links and diff whitespace checks pass. verification/result.json and per-job output contain the complete evidence.

The new tests prove a real SDK chunked download outlasts a scaled silence watchdog, while a stuck chunk still cancels/cleans; exact retry/wait/charge and byte equality; scope/callback error isolation; pending-prefix preservation and replay; all four pool APIs and pool capture cancellation. Network is blocked and replies are synthetic; no deployed consumer, live intent or physical disk durability claim is made.

## Handoff

Worktree: `/private/tmp/tgdata-30-photo-trail-folding`. Branch: `feat/30-photo-trail-folding`. Product-only heartbeat commit: `b789846`; work evidence is separate. Original checkout `/Users/ns/Desktop/projects/telegram-group-scraper` remains on a47ba80 with the user's existing __version__ edit only. No Duncan files, credentials or real account state were changed.

Review gates for#37 are complete and PR38 merged the heartbeat into dev. PR36 remains the historical photo-trail PR. Heartbeat is not released to PyPI or installed in ScrapeOps. Preserve the archive and product branches; no new branch was created.

## Final review and merge

The later maintainer merge request authorized the remaining gates. Merge check8b9c0ec and fresh same-session critique fd6bbb1 passed;12 fresh histories found no defect. PR38 reused the existing product branch and merged into dev7d9840f at2026-10-15T08:06:00Z. Its actual merge candidate passed914 offline checks/7 demos and the published tree/parents match exactly. See [merge-report.md](merge-report.md). Earlier unmerged handoff sections above record the pre-review state. No new branch, release or consumer deployment.
