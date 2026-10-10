# Fresh PR critic prompt — #7 Stage 2, revision4, round2

Review PR22's complete product diff against dev `53306df`, together with revision4,
in this same session. Product is `c6451bb`, implementation evidence `cc5050b`, renewed
fidelity checkpoint `fd655a5`. Treat the plan and passing tests as claims to challenge.

Check verified ownership, request identity and recovery, neutral failure forwarding,
legacy compatibility, cancellation, notifications and cleanup. In particular, probe
nested SDK/budget requests, concurrent work and partial batch failures using actual
Telethon1.45.0 behavior with synthetic transport. Block sockets; no live account or
new credentials. Read relevant implementations and interfaces in full; no inference
from search hits. Review global hooks against the unchanged legacy path as well as
fixed-owner observations. Check conservative evidence, not merely matched strings.

Separate defects from documented limits. Keep every finding grounded in code or an
executed probe. Record counterexamples that disprove suspected risks. Rank premises
by waste-if-false, with first dependent step, waste, scheduled test, cheapest earlier
observation/cost and actual coverage. Flag fixtures that supply the behavior they
claim to observe. Run affordable falsifiers now; do not defer them behind approval.
Include Restart Check and Inherited Lessons tables for the original and repeated
failures. Distinguish one Stage2 PR rejection from archived copies and old PR16.

For each real risk, give two paragraphs: plain self-contained consequence, then
precise paths/symbols/trigger/evidence. Add severity, category, impact, NoobEng and
affected code. For Medium/High findings, propose Quick, Robust (why robust), and
Long-term (why effective) mitigation. Initially leave selected/elegant/last_resort
boxes and Why chosen/For future notes empty. Phase3 only selects/annotates, without
changing risks or severity: compare reach versus extent, identify genuine other
instances before generalizing, apply size/delicacy gates and avoid speculative growth.

Write root `pr-critic.md`, leaving plan critic.md unchanged. Start with model/effort
frontmatter (retained session provenance, unknown if unavailable), then critic-d's
design verdict, a falsifier/status line and PR ACCEPTED/REJECTED, followed by a
high-level summary. Use IMPLEMENT AS WRITTEN, IMPLEMENT AFTER FOLDING THESE IN,
REORDER — TEST BEFORE BUILD, or DO NOT IMPLEMENT — MEANING GAP/WRONG LAYER. Assess
implemented code with executed evidence, not a promise to run an experiment later.

Any Medium/High rejects. A second Stage2 rejection returns to the description and
traverse under CONTRIBUTING §7.4; no direct runtime fix or routine revision5 patch
loop. A genuine invalid premise follows critic-d's deprecation/blocker procedure.
For acceptance, explicitly state any consciously left Lows and known scope limits.
Preserve the first review in archive/round-1. Commit/push/post the new critique and
update PR22/#7 truthfully. No subagent, runtime fixes or merge during this review.
