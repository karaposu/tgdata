---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual LoginFlow, retained event loop, terminal signals and native
SQLite/filesystem publication cannot preserve original outcomes and old credentials
under the proposed command lifetime without replacing the two-module design.
Affordable now: yes — bounded local prototype and tests, no credentials/network.

Experiment: full work-folder candidate combining actual LoginFlow/StoredSession,
native SQLiteSession and ordinary verified reader with controlled source replies;
actual PTY input/SIGINT and actual local publication, with injected I/O failures.
Include the explicit backup persistence barriers selected below. Test successful
phone/code and real-SRP paths, same-process local retry with one code request,
create/replace/conflicts/sidecars, key/DC/own-row reader restore, all publication
effect phases, SQLite commit/close failure, no-echo fallback, and first/repeated
source/input/cleanup interruption plus deferred SIGINT during publication.
Cost: local development and bounded execution; no real account, login or release.
Must precede: step1 and every product edit. The plan already orders the experiment
there; REORDER enforces the unrun gate rather than counting its prose as evidence.
Disqualifying result: after fixture-only corrections, real component composition
cannot meet the described ownership/publication/interrupt guarantees without a
different auth, reader-rotation or durable-recovery architecture.
Passing result: one combined run satisfies every listed case with native objects,
source effects counted, old/new bytes checked, safe outcome/exit assertions, no
secret output and no live sockets. An isolated conversion test or a fake flow/
publisher supplying the desired behavior is non-covering.

## High-level summary

The bounded file-first approach survives. One Medium correction is needed: make
the recovery directory's own persistence barrier explicit before replacing the
old destination. No High or Low findings. No planning blocker is established;
the full combined behavioral premise is still untested and gates product work.

## Premise Inventory — ranked by waste if false

### P1 — one local publication lifetime preserves usable old state
First dependent step1, then2–5. A false effect/persistence model invalidates the
publisher and operator outcomes. Scheduled beforestep1, not yet run. Cheapest
covering test: real SQLite files/link/replace/fsync plus fault injection, checking
bytes and recorded effect phase; instrument sync ordering to establish the chosen
barriers. Isolated inquiries prove native primitives but not the full lifetime.
Documentation explains syscall contracts, not actual platform support or power-loss
behavior. Real local sync support was observed; universal crash durability is not claimed.

### P2 — terminal input and repeated stop share correct lifetime ownership
First dependent step3, but must be tested beforestep1 to avoid building a publisher
for an unusable command driver. One loop with input between settled actions is
plausible from LoginFlow's loop binding and Python's signal behavior. Only actual
PTY/SIGINT and real flow cleanup can close the composition premise. Input stubs
and mocked complete statuses are non-covering. Scheduled combined prebuild, then
permanent tests; no current covering combined run.

### P3 — conversion produces a usable ordinary reader session
First dependent step2. The actual codec/native SQLite/verified-reader isolated
probe already passed, including own-ID0/account rows and no extra SendCode.
Still combine it with the chosen publication/driver and real-SRP path before
product work; a file containing the expected bytes alone is not the entire claim.

### P4 — safe local retries preserve remote effects
First dependent step3. Existing LoginFlow retains completed credentials and
refuses inappropriate action order, but the new command could accidentally call
start/submit again on a local failure. Count actual controlled source calls across
preparation failure/retry and uncertainty. The prebuild must also exercise
complete status plus a reported error and cleanup_pending, rather than assume
every exception means no authorization occurred.

### P5 — conditional live/runtime qualification
Live Telegram delivery/real-account2FA and native Python3.7 remain unqualified.
Exclusive live setup is unavailable and not a required implementation step;
controlled source replies do not close this premise. Python3.11/Telethon1.45 and
Python3.7 grammar are the bounded runtime evidence. These declared limits are
carried unchanged, not rated as new findings.

## Restart Check

No earlier #50 failed implementation exists. The user's missing command/persistence
layer is addressed by steps1–4, while the completed LoginFlow API remains unchanged.
The observed representation mismatch is addressed by step2 and real reader reopen.
Nothing in this request justifies rebuilding authentication or changing readers.

## Inherited Lessons

- Auth completion is not a saved session: separate outcome in step1, actual retry/
  persistence histories beforestep1, operator reporting in step3.
- Valid SQLite bytes alone do not prove safe publication: full combined prebuild
  beforestep1 rather than treating the isolated conversion probe as sufficient.
- CLI-only locks cannot coordinate readers: stopped-reader precondition and
  observed conflict/sidecar refusal, no invented global safety promise.
- Source retry cannot repair local storage: same retained credential and actual
  SendCode/SignIn counts in the prebuild/permanent suite.
- Echo suppression can fail: actual getpass fallback refuses before reading;
  real terminal handling is separately exercised before implementation.

## Risk1 — the recovery directory needs its own parent persistence barrier

**Risk**

The plan keeps the previous session inside a newly created private directory
before replacing it. Saving the backup's entry inside that directory does not
necessarily persist the directory's own name in its parent. If replacement later
has an uncertain durability outcome, the promised recovery path could lack one
of the persistence steps needed to preserve the old credential across a crash.

Step1 creates a staging directory and later says to sync “that directory” after
hardlinking previous.session. It does not explicitly require the destination
parent to be synced after the staging directory is created and before replacement.
Python's tempfile.mkdtemp performs mkdir, not a parent fsync. A directory's entries
and its own parent entry are distinct metadata. The plan's post-replace parent sync
is too late to establish the backup's pre-replacement persistence ordering when
that sync is the operation that fails.

**Severity:** Medium
**Category:** Publication durability / ordering
**Impact:** an incomplete recovery guarantee on supported local filesystems during
the very post-publication uncertainty case the backup is meant to address.
**NoobEng:** synchronizing the contents of a new directory and synchronizing the
parent entry naming that directory are separate operations. A file-level sync
does not implicitly flush all of its containing directory links.
**Affected areas:** planstep1 staging/backup barriers, step5 fault/order coverage,
mandatory combined prebuild.

Primary basis: [fsync's directory-entry requirement](https://man7.org/linux/man-pages/man2/fsync.2.html).
The actual local mkdir/link/fsync primitives were exercised in the inquiry; no
claim is made that a power-loss fault was reproduced on this machine.

### Mitigation — Quick
Weaken the recovery wording and leave the backup as a best-effort diagnostic file.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Make the barrier sequence explicit: sync the destination parent after creating
the private staging directory before authentication/publication; ensure the prior
file's bytes are synced and its backup link matches the initial snapshot; sync the
private directory after creating that link; only then attempt replacement. Keep
the post-publication destination-parent sync as the success barrier. Every failure
of the pre-replacement barriers leaves the destination untouched and cannot proceed
to replace. The combined/permanent tests trace and fault each barrier, rather than
claiming a simulated crash proves physical storage guarantees.
**Why this is robust:** closes the missing ordering within this publisher with
explicit local barriers and tests; no global transaction framework is needed.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Long-term
Introduce a shared durable filesystem transaction abstraction for all library
artifacts, recovery copies and credential publication.
**Why this is long term effective:** could centralize directory/inode persistence
semantics if multiple concrete consumers need the same replacement contract.
Existing batch_files only publishes non-replacing artifacts; it does not need
credential replacement/backup outcomes and is not yet the same full protocol.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Scope checks

No new dependency, reader schema migration or LoginFlow behavior change. The
planned native bridge uses the SDK schema rather than reimplementing it. All
arbitrary-store/public-converter/durable-checkpoint expansion remains excluded.
No need to ask the user for a design decision that current code/probes can settle.
Proceed to tier selection, then the mandatory experiment before folding/product work.
