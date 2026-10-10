# Fresh plan critic — #7 Stage 3

Subject: revision 1 of plan.md beside this file, its desc.md and completed
traverse/finding.md, against merged dev 30ba706 and installed Telethon 1.45.0.
Run sequentially in this session. This is the first Stage 3 plan review, not a PR
review or another rejection of the abandoned broad implementation.

Create critic.md beside plan.md. Start with model/effort frontmatter from current
session evidence (unknown if unavailable), then a document-level verdict, falsifier,
high-level summary, ranked Premise Inventory, Restart Check, Inherited Lessons,
and findings. Keep architectural premises separate from ordinary implementation risks.

Choose exactly IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN,
REORDER — TEST BEFORE BUILD, or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER when
most reproduced failures belong elsewhere). Under verdicts 1–3 name the cheapest
observation that would kill the plan and whether it is affordable now, including
cost/access. An affordable unrun architectural falsifier forces REORDER: specify
experiment, cost, first dependent step, passing result and killing result. A wrong
premise forces deprecation and the skill's blocker procedure; do not patch it.

Read declared blockers first. None are currently open; verify this rather than
rediscovering the explicitly preserved hashless CommunityForbidden/SQLite failure.
For each unproven premise state first dependent step, waste if false, scheduled test,
cheapest earlier test and actual coverage. Rank by wasted work. Synthetic server
replies do not establish live Telegram behavior; they can exercise real SDK parsing,
cache, source errors, ownership, budgeting and cleanup. Mark any supplied domain
assertion non-covering for the new API. Run affordable component experiments before
claiming behavioral coverage. Do not invent live qualification.

Read the actual facade, account_operation, connection_engine, owned_health, health,
budget_client, session_store and existing tests 32/33 before conclusions. Verify these
concepts rather than merely checking that the proposed code has the named functions:

- Does an observation belong to the expected and freshly authenticated account even
  with stale cached identity? Is later budget admission still tied to that owner?
- Are metadata, membership, preview access and readable history separate facts?
  Can partial/min/forbidden/invite forms yield useful unknowns without invented facts?
- Are marked IDs and bare IDs unambiguous across SDK peer namespaces at their
  boundaries? Validate exact session rows, zero/large hashes, missing hashes and
  storage errors. No dialogs, generic string resolver, hash guesses or user aliases.
- Are input grammar, error/result shapes, UTC expiry and public immutability explicit
  enough to implement without inventing policy? Are safe reference labels consistent?
- Does exactly one bounded history probe provide positive evidence, including empty
  history? Reject mismatched/malformed/cache-only replies before confirming access.
- Can source RPC denial become a qualified result without erasing its health record?
  Can local errors, exhausted allowance, waits, transport failures or cancellation
  accidentally become denial/readability? Preserve exception identity and cleanup.
- Do lookup/no-peer paths retain prior group denial? Can older overlapping work erase
  a newer condition? Does complete positive evidence precede semantic confirmation?
- Does notification timing remain after settled cleanup? Preserve legacy behavior,
  persistent client/pool/current_group and existing Stage 1/2 runtime foundations.
- Is the one-module design smaller than alternatives without hiding required rules?
  Reject joining, shared alias state, new storage or a factory/health redesign here.
- Does the SDK minimum/dependency metadata match imported schema, with Python 3.7
  syntax intact? Do offline tests exercise public methods and actual SDK composition,
  rather than supplying the very verdict being tested?

Restart Check: one row per cited previous failure, its established mechanism and the
design element addressing it. Separate already-merged prerequisite fixes from Stage 3
work. Inherited Lessons: map each lesson to the actual step that enforces it, especially
no broad exception translation and no metadata-based health recovery.

For each genuine risk, use subsections rather than a findings table. Risk has two
paragraphs: first explain what a caller experiences without project jargon; second
name exact files/symbols/trigger. Add Severity (High/Medium/Low), Category, Impact,
NoobEng and Affected areas. Medium/High each get Quick, Robust and Long-term proposals;
Robust explains why robust, Long-term why effective over time. Under EACH proposal:

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

Save phase 2 with all boxes empty, then conduct a distinct selection pass changing
only boxes/notes. Name a genuine second instance before generalizing. Compare reach
per extent, reject symptom-hiding fixes absent external pressure, and use the smallest
permanent fix if a broader mechanism would add scope. Only selected mitigations fold
into revision 2; do not re-critique the fold.
