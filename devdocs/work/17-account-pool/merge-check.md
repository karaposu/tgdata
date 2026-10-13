---
model: gpt-6-astra
effort: max
status: PASS_FIDELITY_PR_REVIEW_PENDING
round: 3
plan_revision: 7
---
# Renewed merge check — #17, plan7 implementation

**PASS for PR soundness review of the selected offline delivery.** Product007c2e4,
verificationb62189c, against dev2ddb852d917998d003f9db863fce09a92e9c5712, verified
unchanged on GitHub on2026-10-13. This establishes fidelity, not soundness, two-account
live qualification or permission to merge. The prior two checks/rejected PR reviews
remain historical; the previous check is preserved as merge-check_r2.md.

Read together: triage (including implementation follow-up), description5, folded plan7,
selected plan critic, P0, verification_outcomes.md, both prior PR rejections, the public
outcome ownership finding, and the entire23-file product diff. Full controller/source/
lifecycle/capture/state/observation/facade/batch/progress paths and all new tests, example
and public docs were inspected, not only the latest commit.

## 0 — Warmth, weight and model rule

The same warmed session carries the foundation/public-ownership traverses and module
reads, refreshed against the implementation. Recorded warmth09e0277 is an ancestor;
the audit verifies the description/plan/critic/P0/product chain. No new architecture
skill or delegated review is claimed. Feature-heavy fits the interaction of source
cancellation, three durable namespaces and shared ordinary-client seams. Current
GitHub enhancement/heavy labels agree; all open issue titles refreshed.

Current turn metadata confirms **gpt-6-astra / max**, satisfying CONTRIBUTING §9's
feature-path Astra/xhigh minimum. PROJECT_SPECIFICS remains absent; actual repository
runners apply. #7/#10 are already on dev. Main checkout, duncan and unrelated files
remain untouched.

## 0b — Scope and deviations

The complete product has23 files (+5133/-137), including earlier router/retirement/
storage work. Runtime: AccountPool; pool_source/state/lifecycle/observation/result;
shared progress facade and TgData delegation; batch/message values; opt-in sync/backfill
transport; package exports. Others: pool guide/example, README, daily/backfill references,
smoke README, test31/39/40 and storage cases. All are within recorded triage/inherited
scope. No joining, scheduler, distributed lease, global registry or raw-result store.

Fifteen adjacent runtime modules are byte-identical to current dev. Ten moved public
progress signatures/bodies are AST-identical excluding docstrings. TgData retains its
module-local backfill factory seam. Every other changed branch path is devdocs. Under
§7.6 work/inquiry/archaeology must stay out of any later merge while preserving dev's
own documents; retain this feature branch as archive (§7.7).

Recorded narrow deviations are acceptable: two daily/backfill guide clarifications;
API docstrings/comments over P0; permanent combination of17 new+8 earlier probe groups;
fixture import placement for direct execution; named demo captures retained for inspection.
They change neither executable runtime nor test oracles.35 promoted helper/test bodies
exactly match P0. No runtime correction or weakened assertion occurred during verification.

## 1 — Fidelity to folded revision7

| Step | Implementation and evidence |
|---|---|
| P0 | Full combined candidate passed before production: actual SDK/SQLite/ledger,750 executed groups+3 demos and original-product negative controls. The local proxy sandbox failure was resolved by a full rerun with no runtime change. |
| 1 | Required exact-type single-use PoolReadCapture, immutable snapshots, local binding/finality, bounded diagnostic names, prefix retention without retained task/exception graphs. |
| 2 | _Invocation separates normal completion from caller stop address. _operation releases exclusivity then signals completion synchronously. Close stops/joins the exact invocation, never the application Task. |
| 3 | BatchEngine attaches the actual record list after verified identity/entity resolution. Records append only after validation/media completion. Source body outcome is captured before monitor exit. |
| 4 | Four public data APIs require capture=. One outer writer spans source and caller-owned publication; private readers never rebind. Replay offers actual pending data locally. Ordinary TgData omits the optional engine argument. |
| 5 | Permanent25-group outcome suite plus migrated46/48-group pool suites, public docs and runnable demo explain wrapper/lifetime/receipt boundaries. |
| 6 | Product007c2e4 separate from reportb62189c. Full actual-branch run:750 executed groups+3 demos,3 live skips excluded; compile/88 grammar files. Current hashes and P0 executable parity pass. |
| 7 | E1 explicitly OPEN. Two-account live testing remains unexecuted under the user's one-account/offline-first choice. |

All eight changed P0 runtime modules have exact executable AST parity; six have byte
parity and two differ only in comments/docstrings. All88 Python hashes match the complete
implementation run; compile/3.7 grammar rechecked. Runtime qualification remains
Python3.11.10/Telethon1.45.0, not native3.7.

## 2 — Rationale still supported

Source/account completion, public preparation completion, caller cancellation, available
data and durable acknowledgment are distinct facts. The code gives owned work an exact
completion record and data an explicit caller owner. Progress retains its receipt/state
authority. The source list avoids per-message whole-prefix copies; snapshots/finalization
produce immutable batches on demand. Close does not acquire independent progress calls.

This answers the demonstrated missing boundary while retaining tested routing, quota,
recovery and progress schemas. Scope stays one owning process/event loop, exclusive
sessions, trustworthy UTC and one source reader per group. Providers settle their own
I/O without depending on control of their pool. Shutdown is cooperative; capture is
in memory. Public docs state these limits and account-specific visible history.
Synthetic wire cannot qualify real proxy/access/history assumptions; E1 remains open.

## 3 — Findings answered

The current plan critic's sole Medium concerns stale metadata across empty failover.
The selected robust transition is implemented in _CaptureWriter.attempt/attach and the
admitted _read loop: empty observation/error/account fields reset together, verified
identity attaches to actual source data, and a complete prefix prevents another attempt.
Test40 covers second-account success/failure, held settlement and identity refusal.
No plan High/Medium or Low remains undisposed.

Historical dispositions remain concrete: arbitrary observer callbacks removed; actual
component outcomes survive secondary reporting; source/provider cancellation provenance
and retained native cleanup tested. PR round2's close-consumed cancellation payload is
addressed by caller-owned capture and invocation completion. The upstream inquiry also
challenged wrapper loss without close and application continuation after the library
call. Those histories are in combined P0/permanent40. This mapping cannot substitute
for fresh behavioral soundness review of the public composition.

## 4 — Issue and PR status

Fetched #17 accurately records plan7/product007c2e4/evidenceb62189c, checks T/0–5 and
leaves6/7 open. It reports exactly two rejected PR rounds, preserves history and keeps
E1 pending. This check's commit/posting completes pipeline6;7 stays pending until the
fresh PR critique is committed and posted.

PR26 is draft; its stale body still cites plan5/producta63099e/725 checks. Update it to
this23-file product, required captures/private completion,750 checks and this check.
Preserve Closes#17, selected existing-access scope, E1, archive exclusion and user
approval for merge. No live call or merge is part of this task.

## Evidence

`python devdocs/work/17-account-pool/probes/review3/merge_audit.py` → PASS:
11 ancestry assertions,23 product paths,15 adjacent modules unchanged,8 runtime AST
matches,88 tested hashes/compile/grammar,35 identical promoted functions,10 moved public
methods;30 saved process logs substantiate750 executed groups/3 excluded skips/3 demos.
[Exact audit and hashes](evidence/review3/merge-audit.json).

The full implementation suite is reused because source/test hashes are unchanged.
Fresh adversarial probes belong to the PR critique. This fidelity PASS cannot waive
CONTRIBUTING §7.3's rejection rule if that review finds any High or Medium.
