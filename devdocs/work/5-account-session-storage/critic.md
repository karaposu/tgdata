---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: Telegram refuses the restored key/data-centre pair while accepting
that same pair from a file session.
Affordable now: no — requires a live logged-in account, outside the approved
verification scope. This limitation is inherited; the new local mutation rule
adds no server dependency.

# Critique — issue #5, regenerated plan revision 3

Reviewed in-session against `cc665f4`, its description, the rejected PR critique
`a6deab7`, the runtime adapter and client lifecycle, and the twelve test groups.
This is the plan critique required by §7.4, not a passing PR verdict.

## High-level summary

The re-plan addresses the lifecycle as a whole. Both persistent mutations use
one comparison with the key last synchronized, rather than separate policies
that can disagree at logout. The guard is inside each operation's failure
handler. Unchanged saves still return before reading the store; stores without
delete still return without a mutation. No format or public interface change
is needed. No new High or Medium finding was found in this plan.

## Premise inventory

1. **Live restoration works with the same key and data centre.** First
   dependency: the original feature. Failure wastes that feature. A real
   Telegram comparison is the decisive test, but the approved scope excludes
   it. Scripted transports do not cover server acceptance; the existing
   limitation remains explicit.
2. **Logout invokes close/save and then delete.** First dependency: the shared
   ownership design. Failure would change where the rule must be enforced.
   The real Telethon `log_out()` probe at `a6deab7` already demonstrates the
   order and failure before this re-plan. The probe supplies the server reply,
   but observes Telethon's actual local lifecycle. No late experiment remains.
3. **The same comparison admits the client's own record and rejects another
   login's record.** First dependency: Step 2. The ephemeral prototype below
   runs before production edits and exercises those branches through the real
   lifecycle. It covers the proposed decision, not the final implementation;
   Step 1 regression and Step 4 suites remain required.
4. **Failure containment and existing state remain stable.** First dependency:
   Step 2 refactor. Code inspection places load/parse/mutation in each existing
   try block and leaves synchronization markers untouched on rejection/error.
   No stochastic premise is involved. The specified failure scenarios and
   unchanged-save test directly exercise this after implementation.

## Restart check

Observed failure: stale logout deleted a newer credential.
Established mechanism: guarded close/save was followed by unconditional
`StoredSession.delete`, demonstrated by P4 on Telethon's real log-out method.
Design element: one `_may_mutate()` gate used by save and delete, plus an
end-to-end stale logout regression written before the runtime change.

The re-plan addresses the failed layer and ordering directly. It does not
rebuild unrelated connection or storage structures.

## Inherited lessons

- Bounded cache, opaque integers, mixed-row sorting, safe logging and strict
  decoding stay in the adapter and remain under the original tests.
- The stale-save guard expands into a mutation guard; deletion is no longer
  treated as an unrelated housekeeping operation.
- The first-login rules and constructor/factory paths are untouched.
- Synchronization markers change only after a successful store operation.
- Optional deletion is retained; disabling it was rejected as a symptom fix.
- Cross-process atomicity remains outside this two-method-plus-optional-delete
  interface, explicitly documented; no stronger guarantee is claimed.

## Probe evidence

An ephemeral replacement for `StoredSession.delete` compared the current
stored key with `_synced_key`, then called the original delete only on a match.
Runtime files were unchanged. The archived real-client probe produced:

```text
P1 real connect: data-centre save, then auth-key save — passed
P2 real connect: self identity and stored update positions restored — passed
P3 stale real disconnect: newer stored login preserved — passed
P4 stale real log_out: newer stored login removed: False
P4 store.delete calls: 0
P4 newer stored login preserved: True
P5 prototype same-key delete: ordinary stored logout removal still allowed — passed
```

The prototype intentionally supplies the planned guard. It is evidence about
integration order, not proof the future production helper is correct. That
proof remains the real regression after Step 2, including failure cases.

## Risks and Phase 3 selection

No additional actionable High/Medium/Low risk was found beyond the explicitly
retained boundaries. Phase 3 has no new proposals to select. The robust shared
ownership guard selected in `pr-critic.md` remains the design to implement.
Atomic backend operations remain a future interface change, not a prerequisite.

## Execution preconditions

The maintainer's explicit merge approval and §9 model-rule disposition remain
open. Neither blocks local implementation and review; neither is waived here.
Exact model variant/effort are unavailable, so this artifact records unknown.
