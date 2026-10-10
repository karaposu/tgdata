# Fresh PR critic — #7 Stage 4 / PR24

Subject: the implemented PR24 diff (product de1f758, preparation head9861573)
against dev1ce39d5, together with revision2 plan.md, desc.md and the target codebase.
Run critic-d in this warmed session, never a subagent. Treat prior tests and the
merge check as evidence, not a soundness verdict. Preserve the original plan critic.

Read changed files fully and refresh their real storage/error/public dependencies.
Ultrathink about the contract and its design: should this be a separate attempt
ledger, or is there demonstrated need for a shared abstraction? Does it stay a
Stage4 foundation without implying that Telegram calls are already guarded?

Compute Premise Inventory first, ranked by waste if false: premise, first dependent
step, cost of failure, scheduled test, cheapest earlier test/cost, present covering
evidence. Documentary claims need source; behavioral claims need the actual component.
Stand-ins supplying desired behavior are non-covering. Carry declared blockers;
none may disappear merely through careful wording. State a falsifier, affordability,
and result of the cheapest available probe before final acceptance.

Attack independent dimensions of actual behavior: creation races and shared-file
coexistence; lock/commit failure; lost return; cleanup/cancellation precedence;
complete schema versus partial corruption; timestamps before pruning; policy changes,
backward time, expiry arithmetic and retry hints; error context and exports.
Distinguish normal supported operations from arbitrary external file tampering.
Use additional real SQLite/process probes beyond the existing suite. A deterministic
reference model may check transitions but cannot substitute for storage durability.
Do not contact Telegram, log in, or join anything.

Assess compatibility, package discovery, API expectations, storage/CPU/locking cost,
test blind spots and scope. Identify the smallest adequate architecture. Do not demand
Stage5 features, speculative backends or a wider health redesign. Every Medium/High
must rest on a concrete line of code or reproduced behavior, not imagined danger.

Write pr-critic.md with actual model/effort frontmatter, Gate ACCEPTED/REJECTED under
CONTRIBUTING §7.3, critic-d verdict, falsifier/affordability/result, high-level summary,
Premise Inventory, Restart Check and Inherited Lessons. Restart rows cover the old
table reset, invalid times and broad #7 ownership/source-error failures. Lessons must
name the order or structural boundary that satisfies them. Separate fidelity from
soundness and observed facts from inference. Record in-session execution and limits.

For each risk use two paragraphs: plain self-contained user consequence without
symbols/paths, then exact technical trigger/location. Add Severity Low/Medium/High,
Category, Impact, NoobEng and Affected areas. Medium/High each gets Quick, Robust,
Long-term proposals, including why robust/long-term is effective, and initially:

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

In a separate pass only tick/annotate selection. Establish actual other instances,
prove shared mechanics before generalizing, compare reach/extent, apply the size
gate, and route wider work separately. Do not change risks/severity to suit selection.
No findings means no invented mitigation tiers. Any High/Medium rejects; Low only
may be consciously retained. After rejection, §7.4 requires re-planning, not patches.
This review request does not authorize a merge or Stage5 implementation.
