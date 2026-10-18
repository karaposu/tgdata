Add opt-in, bounded concurrent media downloads to tgdata so small files can overlap their network waits. ScrapeOps should only pass a setting; scheduling belongs in tgdata.

**Requested behavior.** A setting such as `download_concurrency` (final API to qualify), default **1** for compatibility. Try **3** as an initial opt-in setting and measure it. Apply it to both `get_messages` and `get_message_batch`, and make it usable through daily continuation, backfill and account-pool reads. Do not require extra Telegram accounts or parallelize history pagination to achieve this.

**Motivation reported by the caller.** Small photos around 131 KB took roughly 0.4 seconds each, with aggregate throughput reported around 458 KB/s and no rate-limit waits visible in the inspected logs. The hypothesis is that overlapping latency will help; 2–3× more files per minute with 3–4 concurrent downloads is an unmeasured estimate. This issue does not establish that latency is the only bottleneck, that Telegram is not throttling, or that concurrency 3 is universally safe.

**Code confirmed at dev `d8232d1`.** The legacy reader awaits `_process_message` inside its message loop, and that function awaits media downloads. The batch reader awaits `download_blob` before appending each record. Neither loop schedules multiple files concurrently:
- [Legacy reader and media processing](https://github.com/karaposu/tgdata/blob/d8232d1/tgdata/message_engine.py#L260)
- [Batch download and completed-record handling](https://github.com/karaposu/tgdata/blob/d8232d1/tgdata/batch_engine.py#L211)
- [Completed-file publication](https://github.com/karaposu/tgdata/blob/d8232d1/tgdata/batch_files.py#L145)

**Requirements to qualify before implementation:**
- Default 1 preserves each reader's documented ordering, output, file reuse, error and callback behavior. Reject invalid settings before source work. Bound active downloads, queued work and memory; do not create one task per message for unlimited history.
- Downloads may finish out of order, but returned records and batch callbacks retain source order. A batch's partial result/cursor must never skip a failed or unfinished earlier message just because a later download completed. Preserve MessageBatch v1 identities, acknowledgment rules, album/photo-trail integration and restart behavior.
- Cancellation and failure stop new work and settle all owned downloads before releasing/disconnecting their client. Preserve the original exception and cancellation semantics; cleanup failure must not replace it. No detached tasks, continued writes after return, falsely complete files or local file errors reported as Telegram health failures. Define treatment of already completed later files without advancing progress past the gap.
- Respect existing per-account budgets, health ownership and SDK wait/retry policy. On an observed rate-limit response, prevent further affected work from being scheduled and honor the applicable wait/propagation policy with bounded retries. No independent worker retry storm or silent change to a shared client's wait settings. Define whether the limit is per operation/client/account and how simultaneous calls avoid multiplying intended account load; cross-process coordination is outside this request.
- Preserve real download progress heartbeats. Define heartbeat/watchdog behavior when several downloads progress while one stalls; unrelated progress must not permit an indefinitely stuck operation. History pacing and media concurrency remain separate controls.
- Qualify the exposed surfaces explicitly: disk versus in-memory media, optional profile photos, and `download_media_by_id`. Do not accidentally parallelize sender resolution or unrelated source operations by wrapping the entire message processor in unrestricted tasks.

**Validation requested.** Test concurrency 1 and a small N using actual SDK/public reader paths with controlled transport: enforce active/queue bounds, force out-of-order completion, fail an early file after later successes, cancel during downloads and cleanup, exercise rate-limit/budget refusals, cache/content-hash collisions and disk failures, and verify heartbeat plus daily/backfill/pool propagation. Then run a separately authorized, bounded read-only benchmark on an existing group with Telethon 1.45.0: comparable cold-cache media sets at 1 versus 3, record files/minute, bytes/second, errors/waits and peak concurrency. Do not induce flooding to discover limits. Report measured gains; no promised multiplier.

**Boundary.** Parallelism across files, not concurrent chunks within one large file. No automatic account rotation, adaptive throughput controller, distributed scheduler, dependency upgrade or change to durable progress semantics. Implementation/design is not started by filing this issue.

**Related:** #6 (batch contract), #9 (read budgets), #17 (account pool), #18/#19 (daily/backfill), #37 (heartbeats). ScrapeOps supplies the option once tgdata supports it.

---
## Pipeline status

**Direction:** open to implement — ready for qualification; no known prerequisite issue.
**Priority:** P2 — improve daily media throughput; validate the benefit before changing deployments.
**Path:** feature (`enhancement`).
**Weight:** not decided yet; triage must assess concurrency, cleanup and multiple consumers.
**Branch:** none created for this issue. Existing maintainer instruction is no new branch; select a suitable existing branch when implementation is requested.
**Docs:** none yet; qualification artifacts belong in this issue's work folder on the chosen archive branch.
**Session warmth (step W):** filing-only inspection of both readers, blob publication and public entry points at dev `d8232d1`. Full implementation warming/triage has not run.

- [ ] **T — triage** — surface affected contracts and select weight
- [ ] **0 — traverse** — run if warranted; otherwise record why not needed
- [ ] **1 — desc** — qualify this request; post the description as a comment
- [ ] **2 — plan** — blocker-gated implementation plan
- [ ] **3 — critic** — fresh plan critique
- [ ] **4 — fold** — selected findings and required real-component prebuild
- [ ] **5 — implement** — code, docs and meaningful tests
- [ ] **6 — merge gate** — merge check, then PR
- [ ] **7 — PR critic** — fresh diff/plan critique, committed and posted

Resume with CONTRIBUTING.md and triage; preserve the reported observations separately from measured evidence. No implementation, live benchmark or deployment has been performed for this issue.
