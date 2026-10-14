---
model: unknown
effort: unknown
---
# Dynamic critic prompt — issue29

Critique the explicitly selected `step_by_step_impl_plan.md` in this directory against desc.md, traverse/finding.md, the preserved source request and the actual code. Run in this session. Create a `critic.md` file in the same directory as the implementation plan. This output file has a high level summary on top, after the required verdict/experiment and before individual risks.

Read declared blockers first; carry execution preconditions unchanged. Investigate uncertain documentary premises in actual implementations; a behavioural premise needs the real component in its real composition. Treat existing SQLite probes as evidence of existing components only. Do not present synthetic source responses as proof of Telegram completeness.

First inventory premises, ranked by wasted work if false. For each give premise, first dependent step, waste if false, scheduled test, cheapest earlier test/cost and existing coverage. Explicitly label stand-ins supplying the claimed behavior non-covering. Include the claim that a pure observed-post representation plus caller-owned acceptance can survive actual SDK/value/SQLite/daily/backfill composition. If none are unproven, say what was checked rather than silently omitting the inventory.

Audit identity, not merely grouping: caption carrier changes, large signed identifiers, same album ID in two chats, nonadjacent members, reverse arrival, stable bytes/revision independent of input partitions, all caption/media/provenance records retained. Challenge whether stable revision updates satisfy the source request; do not silently turn them into final emissions. Check that no count/timing/page/end/commit signal is advertised as complete membership.

Audit ownership at failure boundaries: raw data versus source receipt, capture versus pending delivery, source cursor versus assembled member range, affected prior-key lookup versus global archive. Confirm exact required lookup and conflict semantics, including mode compatibility. Can a local storage error become false Telegram health? Can serialized validation expose message content? Do bounds cover supplied and produced data before unbounded accumulation, and do loaders, assembler and receiver use compatible caller-selected limits?

Audit the actual receiver integration contract: explicit creation, strict known-state reopen, schema/version/collection validation, lookup failure versus per-key absence, read-current-under-transaction, all posts and input marker committed together, collection-scoped duplicate markers, retry after later growth, lost commit response, rollback/close failure and source ack afterward. Test whether a copied existing example's exception handling could incorrectly acknowledge unconfirmed partial data. Check whether downloaded blob references are mistaken for retained bytes. Keep storage-device loss and distributed ownership distinct from the local receiver guarantees.

Evaluate whole-codebase compatibility, import/circular/package discovery risks, raw schema/hash stability, progress stores, budgets/windows, pool captures, worker callers, Python support, runtime dependencies, resource costs and future #30 composition. Question broader alternatives; future-only advantages must be labeled future-only. Flag a step that is too vague for its critical interface as Medium. Do not manufacture findings already structurally addressed in the plan, and do not pad the report with hypothetical unrelated work.

Start critic.md with frontmatter `model: unknown` and `effort: unknown` unless actual session metadata becomes available. Immediately after it choose exactly IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN, REORDER — TEST BEFORE BUILD, or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant when appropriate). Verdict judges shape/order, not risk count. Under verdict1/2/3 put `Falsifier:` naming the cheapest observation that would kill the plan, and `Affordable now: yes | no — cost`. Affordable-now falsifier means REORDER; no claimed pass without its experiment. Verdict4 uses a dash.

For REORDER, specify Experiment, Cost, Must precede, Disqualifying result and Passing result. The entire combined real-component experiment precedes production step1; no targeted stand-in substitutes. Do not edit or deprecate the plan for REORDER. For DO NOT IMPLEMENT, follow critic-d's exact deprecated-plan/known-blocker procedure and stop before selection.

After high level summary put Premise Inventory before risks. Include Restart Check rows for observed failures cited by the task: failure, established mechanism, design element. Distinguish hypothetical fault histories from reproduced consumer behavior; absence of an established mechanism must not be disguised. Include Inherited Lessons rows with the actual plan ordering that satisfies each; merely acknowledging an untested premise is insufficient.

Each risk uses sections, not a risk table: Risk paragraph1 explains the user-visible failure in plain language without symbols/paths; paragraph2 states exact paths, symbols and triggers. Then Severity (Low/Medium/High), Category, Impact, NoobEng and Affected areas. Each Medium/High gets Quick, Robust and Long-term proposals, with `Why this is robust:` and `Why this is long term effective:`. Under each proposal initially leave these boxes unticked and notes empty:

`- [ ] selected   - [ ] elegant   - [ ] last_resort`

`**Note**` / `*Why chosen:* —` / `*For future:* —`.

Save Phase2 before selecting. Phase3 only ticks boxes and fills notes: enumerate actual other instances before claiming a class, test whether one mechanism serves them without special cases, compare reach/extent, use robust if wider work exceeds scope, and identify prerequisite versus future work by whether the robust fix survives it. Never select quick on merit alone. Elegant/last_resort are exclusive; last_resort implies selected. If there are no Medium/High findings, record that no selection is required. Keep §9 unknown metadata visible without inventing a model assertion.
