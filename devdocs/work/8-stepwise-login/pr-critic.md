---
model: gpt-6-astra
effort: max
---
**IMPLEMENT AS WRITTEN — after the fresh behavioral experiment below.**

**PR Gate: PASS — 0 High, 0 Medium, 0 Low findings.**

Falsifier: an actual local SDK history loses known authorization/challenge data,
releases admission before owned retirement, confuses a component stop with caller
cancellation, leaks a credential in public diagnostics, or cannot load the final
credential into an ordinary client.
Affordable now: yes — the fresh local experiment was executed before this final
verdict. The pre-experiment ordering decision was REORDER/test-before-merge; that
requirement is satisfied, not waived by the implementation suite.

Experiment:16 new adversarial history groups in review/probes.py, using production
LoginFlow, installed Telethon1.45's native client/migration/cleanup, actual SRP,
StoredSession and HealthMonitor. Network transport/replies are controlled; socket
connect/connect_ex are forbidden. No production source or original test changed.
Cost: local seconds, no account/code/password input or service spend; parent process
watchdog75s and per-history15s bounds. No watchdog was needed to terminate a history.
Must precede: this final PR verdict and any merge, not a new runtime implementation.
Disqualifying result: one named ownership/data/credential/consumer assertion fails
on a valid controlled history; a Medium/High rejects under CONTRIBUTING §7.3.
Passing result: every fresh history completes its assertions with no pending owned
tasks or unobserved task exceptions, while retaining explicit live-service limits.
Result: **PASS16/16**, review/results.txt and review/results.json,2026-10-14.

## High-level summary
The implemented diff satisfies its bounded offline contract. One caller-owned login
conversation retains facts; per-call clients own transport work; the application
owns private checkpoint persistence and final session publication. Fresh cancellation,
error-combination, restoration and consumer histories did not find a merge blocker.

Subject: PR28, product877d29d, `c4e6eac...0a3c83d` plus plan.md revision2. Later commits
add only review documents/probes. Base dev remains c4e6eac. Review ran in this same
warmed session using critic-d's fresh adversarial procedure, no subagent. The actual
eight product files and relevant existing factory/session/health/lifetime/SDK paths
were read together; prior PASS reports were treated as evidence with limits, not a
substitute for this review. §9 model/effort independently verified as Astra/max.

## Premise Inventory
### P1 — An invocation owns both facts and actual completion
First dependent plan step:1; waste-if-false: state/lifetime plus all later API/docs.
Test scheduled: prebuild before production and renewed PR histories now. Cheapest
earlier observation: hold the actual native client's transport/flush call, deliver a
late actual TL authorization after caller stop, and compare flow state, caller signal,
admission, and remaining tasks. Affordable local execution completed.
Coverage: late_response_after_stop, queued_stop_reaches_public_boundary,
component_self_cancel, paired_code_and_flush_failure, close_retry_repeated_stop,
component_close_cancel and application_continues_after_call all PASS. The wire
supplies outcomes/timing, not LoginFlow's retention, ownership or cleanup logic.

### P2 — Private state and final credential have distinct usable contracts
First dependent step:1; waste-if-false: state/auth/consumer/docs. Test scheduled:
full prebuild and fresh state/consumer controls. Cheapest earlier observation: restore
code/password and waiting/uncertain checkpoints, then connect an ordinary native
reader from the actual final StoredSession text. Executed locally.
Coverage: delivery_variants, wait_code_and_password, wait_on_uncertain_check,
completed_key_revoked, malformed_phase_matrix and ordinary_client_consumes_credential
PASS. The last test goes beyond construction-only reload: the ordinary native client
connects and verifies self/current authorization, then its saved session reloads.
No DB commit, distributed lease or crashed-process recovery is manufactured by a blob.

### P3 — Common policy and ambient health remain coherent
First dependent step:1; waste-if-false: factory integration and existing consumers.
Test scheduled: implementation suite/full regressions and fresh multi-redirect/real
health controls. Cheapest earlier tests: actual common factory/native migration and
real HealthMonitor around a native ambient RPC followed by nested login. Executed.
Coverage: bounded_double_redirect preserves proxy and stops at2 SendCode requests;
real_ambient_health neither labels nor recovers the stale account. Recorded full
verification still matches current source hashes:28 supported suites,773 executed
cases,3 explicit live skips,5 examples. Ordinary default factory AST remains unchanged
apart from the qualified optional private base seam. No broad rerun was substituted
for independent new evidence.

### P4 — The real provider accepts/delivers this auth exchange
First dependent step:2; waste-if-false: auth adaptation/operational integration.
Test scheduled: separate live qualification, not performed. Cheapest earlier test:
an expressly authorized production login or separately scoped test-DC setup. That
access/input has not been supplied for this task. Controlled wire is NON-COVERING
for actual delivery, restrictions, real-account password acceptance or exit IP.
The PR consistently identifies itself as offline qualified; it does not claim that
this remaining premise is established. No live account operation was attempted.

## Restart Check
| Established failure/mechanism | Actual response in this diff and review |
|---|---|
| SDK repeated send helper can resend | Explicit step eligibility/raw SendCode; unsupported/duplicate input controls; no helper fallback |
| SDK sign_in can raise after auth during update setup | Auth-only _on_login and immediate raw-Authorization observation; late-response and later-failure controls |
| StoredSession save can return without a successful backend write | Isolated memory sink and explicit final credential handoff; ordinary consumer reload; caller publication documented separately |
| Native zero-retry migration changes key/DC | Shared actual session preserved, bounded SendCode retry, native migration and repeated-redirect evidence |
| Cancelled waiters can outlive owned cleanup | Retained body/transport/flush completions, pending-cleanup refusal and explicit retry; fresh paired-failure/cancellation controls |

The earlier plan critic's inaccurate public-disconnect call-site statement is not
inherited as fact: installed _switch_dc calls private _disconnect. Folded plan and
runtime cover that actual boundary. Archived prebuild failures/corrections remain
visible. This review found no missing mechanism requiring a different feature layer.

## Inherited Lessons check
- Cancellation is not rollback: late authorization is retained while the caller
  still receives CancelledError; no second SignIn is sent by recovery.
- Known data is not a Task status: the flow owns progress independently of later
  application-task work; the parent can continue while a new settled input is valid.
- Cleanup is not a cancelled waiter: native close/flush attempts settle before
  release, and failures retain the client for explicit retry.
- Serialization is not ownership or commit: local overlap is refused, latest-state
  exclusivity belongs to the application, and final data is not a store receipt.
- A logged-in account is not an old cached owner: fresh self checks validate the
  phone/known account and the real ambient monitor remains neutral.
- Narrow SDK probes are not complete qualification: the full candidate ran before
  production; this review adds16 distinct groups, while live acceptance remains open.

## Fresh observed evidence
Exact lines from review/results.txt include:
```text
{"case": "late_response_after_stop", "result": "PASS", "observation": {"caller_cancelled": true, "late_authorization_retained": true, "signins": 1}}
{"case": "queued_stop_reaches_public_boundary", "result": "PASS", "observation": {"caller_entered_API": true, "source_requests": 0, "busy_after": false}}
{"case": "bounded_double_redirect", "result": "PASS", "observation": {"SendCode_requests": 2, "step": "restart_required", "proxy_preserved": true}}
Fresh PR probes: 16/16
```
Other groups cover SMS/voice delivery restoration, SignIn signup refusal, waits at
code/password/check phases, component-owned stops, wrong-code plus native flush
failure, repeatedly cancelled close retry, revoked completed credentials, ordinary
client consumption, actual ambient health, application continuation and8 malformed
private state combinations rejected before network. Every group additionally checks
for pending tasks and captured unobserved exceptions. The three expected type-only
cleanup diagnostics correspond to deliberately injected failures.

## Compatibility, scope and complexity
No changes to normal TgData login policy, worker protocol, account budgets, group
operations, pool routing or storage backend semantics. Three new package exports
and one private factory argument are additive. The state schema is explicitly
versioned and private, not an application DB schema or browser credential format.

The auth-only SDK subclass and its two close boundaries have a concrete native
purpose; replacing them with bare helper wrappers would lose already-demonstrated
outcome/cleanup distinctions. No general workflow engine, coordinator or cross-module
health abstraction is added. Current extent is justified by the promised contract.
One fresh connection per input and native server-error delay are documented costs;
cleanup has no bounded-time guarantee. State text is limited64KiB.

## Findings and Phase3 disposition
No supported High/Medium/Low finding. No mitigation tiers to select or fold; Phase3
therefore makes no selections. No runtime fix or test weakening occurred in this
review. PR may be marked ready for review; this verdict is not merge authorization.

## Remaining qualifications and integration
Live code delivery/real-account2FA, physical proxy exit-IP verification and native
Python3.7 execution remain unqualified. Scope excludes concurrent stale checkpoints
and process death during a call; no new safety claim is inferred from these tests.
The separate #17 two-account live gate is still deferred. Keep the branch archive;
exclude work/archaeology docs when a later authorized merge into dev occurs.
