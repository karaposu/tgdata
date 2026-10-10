---
model: gpt-6-astra
effort: max
---
# Renewed Stage 2 merge fidelity check — 2026-10-10

**Gate: PASS for fidelity.** CONTRIBUTING §7.1 only. The renewed fresh PR
soundness critique is next; this does not approve merging. Product `c6451bb`
is unchanged during this gate.

**Compared:** fetched origin/dev and GitHub PR22 base
`53306df2c3d87b558be0b7ed4419a42d3229c5f9`; product/evidence head
`cc5050b051f3249f5397136ec61aacacc6e7d3a0`; the complete three-dot diff, triage,
description, folded revision4 `aee7211`, plan critic `d9eefbe` with its completed
experiment `d2dd499`, first PR rejection `b9a8a5d`, and current verification.
GitHub confirms OPEN/draft PR22 on feat/7-account-health-ownership into dev.
SSH refresh timed out; HTTPS fetch and GitHub API checks succeeded with the same base.

## 0. Warmth, weight and model provenance

Description and triage explicitly retain this session's Stage1 implementation,
review and merge context and identify ancestor53306df. Git confirms ancestry.
Current source/evidence was refreshed for this rework and this gate. No new
archaeology refresh or architecture-skill invocation is claimed. Triage says
feature-heavy, matching issue7's enhancement, heavy and open-to-implement labels.
The bounded inquiry is committed at f19ca2a; the description at8350f39.

§9 provenance remains the recorded same-session gpt-6-astra/max evidence, latest
retained turn2026-10-07T05:34:50.039Z. As in Stage1 and the first Stage2 gate, max
is interpreted as at least the feature row's xhigh. This is retained evidence,
not a fresh model-selector reading; no model change or invented current timestamp
is asserted. The original interpretation remains in archive/round-1/merge-check.md.

## 0b. Diff surface and integration scope

The full product diff has eight files: four runtime files (health.py,
owned_health.py, connection_engine.py, tgdata.py), suite33, README, smoke README
and docs/account_operations.md. All runtime seams and tests are surfaced by triage.
The internal guide was a small documented expansion of the initial implementation;
revision4 explicitly includes it. The weight remains appropriate.

The rework itself changes only three runtime files: the existing facade composition
from3d59455 is retained. This distinction explains revision4's three-file statement;
it does not hide an unplanned facade edit. No account routing, joining, persistence,
legacy-health migration, unmerged #17, duncan or unrelated guide change appears.
No dependency or package-discovery change. The new owned module is in the existing
package and uses the already-required standard library/Telethon dependencies.

All work-folder artifacts are archive material for this branch, excluded from any
future dev merge. No archaeology refresh is in the diff. Keep the branch after
integration. The original checkout's two untracked files remain untouched.

## 1. Fidelity to revision4

| Step | Implementation / evidence | Assessment |
|---|---|---|
| 1 transport-faithful regressions | Suite33 RPCReply uses actual MTProtoSender.send, RequestState and result/error construction; eight pre-change cases recorded 0/8 | Complete; synthetic replies do not supply the SDK error's request identity |
| 2 logical request identity | owned_health._request_key; capture_request_evidence; _AnswerEvidence.__call__ snapshots before await; failure Finding copy and full-success hook use the same names | Complete; namespaced owned keys only, explicit seven-envelope/depth contract, no lazy input consumption |
| 3 refused action | _OwnedHealthMonitor._restricted_request and _recover; replacement and clearing follow account-condition lifetime | Complete; same method/action, owner/start/validity/no-self guards retained |
| 4 failure neutrality | health._mark_legacy_neutral, _legacy_neutral and isolate_call; emission-only guards in report/_on_error | Complete; explicit causes/SDK RPC members, fresh RPC precedence, no ambient error list; classify unchanged |
| 5 composition/docs | Suite33 62 cases; all three documents distinguish owned/legacy names, semantics and callback timing | Complete; request stability and non-FIFO delivery are explicit contracts |
| 6 verify/checkpoint | c6451bb product, cc5050b evidence; 445 actual offline passes, 3 live skips, 3 demos, 63 syntax/grammar checks | Complete; separate commits and published truthful status |

No runtime design deviation from the folded revision. The explicit-cause red test
was strengthened before production edits, keeping its expected zero-event outcome.
Only owned-name expectations changed, as the plan requires; legacy expectations
were not weakened. No final-test failure was patched or architectural addition
introduced. Runtime tests are not rerun wholesale for this document-only gate.

## 2. Does the plan still hold?

The rework keeps the verified operation and fixed ledger, correcting the evidence
feeding them. A single bounded logical-key rule serves request waits and restriction
recovery. One failure marker replaces retained exception lists and crosses task
boundaries without adding a registry. The wrapper change required by the fresh
plan critic is present and narrow. No global sender receipts or generic permission
classifier were added.

The prebuild experiment ran before implementation (d2dd499 before c6451bb). Its
carrier claim is distinct from the attribution predicate, whose real composition
cases are in suite33. Synthetic offline testing cannot establish Telegram server
permission/frozen-account policy, which this stage does not promise. Future group
code still supplies actual group-access semantics. Fresh review must independently
challenge the resulting composition; this fidelity pass does not infer soundness
from the plan or passing tests.

## 3. Every selected finding answered

- Initial plan Medium1: caught authentication/identity invalidation still vetoes
  recovery through _OwnedCall.valid; suite33 retains caught-loss cases.
- Initial plan Medium2: SDK MultiError raw leaves are recorded, full batch success
  alone supplies recovery evidence; retained and new sender-built cases cover it.
- Round1 PR Medium1: success and error keys use namespaced leaves; known wrappers
  no longer alias unrelated waits. Suite33 covers nested wrappers and namespaces.
- Round1 PR Medium2: restriction remembers the refused key and requires its later
  success; tests cover repeated proof, metadata, budget refusal, replacement and
  matching positive recovery.
- Round1 PR Medium3: marker-first / new-RPC-before-old-context emission preserves
  independent failures; tests cover handled/escaping wrappers and prior context.
- Revision3 plan Medium1: immutable keys captured before await; the list-mutation
  test observes the real sent action and verifies no manufactured recovery.
- Additional planning task-hop evidence: original pre-proof error/cause stays
  attribution-neutral through awaited tasks, wrappers and explicit-cause rethrow.

No High or Low was reported by the Stage2 plan critics or first PR critique. The
known Stage1 Low (malformed bootstrap self reply can raise a native error while
still refusing/closing) remains outside this diff and is not silently patched.

## 4. Issue status and preserved history

Fetched issue7 is OPEN. T/0/1/2/3/4/5 reference committed, pushed artifacts. The
445-pass count excludes three live skips; suite33 has62 cases, 21 added in rework.
Step6 and7 are honestly pending before this checkpoint. The current first-round
rejection remains explicit; the old fidelity PASS is not renewed acceptance.
Update step6 after this committed check is posted, and step7 only after the new
review is committed/posted with its verdict.

Original PR review/prompt/probes were moved byte-for-byte to archive/round-1 in this
checkpoint so the fresh review can own root pr-critic.md without erasing history.
The archive contains one distinct rejected Stage2 round, independent of old PR16.

PR22 correctly uses Refs #7, the same staged-work exception as merged PR21, because
lookup/access, allowance and joining remain stages3–5. It must not close all of #7.

## Next

Commit/push and post this check on PR22; run fresh in-session critic-d on the actual
implemented diff and revision4. Any Medium/High rejects under §7.3. A second Stage2
PR rejection requires description/traverse under §7.4, not a direct patch or another
routine re-plan. Merge still requires the user's go-ahead after both gates.
