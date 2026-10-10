---
model: gpt-6-astra
effort: max
---
# #7 Stage 3 source input

User request: `$task-impl` for **Stage3: Group lookup and access checks — resolve a
group's details and check whether the account can access it**. The user supplied
the full task-impl skill and authorized its description → plan → critic-d → fold
→ implementation → verification sequence. No separate permission is needed between
these checkpoints. PR publication, PR review and merge are later requested gates.

Issue7 is the existing feature. Stage1 (verified account/temporary-client lifetime)
and Stage2 (owned health) are merged in dev30ba706. Stage4 join allowance and Stage5
joining remain outside this stage. The old broad PR16 implementation is historical
reference only; its native-error translation and cached-health ownership assumptions
must not be inherited. Its single rejecting review is not a rejection of this new
stage. Stage2's accepted rework and its own separate rejection history are preserved
on feat/7-account-health-ownership; this Stage3 folder starts with no parked desc or
rejected PR critique.

Scope constraints retained from the user: Telethon1.45.0 only; keep the design
bounded, avoid overengineering, do not commit duncan or unrelated guide changes.
Original checkout stays on feat/7-group-operations with its existing untracked
HANDOFF.md/todo.md. The new branch is feat/7-group-lookup-access, created natively
from issue7/dev with gh issue develop, in /private/tmp/tgdata-7-stage3-group-access.

Session is warm from Stage1/Stage2 implementation, reviews and merge; current SDK,
models, factory, ownership, health, budget and public interfaces are being refreshed.
Base30ba706 is the ancestor record. No new archaeology refresh is claimed. Model/
effort provenance remains the retained same-session gpt-6-astra/max record, latest
recorded turn2026-10-07T05:34:50.039Z, not an invented current selector reading.

Description input location for the delegated task-desc pass is explicitly this
folder. Plan target is its desc.md; repository convention names the plan plan.md.
Skill dispatcher is unavailable, so owning skill sources are read/executed in this
session. Traverse runs sequentially without subagents if §5 calls for it.

No live Telegram action, login or membership change is part of this implementation
run. Offline SDK/SQLite composition and official method semantics must be identified
separately; synthetic replies cannot establish live server permission behavior.
