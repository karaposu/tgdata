---
model: gpt-6-astra
effort: max
---
**IMPLEMENT AS WRITTEN — after the affordable review falsifiers were executed.**

Falsifier: a delayed or cancelled self-proof permits a quota claim/group read for
an unverified account, overlapping initial proofs exchange owners, or real SDK
cleanup replaces work outcomes or loses caller cancellation.
Affordable now: yes — executed before this verdict in `pr-critic-probes.py`; the
ownership/admission/cleanup assertions passed. No affordable premise test is left
scheduled after acceptance. This is a post-implementation PR gate, not a new build.

**Gate: ACCEPTED — 0 High, 0 Medium, 1 Low consciously left.**

## High-level summary

PR21 supplies a small internal foundation with explicit account ownership. Its
constructor policy is set before authentication, initial proof uses the temporary
client, and later read admission must agree before quota is reserved or sent.
Cleanup has a separate retained completion and preserves the documented outcomes.

Eight additional probe groups exercised real Telethon1.45 and real SQLite with
synthetic replies and forbidden sockets. They confirmed delayed admission, reversed
proof completion, normal iterator use, cancellation and failures late in SDK close.
One Low records a diagnostic gap for unexpected missing-self response shapes
during the SDK's own connection bootstrap. It does not permit group work, quota
spend or login prompts, and the client still closes.

Subject: published PR21 diff from dev `95ed4c7` to `611522e`; unchanged product
`2fe9aeb`; folded revision2 `plan.md`. The prompt was saved separately in
`pr-dynamic-critic-prompt.md` (`48bdcf7`). Original planning critic files remain
untouched. This review ran afresh in the same warmed session, with no subagent.

The published six-file product diff matches local changes/hunk coordinates after
normalizing GitHub's different function-heading annotations. Normalized SHA256:
`dd3b33efdf2d5f93aedae74e9c11fd53f4115d441bed038cad903e559510507a`.
Later commits in this review contain work-folder evidence only.

## Premise Inventory

### P1 — ownership proof and admission compose in the actual SDK

**Premise:** direct self RPC identifies the temporary client independently of
cached identity, and a later proof happens before actual budget reservation/send.
**First dependent step:** 1, then integration Step3. **Waste if false:** the handle
and budget integration would need redesign. **Original test timing:** prebuild
experiment before Step1, then Step4 regressions. **Cheapest test now:** delay actual
SDK request resolution, change the synthetic account before admission, and inspect
the real budget. **Coverage:** original28 cases plus delayed_resolution,
cancel_admission, reversed_initial_proofs and successful_iterator below. Real SDK
dispatch and budget code execute; the wire supplies replies, not the admission
decision. Confirmed for the private contract; no global health guarantee inferred.

### P2 — retained close preserves outcome under asynchronous failures

**Premise:** actual SDK disconnect settles before the context exits while repeated
caller cancellation is preserved separately from cleanup failure.
**First dependent step:** 2. **Waste if false:** cleanup implementation and callers
depending on it need revision. **Original test timing:** SDK cancellation probe
before Step1, then Step4 failure matrix. **Cheapest test now:** fail session.close
after the transport closes; cancel a failed operation twice while disconnect is
pending, then fail close too. **Coverage:** session_close_failures and
cancel_over_primary_and_failed_close run actual disconnect/_disconnect_coro;
only the session/transport failure is injected. All four late-close outcome
combinations preserved work outcomes; cancellation precedence also held.

### P3 — ordinary clients and preconstruction failures retain their behavior

**Premise:** the optional kwargs/owner binding affect only the new context; store
load/config failures occur before client connection. **First dependent step:** 2.
**Waste if false:** existing factory users regress. **Original test timing:**
factory/source analysis, then all supported offline suites. **Cheapest test now:**
bad store snapshot, failed load and missing required proxy. **Coverage:** zero
clients constructed in each new probe; existing ordinary factory tests and full
regressions pass on the unchanged product. No package export/schema alteration.

### P4 — explicit malformed-self normalization covers the complete entry path

**Premise:** all empty/malformed self data reaches the handle's normalizer.
**First dependent step:** 1/2 diagnostic handling. **Waste if false:** diagnostic
and test coverage need clarification; ownership/cleanup structure still holds.
**Original test timing:** Step4's missing-self tests use a populated message box.
**Cheapest test now:** return the same shapes to a normal empty message box during
SDK connect. **Coverage:** bootstrap_self_shapes below disproves the broad reading.
This becomes Low1 because it affects abnormal-response classification, while
normal authentication error replies, refusal and cleanup remain covered and sound.

No untested behavioral premise necessary for the selected internal scope remains
behind the acceptance decision. Live Telegram service/account behavior is not
claimed from synthetic replies; no live account or credential was used.

## Restart Check

| Historical failure | Established mechanism | Current evidence |
|---|---|---|
| Fresh account differs from stale cache | cached self ID is not authoritative | explicit self RPC; original B/A/B case and reversed proofs |
| Auth policy applied after authentication | SDK connect can call get_me/GetState | kwargs passed before constructor/connect; original auth wait/server cases |
| SDK hides last exhausted RPC | default raise_last_call_error=False | fixed constructor option, original error identity retained |
| Apparent concurrency without real overlap | immediate fixture futures | original concurrent bodies plus new initial proofs completed in reverse order |
| Event B but summary A | old unqualified health storage | explicitly Stage2; not a success claimed by Stage1 |

## Inherited Lessons and design assessment

The code proves ownership before yielding; it does not merely relabel a health
event. It adds one private context, one handle and one close helper rather than a
registry, credential-generation framework, client router or database. The budget
provider's existing fresh-ID seam is reused with an optional three-line branch.

The raw-client and opening-task restrictions are suitable for the requested
internal foundation: actual SDK iteration works inside the owning task, and
independent operations can overlap. They would be insufficient for a public
arbitrary-client API, which is explicitly excluded. No evidence justifies adding
that larger framework here. Later health integration must consume the verified
owner; passing this gate does not approve that unimplemented stage.

The plan's terminal-proof-failure mitigation is implemented using its existing
active flag. Cleanup does not share that admission guard, so closing the handle
does not prevent SDK resource disposal. No new import cycle, packaging boundary,
schema migration or ordinary-client policy change was found.

## Low 1 — missing-self normalization starts after SDK bootstrap

**Risk**

If the initial connection receives an unexpected empty or incomplete account
response, the caller can see a low-level Python error instead of the library's
explicit authentication or identity error. The operation still refuses to run
and closes its connection. The test coverage currently makes the more helpful
error look uniform because those tests bypass the SDK's initial self lookup.

`ConnectionEngine._account_operation` at connection_engine.py:658 awaits connect
before the explicit normalizer at account_operation.py:70. Telethon1.45
telegrambaseclient.py:613–616 calls get_me when its message box is empty;
users.py:170–174 indexes the reply and accesses User fields. The existing
test32:330–342 fixtures set cached=111 and pre-populate that message box. With the
ordinary empty box, pr-critic-probes.py::bootstrap_self_shapes reproduces None →
TypeError, [] → IndexError and [UserEmpty] → AttributeError, before the normalizer.

**Severity:** Low
**Category:** Diagnostic consistency / test coverage
**Impact:** less actionable error classification for these unexpected reply shapes;
no wrong-account work, quota spend, prompt or failure to attempt close was observed.
**NoobEng:** Telethon performs its own self lookup while connecting, earlier than
the library's explicit identity check. The later check cannot normalize a reply
the SDK already rejected. Standard UnauthorizedError/AuthKeyError replies are
handled separately and correctly; this probe is not evidence of live logout failure.
**Affected areas:** private context entry diagnostics and missing-self regression
coverage, not admission ownership or normal authentication-error handling.
**Disposition:** consciously left for this internal stage. If broad response-shape
normalization becomes a public guarantee or this occurs on a real session, address
the bootstrap boundary with a narrowly justified contract/test change. Do not
catch every TypeError/AttributeError as “logged out”, which would hide local bugs.

## New probe evidence

Command: `.venv/bin/python devdocs/work/7-group-operations/stage-1-account-operation/pr-critic-probes.py`
using the existing project venv from the Stage1 worktree. Exit0; eight probe groups.
The script runs actual SDK/SQLite code, with socket.connect/connect_ex forbidden.
Selected observations rendered compactly (synthetic account IDs):

```text
delayed_resolution: actual=333, claims=0, history_sends=0, closed=true
cancel_admission: cancelled=true, claims=0, history_sends=0, close_attempts=1
reversed_initial_proofs: opened=[222,333], verified_order=[333,222], owners_correct=true
session_close_failures: OSError and CancelledError each preserve success and primary error; 4 sanitized logs; SDK background tasks finished
cancel_over_primary_and_failed_close: outcome=CancelledError, close_attempts=1, detached_close=false
preconstruction_failures: OSError / ValueError / ProxyConfigError; built_clients=0
successful_iterator: message_ids=[101], billed_account=222, billed=1, cached_account=111
bootstrap_self_shapes: None/TypeError, []/IndexError, UserEmpty/AttributeError; body_entered=false and closed=true in all three
```

The complete emitted JSON observations are preserved in pr-critic-probes-output.md.
The session-close probe intentionally uses an async failure injector supported by
SDK maybe_async; its experimental-async-session warning is fixture-specific.

## Validation scope and Phase 3

The product is unchanged since its 383 actual offline passes (28 new), three live
skips, three offline example runs and 61-file compile/grammar checks. Those are
retained validation evidence, not represented as rerun here. New review probes
and their compile/grammar check ran in this review. Published diff verification
initially detected only GitHub versus local hunk function-heading labels; after
normalizing those annotations, all changes and hunk coordinates matched exactly.

Phase3: no High/Medium exists, so there are no mitigation tiers to select or fold.
Low1 is recorded and consciously left under §7.3. No runtime patch was made during
review. No re-plan is required by this gate.

Limits: Telethon1.45, Python3.11 execution/3.7 grammar only, offline synthetic replies,
one completed cleanup attempt with no shutdown time guarantee, and private lexical
use. The available dated same-session Astra/max evidence and higher-effort
interpretation are in model-verification.md; no new model selector reading claimed.

PR21 can leave draft after this review is committed and posted. It is ready for
the user's merge decision, not merged by this review. Keep #7 open for later stages
and exclude work-folder/archaeology artifacts during eventual integration.
