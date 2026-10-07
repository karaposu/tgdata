---
model: gpt-6-astra
effort: max
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the real SDK's connect/self/dispatch/disconnect composition bypasses
constructor policy, fresh identity or the existing before-reservation hook.
Affordable now: yes — a local offline probe, minutes, no account or network.

Experiment: build the real current-dev factory client with the proposed constructor
kwargs supplied by a test subclass; run real Telethon connect, self RPC and _call
against scripted transport replies, and real disconnect under repeated cancellation.
Include real SQLite read admission with a mismatching self reply at its existing
identity hook. The transport supplies replies only; it must not supply proof,
retry policy, cleanup ordering or budget refusal.
Cost: minutes, no money/account/network.
Must precede: Step 1 (the first dependent implementation step).
Disqualifying result: policy takes effect only after auth, self proof uses stale
cache, actual send bypasses identity admission, or retained disconnect completion
cannot survive caller cancellation without changing the ownership/lifecycle design.
Passing result: original auth wait/server failures propagate under fixed policy;
fresh self ignores stale cache; disagreement precedes claim/send; actual disconnect
settles before preserved cancellation is delivered. Document SDK server backoff.

Result: PASS — real factory/Telethon connect, fresh self, zero-flood-sleep policy, original final RPC error, real SQLite before-send admission and retained disconnect under two cancellations all behaved as specified. ServerError still requests the SDK's final 2-second backoff. 2026-10-08. Evidence: `prebuild_probe.py`; sockets forbidden.

## High-level summary

The selected shape is small and matches Stage 1. Earlier probes individually cover
the dangerous SDK seams; this plan waits until Step 4 to exercise their combined
composition. Run that cheap check first. One Medium finding tightens the meaning
of “mismatch stops the operation”: an already invalidated owner must not be reused
after a caller catches the first refusal. No health redesign is needed.

## Premise Inventory

### P1 — configured SDK composition supports the scoped lifecycle

Premise: constructor settings govern connect's internal authentication and actual
request dispatch; the client can then complete a retained disconnect attempt.
First dependent step: 1. Waste if false: Steps 1–3 and rewritten tests, rather than
only a fixture change. Test scheduled at: Step 4. Cheapest earlier test: the
experiment above, minutes. Coverage: real SDK auth-wait and disconnect probes in
the same session cover individual parts, but not the full new composition. A fake
client that simply yields B and closes on command would be non-covering. Scripted
wire responses through the actual SDK observe the local behavior at issue; they
do not claim to establish live-server availability or account privileges.

### P2 — actual send continues to use the existing admission hook

Premise: fresh proof can be used by `_BudgetSender` before its SQLite reservation
and actual sender.send. First dependent step: 3. Waste if false: Step 3 and related
Step 4 tests. Test scheduled at: Step 4. Cheapest earlier test: real mixin/SDK/SQLite
with a temporary identity hook using real self RPC, included above. Coverage:
test18 observes unowned fresh billing; it does not yet compare expected ownership.
No assumption is made about the unmerged #17 implementation being accepted.

## Restart Check

| Prior observed failure | Established mechanism | Addressed here |
|---|---|---|
| Expected identity and cached identity disagree | `_self_id` is not fresh authority | Steps 1/2 use actual self RPC and expected numeric ID |
| Authentication sleeps before body policy | connect can call self/GetState before later mutation | Step 2 constructor-time policy |
| Final RPC becomes generic retry error | SDK default `_raise_last_call_error=False` | Step 2 preserves final RPC error |
| Event B but health summary A | unqualified health storage plus cached identity callback | Explicitly Stage 2, not claimed fixed by this implementation |
| Apparent overlap without interleaving | immediately completed fake futures | Step 4 pending-event overlap assertions |

## Inherited Lessons

| Lesson | Ordering that satisfies it |
|---|---|
| Do not repair only the visible account label | Step 1 defines proof before any future health consumer |
| Actual SDK composition matters more than an agreeing fake | Prebuild experiment before Step 1; Step 4 keeps regression evidence |
| Scope growth obscured the earlier prerequisite | No public group/health/router/schema changes in any step |
| Cleanup must preserve remote-work meaning | Step 2 defines precedence before new operation consumers exist |

## Risk 1 — a refused owner can remain usable

**Risk**

If an account changes or loses its login during an operation, refusing just one
attempt is weaker than stopping that operation. A caller that catches the refusal
could reuse the same temporary client, even though the original ownership proof
has failed. That would make later code responsible for remembering the safety rule.

In `tgdata/account_operation.py`, proposed `_AccountOperation.verify_account()`
raises on mismatch/auth loss/unverifiable self but the revision1 plan only calls
`_close()` at context exit. The `_tgdata_account_operation` binding in
`BudgetClientMixin._read_budget_account` can therefore attempt admission again if
the body catches `AccountIdentityError` or `AuthRequiredError` and continues. Make
identity-invalidating proof failures terminal for this handle before raising.

**Severity:** Medium
**Category:** Ownership/lifetime contract
**Impact:** later internal callers can accidentally continue a refused operation.
**NoobEng:** proof and lifetime live together; once proof fails, a new operation
with a new client should be needed, rather than another check on the same handle.
**Affected areas:** new private handle and owned budget branch only.

### Mitigation — Quick

Document that callers must not catch identity/auth refusals inside the context.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Mark the handle inactive before raising an identity mismatch, unavailable/malformed
self identity or auth-loss error. Ordinary transient RPC/transport failures keep
their original exception and do not silently assign another owner. Test that a
caught refusal leaves handle.client, verify_account and subsequent budget admission
closed, even if the scripted account changes back. Cleanup still executes once.

**why this is robust:** it enforces this context's stop rule using the existing
active flag, without any global owner state or additional client framework.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* No accepted second owner-handle instance exists on dev. The unmerged #17 pool has a different multi-client lifetime, not the same class requiring one supervisor. The active flag closes this instance in a few lines; a supervisor expands scope and would still need this handle boundary.
*For future:* —

### Mitigation — Long-term

Guard every arbitrary SDK dispatch with a credential-generation supervisor and
coordinate all clients sharing a session or pool account.

**why this is long term effective:** a genuine public multi-client operation API
could then enforce credential revocation beyond one internal lexical handle.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit only if a public arbitrary-client API is requested. It is not a prerequisite for the private operation; the terminal handle rule survives that future work.

## Other checks

No schema migration, package discovery change or circular import is needed: pass
an authentication-error factory into the internal module; budget dispatch consumes
the attached handle without importing the connection engine. No new public export.
Proof adds one self RPC per existing admission point, not another metadata pass.
Constructor kwargs do not replace proxy/session/device configuration. Keep SDK
server-error backoff explicit; zero retries does not remove its final two-second
sleep. Auth error text must explain that this operation cannot log in; account
setup happens separately. Logging cleanup failures is best effort and type-only.

Execution blockers: none. Remaining live behavior is outside this offline stage;
no request is made to run live joins or retrieve credentials.
