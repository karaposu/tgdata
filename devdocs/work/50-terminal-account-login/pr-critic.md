---
model: gpt-6-astra
effort: xhigh
---
**IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: the existing LoginFlow/native-session/terminal composition cannot
preserve settled source ownership and truthful publication outcomes within a
bounded command adapter, so the two-module plan would need replacement.
Affordable now: no remaining unexecuted observation of that scope — the cheapest
combined experiment ran before implementation, and fresh actual-component probes
have now run against this PR. They establish a local interruption defect, not a
failure of the source/session representation or the file-first contract. A revised
driver still needs its own combined prebuild before implementation; this verdict
does not claim that an unwritten correction has passed.

## High-level summary — PR gate REJECTED

One **Medium** finding; no High or Low findings. A real Ctrl-C delivered inside an
authentication coroutine can finish its task with KeyboardInterrupt. The command
then runs that completed task through the event loop again and hangs. Additional
Ctrl-C does not resolve it. This violates the explicit interruption contract and
was reproduced with actual terminal input and actual native SRP computation.

The other17 fresh functional cases passed. Existing exact-tree1,005 offline
checks/34 suites, seven demos and isolated installation also passed, but their
terminal interruption cases hit suspended/waiting work and missed this branch.
The file-first design and existing LoginFlow remain reusable; no finding justifies
rebuilding authentication or adding a general persistence framework.

Under CONTRIBUTING §7.3 one Medium rejects. PR51 must remain draft. Under §7.4,
next is revision3 re-planning, taking this finding as input, then a fresh plan
critique/fold and combined real-component prebuild before implementation. No
product patch or merge is performed during this review.

## Subject, provenance and reading

PR51: head69c240731e9f8dcee794e3f4a88372d8cd9af118, base
77f2f53eba8bdc6922127a3b9118bf17de4efabf; folded revision2 plan on archive
feat/50-terminal-account-login. Published diff downloaded after opening PR and
compared to local diff; only the setup.py hunk-heading label differs, no patch
content. Same warmed session, no subagent. Current-thread metadata
2026-10-16T11:31:47.031Z confirms gpt-6-astra/xhigh (§9 satisfied).

Read all seven changed files in full with triage/desc/plan/plan-critic/prebuild/
verification. Reread full LoginFlow, StoredSession, native SQLiteSession and
controlled transport fixture41, plus owned disconnect and the actual Python3.11
run_until_complete callback/driver. Config/factory/ordinary-reader and health/budget
context retained from the same warmed implementation session. Permanent tests are
supplementary evidence, not the source of the fresh verdict.

## Premise Inventory

### P1 — interruption and owned retirement compose across every execution phase

First dependent step3; waste is its terminal driver plus step5's acceptance coverage
and packaging if a fundamentally different lifecycle is needed. Scheduled in the
combined prebuild beforestep1, then permanent PTY cases. Cheapest earlier covering
test is real SIGINT during a running native authentication coroutine, not only while
its event loop is waiting. The existing source-stop PTY case interrupts a held
Future and is **non-covering for this specific executing-task branch**.

Fresh signal_inside_action and actual PTY/SRP probes fail. This is a missed branch
in the existing ownership mechanism, with a concrete local trigger and code path.
There is no evidence that LoginFlow or native file conversion must be replaced.
The revised driver must be tested in the full composition before product edits.

### P2 — local publication preserves old bytes and distinguishes uncertain effects

First dependent step1 and then2–5; false publication semantics would invalidate
the file owner and operator contract. Full combined prebuild precededstep1. Fresh
late-sidecar, changed-target retry and four real link/replace before/after-effect
fault histories pass. They observe contents and retained recovery files, rather
than supplying a fake publication result. The previously selected parent/backup
barriers remain present and permanent fault tests pass. No claim of physical
power-loss or uncooperative-writer qualification follows from these probes.

### P3 — completed credential is reusable by the ordinary reader

First dependent step2. Real codec/native SQLite and actual ordinary-reader reopen
were tested before implementation, including optional account-cache absence and
SRP. Fresh native DC migration with its different auth key reopens through an
actual account operation. Fractional available update date, large takeout ID and
absent optional cache transfer correctly through native state export/publication.
Native constructor failure retires the opened sqlite3 connection and preserves
old bytes. A hand-made complete flow or dummy file is not the coverage used here.

### P4 — local retries and uncertain source replies do not replay authentication

First dependent step3. The prebuild and permanent suite covered successful local
retry. Fresh source-loss/check/re-input, second uncertainty, expiration, wrong/
correct SRP and target-change-during-local-retry histories count actual controlled
SendCode/SignIn calls. Seventeen additional functional cases pass. Native DC
migration legitimately makes two SendCode requests as existing LoginFlow specifies;
no local save retry does so. Repeatedly failed retirement refuses publication.

### P5 — qualification limits carried unchanged

Live Telegram delivery/real-account2FA and native Python3.7 execution remain
unqualified, as declared. Controlled source responses cannot establish Telegram's
live acceptance. No exclusive authorized live setup is available for this gate;
it is supplemental, not an unfulfilled required offline step. Grammar checks
establish syntax only. Filesystem scope remains trusted local POSIX and stopped
readers; it does not promise global ownership, bounded syscall latency or SIGKILL
recovery. These are preconditions/limits, not new rated findings.

## Restart Check

No earlier rejected #50 PR exists. The missing installed command/persistence layer
is addressed by the terminal adapter and private native publisher. The known
opaque-string/native-SQLite mismatch is handled by actual conversion/reopen. Plan
Risk1's missing backup-directory barrier is answered before replacement. Plan
Risk2's optional own-cache row is answered without inventing an access hash. The
new observed failure is in terminal event-loop driving; a broader auth/store
rewrite would not target its established mechanism.

## Inherited Lessons

Authentication is not publication: separate outcomes and actual file-effect probes
precede product work. A CLI marker cannot coordinate existing readers: documented
stopped-reader precondition, with actual late-conflict checks. Storage retry must
not resend codes: source effects counted in combined/fresh histories. Optional
metadata is not identity: row0 validated and absent own hash accepted. More passing
waiting-state cancellation tests do not prove interruption while synchronous code
runs inside a coroutine: that last lesson was missing, and the revised ordering
must put actual executing-task signal cases in the combined prebuild.

## R1 — Ctrl-C inside an authentication task can leave the command stuck

**Risk**

An operator presses Ctrl-C while the command is processing a login input or
computing the password proof. Instead of stopping, the command can remain stuck
indefinitely, even after another Ctrl-C. The code meant to finish cleanup starts
waiting again on work that has already ended with an interruption exception.
The operator must terminate the process externally and loses the current login
conversation. A normal stop cannot be trusted in the very authentication phase
where the command promises it.

In tgdata/login_cli.py:40–59, _drive catches KeyboardInterrupt from
loop.run_until_complete(task), sets stopped and cancels only if task is not done.
It unconditionally loops back to run_until_complete even when task is already done
with KeyboardInterrupt. On Python3.11.10, asyncio.base_events._run_until_complete_cb
explicitly returns without loop.stop for a future carrying KeyboardInterrupt or
SystemExit, because the initial exception already ended run_forever. Re-entering
run_until_complete on that done task therefore leaves the loop running with no
completion callback that will stop it. Real SIGINT within LoginFlow.start's
validation or the password/SRP action reproduces this. The installed default
SIGINT handler in main makes this a real terminal interleaving, not an artificial
unsupported exception type. Another SIGINT re-enters the same faulty path.

**Severity:** Medium
**Category:** Cancellation / command lifecycle
**Impact:** Ctrl-C fails to terminate a deliberate authentication; the user needs
external process termination and cannot rely on the documented stop/cleanup outcome.
The probes do not demonstrate an overwritten old credential or secret disclosure.
**NoobEng:** KeyboardInterrupt can enter Python while code is running inside an
async task, not only while the event loop waits. A task that already failed needs
its result consumed and owned cleanup settled; running the finished task through
the loop again is not equivalent to draining pending work.
**Affected areas:** login_cli._drive, main's SIGINT policy, source/cleanup lifetime,
planstep3/5 and the terminal interruption guarantee in docs/terminal_login.md.

**Evidence:** signal_runner.py reports both uninstrumented histories timed out at
5 seconds. Both diagnostic runs record `DONE_TASK_KEYBOARD_INTERRUPT_REENTER 1`
before timing out. pty_native_srp.py uses actual getpass, actual SRP compute_check
and an actual SIGINT while computation is active, then another SIGINT:

```text
native_srp_interrupted=true
all_hidden_inputs_sent=true
additional_sigint_sent=true
timed_out=true
exit=-9
child_result=false
secret_echo=false
```

Exit-9 is the probe parent's bounded kill of its own synthetic child after7 seconds,
not an exit returned by the command. Native Python driver source confirms the
callback behavior above. The existing permanent source_stop case interrupts an
awaited Future, which follows a different cancellation path and passes.

### Mitigation — Quick
Detect a done task in the KeyboardInterrupt handler and immediately report stop,
without establishing the state of other owned work or changing signal ownership.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Re-plan the terminal driver's interruption ownership: distinguish pending work
from an already completed interrupted task, consume terminal results exactly once,
and settle all work it owns before returning the original stop. Consider converting
SIGINT into an owned cancellation request while async actions run, retaining the
separate input and publication policies. Cover first/repeated signals during
actual validation, native SRP, source awaits and cleanup, including complete auth
and post-publication stop, in the full combined prebuild before product changes.
**Why this is robust:** closes the local driver lifetime rather than merely
avoiding one loop iteration; uses the existing auth and publisher contracts and
tests the actual phase distinction that failed.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The only concrete consumer of this mixed hidden-input/async-login/
synchronous-publication lifetime is login_cli. The worker has a different process
and job contract; one shared mechanism is not established without special cases.
The local ownership correction and full composition tests close this instance
with the least extent. Quick can abandon owned work; a new cross-command framework
adds unproved coupling. Robust is selected on merit, not external pressure. It
informs revision3 re-planning; this selection does not authorize an in-place patch.
*For future:* —

### Mitigation — Long-term
Introduce a common process/terminal task supervisor for all commands and migrate
the worker and future interactive tools to its signal and cleanup lifecycle.
**Why this is long term effective:** could centralize such policy if multiple
commands need exactly this mixed synchronous-input/async-auth/synchronous-publication
contract. The existing worker owns a different job/process lifecycle, so that
shared class has not been established.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Verification and records

pr-probes/ contains scripts, both matrix attempts, timeout/diagnostic results and
the native-PTY transcript. The first matrix run's direct session-state mutation
was overwritten by native disconnect; its fixture was corrected to populate the
actual message box, with the same expected values. Full17-case matrix then passed.
No product or permanent test changed. Source hashes match the published tree.

Issue50's steps through5 and merge-check evidence are committed. Step6 may now name
PR51/merge-check98f4a59; step7 must record this completed but rejected critique,
not imply merge clearance. PR remains draft; no merge, release, real login or
ScrapeOps deployment occurred. Phase3 will select mitigation only; §7.4 re-planning
remains the next development step.
