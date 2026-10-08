---
model: gpt-6-astra
effort: max
---
# Fresh PR critic prompt — PR21, Stage 1

Subject explicitly: published PR21 diff, dev95ed4c7 to review head611522e,
product2fe9aeb, AND this folder's folded revision2 plan. Apply critic-d afresh in
the same warmed session under CONTRIBUTING §7.2/§7.5; no subagent. Preserve the
original critic.md and dynamic_critic_prompt.md. Write results to pr-critic.md.

Fidelity already passed; that does not establish soundness. Read all six product
files and complete relevant factory, budget/session implementations, plus actual
SDK functions. Never infer implementation behavior from a grep or the author's
summary. Use the plan to distinguish deliberate bounds from unnoticed defects.

First inventory behavioral premises: real SDK self/entry behavior, before-send
admission, cancellation and session-close ordering, ordinary-client compatibility.
For each name its first dependent step, waste if false, original test timing,
cheapest test now and whether existing evidence observes the behavior or replaces
it with an agreeing fake. Run affordable falsifiers during this review before
rendering a passing gate. Quote actual probe observations. Synthetic wire replies
are allowed; do not replace the SDK mechanisms being tested.

Challenge at least these paths beyond the author's suite:

1. The account changes after request resolution begins but before actual admission.
   Force a pending resolution/proof, and inspect real SQLite claim/send ordering.
2. Cancellation while a fresh budget-admission proof is pending: zero claim/send,
   original cancellation and completed actual SDK disconnect.
3. Independent contexts whose initial self proofs complete in the opposite order
   to opening; numeric owners must not cross. The evidence must contain true overlap.
4. SDK cleanup fails after the sender has disconnected, during session.close: does
   success/primary error survive, with sanitized diagnostics and no pending task?
5. Cancellation arrives after work failed and while closing is still pending, then
   closing also fails. Test the documented precedence rather than guessing it.
6. Store-load/config/proxy failure before construction must never open a connection
   or create a misleading identity. Inspect factory defaults and package imports.
7. Check the successful iterator path as well as the author's refused iterator
   path; ensure creator-task enforcement does not break normal SDK iteration.
8. Missing/malformed self data before the context's explicit verification may be
   consumed by connect's own get_me. Assess actual failures and distinguish valid
   auth errors from impossible/malformed synthetic wire replies.

Investigate any concrete additional risk found by reading. Do not grow the stage
into public SDK supervision, health registries, live tests or a pool scheduler.
Explicitly assess whether raw-client/task restrictions are a suitable internal
contract, not simply whether a more general framework could be imagined.

Output: model/effort frontmatter, critic-d document verdict and falsifier line,
Gate ACCEPTED/REJECTED under §7.3, high-level summary, ranked Premise Inventory,
Restart Check and Inherited Lessons. Each real risk needs plain then precise Risk
paragraphs, severity/category/impact/NoobEng/affected areas. No risk table. A Medium
or High requires an exact code/probe anchor and Quick/Robust/Long-term proposals
with rationale and initially empty selected/elegant/last_resort boxes/notes. Phase3
selects separately by reach/extent and the real-instance/generalization size gates.

Any High or Medium rejects; do not patch the product under review. Record a
re-planning handoff under §7.4 if rejected. A wrong-layer/meaning-gap finding follows
critic-d's explicit deprecation/blocker procedure. Zero findings is allowed;
do not pad with speculative or cosmetic issues. Name limits of evidence, including
SDK1.45-only/offline scope, same-session review and dated model metadata.
