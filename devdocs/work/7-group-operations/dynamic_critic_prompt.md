---
model: unknown
effort: unknown
---

# Dynamic plan critic for issue #7

Critique `plan.md` revision1 against desc.md, triage, traverse/finding.md and the
current codebase at the #6 merge plus #7 work artifacts. Run in this warmed
session. Target Telethon1.45.0 only; do not delegate or join a live group.

Read all affected runtime interfaces, especially factory MRO, ephemeral auth and
cleanup, health context/identity/recovery, read sender guard, SQLite sessions,
StoredSession entity filtering and actual vendor UserMethods._call. Challenge
premises rather than treating detailed plan text as evidence. Use real SDK and
local storage probes where cheap. Do not count scripted Telegram acceptance as
live behavior evidence.

Test these task-specific concerns:
- Are metadata, membership, read evidence and acknowledged/pending/interactive
  joining distinct even for missing ID, forbidden/min/peek and empty updates?
- Can projection/cache failure after acknowledgment look like failed joining?
- Does numeric resolution really use a known peer; can native parser/session
  errors inherit a prior RPC through __context__ and produce false health?
- Do ephemeral operations report the account they actually used, with concurrent
  public calls and stale primary session caches? Where is that identity bound?
- Are retries, wrapper/batch variants, fresh identity, policy replacement, clock
  rollback, transaction cleanup and uncertainty charged at the actual sender?
- Are read and join units independent while all clients inherit existing controls?
- Do every exit, cancellation and auth failure preserve existing lifecycle and
  avoid prompts? Can cleanup replace the original work outcome?
- Do health recovery and private-token handling reflect proof, not successful
  metadata, and avoid credential-bearing log/exception fields?
- Are APIs, schema versioning, imports and public docs concrete enough to build?
  Identify Medium if a complex step leaves its failure behavior unspecified.
- Does worker #10 justify portability without dragging in distributed policy or
  interaction workflows now? Compare any wider refactor's reach and extent.

Create `critic.md` beside the plan, frontmatter model/effort from actual context
or unknown, then a document verdict, falsifier and high-level summary. Verdict is
exactly IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN, REORDER — TEST
BEFORE BUILD, or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant permitted).
Falsifier states cheapest observation that kills the plan and affordability/cost.
Affordable unperformed falsifier forces REORDER with experiment, cost, first
preceded step, passing/disqualifying result; never replace real behavior with a
stand-in that simply supplies the desired premise.

Compute Premise Inventory first, immediately after summary: premise, first
reliant step, waste if false, test scheduled, cheapest earlier test/cost and actual
coverage. Rank by waste. Include vendor behavior and all hedges; label supplied
server replies non-covering for live semantics. Read declared blockers; do not
rediscover them as risks. Carry execution blockers unchanged. A wrong/open
planning premise forces DO NOT IMPLEMENT and the skill's deprecation procedure.

Restart Check: where prior observed failures are cited, map each established
mechanism to the element addressing it. Missing majority means WRONG LAYER.
Inherited Lessons: map each lesson to the ordered step proving it before dependent
work; prose acknowledgment alone does not close it.

For each real risk use sections, not a table: Risk in two paragraphs (plain
self-contained consequence first; precise file/symbol/trigger second), Severity,
Category, Impact, NoobEng, Affected areas. Every Medium/High gets Quick, Robust,
Long-term proposals, including 'why this is robust' and 'why this is long term
effective'. Under each initially write unticked selected/elegant/last_resort boxes
and empty Why chosen/For future notes. Avoid invented minor findings.

Then run a separate selection pass that only ticks boxes and adds notes. Name
other genuine instances before claiming a class; compare one mechanism's reach
against extent; reject fake shared abstractions; apply size/blocked/delicate gates.
Fold only selected proposals later. Record unchosen future conditions specifically.
