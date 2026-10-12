---
model: gpt-6-astra
effort: max
---
# Dynamic critic-d prompt — #10 worker plan

Ultrathink. Critique `step_by_step_impl_plan.md` revision1 at079ea54 against its
description, completed traverse and actual dev68f6bbd. Work in this warmed session,
never a subagent. No runtime implementation before the gate. All tests are offline;
fake wire may deliver synthetic replies but must not supply ownership/transport
behavior that the critique claims to observe.

Read the declared blocker sections first. There is no known offline planning
blocker; carry live qualification as an external precondition, not a fresh risk.
Question the selected structure, not merely its helper names or code style.

Probe these concepts and adjacent counterexamples:

- Source ownership: the expected account must own every group/read/join admission;
  ordinary raw-reader fallback must not smuggle broad/unbounded discovery into a
  bounded worker job. Inspect cached/private IDs, public handles and invite targets.
- Completion: original source error/batch/partial records, actual disconnect,
  deferred health, reply serialization and caller receipt are different events.
  Check the proposed private failure receipt under setup/caller/internal cancellation.
- Process lifetime: real buffered versus raw stdin/stdout, short/broken writes,
  idle/active/output signal handling, interpreter shutdown, unowned tasks/threads
  and no extra admission under backpressure. Do not assume catching BrokenPipeError
  establishes the specified exit code or that a signal prevents a final buffered flush.
- Protocol: strict complete framing, finite limits, exact signed64 identifiers,
  monotonic request IDs and consumption on invalid jobs, no raw input/error text,
  no silent partial omission or fabricated health. Confirm oversize/encoding failures
  are explicitly transport failures with safe source metadata, never empty success.
- Storage/capabilities: existing policies, no budget reset, session alias handling,
  trusted bootstrap versus job data, disabled joins, preserved request provenance,
  and uncertain source mutation after lost output. Do not add a queue, HTTP service,
  process supervisor or #17 dependency without a demonstrated missing requirement.
- Compatibility: additive helper/BatchEngine changes, default callers, one session
  per account and actual package/module/console invocation without work-folder imports.

Save `critic.md` with model/effort from current metadata first, then one document
verdict: IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE
BUILD; or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant when appropriate).
Immediately name the cheapest falsifier and its affordability. Affordable untested
behavioral premises tested after dependent implementation require REORDER: name the
actual-component experiment, cost, first dependent step and pass/disqualifying result.

Follow with a high-level summary, then ranked Premise Inventory before risks. For
each premise state first dependency, waste, scheduled test, cheaper earlier test
and coverage; label non-covering fixtures. Include Restart Check for prior failures
and Inherited Lessons with actual ordering/evidence. No Medium/High without precise
source/contract evidence or reproduced behavior; no speculative findings or padding.

For each risk: two paragraphs (plain consequence, then exact paths/symbols/trigger),
Severity/Category/Impact/NoobEng/affected areas. Medium/High get quick/robust/long-term
mitigations with robustness/long-term rationale and empty selected/elegant/last_resort
boxes and Why chosen/For future notes. Commit Phase2 before selection. Phase3 only
ticks/fills: compare reach versus extent, enumerate real shared instances before a
generic fix, and prefer the smallest permanent closure of the demonstrated boundary.
Do not patch product code, quietly change severity, fold unselected proposals or
re-critique after the eventual fold. A meaning gap uses the skill's explicit stop/
deprecated-plan procedure; no optimistic implementation past it.
