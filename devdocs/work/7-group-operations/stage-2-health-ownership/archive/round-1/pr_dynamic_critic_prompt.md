# Fresh PR critic prompt — #7 Stage 2 / PR22

Subject: the implemented diff from dev53306df to product3d59455 (PR22 opened at
1625e09), together with folded plan.md revision2 and desc.md in this stage folder.
Review soundness afresh in this warm session. No delegation, no runtime edits,
no live Telegram work, no merging. Keep the original plan critic untouched.

Read all relevant source and interfaces in full: owned_health, health, facade,
connection factory, Stage1 account_operation, budget_client, session store,
test16/test32/test33 and product docs. Inspect actual Telethon1.45.0 request/error/
disconnect code. Use the original inquiry and critic as evidence, not authority.
The merge fidelity check passing is not evidence that the design is sound.

Challenge:
- Fixed owner in both sinks, unknown snapshots, immutable labels, client/task/
  lifetime binding, caught auth/identity loss and same-owner independence.
- Ownership before proof, cleanup attribution, enclosing/child contexts and
  exception exclusions: can another error be swallowed or relabeled?
- Actual SDK request representations: wrappers added by policy, errors built by
  the real sender, request lists, generators and nested budget verification.
  Do failure keys and success keys describe the same logical request?
- Evidence quality: can repeated identity/metadata verification satisfy a
  restriction or wait recovery without the refused action succeeding? Does the
  explicit group assertion correctly keep semantic interpretation in group code?
- Temporal ordering: calls overlapping authentication, recording and cleanup;
  old work clearing new conditions; queued notifications delivered out of order.
- Callback sync/async failure/cancellation, recursion, task outcome retrieval,
  cooperative close, self-close and two concurrent closing observers.
- Ordinary public-path compatibility; honest docs and tests that inject at the
  right seam instead of supplying the very behavior they claim to test.
- Scope/complexity: prefer the smallest complete ownership boundary. Do not turn
  an evidence mismatch into global routing, persistent request traces or migration.

Run additional offline probes for behavioral claims on actual SDK/asyncio code;
synthetic transport is allowed, synthetic ownership/recovery outputs are not.
Quote observed output and identify non-covering fixtures. Ground every Medium in
code or an executed probe; record counterexamples that disprove suspected risks.

Write pr-critic.md, with model/effort frontmatter, Gate ACCEPTED/REJECTED using
CONTRIBUTING7.3 (any High/Medium rejects), design verdict, falsifier/status and a
high-level summary. Then Premise Inventory ranked by waste-if-false: premise,
first dependent step, waste, planned test, cheapest earlier test/cost, actual
coverage/observations. Include Restart Check and Inherited Lessons tables.
Use critic-d's design verdict vocabulary; the PR rejection consequence is re-plan
under7.4, never patching this implementation during review.

For each risk use sections, not a risk table. Give two Risk paragraphs: plain
self-contained consequence, then precise paths/symbols/conditions. Add Severity,
Category, Impact, NoobEng and Affected areas. Medium/High needs Quick, Robust
(with why this is robust), Long-term (with why this is long term effective).
Phase2 writes every proposal with unticked selected/elegant/last_resort boxes and
empty Why chosen/For future notes. Phase3 only selects/annotates those options,
using reach/extent, genuine named other instances, size and delicacy gates.
Do not select speculative architecture merely because it says long-term.
If a true meaning gap invalidates the plan shape, follow critic-d2.5; otherwise
record concrete mitigations for the required revision3 re-plan.

Separate known baseline limitations from new regressions and conscious contract
choices. Explicitly say this was a fresh in-session critique, which probes ran,
what remains untested, and which Lows are consciously left if the gate accepts.
Commit review and probe artifacts, post the review on PR22, update its draft/status
and #7 truthfully. Do not replace a rejecting review with silent fixes.
