# Critic prompt — #17 retirement rework

Ultrathink. Critique this folder's plan.md revision1 against the scoped desc.md,
the parent#17 contract/selected mitigations, actual branch8d3db76 and dev68f6bbd.
Run in the current warmed session. Read complete relevant implementations and test
behavior with real SDK/asyncio/SQLite composition, not a fake retire method that
returns the desired status. No product edits during critique.

Examine ownership beyond the awaiting coroutine: SDK disconnect tasks, active pool
calls and the observed source child. Does cancellation mean those tasks ended? Can
repeated or independently delivered cancellation release a guard, hide an active
child or allow late writes/client reuse? Check success, internal cancellation,
ordinary failure, caller cancellation, and both at once. Test failed retirement
refusal and explicit retry; distinguish safe non-use from successful closure.

Trace shutdown while a read is ending and context exit while a body already failed.
Preserve caller cancellation, source exception/prefix identity, completed outcome
before observers, repaired stored credentials, durable unknown attempts and local
health neutrality. Check policy precedence/current factory without changing #7 or
ordinary clients. Judge whether any proposed shared helper has real common callers
and compatible semantics; avoid a new lifecycle framework or joining feature.

Run cheap falsifiers before accepting the sequence. In particular examine repeated
caller cancellation while actual source/SDK cleanup is held, not only one cancellation
of a successful disconnect. If an unproven candidate composition is tested only after
its implementation, specify a REORDER experiment before any build. Parent live E1
is an execution precondition for a later gate, not a new planning finding.

Create critic.md here, preserving the parent's critic. First write current-session
model/effort YAML frontmatter (unknown if unavailable), then exactly one skill verdict:
IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD;
or DO NOT IMPLEMENT — MEANING GAP/WRONG LAYER. Put Falsifier and Affordable now
directly below it, then a high-level summary. Compute Premise Inventory first:
premise, first dependent step, waste if false, scheduled test, cheapest earlier
test/cost, covering versus non-covering evidence. Rank by waste. Include Restart
Check and Inherited Lessons with mechanisms and ordering, not assurances.

Every finding needs two Risk paragraphs (plain consequence, then exact symbols/
paths/triggers), Severity, Category, Impact, NoobEng and Affected areas. Medium/High
needs quick/robust/long-term proposals with their why fields; initially all
selected/elegant/last_resort boxes unticked and Why chosen/For future notes empty.
Only concrete code/probe evidence supports a finding. Quote observed output and
label fault injection and synthetic network limits.

Phase3 separately selects by reach/extent: name actual other instances before
calling a remedy class-wide, apply the size gate, and route broader changes rather
than sneaking them into this repair. Do not invent findings or prefer a large
abstraction by its name. For REORDER specify real experiment/cost/first dependent
step/pass/fail before continuing. For a genuine meaning gap follow the skill's
deprecation/blocker procedure and stop, rather than patching the plan's premise.
