---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the full native SDK/StoredSession/SRP/cancellation composition cannot
continue a restored code/password step or loses known auth/challenge/key/DC during
native connection/migration/cleanup, or returns a credential the consumer cannot load.
Affordable now: yes — local candidate and controlled wire, no real account or payment.

Experiment: full isolated candidate described in plan's prebuild gate, with actual
native connect, raw auth TL serialization, SRP, migration/disconnect, serializer,
factory mixins and consumer loading. Include the native disconnect ownership risk
below. Run all combined histories, not a targeted subset.
Cost: local development/test time, installed Telethon1.45, zero network/account spend.
Must precede: step1 and every production step; the plan already reserves this gate.
Disqualifying result: a semantic assertion above fails with a correctly constructed
real-component fixture; stop/deprecate, do not patch around the false premise.
Passing result: every combined history passes with actual local components and no
socket use; observation scope excludes Telegram server delivery/acceptance.
Result: PASS — 23/23 full combined local-component groups, 2026-10-14.
Evidence: prebuild/REPORT.md, full-result.txt and manifest.json; all attempts retained.

## High-level summary
The bounded conversation and caller publication contract survive. No broader auth
service or health refactor is needed. One Medium detail must be folded: retain native
disconnect completion even when the SDK itself initiates it during migration. Old
narrow probes are insufficient; full candidate must run before production. Live
service acceptance remains an explicit qualification limit, not a simulated PASS.

## Premise Inventory
### P1 — Complete local SDK composition preserves actual progress
First dependent step:1. Waste if false: all five production steps. Test scheduled
at: prebuild before1. Cheapest earlier test: that same full candidate, affordable.
Coverage: five narrow SDK probes are PARTIAL; no candidate composition exists yet.
Controlled wire must not supply state retention/cleanup/SRP/serializer behavior.

### P2 — Restored credential and challenge continue in the native client
First dependent step:1. Waste if false: state/auth/test/docs design. Test scheduled:
full prebuild. Cheapest earlier test: actual serialized state, new instance, raw
auth requests with byte serialization and final real store reload. Narrow StringSession
probe covers the negative counterexample, not this candidate. Server acceptance of
the challenge remains P4, not something the wire can prove.

### P3 — Per-step route/device and ordinary consumer behavior remain compatible
First dependent step:1. Waste if false:1–5. Test scheduled: prebuild and full final
suite. Cheapest earlier test: native client constructed through the real common
factory with the exact planned private seam; compare actual InitConnection/proxy
on restore and native DC switch. Existing tests12/13/15/17 cover baseline behavior
but not the new subclass. Factory source is documentary evidence, not execution.

### P4 — Telegram production accepts the selected existing-account auth exchange
First dependent step:2. Waste if false: auth integration/adaptation. Test scheduled:
no live step in this offline delivery; limitation explicit in description/guide.
Cheapest earlier test: user-authorized production login or separately scoped test-DC
account. No currently authorized setup for code delivery/password submission exists
for this task. Access/input is external; controlled wire is NON-COVERING for the
service. Official auth method contract plus exact1.45 native implementation make the
offline API implementable, but do not close production qualification. Do not mark
live done or infer current account authority from earlier unrelated tests.

## Restart Check
| Observed failure | Established mechanism | Design element |
|---|---|---|
| Repeated SDK start resends | inquiry probe: helper hash cache turns send into ResendCode | explicit one-start flow/raw request |
| sign_in raises after authorization | inquiry probe: _on_login GetDifference fails | direct observation/auth-only hook |
| Save returns without stored credential | actual StoredSession swallows backend error | explicit caller publication |
| Zero-retry call changes key/DC on error | inquiry native migration probe | actual session retained on all exits |
| Prior pool cancellation let retirement outlive admission | prior #17 history and native shielded cleanup mechanism | owned invocation plus cleanup refusal; risk1 covers inner SDK boundary |

## Inherited lessons and compatibility
Known state, owned completion and actual caller cancellation are different facts.
The candidate must capture values before cleanup and cannot treat the handler Task
as a join handle. Reuse of the common factory and transient StoredSession avoids a
second policy/store authority. Public exports are additive; ordinary constructor
defaults, login policy, quotas, group operations and worker protocol are unchanged.
No application DB schema is imposed. New status/private state are versioned public
contract; opaque state carries credentials and requires protected app storage.
Latency includes one connection per step, native server-error delay and unbounded
settled cleanup. State is limited64KiB; no connected resources between human inputs.

## Risk1 — Native migration can hide a still-running disconnect
**Risk**

A login may change Telegram servers while processing an input. If its caller stops
at that moment, the SDK can continue closing the old connection after the awaiting
task has been cancelled. Starting a second cleanup without retaining the first one
does not prove that the original close finished, so the flow could release ownership
while work it started still runs.

Telethon1.45 `TelegramBaseClient.disconnect()` creates and shields a new
`_disconnect_coro` task on each call. `_switch_dc()` awaits that public method.
Step1's final `_disconnect_owned()` retains its own close attempt, but does not by
itself retain an earlier native migration close whose shield waiter was cancelled.
The private auth subclass needs one retained disconnect completion reused by all
waiters until it settles; a later deliberate retry may start a new attempt after a
failed completion. Include cancellation during the native migration path itself.

**Severity:** Medium
**Category:** Ownership/phase ordering
**Impact:** premature admission/export and orphaned native cleanup.
**NoobEng:** awaiting a cancelled shield wrapper is not awaiting its underlying SDK
task. Two independently started close calls are not a durable handle to the first.
**Affected areas:** new login invocation/subclass, native migration and close retry.

### Mitigation — Quick
Disallow auth DC migration, returning restart_required immediately.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
The auth-only subclass retains the native disconnect completion and returns shielded
waiters to it. Reuse pending completion on final cleanup; only after settled failure
may close retry start a fresh attempt. Test native migration cancellation, repeated
caller cancellation and no pending owned task after the invocation finishes.
**why this is robust:** every disconnect origin in this auth client shares the same
actual completion boundary; it does not guess from is_connected or one waiter.
- [x] selected   - [x] elegant   - [ ] last_resort
**Note**
*Why chosen:* one native completion owner closes this auth instance with minimal extent. Other engine/pool clients exist but their reuse/reconnect policy needs separate qualification; a universal adapter is not established as one interchangeable mechanism.
*For future:* —

### Mitigation — Long-term
Investigate a common SDK disconnect ownership adapter for all short-lived and pool
clients, with dedicated compatibility qualification across their reconnect policy.
**why this is long term effective:** if their native migration paths share exactly
this mechanism, one adapter could centralize all native retirement observations.
- [ ] selected   - [ ] elegant   - [ ] last_resort
**Note**
*Why chosen:* —
*For future:* revisit only after an independent audit demonstrates the same missing native boundary in ordinary/pool clients; keep outside this credential feature.

## Gate record
Phase2 completed with mitigation boxes empty. No known planning blocker or wrong
layer; no execution blocker carried. No production code before the full prebuild.

Phase3: robust selected/elegant; no last_resort. No risk/proposal rewritten.

## Experiment call-site correction
The precise Risk1 text above incorrectly names public disconnect as `_switch_dc`'s
callee. Installed1.45 actually awaits private `_disconnect`; public disconnect's
shielded flush is a separate boundary. The full candidate applies the selected
completion-owner rule at BOTH boundaries. The initial public-only implementation
caused the unchanged duplicate-close assertion to fail; the named feasibility
falsifier (lost progress/unsettled work/unloadable credential) was not observed.
See prebuild/REPORT.md for the complete correction history, not an assumed PASS.
