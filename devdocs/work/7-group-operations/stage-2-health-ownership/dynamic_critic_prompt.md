# Dynamic critic prompt — Stage2 revision3

Subject: plan.md revision3 at530ea36, desc.md, pr-critic.md and replan-evidence.md
in this folder, against product3d59455 / dev53306df. Review in this warm session,
without subagents. Do not rewrite the original PR review or the round-one archive.

Read relevant implementations/interfaces in full: owned_health, health, factory
request hook, account_operation, budget_client, facade and real-SDK tests/probes.
Inspect Telethon1.45.0 source for anything about request resolution, envelopes,
batch inputs, error construction or propagation. No live Telegram work.

Question the concepts and the smallest viable boundary:
- Does one namespaced leaf key represent both actual failed and successful RPCs?
  When is that identity captured? Can a list, iterator or envelope change while
  the SDK awaits and supply evidence for an action that never ran?
- Does restriction recovery actually retry the refused action under the right
  owner/method/generation, including identity-request refusals, nested budgets,
  condition replacement, missing metadata and caught invalidation?
- Does an attribution marker survive genuine SDK errors, Stage1 wrapping,
  child tasks and cleanup while leaving diagnostics/polling unchanged?
- Does marking only explicit causes/MultiError leaves avoid absorbing unrelated
  implicit context? Can a fresh RPC still report before an older marked ancestor?
  Are traversal bounds, cycles, marker failures and original outcomes covered?
- Are legacy names/timing, fixed owner/query copies, source-time caught failures,
  partial MultiError policy, group semantics and post-cleanup notifications intact?
- Can the plan be simpler without losing these guarantees? Reject speculative
  migration, global provenance registries, permission engines and queue workers.
  Flag underspecified delicate steps as Medium; do not add hypothetical padding.

Write critic.md here with model/effort frontmatter from session context (unknown
if unavailable). Open with the design verdict, falsifier/cost and high-level
summary. Choose IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN,
REORDER — TEST BEFORE BUILD, or DO NOT IMPLEMENT — MEANING GAP/WRONG LAYER.
Verdict depends on shape/sequence, not finding count. An affordable unexecuted
falsifier requires REORDER: define the real composition experiment, cost, first
dependent step, exact passing and disqualifying outcomes. It runs before any
plan step. Never treat a helper supplying the proposed behavior as proof of it.

Compute Premise Inventory first, ranked by waste-if-false. For each: premise,
first dependent step, wasted work, scheduled test, cheapest earlier observation/
cost, current coverage and what it does not prove. Vendor/async behavior belongs
even if not hedged. Carry declared execution blockers unchanged. An open planning
blocker invokes the deprecation procedure rather than mitigation.
Include Restart Check (every reproduced failure / established mechanism /
addressing design element) and Inherited Lessons (lesson / satisfying order).

Risks are sections, not a risk table. Each has a plain self-contained consequence
paragraph, then a precise paragraph with code paths and trigger conditions.
Include Severity, Category, Impact, NoobEng, Affected areas. Every Medium/High gets
Quick, Robust (why this is robust), Long-term (why this is long term effective).
Phase2 initially writes every proposal with:
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

Phase3 only ticks/annotates existing proposals. Require actual other instances
before claiming a class-wide fix; compare reach/extent, size and delicacy. Select
the smallest complete fix; record genuinely deferred alternatives. Do not soften
the finding to justify a favorite tier. A selected change may expand a concrete
step, but cannot silently replace the plan's architecture.

Respect task-impl gates. If REORDER, specify the experiment without editing the
plan, then select mitigations. Fold only selected proposals after a PASS; never
re-critique the folded plan in this run. If the plan must be deprecated, preserve
it and update the description's blockers. Keep this plan review distinct from
the later fresh PR critique required after implementation.
