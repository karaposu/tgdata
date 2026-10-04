---
model: unknown
effort: unknown
---

# Plan — session storage across the whole login lifecycle (issue #5)

**Revision 3 — regenerated after PR #13 was rejected.** Input: description,
triage, revision 2 (available at `24ddeb8`), and `pr-critic.md` at `a6deab7`.
This replaces the prior implementation sequence. The original four Medium
mitigations remain required; the PR finding extends the ownership rule to all
persistent mutations rather than adding an independent deletion workaround.

## What is the task

Let an application supply synchronous storage for each account's complete
restartable Telegram session, keeping file sessions as the default. Persist
the login, data centre, group cache, own identity and update positions without
keeping every message sender. Every mutation of the stored account record —
saving or deleting it — must respect a login replaced since this client last
loaded or saved. The store interface stays load/save with optional delete.

## Huge Hard Blockers

### Planning Blockers

None open. The newly relevant order is established by Telethon 1.45.0's source
and the real-client probe: logout disconnects (guarded save), then deletes.
P4 at `a6deab7` shows deletion removing a newer login. Existing transport and
server behavior is supplied by the probe; live server acceptance of restored
credentials remains unverified under the approved offline scope.

The original decisions remain settled: target Telethon 1.45.0, synchronous
methods, no shipped backends, no migration or encryption layer, and plain
in-memory clones for side connections. Atomic cross-process operations remain
outside this interface; the documented check/mutation window is retained.

### Execution Blockers

- **What must happen:** maintainer gives the explicit merge go-ahead and
  resolves the §9 model-rule exception in the merge check.
- **Who:** maintainer.
- **Blocks:** integration into dev after Step 4; not implementation or review.
- **Status:** OPEN. Exact model variant/effort are unavailable in this session;
  the inherited plan/critic record an Opus variant outside §9's feature row.

## How this implementation moves toward desired state

The serializer, factory wiring and default-file behavior already exist in
`a0e0779`. Their six-suite offline verification passed. The remaining defect
is not in serialization: two operations mutate one stored record, but only
one checks which login it owns. A single comparison, called by both save and
delete, makes their decisions consistent. A failed ownership check is treated
like the corresponding save/delete failure, with credential-free logging.

The regression runs the actual logout lifecycle, so it observes the join
between disconnect/save and deletion instead of testing them independently.

## High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | State and test ownership across the lifecycle | A failing regression for stale real logout and passing baseline cases |
| 2 | One ownership check for both storage mutations | Saves and deletes preserve a replacement login; ordinary logout still deletes |
| 3 | Align user documentation and verification records | Clear conditional-delete contract and accurate scope |
| 4 | Verify, commit, repeat merge check and PR critique | Updated PR #13 eligible for the maintainer's decision if no High/Medium remains |

## Step 1 — Put the lifecycle promise into the contract and tests

### Proposed changes

Update description criterion 7: a client never overwrites **or removes** a
login it did not load or save. The same-key last-writer cache rule stays.
Extend `test_17_session_store.py`'s logout group using Telethon's real
`log_out()` with scripted responses:
- ordinary logout deletes the client's own stored key;
- a client holding A, after storage changes to B, logs out A but leaves B;
- the same holds when the old client loaded no key before a new login;
- an externally removed record stays absent without a stale delete call;
- the save and delete phases together warn at most once for a stale client;
- failure to read the current stored key prevents deletion and logs only the
  exception type; failed delete remains credential-free;
- a store without delete still works.

Retain the eleven other test groups, including corrupt-key rejection,
unchanged-save elision, exact integers, own identity, mixed rows and clones.

### Output

Contract and regression identify the persistent-mutation rule end to end. The
stale-logout case fails on `a0e0779`, as the archived PR probe already shows.

### Safe in nature

True — description and offline tests only; synthetic credentials, no sockets.

### Peripheral concepts

Telethon log_out/disconnect, _synced_key, optional store deletion, log capture

### Hardness Lvl

2

## Step 2 — Centralize the ownership check

### Proposed changes

In `StoredSession`, extract the current save comparison into `_may_mutate()`:
1. Load the current stored string and parse its key, or use None if absent.
2. Compare that key to `_synced_key` (the key this client last loaded/saved).
3. When equal, return True. When unequal, warn once through `_warned` and
   return False. The warning says the record was neither overwritten nor
   deleted. Do not update the synchronization markers on rejection.

`save()` still dumps first and returns immediately if unchanged. Otherwise,
it calls `_may_mutate()` inside its existing try block before store.save.
Successful saves update both synchronization markers as today.

`delete()` checks for the optional method inside its try block. If absent,
return. If present, call `_may_mutate()` before invoking it. Only successful
deletes reset the synchronization markers. A check/load/parse/delete failure
is caught by the delete handler: ERROR with name and exception type, no error
text or traceback. Each later delete attempt may retry normally.

No other runtime module, dependency, exported symbol, constructor, format,
login-prompt rule or file-session behavior changes. The ownership read and
mutation remain separate operations; no atomic backend API is introduced.

### Output

The shared credential ownership invariant is enforced by both persistent
mutations, including real logout's save-then-delete path.

### Safe in nature

False — modifies credential persistence. The regression in Step 1 is the gate.

### Peripheral concepts

StoredSession.save/delete, logger, deterministic dump, synchronization markers

### Hardness Lvl

2

## Step 3 — Document the corrected lifecycle

### Proposed changes

Update the module and README wording: an optional delete removes the record
only if it still belongs to the login that client last synchronized. Keep the
SQLite example and all existing storage/failure/atomicity boundaries.
Update smoke-test documentation and the implementation record with the PR
finding, correction and actual results. Preserve the first rejected review
in git and as a named round-one record before replacing the current review.

### Output

The published contract describes both mutations and does not imply that a
stale logout removes a newer login.

### Safe in nature

True.

### Peripheral concepts

README Authentication section, test_17 coverage, PR #13 review artifacts

### Hardness Lvl

1

## Step 4 — Verify and return the same PR to review

### Proposed changes

Compile touched files; run test_17 and the five existing suites (16, 15, 14,
13 and 12) in their offline modes. Pass a nonexistent config to 12/13 so live
checks cannot read the account config. Localhost-only proxy checks may need
sandbox escalation. Repeat P1–P4 with P4 now asserting preservation, not merely
printing the old failure. Recheck the SQLite example where the documented
lifecycle changed.

Commit code/tests/user docs separately from work-folder documents; exclude
the stray group-discovery edit. Push to the existing feature branch and keep
PR #13. Update #5's boxes only when backed by the new commits. Regenerate the
merge check and run another in-session PR critique with probes. Any High or
Medium rejects again; a second rejection returns to the description/traverse
per §7.4. A passing code review still awaits the maintainer's merge approval
and disposition of §9. Do not merge, close #5, deploy or start another issue.

### Output

Verified commits and a fresh, evidence-backed review on PR #13, with the final
integration decision left to the maintainer.

### Safe in nature

True — verification and feature-branch publication; integration is gated.

### Peripheral concepts

Offline suites, merge check, PR critic, issue status, archive branch, §9

### Hardness Lvl

2
