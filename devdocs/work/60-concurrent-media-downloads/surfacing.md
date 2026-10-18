# Issue60 triage surfacing
## User Input
Surface what opt-in bounded concurrent downloads touches in current tgdata.
## Reception
Artifact / signal-first; bounded current merged product, its public consumers,
actual Telethon1.45 and adjacent ownership tests. Same-session prior workspace used.
## Traversal Trace
1. readers: `tgdata/message_engine.py` — core, HIGH; recency 2026-10-16T09:36:36.597883+00:00
2. readers: `tgdata/batch_engine.py` — core, HIGH; recency 2026-10-16T09:36:36.592085+00:00
3. files: `tgdata/batch_files.py` — core, HIGH; recency 2026-10-16T09:36:36.592374+00:00
4. observation: `tgdata/batch_heartbeat.py` — core, HIGH; recency 2026-10-16T09:36:36.592684+00:00
5. observation: `tgdata/health.py` — core, HIGH; recency 2026-10-16T09:36:36.595543+00:00
6. source: `tgdata/connection_engine.py` — core, HIGH; recency 2026-10-16T09:36:36.593818+00:00
7. source: `tgdata/budget_client.py` — core, HIGH; recency 2026-10-16T09:36:36.593163+00:00
8. delivery: `tgdata/sync_engine.py` — core, HIGH; recency 2026-10-16T09:36:36.626524+00:00
9. delivery: `tgdata/backfill_engine.py` — core, HIGH; recency 2026-10-16T09:36:36.591297+00:00
10. pool: `tgdata/account_pool.py` — core, HIGH; recency 2026-10-16T09:36:36.590070+00:00
11. pool: `tgdata/pool_source.py` — core, HIGH; recency 2026-10-16T09:36:36.600321+00:00
12. pool: `tgdata/pool_lifecycle.py` — sub, HIGH; recency 2026-10-16T09:36:36.599318+00:00
13. pool: `tgdata/pool_observation.py` — sub, HIGH; recency 2026-10-16T09:36:36.599692+00:00
14. tests: `tgdata/smoke_tests/test_44_batch_heartbeat.py` — core, HIGH; recency 2026-10-16T09:36:36.623925+00:00
15. facade: `tgdata/tgdata.py` — core, HIGH; recency 2026-10-16T09:36:36.627174+00:00
16. policy: `CONTRIBUTING.md` — umbrella, HIGH; recency 2026-10-16T09:36:36.558662+00:00
17. SDK: installed Telethon1.45 UserMethods._call, _DirectDownloadIter,
DownloadMethods._download_file, TelegramBaseClient._get_cdn_client — core,HIGH;
recency: source none,value null (inspected through Python source introspection).
18. Vendor: https://docs.telethon.dev/en/stable/modules/client.html and
https://docs.telethon.dev/en/stable/quick-references/faq.html — sub,HIGH;
recency: source none,value null.
## State Summary
Purpose: identify scope before weight/design. Coverage: readers/files/request-budget/
heartbeat/pool source and lifecycle confirmed at implementation resolution; health,
facade/backfill/pool orchestration confirmed relevant paths; remaining whole consumer
contracts and additional tests are frontier for planning. No feature-owned concurrent
media scheduler exists in traversed readers. Concepts: ordered completion(prefix,
entries1–2), blob publication(3), task ownership(4–6,12–13), sender admission(7,17),
receipt replay(8–10), configured source policy(11,17), live performance(18).
Recency per local item above is descriptive only; no item filtered by timestamp.
Workspace populated now,18 entries/core14 sub3 umbrella1; coverage not exhaustive
implementation qualification. Four region cycles, boundary discovery unnecessary.
## Frontier / self-check
FLAG: SDK hidden waits/exported/CDN sender lifetimes, concurrent operation scope,
child observation ownership and stalled-first-prefix behavior need focused traverse.
No claim of measured speedup or safe Telegram concurrency. No omitted uncertain item;
missed-relevance/over-coverage/territory/recency/artifact checks reviewed. Triage can
weigh the multiple consumers, but the frontier must resolve before description.
