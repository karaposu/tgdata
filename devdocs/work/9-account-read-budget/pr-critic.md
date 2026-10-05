---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a supported live Telegram read returns more message slots than its
explicit request bound. That would invalidate the hard pre-dispatch ceiling,
even though the implementation charges the actual response and stops afterward.
Affordable now: no — a decisive server observation requires an authorized live
account; this run's agreed verification boundary is offline. Scripted oversized
replies test defensive handling, not server conformance.

# Fresh PR critique — #14 / issue #9

**PR gate result: PASS — 0 High, 0 Medium, 0 Low findings.** No runtime changes
are required by this review. This is a code soundness verdict under
CONTRIBUTING §7.3, not model-policy certification or permission to merge.

Subject: PR #14's diff from `af593fc` to `293bfbc`, together with
`step_by_step_impl_plan.md` revision 2. The implemented runtime/user docs/tests
are exactly commit `07d983a`; subsequent commits before this critique contain
only work notes. Reviewed on 2026-10-05 in the same warmed session, without a
subagent, using `pr-dynamic-critic-prompt.md` and the critic-d three-phase process.
The initial `critic.md` and its prompt remain unchanged.

## High-level summary

The shared admission guard is in the actual Telethon request loop, so hidden
application-level retries cannot reuse a single reservation. The ledger's
transaction is committed before enqueueing, never held over a network await,
and an unsuccessful request leaves its conservative charge intact. The
authenticated self response selects the account; stale cached IDs do not.

The review followed the complete changed components and their surrounding
engine/health control flow, plus SDK request, pagination, sender recovery and
download recovery code. Six additional adversarial groups passed on both
Telethon 1.45.0 and 1.33.1. They include an independent ledger oracle and actual
SDK re-fetch paths that the implementation suite's media stand-in did not
exercise. No concrete accounting bypass, cursor loss, swallowed budget stop
or invented Telegram health verdict was reproduced.

The implementation matches the selected scope, not every possible reading of
the original issue: callers must enable the budget and share its local SQLite
file; metadata/previews, passive updates and file bytes are excluded. These
boundaries and the unverified live-server premise are already explicit in the
description, plan, issue and README.

## Premise inventory

### 1. A supported request bounds the returned message slots

First dependent step: plan steps 1–2, where requested capacity becomes a ceiling.
Waste if false: the hard-ceiling interpretation and its dispatch contract would
need revisiting across all readers. Scheduled test: defensive oversized-reply
handling in step 4; live conformance is outside the run. Cheapest decisive
observation: send each supported request to a live authenticated account and
compare actual slots with bounds. Access/authorization is unavailable within
this run. Current coverage: request definitions/documentation and scripted
replies; **non-covering for live server behavior**. The premise remains open as
a known execution boundary, not silently certified by the green tests.

### 2. Capacity is atomic and remains correct across policy/time/restart changes

First dependent step: step 1. Waste if false: every reader can overspend or
incorrectly stop, so adapter/engine work would rely on a false ledger. Scheduled
test: real four-process SQLite probe before planning and implementation tests
in step 4. Cheapest earlier test: the same real transaction composition, which
already ran before build. Current coverage: 40 competing claims admitted exactly
98/100 units, plus this review's 960 deterministic randomized transitions per
SDK run against an independently computed balance, cap, reserved amount and
retry boundary. Policy changes, reopening, refunds, expiry, oversize settlement
and backward time are included. A separate in-flight test proves that an old
response cannot refund seven units admitted in a newer window. These execute
real SQLite; no fake ledger supplies its behavior.

### 3. SDK retries and implicit re-fetches reach the guard

First dependent step: step 2. Waste if false: the advertised common guard would
need moving or extending before any reader can rely on it. Scheduled test:
real `_call` retry probe before build, implementation step 4, then fresh PR
probes. Cheapest earlier test: actual SDK request loop with a recording sender;
already executed before build. Current coverage: fresh identity, retry admission,
cached waits, entity-resolution delay, supported request families, nested
wrappers and batch refusal in the implementation tests; new real
`Message.get_sender()` and media file-reference recovery flows in this review.
Those paths propagate `ReadBudgetExceeded` without sending the denied message
request. Scripted transport supplies errors/replies; SDK control flow and the
guard are real. No additional affordable behavioral check is deferred.

### 4. Resizing a page preserves iterator position

First dependent step: step 2. Waste if false: chronological/after-ID fetches and
polling could skip messages while the ledger appears correct. Scheduled test:
pre-build real iterator probe, then forward/reverse/ID tests in step 4.
Cheapest earlier test: observe actual outgoing limits/offsets and yielded IDs
on the installed SDK; it ran before planning. Current coverage: 37-item reverse
page growing to 100, refused ID chunk resumption, filtered rows, and a fresh
forward-resume probe yielding ten consecutive IDs with a 3-to-7 page change.
The real SDK calculates offsets; synthetic messages do not establish live
Telegram's result selection. Both tested versions preserve the observed cursor.

### 5. Engine exception paths preserve useful partials and stop locally

First dependent step: step 3. Waste if false: fetched work could disappear or
polling could spin on a local policy stop. Scheduled test: step 4, after the
new implementation exists; this is a code property rather than an untested
vendor premise. Cheapest decisive observation: run the actual engines with
scripted transport interruptions. Current coverage: implementation fetch/search/
media/discovery/polling/callback tests; new discovery connection-failure probe
retains five links from the first page when the next attempt exhausts capacity.
Real sender/media re-fetch stops reach the public error with a partial frame
and no Telegram health event. These are observed engine/SDK flows.

## Restart check and inherited lessons

This feature addresses missing enforcement, not a restart after an incident or
an abandoned design. No wrong-layer finding was established. The existing
discovery username-wait incidents remain handled by the unchanged resolution
path; the read budget is not claimed to repair those historical incidents.

- **Session load/save is not atomic accounting:** step 1 uses a separate
  transactional ledger; the real process probe preceded build.
- **Session labels/cache rows are not authenticated identity:** the initial
  critic's Medium was folded into steps 2–5. Each dispatch/page/status query
  reads self identity, with no long-lived billing cache.
- **SDK behavior must be observed:** retries/reverse paging had pre-build
  probes, two-version implementation coverage, and fresh implicit-read probes.
- **A local stop is not an account restriction:** the error family suppresses
  incidental exception context; actual media recovery and engine tests confirm
  no invented verdict. Existing health/flood suites remain green.
- **Processed output must survive interruption:** step 3 attaches partials;
  both immediate quota exhaustion and a connection-failure retry were observed.

## Source and probe evidence

The critical admission sequence is `tgdata/budget_client.py:72`: fresh identity,
atomic `_reserve`, real sender enqueue with no intervening await, then response
settlement. `ReadBudget._transaction` (`tgdata/read_budget.py:188`) closes each
short connection on every path; `_reserve` (`:292`) commits denied snapshots
before raising and `_settle` (`:309`) changes only the still-active token once.
Paging/ID restoration is in `tgdata/budget_client.py:116`.

Full source reads covered the changed ledger/adapter/factory, message and
discovery engines, façade, health reporting, exports, test_18 and README; the
surrounding source had also been read during the warmed implementation session.
SDK reads included UserMethods._call/get_me, RequestIter, message/ID iterators,
SenderGetter, ChatGetter, Message._reload_message and file-reference recovery.

Run the new probes with:

```bash
.venv/bin/python devdocs/work/9-account-read-budget/probe_pr_budget.py
PYTHONPATH=/private/tmp/tgdata-issue9-telethon-1.33.1 .venv/bin/python devdocs/work/9-account-read-budget/probe_pr_budget.py
```

The second command uses the isolated 1.33.1 install from implementation
verification; it does not downgrade the project environment. All probe files,
credentials and account IDs are synthetic/temporary. Sockets are blocked.

Exact final output on 1.45.0:

```text
PR #14 adversarial probes — Telethon 1.45.0; runtime code unchanged
Ledger oracle: 960 randomized transitions match independent accounting, including restart and rollback
In-flight policy/expiry: lowering the cap stops sends; an old reply cannot refund seven new-window units
Missing sender: real Message.get_sender re-fetch is refused, its budget error propagates, two slots stay charged
Expired media: real SDK download/refetch stops at quota; one file request, one charged message, no health verdict
Discovery reconnect: five mined links survive a failed second read and exhausted retry; six units charged
Forward resume/wrappers: ten consecutive IDs, correct resized cursor; nested and batched guards prevent sends
All six adversarial probe groups passed
```

On 1.33.1 the header reports `Telethon 1.33.1`; the remaining seven lines are
identical. The first compatibility attempt used FileReferenceExpiredError,
which 1.33.1 does not recover from; its ordinary warning/missing-media behavior
was not a budget regression. The probe now uses FilerefUpgradeNeededError,
the actual recovery trigger both versions support. Assertions stayed unchanged;
both full probe runs then passed. No runtime code was edited to obtain a pass.

The prior 95 offline groups, 28-group 1.33.1 run and README example remain
applicable: `git diff 07d983a HEAD -- README.md tgdata` is empty. Three live
checks remain skipped. The two new modules parse under Python 3.7 grammar;
that is a syntax check only, not execution on a Python 3.7 interpreter.

## Findings

None meeting Low, Medium or High severity were established from the reviewed
diff and probes. There is no rejected-PR re-plan triggered by §7.3.

## Phase 3 — mitigation selection

Executed after the findings pass. There are no Medium/High risks and therefore
no mitigation proposals to rank or select. No selection boxes, speculative
refactors or new prerequisites were manufactured. The Phase 2 verdict and
severity counts remain unchanged.

## Qualifications for the merge decision

The known live-server premise, selected accounting exclusions, synchronous
SQLite busy timeout and clock assumptions remain documented limits. The review
does not establish a safe numeric rate for Telegram or production latency
under arbitrary contention.

CONTRIBUTING §9 specifies the feature model/effort assignment. Exact active
variant and effort are unavailable, so this review records `unknown` and
cannot certify compliance. The merge check already flags this; it is not
hidden among code severity counts. Actual integration still needs the user's
go-ahead, must exclude work-folder documents, and must retain the archive branch.
