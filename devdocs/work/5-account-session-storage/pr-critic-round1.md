---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: a real Telegram login restored from this store is refused while the
same key/data centre from a file session is accepted.
Affordable now: no — requires a live authenticated account; the approved
verification scope excludes live Telegram operations.

**PR verdict: REJECTED — one Medium finding.** Reviewed in this warmed session
against `origin/dev` at `110996c` and PR #13 through `24ddeb8` (runtime code
`a0e0779`, SQLite example `7a2f549`). No subagent was used. Under §7.4 the next
step is a revised plan and critique, not a sequence of patches to this diff.

## High-level summary

The storage and factory integration fit the existing architecture. The new
probe exercises real Telethon `connect()` with a scripted transport: both
save points run, and restored self identity and update positions are consumed
correctly. This improves the evidence behind the earlier accepted Low 7.

The credential lifecycle is incomplete at logout. Closing an old client keeps
a newer stored login, but logging that client out then deletes that newer
record. The same-session save tests cannot detect this because the existing
logout test uses only one client. This is a new lifecycle defect, not the
already documented cross-process load/save race.

## Premise inventory

1. **A restored key/data centre can resume a real Telegram login.** First
   dependency: the entire feature. Failure wastes the feature. Live testing is
   not scheduled, by the approved scope; a live side-by-side restoration would
   be the cheapest decisive test, but needs account access and authorization.
   Constructor and scripted-transport probes cover the client implementation,
   not Telegram's acceptance of the key.
2. **All mutations preserve a newer stored login.** First dependency: the
   session adapter. Failure loses the replacement credential. The original
   tests cover saves but not stale logout. The inexpensive real-client logout
   probe below now refutes this premise for deletion. The structure survives;
   the lifecycle rule must cover both save and delete before implementation
   can be accepted.
3. **Telethon restores own identity/update state and calls session saves.**
   First dependency: serialization. Existing tests cover constructor,
   disconnect and auth-key callback. This review's P1/P2 execute the real
   `connect()` method with a scripted sender, parked background loops and
   synthetic state. They cover local Telethon behavior, not the network or
   actual server replies. Both passed before this verdict.
4. **File defaults, cache bounds and opaque values remain intact.** First
   dependencies: factory and serializer. The existing 65 offline checks plus
   the SQLite reopen probe cover these deterministic behaviors. No new
   unsupported premise was found there.

## Restart check and inherited lessons

This feature adds a missing capability; it is not a restart after an incident.
Its inherited first-login protection remains relevant: strict decoding and
load-error propagation prevent damaged credentials from becoming an empty
session. The corrupt-key case found during implementation is covered.

- Save at close: exercised through real Telethon disconnect, including P3.
- Keep the group cache and own identity: covered by restoration tests and P2.
- Failed load must raise: covered by test_17's failure and login groups.
- Never replace a newer login: save is covered; deletion fails P4 below.
- Optional delete: ordinary logout is covered, but ownership of deletion was
  not represented in revision 2.
- Default files and in-memory clones: covered by the existing factory and
  clone tests.
- Synchronous storage and non-atomic cross-process operations: documented
  boundaries retained; no new store interface is proposed here.

## Probe evidence

Command: `.venv/bin/python devdocs/work/5-account-session-storage/probe_pr_lifecycle.py`

```text
P1 real connect: data-centre save, then auth-key save — passed
P2 real connect: self identity and stored update positions restored — passed
P3 stale real disconnect: newer stored login preserved — passed
P4 stale real log_out: newer stored login removed: True
P4 store.delete calls: 1
P4 newer stored login preserved: False
```

The fixture blocks socket connections. P4 supplies a successful server reply
to logging out the old key, then runs Telethon's actual log-out/disconnect/
session-delete chain. It does not claim to test live server behavior. The
initial P2 probe used a nonexistent `self_hash` attribute; after reading
`EntityCache`, it was corrected to `get(self_id).hash` and all probes ran.

## Risk 1 — An older client's logout deletes a replacement login

An application can hold an old connection while another connection logs the
same account in and replaces the saved login. If the application later logs
the old connection out, the newer saved login disappears too. The newer
connection may keep running, so the damage can be noticed only on restart,
when the account needs to be logged in again.

`StoredSession.save()` compares the store's current auth key with
`_synced_key`, but `StoredSession.delete()` calls `store.delete(self._name)`
unconditionally. Telethon 1.45.0's `log_out()` first disconnects (calling
`close()` and the guarded save), then calls session `delete()`. With old key A
in the client and replacement key B in storage, the save correctly skips;
delete then removes B. P4 reproduces this on the real client lifecycle.

**Severity:** Medium

**Category:** credential lifecycle / delayed loss of persisted login

**Impact:** a valid replacement session is removed by a client that never
loaded it; the existing warning says changes are not saved while the record
is nevertheless deleted.

**NoobEng:** login ownership must apply to every persistent mutation. Guarding
only the whole-record write leaves logout as a second, unguarded mutation of
the same account record.

**Affected areas:** `StoredSession.save`, `StoredSession.delete`, description
criterion 7, plan Step 1 and the logout/two-client tests.

### Mitigation — Quick

Omit deletion from the store contract or never call it. This avoids removing
the newer login, but ordinary logout leaves a revoked stored credential and
breaks the intended optional-delete behavior.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Re-plan around one ownership check used by both changed saves and deletion.
Read and compare the stored key with `_synced_key`; when different, skip the
mutation and warn once. Failures of the check or delete keep the existing
credential-free logging. Test ordinary deletion, stale deletion after a new
login, and deletion after external removal through real Telethon logout.

**Why this is robust:** both persistent mutation paths enforce the same rule,
without changing the application store interface or default file sessions.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Phase 3: the two actual instances are save and delete in the same
adapter. One comparison serves both without per-operation policy branches.
The robust change has the best reach for its scope and keeps the agreed store
interface. It must enter a revised plan before implementation.
*For future:* —

### Mitigation — Long-term

Add atomic conditional save and delete operations to the store interface,
using the expected key or a version token at the backend.

**Why this is long term effective:** the backend can enforce ownership even
when separate processes race between the local check and the mutation.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Conditional backend operations would address true cross-process
races, but expand the agreed synchronous load/save/delete interface. The local
ownership guard remains useful, so this is future work rather than a prerequisite.

## Model rule

The §9 exception recorded in `merge-check.md` remains unresolved. The exact
model variant and effort are unavailable here; this review does not claim
compliance or substitute test results for the maintainer's decision.
