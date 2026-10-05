---
model: unknown
effort: unknown
---

# Triage — issue #6

## User Input

Use task-impl on GitHub #6, “Return fetched messages as a stable, versioned raw batch”.
The request asks for messages, an explicit next-message cursor and media files
named by content hash, so repeat delivery is recognizable.

**Weight:** feature-heavy. A new public data contract serves readers and future
processors/worker #10. Cursor advancement, serialization and file publication
cross boundaries; lost records or unstable identity can be silent.

**Warmth:** retained from full source reads during #5 and #9 and the #9 fresh
review/merged-tree verification. Base `d39a4df` is the tested #9 merge on dev.
Models/exports and relevant SDK iterator/download paths were read for #6.
No new cold-session archaeology pass is needed.

**Traverse:** required by CONTRIBUTING §5: this creates a data contract that
later worker/processor work will stand on, and couples cursor progress to
messages and media publication. Run the full pass in this folder's `traverse/`
before writing the feature description.

**Related-issue sweep:** all ten open/closed issue titles read. Reuse #6; no
same-task duplicate. #10 is the later consumer. #9 is already integrated and
its quota interruption semantics are relevant; #5's session storage and #4's
health reporting are existing constraints. #7 group operations and #8 login
are independent. #3 remains outside this offline task. Issue #6 and #10 have
no additional discussion decisions. Historical `devdocs/scoped/6` is an
unrelated date-range fix and is not this issue's specification.

## Traversal Trace

Mode: artifact; entry: signal-first; territory: explicit-bounded. Purpose:
surface what the versioned message-batch contract touches, not select its
schema or implementation. Three passes: existing records/exports, read/media
and interruption paths, then vendor/package/tests/adjacent issues. Recency
cells are `source / value`, descriptive only.

| # | Region | Item identifier | Relevance | Confidence | Recency (UTC) |
|---|---|---|---|---|---|
| 1 | records | `tgdata/models.py` — MessageData / GroupInfo | core | HIGH | filesystem / 2026-10-03T07:54:30.530271+00:00 |
| 2 | readers | `tgdata/message_engine.py` — fetch_messages / _process_message / resume state | core | HIGH | filesystem / 2026-10-05T09:14:38.468091+00:00 |
| 3 | public API | `tgdata/tgdata.py` — get_messages / search_messages / delegation | core | HIGH | filesystem / 2026-10-05T09:40:30.686672+00:00 |
| 4 | exports | `tgdata/utils.py` — export_to_json / export_to_csv | core | HIGH | filesystem / 2026-09-30T07:14:29.956982+00:00 |
| 5 | media | `tgdata/message_engine.py` — _download_or_reuse / download_media_by_id | core | HIGH | filesystem / 2026-10-05T09:14:38.468091+00:00 |
| 6 | connections | `tgdata/connection_engine.py` — session / factory / authentication | sub | HIGH | filesystem / 2026-10-05T09:40:30.662542+00:00 |
| 7 | quota | `tgdata/budget_client.py` — send admission / iterator wrapping | core | HIGH | filesystem / 2026-10-05T09:07:29.764286+00:00 |
| 8 | quota | `tgdata/read_budget.py` — local errors / partial_result | sub | HIGH | filesystem / 2026-10-05T09:02:33.056613+00:00 |
| 9 | health | `tgdata/health.py` — classification / _reported context | sub | HIGH | filesystem / 2026-10-03T19:35:48.952728+00:00 |
| 10 | package | `tgdata/__init__.py` — public exports | sub | HIGH | filesystem / 2026-10-05T09:14:38.445488+00:00 |
| 11 | docs | `README.md` — message/media/budget contracts | sub | HIGH | filesystem / 2026-10-05T09:41:27.638572+00:00 |
| 12 | tests | `tgdata/smoke_tests/test_18_read_budget.py` — real SDK scripted-sender fixtures / quota interruptions | core | HIGH | filesystem / 2026-10-05T09:40:30.639272+00:00 |
| 13 | tests | `tgdata/smoke_tests/README.md` — offline/live suite inventory | sub | HIGH | filesystem / 2026-10-05T09:41:27.663326+00:00 |
| 14 | package | `setup.py` — package discovery / Python and Telethon bounds | side | HIGH | filesystem / 2026-10-03T07:29:10.872688+00:00 |
| 15 | vendor | `.venv/lib/python3.11/site-packages/telethon/client/messages.py` — _MessagesIter / _IDsIter | core | HIGH | filesystem / 2026-10-03T09:09:32.892107+00:00 |
| 16 | vendor | `.venv/lib/python3.11/site-packages/telethon/client/downloads.py` — download_media / file object writes / reference refresh | core | HIGH | filesystem / 2026-10-03T09:09:32.891600+00:00 |
| 17 | vendor | `.venv/lib/python3.11/site-packages/telethon/requestiter.py` — iterator completion / buffered state | sub | HIGH | filesystem / 2026-10-03T09:09:32.887635+00:00 |
| 18 | history | `devdocs/scoped/6/desc.md` — unrelated historical date-range fix | side | HIGH | filesystem / 2026-07-19T20:10:45.369120+00:00 |
| 19 | issues | GitHub #6 original request and empty discussion | core | HIGH | none / null |
| 20 | issues | GitHub #10 worker request and empty discussion | sub | HIGH | none / null |
| 21 | issues | all open/closed issue titles; #9 merged outcome | sub | HIGH | none / null |

## State Summary

Territory: tgdata's message/public/media/export/quota paths, relevant Telethon
1.x control flow, package/tests/docs and GitHub #6/#10. Purpose: identify the
inputs for a stable batch contract with explicit continuation and media identity.
The listed implementations are confirmed at function resolution, with whole
module reads retained in this warmed session. Historical live demo scripts are
known as live examples, not claimed to be an offline suite.

Confirmed absent: a versioned raw envelope, a batch identity, a returned cursor
contract, a content-addressed media publisher and a worker/receiving service.
Existing DataFrame exports, batch callbacks and message-id filenames are
present and surfaced; absence here concerns the requested new contract only.

Concept names and provenance: message record → 1; scan/resume state → 2;
public reader → 3; JSON export → 4; media file identity → 5/16; shared
admission → 7/8; local versus Telegram error → 9; SDK paging → 15/17;
future receiving consumer → 20. These are names, not an adjudicated design.

Recency distribution by region (oldest / newest / no-mtime count / total):
- records: 2026-10-03T07:54:30.530271+00:00 / 2026-10-03T07:54:30.530271+00:00 / 0 / 1
- readers: 2026-10-05T09:14:38.468091+00:00 / 2026-10-05T09:14:38.468091+00:00 / 0 / 1
- public API: 2026-10-05T09:40:30.686672+00:00 / 2026-10-05T09:40:30.686672+00:00 / 0 / 1
- exports: 2026-09-30T07:14:29.956982+00:00 / 2026-09-30T07:14:29.956982+00:00 / 0 / 1
- media: 2026-10-05T09:14:38.468091+00:00 / 2026-10-05T09:14:38.468091+00:00 / 0 / 1
- connections: 2026-10-05T09:40:30.662542+00:00 / 2026-10-05T09:40:30.662542+00:00 / 0 / 1
- quota: 2026-10-05T09:02:33.056613+00:00 / 2026-10-05T09:07:29.764286+00:00 / 0 / 2
- health: 2026-10-03T19:35:48.952728+00:00 / 2026-10-03T19:35:48.952728+00:00 / 0 / 1
- package: 2026-10-03T07:29:10.872688+00:00 / 2026-10-05T09:14:38.445488+00:00 / 0 / 2
- docs: 2026-10-05T09:41:27.638572+00:00 / 2026-10-05T09:41:27.638572+00:00 / 0 / 1
- tests: 2026-10-05T09:40:30.639272+00:00 / 2026-10-05T09:41:27.663326+00:00 / 0 / 2
- vendor: 2026-10-03T09:09:32.887635+00:00 / 2026-10-03T09:09:32.892107+00:00 / 0 / 3
- history: 2026-07-19T20:10:45.369120+00:00 / 2026-07-19T20:10:45.369120+00:00 / 0 / 1
- issues: null / null / 3 / 3

Workspace: populated=true; populated-at=2026-10-05T10:46:11.742992+00:00; extent=all surfaced core
regions at function resolution. No uncovered core region or overload flag.

## Frontier

Resolve what “raw” and “repeat upload” mean; distinguish replaying a saved
snapshot from fetching a mutable Telegram history again. Establish cursor
ownership and advancement when records/media fail, stable IDs/JSON types,
media modes and hash publication, and how quota partials remain resumable.
These questions belong to traverse and the subsequent description/plan.

## Telemetry and self-assessment

Three cycles; 21 items; tags {'core': 10, 'sub': 9, 'side': 2}. Eighteen filesystem-backed
items and three remote items without mtime. Boundary discovery not needed;
workspace overload did not fire. Coverage converged; uncertain items were not
excluded. Checked missed relevance, irrelevant/over-coverage, territory binding,
artifact sufficiency, workspace consistency, recency biases, interpretive
overstep, purpose loss and downstream self-coupling. **PROCEED** to traverse.
