---
model: unknown
effort: unknown
---

# Surfacing — stable batches, continuation and replay

## User Input

Purpose and variants: `../_branch.md` (derived from the full issue request in
`../source-input.md`). Territory: tgdata, relevant installed Telethon source,
existing public docs and #6/#10. Prior artifact: `../../triage.md`; prior workspace:
same warmed session, explicitly retained. Refined purpose: surface evidence
for the four raw-batch/replay readings without selecting among them.

## Traversal Trace

Artifact mode; signal-first entry; explicit-bounded territory. Entries 1–21
carry the prior trace with relevance rechecked for this purpose. Entries 22–27
record the additional serialization/identity/interface/framing reads. No item
is filtered by recency. Cells record source/value.

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
| 22 | vendor | `.venv/lib/python3.11/site-packages/telethon/tl/tlobject.py` — TLObject.to_dict / to_json / _json_default | core | HIGH | filesystem / 2026-10-03T09:09:32.903513+00:00 |
| 23 | identity | `.venv/lib/python3.11/site-packages/telethon/utils.py` — get_peer_id implementation | core | HIGH | filesystem / 2026-10-03T09:09:32.888304+00:00 |
| 24 | vendor | `.venv/lib/python3.11/site-packages/telethon/tl/custom/message.py` — Message constructor interface / metadata access | core | HIGH | filesystem / 2026-10-03T09:09:32.906527+00:00 |
| 25 | compatibility | `README.md` — existing media reuse / DataFrame and callback promises | sub | HIGH | filesystem / 2026-10-05T09:41:27.638572+00:00 |
| 26 | framing | `devdocs/work/6-versioned-message-batches/traverse/articulate_simple.md` — I1 MQ1–4 / WHY / four variants | core | HIGH | filesystem / 2026-10-05T10:49:34.386156+00:00 |
| 27 | framing | `devdocs/work/6-versioned-message-batches/traverse/_branch.md` — derived Question / Goal / Scope | core | HIGH | filesystem / 2026-10-05T10:50:44.056815+00:00 |

## State Summary

Coverage: records, readers, exports, media, connections, quotas, health, package,
docs, tests, history and issue inputs are confirmed at the resolutions recorded
in the trace. New serialization and peer-identity functions are confirmed in
full; the expanded vendor Message interface is confirmed at constructor/field
resolution. New framing inputs are confirmed in full. Live server mutation and
remote delivery behavior are not observed by source inspection.

Confirmed absent in the traversed repository: a versioned raw-envelope model,
public batch continuation object, content-addressed publisher, batch identity
and receiving worker. No existing batch-format fixture/schema constrains a v1.

Concept names with provenance: presented row (1/2/4); scan position (2/15/17);
media artifact (5/16/25); admission boundary (7/8); failure classification (9);
wire JSON (22); peer namespace (23); message metadata interface (24);
replay/refetch ambiguity (26/27); downstream worker (20).

Recency distribution (descriptive, derived from the trace):

```json
{
  "records": {
    "newest": "2026-10-03T07:54:30.530271+00:00",
    "oldest": "2026-10-03T07:54:30.530271+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "readers": {
    "newest": "2026-10-05T09:14:38.468091+00:00",
    "oldest": "2026-10-05T09:14:38.468091+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "public API": {
    "newest": "2026-10-05T09:40:30.686672+00:00",
    "oldest": "2026-10-05T09:40:30.686672+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "exports": {
    "newest": "2026-09-30T07:14:29.956982+00:00",
    "oldest": "2026-09-30T07:14:29.956982+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "media": {
    "newest": "2026-10-05T09:14:38.468091+00:00",
    "oldest": "2026-10-05T09:14:38.468091+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "connections": {
    "newest": "2026-10-05T09:40:30.662542+00:00",
    "oldest": "2026-10-05T09:40:30.662542+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "quota": {
    "newest": "2026-10-05T09:07:29.764286+00:00",
    "oldest": "2026-10-05T09:02:33.056613+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "health": {
    "newest": "2026-10-03T19:35:48.952728+00:00",
    "oldest": "2026-10-03T19:35:48.952728+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "package": {
    "newest": "2026-10-05T09:14:38.445488+00:00",
    "oldest": "2026-10-03T07:29:10.872688+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "docs": {
    "newest": "2026-10-05T09:41:27.638572+00:00",
    "oldest": "2026-10-05T09:41:27.638572+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "tests": {
    "newest": "2026-10-05T09:41:27.663326+00:00",
    "oldest": "2026-10-05T09:40:30.639272+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  },
  "vendor": {
    "newest": "2026-10-03T09:09:32.906527+00:00",
    "oldest": "2026-10-03T09:09:32.887635+00:00",
    "no-mtime-count": 0,
    "total-items": 5
  },
  "history": {
    "newest": "2026-07-19T20:10:45.369120+00:00",
    "oldest": "2026-07-19T20:10:45.369120+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "issues": {
    "newest": null,
    "oldest": null,
    "no-mtime-count": 3,
    "total-items": 3
  },
  "identity": {
    "newest": "2026-10-03T09:09:32.888304+00:00",
    "oldest": "2026-10-03T09:09:32.888304+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "compatibility": {
    "newest": "2026-10-05T09:41:27.638572+00:00",
    "oldest": "2026-10-05T09:41:27.638572+00:00",
    "no-mtime-count": 0,
    "total-items": 1
  },
  "framing": {
    "newest": "2026-10-05T10:50:44.056815+00:00",
    "oldest": "2026-10-05T10:49:34.386156+00:00",
    "no-mtime-count": 0,
    "total-items": 2
  }
}
```

Workspace: populated=true; populated-at=2026-10-05T10:53:50.574600+00:00; extent=27 surfaced items,
all core regions confirmed at the stated resolution. No overload or uncovered
local-core frontier. Live/server/receiver boundaries are explicit, not supplied
by this pass. No reinvocation is required before sensemaking.

## Frontier

Interpret the four variants against the actual export, filtering, identity and
media boundaries. Determine whether repeated delivery refers to saved snapshots
or newly observed Telegram state; distinguish cursor progress from presentation
rows and complete media. Decide which version guarantees can be owned by tgdata
without implementing the later receiver. Behavioral checks belong downstream.

## Telemetry and self-assessment

Two cycles in this invocation (prior record/reader paths, then wire/identity/
framing); 27 items: 15 core, 10 sub, two side, zero umbrella. Boundary discovery
not fired. Content and tags are retained in the session; the artifact holds
identifiers and traversal state, not item contents. Checked all nine operational
modes and the three identity-eroding modes, with no flags. Convergence holds;
manual required-section/metadata check 7/7. **PROCEED**.
