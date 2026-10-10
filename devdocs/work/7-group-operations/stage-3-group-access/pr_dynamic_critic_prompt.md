# Fresh PR critic — #7 Stage 3 / PR23

Subject: the implemented product diff **30ba706...a2afc05**, as published in PR23
(feat/7-group-lookup-access into dev), together with plan.md revision2 d15b5d5 and
its desc.md. Branch head at publication1348028 adds only process records. Read the
actual code, not its implementation summary. This is a new in-session soundness
review under CONTRIBUTING §7.2; the passing merge-check establishes fidelity only.

Ultrathink. Challenge whether this small public layer asks the right questions and
whether its observations follow from evidence. Do not protect the plan's decisions,
copy its critic verdict, or inflate a hypothetical into a finding. Read relevant
functions/files in full and write/run probes for claims about behavior. No subagent.
No product edits or live Telegram actions. Keep all existing plan/critic artifacts.

Create **pr-critic.md** beside this prompt, starting with model/effort frontmatter
from current session evidence (unknown if unavailable). Use critic-d's document
verdict vocabulary, followed by an explicit §7.3 PR decision and High/Medium/Low
counts. Immediately below the verdict give the cheapest falsifier and its current
cost/access/affordability. For an affordable unrun architectural falsifier, REORDER
requires naming and running the real-component experiment before an accepting verdict.
An unresolved wrong premise follows the meaning-gap procedure, not a patch list.
Any High or Medium finding rejects this PR and triggers §7.4 re-planning; do not patch
runtime code during review. Lows alone may remain consciously accepted.

Read Known Blockers/Huge Hard Blockers first. None are open for offline work. The
hashless CommunityForbidden file-cache failure and offline-only permission evidence
are declared limitations, not undisclosed new bugs; neither can be waved away if the
implemented contract actually depends on them succeeding.

After a high-level summary, build a ranked Premise Inventory: premise, first dependent
step, waste if false, scheduled test, cheapest earlier test and current coverage.
Distinguish actual SDK/budget/task/cache behavior from supplied synthetic server data.
A fake GroupAccess or a manually supplied semantic confirmation cannot prove the new
API's inference. State clearly what remains live-server qualification.

Investigate these conceptual boundaries, allowing other real findings to emerge:

1. **Owner:** expected account versus cached identity; fresh proof before group work;
   budget re-verification, separate accounts, shutdown and legacy attribution isolation.
2. **Meaning:** metadata, member/approval/payment hints, invite Already/Peek/plain,
   minimal/forbidden/community shapes, and what readable/denied/unprobed actually claim.
   Does any absence or invalid reference become an invented fact? Is using the existing
   RPC classifier appropriate to the documented outcome, and is the source reason kept?
3. **Reference identity:** exact typed numeric cache rows, marks/bounds/hash0, stale rows
   versus a fresh reply, username aliases, case-sensitive invite labels and no dialog
   fallback. Can a fresh minimal response incorrectly borrow an old complete cache peer?
4. **Evidence:** one bounded history probe; empty versus cache-only/mismatched replies;
   malformed nested TL shapes and error classification. Does the caller receive a
   result or error consistent with the public contract before health is confirmed?
5. **Ordering:** older/newer reads and denials in both completion orders; retained quota
   on failure/cancellation; errors while cleanup is delayed/fails; notification effects
   after the source disconnect attempt. No fake recovery from metadata or diagnostics.
6. **Compatibility/extent:** package exports/imports, minimum SDK, Python syntax, existing
   client/pool/current_group and legacy behavior; no unnecessary engine, registry,
   persistence, permission framework or premature join implementation. Ask whether an
   existing foundation suffices before proposing more infrastructure.
7. **Evidence quality:** review suite34's fixture and all assertions; run independent
   public-path probes for uncovered intersections. Existing494 passes establish the
   tested product, not all possible vendor outcomes. Do not repeat every unchanged
   suite merely to manufacture a fresh count.

Provide Restart Check rows mapping established previous failure mechanisms to the
actual changes/prerequisites; empty mechanisms must not be invented. Map inherited
lessons to enforced order/evidence. Give exact source lines and reproduced output for
any behavioral finding, stating what the probe supplies and what it observes.

For each risk use subsections, not a findings table: two Risk paragraphs (plain caller
consequence, then precise files/symbols/trigger); Severity; Category; Impact; NoobEng;
Affected areas. Medium/High receive three proposals (Quick/Robust/Long-term), including
why robust/why effective long term, each initially with empty selected/elegant/last_resort
boxes and empty Why chosen/For future notes. Save that pass before selecting proposals.
Phase3 changes only boxes/notes. Enumerate a genuine second instance before generalizing;
compare reach per extent and reject larger mechanisms without demonstrated benefit.
Selected proposals are recommendations for a required re-plan, not permission to patch.

Finish with review evidence, consciously retained limitations/Lows, §9 provenance and
which next gate remains. Do not call an accepted critique a merge or a live validation.
