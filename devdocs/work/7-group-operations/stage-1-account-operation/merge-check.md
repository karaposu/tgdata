---
model: gpt-6-astra
effort: max
---
# Stage 1 merge check

**Gate: PASS — fidelity check only; fresh PR critique is still required.**

Subject: `origin/dev...1885d43`, product commit `2fe9aeb`, together with this
folder's triage, description, revision2 plan, selected critic, design finding and
verification record. Freshly fetched dev remains `95ed4c7`, also the merge base.
No base movement or product change has invalidated the recorded tests.

This check ran in the same warmed session. It is not the later soundness critique
and does not authorize a merge.

## 0 — warmth, weight and model

PASS. Warm intake `7b0e89d` is an ancestor of the branch; triage names the refreshed
factory, admission, session, health and actual SDK lifecycle contracts. Description
records retained #18/#19/#17 context plus the #7 reassessment. The description now
names the intake commit explicitly, and triage now has its missing model/effort
frontmatter. These are record clarifications, not new warming or runtime changes.

GitHub #7 is labelled enhancement and heavy, matching feature-heavy triage.
The weight remains justified even though the runtime addition is small.

§9 flag: `model-verification.md` records the available same-session Astra/max
metadata, including its earlier timestamp. Max is treated as the higher-effort
setting satisfying the Astra/xhigh feature row. No new selector reading or
independent reviewer agent is claimed.

## 0b — surfaced territory and actual diff

PASS. Existing changed runtime files are exactly the surfaced connection factory
and budget provider. The new internal account_operation module implements the
ownership/lifetime boundary explicitly identified by triage and traverse.

The new test32 file and docs/account_operations.md did not exist to be surfaced;
both were explicitly planned in Steps 4/5. The smoke-test README entry is the
planned documentation companion. These do not require a heavier classification:
the work was already heavy. No health model, new schema, pool router, public TgData
method, group resolver or join implementation entered the product diff.

Product diff: six files, 902 added/two removed lines, including 621 test lines and
93 documentation lines. Runtime is a 133-line internal module plus the factory/
context and three-line budget-provider changes. Workflow artifacts are separate
commits and must remain excluded from eventual integration under §7.6.

## 1 — implementation versus plan

| Planned step | Evidence in the product | Result |
|---|---|---|
| 1: expectation/proof/lifetime | account_operation.py strict positive-int check, fresh GetUsers(InputUserSelf), read-only owner/client, task/active checks before and after proof | PASS |
| 2: configured temporary client and cleanup | connection_engine.py constructor kwargs precede connect; auth normalization restricted to setup/proof; finally closes handle and awaits retained cleanup | PASS |
| 3: admission agreement | budget_client.py owned branch delegates to verify_account before existing reserve/send; ordinary branch unchanged | PASS |
| 4: offline contract suite | test32 uses actual SDK connect/dispatch/disconnect, real SQLite budgets and event-forced overlap; 28 cases | PASS |
| 5: docs and verification | maintainer contract, smoke-test entry, 383 actual offline passes/three live skips, three example runs and 61-file compile/grammar checks | PASS |
| 6: separate commits/status | product2fe9aeb, notes1885d43, pushed branch; #7 Stage1 T/0–5 checked with commit evidence | PASS |

Named implementation details/deviations: first-login error text was clarified to
say authenticate separately, avoiding a misleading interactive-login suggestion
on a path that never logs in. This fulfills the planned explicit-auth contract.
Three local test-fixture corrections are recorded in verification.md; they did
not change expected outcomes or runtime design. There are no unexplained product
deviations. No Stage1 API is exported at package top level.

## 2 — whether the plan still holds

PASS. Actual SDK probes established the policy/dispatch/cleanup seams before code
was built. The final code keeps one fresh client and immutable expected owner per
private lexical operation, with no global owner registry. The plan's central
simplification survived implementation.

Limits remain explicit: caller code must not detach/rebind the raw SDK client;
cleanup settles one attempt without promising a timeout or successful closure
when the SDK fails; SDK server errors can still have a final two-second backoff.
Health ownership remains Stage2 and is not represented as fixed here.

## 3 — plan critic findings

PASS. The only Medium finding required terminal invalidation after identity/auth
proof fails. `_identity_error` and missing/auth-error branches close the handle
before raising. The closed binding remains on the client. Test32 catches refusals,
changes the reply back and proves subsequent handle/budget admission still refuses
without a claim/send. The chosen robust mitigation is present; no High/Low was
left unanswered. The prebuild REORDER experiment has a committed PASS (`542c68e`)
before the folded plan (`ad66e32`) and product (`2fe9aeb`).

## 4 — issue status and publication scope

PASS. Current #7 status is Stage1-specific and backed by committed T/0–5 artifacts.
Steps6/7 remain pending until the PR and critique exist. The original request and
old PR16/revision3 history remain intact; whole #7 is OPEN.

This PR will use **Refs #7**, not a whole-issue closing directive: the user selected
only Stage1 and later stages are still required. That is an intentional staged
exception to §6.6's usual whole-issue `Closes` wording, consistent with this plan's
explicit requirement to keep #7 open. PR16 is not reused or merged.

## Validation and next gate

Same product commit as verification.md: 383 actual offline passes (28 new), three
legacy live checks skipped, three offline examples, compile/Python3.7 grammar for
61 files. No live Telegram work. Current full diff passes whitespace checking.
No repetitive full-suite rerun is needed for these record-only changes.

Open a Stage1 PR into dev, post this check, then run fresh in-session critic-d
on its published diff and revision2 plan with additional behavioral probes. Any
High/Medium rejects under §7.3 and sends the work to re-planning under §7.4.
