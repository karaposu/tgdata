---
model: unknown
effort: unknown
---
# Fresh PR critic prompt — PR35 / issue29

Subject explicitly selected: the published PR35 diff (`origin/dev...feat/29-album-assembly-pr`, base e5cdad7, head19d421f) together with the archive branch's `step_by_step_impl_plan.md` revision2, reached through plan.md. Create **pr-critic.md**, preserving the original critic.md. Run in this warm session without subagents. Evaluate soundness independently of fidelity and the earlier favorable test results.

Read the entire changed code, tests and guide, plus relevant raw serialization, source receipt and storage implementations. Confirm the published tree matches the exact reviewed source. Do not treat passing implementation-shaped tests or a large test count as a proof. Construct new falsifying inputs and failure histories against actual components; record code locations, commands and observed output. Synthetic observations can test local assembly/receiver contracts but cannot establish Telegram global completeness.

Audit these concepts and their interactions:

- Stable observed entity identity versus source batch/receipt identity. Preserve chat/group scope, all captions, large identifiers, input immutability and partition-independent revisions; test more than the original one-album fixtures.
- Replay closure: after an input commits, can unchanged policy and the same exact pending raw batch replay after a lost ack? Compare first acceptance versus the changed prior-state cost, including byte/member boundary conditions and later album growth. Compare destination data/markers, source pending/cursor and actual source call count separately.
- Resource refusal: inspect every load/parse/merge boundary, where aggregate limits are checked, whether accepted state can become unreadable without a policy change, and what the documented serialized-work bound actually promises versus physical memory.
- Strict receiver open, schema/version/namespace, authoritative None versus failed lookup, current state under transaction, rollback, uncertain commit/close, recognized input whose stored projection is missing, and competing writers. Check data survives rather than merely counting exceptions.
- Public serialization: independent construction and reload, canonical hash, duplicate keys, unsupported fields, malformed member identities/types and content-free local errors, including incidental Telegram exception context. Inspect private validator reuse and package discovery/Python compatibility.
- Observe-only boundaries: no inferred album completion, no hidden fetch/lookahead, no raw hash/cursor/budget/schema changes. A captured/partial batch is data, not automatic ack authority; examples must not turn local receipt failure into Telegram health or source progress.
- Simplicity and future scope: does the small operation plus receiver example satisfy the request? Do not add photo trails, a scheduler, leases, edit reconciliation or a new archive engine to repair an unrelated concern. Future-only alternatives must be marked as such.

Output starts with truthful model/effort frontmatter (unknown if unavailable), one of critic-d's four document verdicts, Falsifier and Affordable-now lines, any experiment/result, high-level summary and **Gate: PASS or REJECTED**. Every High or Medium rejects under CONTRIBUTING §7.3. §9 unknown metadata is an explicit independent merge prerequisite, not fabricated proof of a code defect or a claimed waiver.

Compute a Premise Inventory before risk items: premise, first dependent step, waste if false, scheduled test, cheapest earlier falsifier/cost and actual coverage; mark behavior-supplying stand-ins non-covering. Run affordable falsifiers now before claiming a soundness pass. Include Restart Check (observed failure / established mechanism / design response) and Inherited Lessons (lesson / satisfying ordering). Distinguish plan decisions from implementation deviations and historical evidence from fresh observations.

Each real risk is a section: two Risk paragraphs (plain self-contained user consequence, then precise paths/symbols/trigger), Severity, Category, Impact, NoobEng and Affected areas. Medium/High findings must rest on code or a reproduced probe and get Quick, Robust and Long-term proposals, with robust/long-term explanations. Initially save all three proposal checkboxes unticked and notes empty. Then Phase3 only selects/fills notes, comparing reach/extent, naming genuine other instances before generalizing, and rejecting larger class mechanisms that need special cases or exceed scope. No quick fix on merit alone.

If the entire plan shape rests on a disproved premise, follow critic-d's meaning-gap/deprecated-plan procedure. Otherwise a Medium/High **PR** finding rejects and sends the next work to revision3 re-planning under CONTRIBUTING §7.4; selected proposals are inputs to that plan, not permission to patch production during this review. Commit the critique/probe evidence on the archive branch and post the critique on PR35. Keep original implementation/plan critique evidence intact.
