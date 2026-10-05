---
model: gpt-6-astra
effort: max
---

# #7 — merge check

**Verdict: technical fidelity PASS; process qualifications remain.**

The implemented feature matches the folded plan, with the documented corrections
below. All three Medium plan-critic findings are answered. No unresolved runtime
plan deviation was found in this check. This does not authorize merging: the PR
and its fresh critique are still pending, §9 model/effort has now been verified,
and the publication follow-ups below must remain visible.

## Reviewed state and evidence

Checked 2026-10-05 in the same warmed session. Target `origin/dev` was fetched and
remains `45bab7172621f576fa5e4b3265f87ec20da04fd5`, also the merge base and an
ancestor of this branch. Starting branch head was
`581c7f68ff619773344ed099d1426795757cdba5`; runtime/test/dependency content remains
identical to implementation commit `8e245f8f1d001c30ecd561e173e8742302cc313d`.

Read together: triage.md, desc.md, the pre-implementation folded plan at2601f94,
current plan.md, critic.md, implementation.md, verification.md, traverse finding/
state, the actual13-file product diff, and GitHub issue7's live body/labels/comments.
The additional files in the branch diff are this issue's work records. There is
no PR for `feat/7-group-operations` at review time.

The existing verification receipt reports151 offline groups passing and3 live
checks skipped on Python3.11.10/Telethon1.45.0. Raw saved runner outputs were
cross-checked: test20=25,19=33,18=28,17=12,16=21,15=11,14=11,13=5 plus1 skip,
12=5 plus2 skips. Runtime has not changed since that run, so it was not repeated.

Three targeted supplementary probes ran successfully in `merge-check-probes.py`:

- Real SDK retry of the access request makes two sends of limit1; the read budget
  retains the failed attempt and settles the successful empty response.
- A metadata lookup with group recovery disabled still recovers a recorded
  account logout and an authorization flood wait that the SDK slept through.
- Real SQLite operations with an injected close fault preserve a primary local
  failure; a cleanup-only fault becomes a local storage error. An actual read-only
  SQLite connection refuses admission without recording a charge.

Sockets were blocked, all credentials/replies synthetic, and files temporary.
The probes observe SDK dispatch, health and SQLite behavior; they do not establish
live Telegram acceptance. They are supplementary evidence, not extra groups
silently added to the151-group regression total.

## 0 — Was the work warm and weighed?

**Satisfied after record repair.** The pre-implementation triage commit15edbe0
records retained full-source context from #5/#9/#6 and refreshed group/client/
health/budget/SDK paths. Its anchor45bab71 is in the branch ancestry. The same
session performed this check and re-read the actual new modules, shared changes,
public docs and tests. No cold-session or fresh-agent handoff is claimed.

The required top-of-desc warming line was missing even though its evidence was
already committed in triage and present in the issue body. This check restores
that line from the contemporaneous record and explicitly dates the repair.
It does not claim that the line existed when the description was first committed,
or invent a new archaeology run. Archaeology files remain unchanged under §4.1's
retained-session/warming-by-reading provision.

Triage calls this feature-heavy. GitHub labels are `enhancement`, `heavy`, and
`open to implement`; path/weight agree. The required full traverse is complete
at8129809, with the six upstream outputs archived and the route map/index retained.

## 0b — Did the diff stay within the surfaced territory?

**Yes at concept level; five product paths were not literally listed.**

Eight modified existing files were surfaced explicitly: README.md, setup.py,
tgdata/__init__.py, budget_client.py, connection_engine.py, health.py, tgdata.py,
and smoke_tests/README.md. The following additions/companion file were not literal
triage rows:

| Path | Relation to surfaced work |
|---|---|
| tgdata/group_operations.py | New metadata/result/access/join implementation for triage records/public API/access/SDK regions |
| tgdata/join_budget.py | New allowance resource for the surfaced persistence/admission region |
| tgdata/join_client.py | New actual-send guard alongside surfaced BudgetClientMixin/factory/SDK retry seams |
| tgdata/smoke_tests/test_20_group_operations.py | New regression suite using the surfaced auth/health/read-budget harnesses |
| requirements.txt | Companion dependency declaration to surfaced setup.py; align the minimum with the used1.45 result types |

These are implementation discoveries within the weighed feature. Heavy remains
the correct classification. No read-budget schema migration, discovery change,
worker/login/payment implementation, duncan file or unrelated guide edit appears.
All work-folder artifacts belong to #7 and must remain on the archive branch
when the product diff is eventually merged under CONTRIBUTING §7.6.

## 1 — Does implementation match the plan?

**Yes, with named refinements and wording corrections.**

| Plan step | Implementation and verification |
|---|---|
| 1 References/results | group_operations.py `_parse_target`, frozen metadata/lookup/access/join classes and `to_dict`; grammar/projection/privacy tests |
| 2 Durable allowance | join_budget.py configuration/status/atomic `_claim`, independent versioned tables, monotonic observed clock and rolling expiry; persistence/process/contention/failure tests |
| 3 Actual-send admission | join_client.py `_JoinSender.send` and `_call`; fresh identity before committed claim, then no await before enqueue; retry, wrapper, batch, changing-ID and factory tests |
| 4 Ephemeral facade/health | TgData `_group_operation` and `get_join_budget`; GroupEngine resolver/read/join paths; HealthMonitor group-recovery flag and owned account override; lifecycle/health/error tests |
| 5 Offline coverage | test20 has25 behavioral groups spanning the21 planned areas; supplemental probes here explicitly inspect retry wording, account/wait recovery and ledger cleanup |
| 6 Docs/dependencies | README contract/examples, smoke-test index, exports and matching setup.py/requirements.txt minimum1.45.0 |
| 7 Verify/commit | recorded151 offline passes/3 live skips; implementation8e245f8 and separate work-notes581c7f6; branch pushed, issue step5 complete |

Differences from the plan as it stood before implementation:

1. Numeric resolution now checks an exact stored row before get_input_entity.
   The SDK can cast PeerChat without a stored row. The extra query enforces the
   existing known-cache requirement and prevents ambiguous/missing IDs from sending.
2. Native KeyError for an empty resolved-peer result joins ValueError/TypeError
   translation. It is a local resolution failure, not a Telegram health finding.
3. The new facade suppresses incidental implicit context for non-RPC exceptions,
   preserving the exception object, traceback and explicit cause. This closes the
   same error-provenance problem when a transport failure occurs inside a caller's
   unrelated RPC handler; the old global classifier remains unchanged.
4. The exclusively owned ephemeral client's flood threshold becomes zero after
   authorization, covering nested SDK identity/entity requests as well as direct
   operation RPCs. Existing authorization wait behavior is retained.
5. Optional post-ack warning emission is also protected from failing caller
   logging handlers, so warning delivery cannot erase an acknowledged join.
6. Dependency declarations were raised to Telethon>=1.45.0,<2.0 because the
   implementation imports its wrapped join result types. This follows the user's
   selected1.45 target. The plan's old “Safe in nature: True — documentation only”
   label for step6 was therefore inaccurate; corrected toFalse during this check.
7. The status-test fixture now supplies account222 instead of accidentally opening
   the default account111. The expected fresh-account behavior was not weakened.

Items1–7 are already described in implementation.md and, except the fixture,
were reflected in the plan at581c7f6. This review additionally clarifies two
phrases rather than changing runtime behavior:

- “One history request” means one logical SDK invocation. Existing SDK retries
  can create additional sends; each is bounded and read-budgeted. The description,
  plan and public README now state this explicitly, grounded by the new probe.
- get_join_budget returnsNone only when no JoinBudget object was supplied. A
  supplied ledger without an account policy raises configuration error, as the
  implementation and public README already specified. The plan now says so.

One trailing blank line in traverse/source-input.md caused a whole-branch
`git diff --check` warning; removed without changing source-input content. The
previous receipt's working-tree check had not checked that already-committed
artifact. The full target-to-working-tree whitespace check now passes.

## 2 — Does the plan still make sense?

**Yes.** Metadata, membership, readable history and mutation acknowledgment retain
separate meanings. Durable policy outlives ephemeral clients; actual-send admission
covers hidden retries and freshly verified identity. Missing/uncertain results
remain explicit. The shared factory, separate read units and legacy GroupInfo
remain in their intended roles.

The numeric helper discovery, error provenance, cache-write failure and retry
probe sharpen the implementation details; they do not invalidate the observation/
admission architecture. The two wording repairs remove stronger promises than
this shared SDK composition actually makes. No replacement design or new feature
is needed on the evidence of this fidelity review.

## 3 — Were every High/Medium critic finding answered?

**All3 Mediums answered;0 Highs and0 deferred Lows in the plan critic.**

| Finding | Concrete answer | Evidence |
|---|---|---|
| Risk1: local enrichment erases join acknowledgment | GroupEngine.join_group at group_operations.py:283 retains acknowledged status, catches optional nested projection/cache failures and contains warning-handler failure | test_ack_without_details_and_unknown_reply; test_ack_survives_real_cache_failure; test_ack_survives_warning_failure |
| Risk2: native local errors inherit unrelated RPC health | local error bases/parser/cache translation; outer RPC-only access-denial catch; new facade context isolation at tgdata.py:201 | test_native_errors_inside_rpc_handler; test_denials_and_other_errors; private-diagnostics tests |
| Risk3: ephemeral events use stale primary account | HealthMonitor.call account override, owned note_account at health.py:562, fresh join/read identity notes, unknown pre-auth identity | test_health_recovery_and_identity; test_concurrent_identity_and_callback_reentry; fresh/changing-account tests |

The selected robust mitigations are present. No unselected long-term subsystem
was introduced. Wider receipt/origin/identity migrations remain the critic's
recorded future work, not hidden unfinished requirements of this implementation.

## 4 — Is the issue status complete and honest?

**Committed-artifact ticks are supported; publication/remaining gates stay pending.**

T=15edbe0; traverse=8129809; description=a4944e1; plan=bd13e4b;
critic=a647aeb; fold=2601f94; implementation=8e245f8 with notes581c7f6.
The live issue correctly leaves step6 (merge-check plus PR) and step7 (PR critic)
unchecked. This check completes the reading/artifact portion of step6 only.
The issue update must name this report and preserve the PR/critic pending state.

The issue has0 comments, so the §6.5 description-posting instruction has not
been fulfilled even though the description artifact exists. Record that publication
follow-up rather than implying every procedural sub-action was done. No PR exists,
so posting this merge check as a PR comment is also pending PR creation. These
posting tasks belong in the next publication step; neither is silently certified
by this document. No PR, merge, issue close or live group action was performed.

## §9 — Model and effort qualification

**VERIFIED after the initial merge check.** The active session’s23 available
turn_context records consistently name GPT6 Astra at max effort, including this
feature’s work. See model-verification.md for the scoped evidence and official
reference. Max is the higher effort setting; the record does not claim the literal
xhigh value. This satisfies the rule’s required model/adequate-effort intent without
a downgrade or waiver. Earlier unknown frontmatter has been corrected transparently.
The fresh PR critique remains a separate required gate.

## Disposition

The requested merge-check artifact is complete and ready to accompany the PR.
Before merge: finish publication (description reference/comment and this report
on the PR), obtain the fresh PR critique, and obtain
the user's merge go-ahead. Keep duncan excluded and retain work documents on the
feature archive branch. If runtime code or target dev changes, revisit the
corresponding fidelity and verification evidence before treating this check as current.
