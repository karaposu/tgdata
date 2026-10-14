---
model: gpt-6-astra
effort: max
---
# #8 merge check — PASS

**Gate:** PASS for fidelity to the bounded offline implementation contract.
**Reviewed product:**877d29d; branch evidence head:b76f1f6 before this review.
**Base/current remote dev:**c4e6eac89341b204b2749e9d15add578e0706965, freshly fetched.
Merge base equals dev; no integration drift or conflict. The later PR critic is
separate and still pending. This PASS is not approval to merge or a live-login PASS.

## 0 — Warmth, weight and model rule
Same warmed session as implementation. Read triage, description, folded plan,
prebuild critic and correction history, all eight changed product files in full,
the actual diff and exact verification record together. Shared factory/session/
health/lifetime and native SDK context is retained/refreshed, not delegated.

Triage a481e32 records warm source reads at c4e6eac, verified ancestor of this
branch. desc.md's Foundation originally linked that record; this checkpoint adds
the explicit Session warmth record required by §4.2. No missing historical warm-up
is fabricated. Feature-heavy matches GitHub enhancement+heavy labels.

§9: latest session turn metadata confirms gpt-6-astra/max. This is the required
feature model family at effort above its xhigh minimum; neither model nor effort
is inferred from artifact claims alone. No subagent used. PROJECT_SPECIFICS absent.

## 0b — Scope against triage
The eight product paths are README.md, docs/stepwise_login.md,
examples/stepwise_login.py, tgdata/__init__.py, tgdata/connection_engine.py,
tgdata/login.py, tgdata/smoke_tests/README.md and test_41_stepwise_login.py.
All fit the surfaced API/factory/exports/test/docs/example territory. StoredSession
is reused rather than changed. No new health model, coordinator, database backend,
worker protocol, pool login, quota or group operation is introduced. Heavy weighting
remains appropriate. Other diff paths are #8's isolated process/evidence archive.

## 1 — Implementation against the plan
Step1: one private state owner, safe status, exact checkpoint schema/binding, frozen
effective device values and isolated StoredSession. Common factory's only behavioral
changes are the private base parameter and its selection; ordinary defaults unchanged.
Owned child execution retains observed progress and waits for native retirement;
failed retirement retains the client and blocks further work/export.

Step2: deliberate raw SendCode/SignIn/GetPassword/CheckPassword, actual SDK SRP,
auth-only _on_login observation, explicit unknown/expired/unsupported/wait handling,
fresh self identity and authorization-only check. Final output is the #5 credential;
publication remains the caller's separate store operation.

Step3:23-group actual SDK suite, native transport boundaries, independent SRP verifier,
session consumer loading, privacy, proxy/device binding and cancellation controls.
Step4: README, full guide, smoke index and executable offline multi-handler example.
Step5: focused and full supported verification, product commit separate from evidence.

Named refinements/deviations:
- Native migration calls private _disconnect, correcting the plan critic's initial
  public-disconnect account. Folded revision2 explicitly owns both physical transport
  and public flush completion. The prebuild preserves the discovery and failed local
  attempts; it did not claim those earlier attempts passed.
- Retaining one shared StoredSession object preserves actual DC/key mutations;
  no separate copied session layer is needed for the plan's “copy actual state” intent.
- SDK child loggers use the private disabled logger too. This closes the stated
  diagnostic policy at the actual getChild call site; no global logging change.
- Cancellation-safe application persistence is explained in prose, not a pretend
  universal finally-save database helper. The storage/exclusivity obligation is explicit.
- Five demos ran, including the existing worker demo in addition to the planned
  older three/new login demo; package-export compatibility justified that extra check.

## 2 — Does the plan still hold?
Yes for the explicitly bounded contract: completed-step portability, one owner and
deliberate final credential publication. Memory-only use remains possible. It does
not claim crash-atomic replay or concurrent stale-copy coordination. Adding a new
login service/provider would add an unrequested owner rather than fix this contract.
The initial native call-site error is corrected in the folded plan and critic
experiment note, not left as current rationale. Live provider acceptance is still
unqualified and explicitly documented in public and work docs.

## 3 — Every plan-critic finding
The sole Medium finding, Risk1, selected the bounded completion-owner mitigation.
_LoginClient retains native transport and full-close futures; new connect and explicit
failed-close retry manage their lifetimes. _execute uses _disconnect_owned's receipt;
_invoke retains its child and preserves caller cancellation. The unchanged migration
cancellation assertion passes in the complete prebuild and runtime suite.
No High or Low plan findings remain unaddressed. The full candidate gate preceded
production in1a234b0. This fidelity check does not substitute for independent fresh
probes of whether those boundaries are sound.

## 4 — Issue status and evidence
Read current #8: stepsT/0–5 checked and linked to committed artifacts; steps6/7 remain
unchecked until this check/publication and the fresh critic finish. Original prompting
history is explicitly marked stale; actual current headless behavior is described.
No false closure of live login, #17 two-account testing, PR review or merge.

Fresh source-hash audit confirms every file in verification/result.json still matches.
Recorded28-suite PASS =773 actually executed offline cases plus3 explicit live skips;
all5 demos passed. Runtime/test bytes match the final prebuild, factory AST matches the
exact qualified seam, imports/compile/Python3.7 grammar passed. Native Python3.7 and
live Telegram delivery/2FA are not claimed. No broad rerun is needed for unchanged
code; fresh PR probes will target previously uncovered behavior.

## Publication and eventual integration
Open PR into dev with Closes #8 and post this check; then run a fresh in-session
critic-d of the real diff together with plan revision2. Any Medium/High rejects
under §7.3 and goes to §7.4 re-planning. No automatic patch/merge is authorized.
Eventually exclude devdocs/work and archaeology changes from the dev merge and keep
the feature branch as the archive (§7.6–7.7). Main checkout and duncan remain untouched.
