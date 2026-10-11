---
model: gpt-6-astra
effort: max
---
# #7 Stage 5 — merge check

**Gate: PASS — fidelity.** Date:2026-10-11. Fresh PR soundness critique remains the
next gate after publication; this check does not authorize merging.

Subject: product diff `f15f1a8..4b4ae21`, reviewed with Stage5 triage, description,
plan revision2, pre-implementation critic and verification. Branch head at review:
`285c1c8`; freshly fetched `origin/dev` is still `f15f1a8`. No intervening base change.
All13 product paths were read, including the complete865-line joining test suite;
the inherited ownership/health/ledger/SDK seams were refreshed in this same session.

## 0 — Warmth, weight and model

The description records retained Stages1–4 context at the exact merged base
`f15f1a864f07905aee1c8d679f6039fb5c898ae6`. That commit is an ancestor of this branch.
This reviewer is the same warmed session. Current group resolution, account operation,
facade/factory, owned health, JoinBudget, read-budget adapter and installed Telethon
dispatch/request/result code were re-read at their relevant complete implementations.
No new archaeology refresh or cold subagent review is claimed.

Triage exists at`9e3fb4e`: feature-heavy,26 surfaced items. GitHub currently has
`enhancement`, `open to implement`, `heavy`, matching the path/weight. The irreversible
mutation and ownership/admission boundary justified heavy; the final scope confirms it.

CONTRIBUTING §9 requires Astra at xhigh or the specified Fable/max alternative for
this feature gate. Matching session metadata, re-read now, reports `gpt-6-astra` /
`max`, turn context `2026-10-11T01:51:41.282Z`, thread
`01a108f3-12f8-7ef2-bc82-745d4feb2a25`. The requirement is satisfied. Artifact
frontmatter reflects that evidence, not an inferred model name.

## 0b — Triage boundary

The source changes stay at the surfaced group-domain, facade/factory and SDK-admission
seams. `join_client.py`, GroupJoin and test36 are new deliverables at those seams.
Package exports and public docs are the surfaced public-contract boundary. No health,
account-operation, read-budget, session-store or JoinBudget implementation changed.

One preexisting file was not named separately in triage: `test_29_backfill_public.py`.
Its exact constructor-list assertion had to include the plan's trailing `join_budget`
argument and None default. The old positional backfill call remains. This is a
documented compatibility assertion update, not a backfill behavior change or a
reason to reclassify work already weighed heavy. There are no other unexpected
product areas, configuration edits or unrelated files.

## 1 — Implementation against each step

1. **Outcome/interpreter:** `group_operations.py` adds frozen GroupJoin and the
   bounded helper. Existing resolution remains unchanged. Membership/payment
   observations avoid mutation; direct supported peers keep the resolved ID/hash;
   invites retain token case. Three special RPC outcomes require the exact original
   mutation object. Ok validates one of seven Updates roots; WebView validates its
   used signed64 fields. Metadata stays preflight, with no post-ack enrichment.
2. **Admission:** `join_client.py` classifies two mutation families and only the
   supported envelope, rejects batches/unknown wrappers/families/depth, binds the
   verified handle/client/task, and wraps the passed sender only. Every new enqueue
   re-proves owner, completes synchronous `_claim`, then sends with no intervening
   await. Invalid policy/claim returns fail locally; usage is never refunded.
3. **Composition:** the factory's MRO and inactive marker match the plan. The optional
   constructor argument is appended. The facade validates local input/config, uses
   `_account_health_operation`, checks owner policy, activates and finally clears
   the marker. It does not call `confirm_group_access`, alter legacy clients or
   add an engine-wide join ledger.
4. **Tests:**44 groups cover the public composition and declared fault matrix.
   Real SDK serialization/decoding/error construction and real SQLite coexist with
   a clearly synthetic transport. Held replies force overlap; cancellation and
   delayed/failed cleanup are exercised. Direct malformed/local fixtures are labeled.
   Neither test output nor docs claims live membership from these fixtures.
5. **Exports/docs:** GroupJoin and UnsupportedJoinRequest are exported. README,
   group/account/allowance docs and new group_joining.md describe guard scope,
   explicit policy, all outcomes, unknown preflight IDs, source provenance,
   uncertainty, no refunds and optional separate read proof. No rate is sold as safe.
6. **Verification/record:** product`4b4ae21` and separate work`285c1c8` are pushed;
   committed verification reconciles all22 suites,3 demos,69-file compilation/grammar
   and the product export. Stage5 remains unmerged and unrelated checkout state is intact.

Deviation: only the constructor assertion update named above. It follows the planned
additive signature, is recorded in the product commit and verification, and retains
the behavior being protected. A test-fixture title construction was corrected before
the first test execution. No architectural deviation or hidden runtime fix.

## 2 — Does the plan still make sense?

Yes. The merged prerequisites make a bounded consumer sufficient: one portable
outcome, a small admission adapter and a facade method. No generic raw-client
authority scheme, refund protocol, result journal or renewed health redesign emerged.
The actual installed1.45/layer229 result wrapper and exact request identity were
examined before implementation. Tests exercise that composition, not just a helper
that supplies the intended behavior.

The known uncertainty is stated accurately: failure after admission may follow a
remote mutation; metadata is preflight; joining is not history access. Live Telegram
acceptance is an unclaimed, separately authorized frontier. No hidden live-validation
requirement is passed off as an offline result.

## 3 — Prior critic closure

The plan critic`752b8bf` had0 High/0 Medium/0 Low and a REORDER prerequisite: cancel
before completed self proof and after admitted enqueue, using the real SDK/SQLite/
owned cleanup composition. Experiment`ab26367` passed before product edits:0 sends/
0 charge before proof;1 send/1 retained charge after enqueue; cancellation propagated
and one disconnect attempt settled. Fold`aee1a70` records zero mitigations and
unchanged steps. Delivered test36 repeats both public-path cases and adds cleanup/
callback/overlap cases. The prerequisite was answered rather than deferred.

Consciously unchanged inherited Lows: Stage3's malformed ChatInviteAlready nested
peer can leak AttributeError but stops before mutation; Stage4's fractional-expiry
rounding may briefly report zero retry delay while refusing admission. No new fix
for either is claimed, and neither ledger nor existing resolver was patched here.

## 4 — Issue status and verification honesty

The current Stage5 block on#7 correctly checks T,0–5, each backed by a committed
ancestor: `9e3fb4e`, `068ae99`, `0565b3f`, `789b588`, `752b8bf`/`ab26367`, `aee1a70`,
`4b4ae21`/`285c1c8`. Steps6/7 are still unchecked at this check's write time. They
must be updated only after the corresponding artifacts/publication. Earlier completed
stages and original issue text are preserved; parent#7 remains open.

Verification evidence is tied to the unchanged product commit: **573 actual offline
groups passed,3 live skips**, including44 new groups;22 suites total. The first run's
one obsolete-signature assertion failure is retained and its23/23 rerun recorded.
All other21 suites passed. Three demos passed, with backfill restart0 source reads;
69 files compile and parse with Python3.7 grammar; exported-tree test36 passes44/44.
No native Python3.7 or live Telegram run is claimed. Counts and commit ancestry were
checked again during this gate; no unnecessary repeat of the whole suite was made.

## Publication and integration boundary

Publish a PR into `dev` with `Closes #7`, post this check, then run fresh in-session
critic-d over the implemented diff together with revision2. One High/Medium rejects
under §7.3 and requires the §7.4 process; do not patch review findings ad hoc.

At an eventual authorized merge, exclude `devdocs/work/` and any archaeology refresh,
test the merged product and retain this feature branch as the archive. This task
authorizes review/publication only, not merging or live joining.
