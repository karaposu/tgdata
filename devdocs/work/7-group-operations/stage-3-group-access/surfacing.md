---
model: gpt-6-astra
effort: max
---
# Stage3 triage surfacing

## User Input

Surface what #7 Stage3 group lookup and access checks touches, using merged dev30ba706,
its predecessor stages, old PR16 evidence, the installed Telethon1.45.0 and official API
references. Purpose: establish breadth and coverage for triage, not choose implementation.

## Traversal Trace

| # | Region | Item identifier | Relevance | Confidence | Recency annotation |
|---|---|---|---|---|---|
| 1 | contracts | source-input.md | core | HIGH | {source: filesystem, value: 2026-10-10T13:00:47.957367+00:00} |
| 2 | facade | tgdata/tgdata.py: TgData/_account_health_operation/get_account_health | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.910489+00:00} |
| 3 | ownership | tgdata/account_operation.py: verified handle/lifetime | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.879070+00:00} |
| 4 | factory | tgdata/connection_engine.py: _new_client/_account_operation/_AnswerEvidence | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.881875+00:00} |
| 5 | health | tgdata/owned_health.py: observation/evidence/group assertion | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.886076+00:00} |
| 6 | health | tgdata/health.py: classification/normalisation/isolation | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.883042+00:00} |
| 7 | budgets | tgdata/budget_client.py: request cost/admission | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.881386+00:00} |
| 8 | storage | tgdata/session_store.py: entity cache/store-backed session | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.887756+00:00} |
| 9 | models | tgdata/models.py: GroupInfo | core | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.885560+00:00} |
| 10 | existing-reads | tgdata/batch_engine.py: explicit peer/history results | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.880315+00:00} |
| 11 | existing-reads | tgdata/message_engine.py: GroupAccessError and entity lookup sites | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.885001+00:00} |
| 12 | public-surface | tgdata/__init__.py: exports | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.878583+00:00} |
| 13 | dependencies | setup.py: Telethon requirement | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.877424+00:00} |
| 14 | dependencies | requirements.txt | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.876821+00:00} |
| 15 | prior-attempt | old branch tgdata/group_operations.py | core | HIGH | {source: filesystem, value: 2026-10-05T17:55:15.592847+00:00} |
| 16 | prior-attempt | old branch #7 desc.md/pr-critic.md | core | HIGH | {source: filesystem, value: 2026-10-05T19:28:42.376926+00:00} |
| 17 | merged-foundation | Stage2 HANDOFF.md/accepted plan and PR critique (retained session) | core | HIGH | {source: filesystem, value: 2026-10-10T12:25:29.899775+00:00} |
| 18 | future-consumer | #17 existing-access routing desc.md | side | HIGH | {source: filesystem, value: 2026-10-07T21:19:40.376169+00:00} |
| 19 | sdk | Telethon1.45 UserMethods.get_entity/_call | core | HIGH | {source: filesystem, value: 2026-10-03T09:09:32.893062+00:00} |
| 20 | sdk | Telethon1.45 generated Chat/Channel/ChatInvite shapes (layer229) | core | HIGH | {source: filesystem, value: 2026-10-03T09:09:32.917819+00:00} |
| 21 | sdk | Telethon1.45 MTProtoSender/RequestState error association (retained session) | core | HIGH | {source: filesystem, value: 2026-10-03T09:09:32.899341+00:00} |
| 22 | tests | test32 real-SDK operation fixture | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.902728+00:00} |
| 23 | tests | test33 owned-health fixture and sender-built replies | sub | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.903061+00:00} |
| 24 | vendor | https://core.telegram.org/method/messages.checkChatInvite | core | HIGH | {source: none, value: null} |
| 25 | vendor | https://core.telegram.org/method/messages.getHistory | core | HIGH | {source: none, value: null} |
| 26 | vendor | https://core.telegram.org/constructor/chatInvitePeek | core | HIGH | {source: none, value: null} |
| 27 | workflow | CONTRIBUTING.md: stages/scope/checkpoints | umbrella | HIGH | {source: filesystem, value: 2026-10-10T12:58:17.842112+00:00} |

## State Summary

**Territory:** the listed current modules/interfaces, scoped historical evidence and
specific official references. **Purpose:** classify Stage3 breadth. Artifact mode,
signal-first, explicit bounded territory; boundary discovery was not needed.

**Coverage:** the listed regions are confirmed at interface/function resolution,
using current reads and retained full implementation/review context. Existing-reads
is scanned at the relevant group-resolution/error seams; no legacy rewrite is in scope.
Unmerged #17 is a side reference, not a prerequisite or source to merge.

**Confirmed absent:** no current public lookup_group/check_group_access or joining
API on dev; no Stage3 parked description or rejecting PR review; no applicable AGENTS.md
or PROJECT_SPECIFICS.md found. These are absence observations, not permission to invent
a general resolver or another issue.

**Concept names / provenance:** verified owner (2–4); request evidence (5–6,21);
read admission (7); cached peer (8–11,19); group metadata (9,20); read-only preview
(20,24,26); bounded history read (25); exact source failure (16,19,21); staged task
(1,17,27). These are labels, not interpretation or architecture selection.

**Recency distribution (metadata only):**
- contracts: newest=2026-10-10T13:00:47.957367+00:00, oldest=2026-10-10T13:00:47.957367+00:00, no-mtime-count=0, total-items=1
- facade: newest=2026-10-10T12:58:17.910489+00:00, oldest=2026-10-10T12:58:17.910489+00:00, no-mtime-count=0, total-items=1
- ownership: newest=2026-10-10T12:58:17.879070+00:00, oldest=2026-10-10T12:58:17.879070+00:00, no-mtime-count=0, total-items=1
- factory: newest=2026-10-10T12:58:17.881875+00:00, oldest=2026-10-10T12:58:17.881875+00:00, no-mtime-count=0, total-items=1
- health: newest=2026-10-10T12:58:17.886076+00:00, oldest=2026-10-10T12:58:17.883042+00:00, no-mtime-count=0, total-items=2
- budgets: newest=2026-10-10T12:58:17.881386+00:00, oldest=2026-10-10T12:58:17.881386+00:00, no-mtime-count=0, total-items=1
- storage: newest=2026-10-10T12:58:17.887756+00:00, oldest=2026-10-10T12:58:17.887756+00:00, no-mtime-count=0, total-items=1
- models: newest=2026-10-10T12:58:17.885560+00:00, oldest=2026-10-10T12:58:17.885560+00:00, no-mtime-count=0, total-items=1
- existing-reads: newest=2026-10-10T12:58:17.885001+00:00, oldest=2026-10-10T12:58:17.880315+00:00, no-mtime-count=0, total-items=2
- public-surface: newest=2026-10-10T12:58:17.878583+00:00, oldest=2026-10-10T12:58:17.878583+00:00, no-mtime-count=0, total-items=1
- dependencies: newest=2026-10-10T12:58:17.877424+00:00, oldest=2026-10-10T12:58:17.876821+00:00, no-mtime-count=0, total-items=2
- prior-attempt: newest=2026-10-05T19:28:42.376926+00:00, oldest=2026-10-05T17:55:15.592847+00:00, no-mtime-count=0, total-items=2
- merged-foundation: newest=2026-10-10T12:25:29.899775+00:00, oldest=2026-10-10T12:25:29.899775+00:00, no-mtime-count=0, total-items=1
- future-consumer: newest=2026-10-07T21:19:40.376169+00:00, oldest=2026-10-07T21:19:40.376169+00:00, no-mtime-count=0, total-items=1
- sdk: newest=2026-10-03T09:09:32.917819+00:00, oldest=2026-10-03T09:09:32.893062+00:00, no-mtime-count=0, total-items=3
- tests: newest=2026-10-10T12:58:17.903061+00:00, oldest=2026-10-10T12:58:17.902728+00:00, no-mtime-count=0, total-items=2
- vendor: newest=null, oldest=null, no-mtime-count=3, total-items=3
- workflow: newest=2026-10-10T12:58:17.842112+00:00, oldest=2026-10-10T12:58:17.842112+00:00, no-mtime-count=0, total-items=1

**Frontier for deeper inquiry:** response/membership/read-access distinctions;
reference resolution bounds; malformed/missing peer evidence; mapping domain results
to Stage2 explicit group recovery; portable result ownership; SDK/request fixtures.
These relevant items are included, not filtered by uncertainty or filesystem age.

**Workspace populated:** true; populated-at 2026-10-10T13:00:47.957769+00:00;
extent:27 tagged items in the bounded territory. Items remain in this session context;
this artifact intentionally contains no copied item content.

**Telemetry:**3 cycles (current contract/source, historical consumers, SDK/vendor);
27 items: 18 core, 7 sub, 1 side, 1 umbrella;24 with mtime,3 without. No overload trigger.
Checked missed relevance, territory binding, workspace/artifact agreement, recency bias,
interpretive overstep and purpose loss. Relevant unknowns retained in the frontier.
**Self-assessment: PROCEED** — sufficient breadth for triage; deeper meaning is the
next inquiry, not a silent assumption in this surface map.
