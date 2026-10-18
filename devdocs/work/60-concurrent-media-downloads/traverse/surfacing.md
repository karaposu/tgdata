# Surfacing — media ownership inquiry
## User Input
Territory: current tgdata read/media/source/progress paths and installed Telethon1.45.
Purpose: draw evidence for all four articulations in _branch.md. Artifact/signal-first;
explicit-bounded; same-session prior workspace ../surfacing.md, refined to ownership.
## Traversal Trace
1. Readers: message_engine.fetch_messages/_process_message and BatchEngine._fetch_batch
   — core,HIGH; local recency in ../surfacing.md entries1–2.
2. Local artifacts: batch_files.download_blob/_owned_stream/_publish and legacy
   _download_or_reuse — core,HIGH; local recency prior entries1,3.
3. Task observers: health._Call/_CURRENT/_SleepCapture, batch_heartbeat._Observer/
   _current and account_operation._AccountOperation — core,HIGH; local provenance.
4. Source requests: connection_engine._client_class/_PerCallFloodThreshold/session,
   budget_client._BudgetSender/_request_cost — core,HIGH; prior entries6–7.
5. SDK request/download paths: UserMethods._call, _DirectDownloadIter, _download_file,
   _get_cdn_client — core,HIGH; source none,mtime null (installed introspection).
6. SDK lifetime observation: ../evidence/sdk_lifetimes.py and .json — core,HIGH;
   filesystem timestamp captured below; actual SDK path/controlled transport.
7. Existing consumers: SyncEngine.prepare/acknowledge, BackfillEngine.prepare,
   AccountPool._read/read/get_message_batch/sync_group/prepare_backfill,
   _OwnedSource.run/session, pool_lifecycle — core,HIGH; prior entries8–12.
8. Existing probes: smoke19 actual SDK/files fixtures, smoke18 budget sender,
   smoke44 task-scope/heartbeat/public consumers — sub,HIGH; filesystem below.
9. Vendor FAQ/client wait documentation — sub,HIGH; source none,mtime null.
## State Summary
Confirmed: all surfaced implementation seams at required purpose resolution. Consumer
forwarding/receipt paths read; no global account download gate found in these paths.
No concurrent media abstraction found. External live timing remains unknown, not a
source of correctness proof. Recency descriptive only, no relevance filtering.
Concept names/provenance: prepared-prefix(1), temporary output(2), explicit task
membership(3), retry admission(4–5), borrowed-sender lifetime(5–6), replay/ack(7),
no-network native probes(8), measured throughput versus concurrency policy(9).
Workspace populated, three cycles,9 trace groups/core7 sub2; script absent, manual
trace/tag/provenance/coverage/absence/frontier/metadata checks7/7. PROCEED.
## Frontier
Compare coordination extents and implicit versus explicit task ownership; source
wait versus propagated failure; row versus durable-batch completion. SDK cancellation
observation is evidence, not a prescribed solution. Live gain remains unmeasured.
## Recency metadata
- tgdata/account_operation.py: source filesystem, value 2026-10-16T09:36:36.589523+00:00.
- devdocs/work/60-concurrent-media-downloads/evidence/sdk_lifetimes.py: source filesystem, value 2026-10-18T05:17:37.466549+00:00.
- devdocs/work/60-concurrent-media-downloads/evidence/sdk_lifetimes.json: source filesystem, value 2026-10-18T05:17:38.420515+00:00.
- tgdata/smoke_tests/test_19_message_batches.py: source filesystem, value 2026-10-16T09:36:36.614404+00:00.
- tgdata/smoke_tests/test_18_read_budget.py: source filesystem, value 2026-10-16T09:36:36.614000+00:00.
