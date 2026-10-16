---
model: gpt-6-astra
effort: xhigh
---
**IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: terminal, source and publication ownership cannot be kept within the
bounded command adapter, requiring replacement of the feature's auth/file contracts.
Affordable now: no remaining unexecuted test of that structural claim — the current
complete component probes have run. They establish the concrete local terminal
ownership defect below, not a need to replace LoginFlow/native publication. A new
input contract/candidate requires the upstream description/traverse pass before
its experiment; this verdict does not approve any unbuilt correction.

## High-level summary — PR gate REJECTED

One **Medium** finding; zero High/Low. A first Ctrl-C during hidden-input terminal
restoration can prevent echo from being re-enabled. It occurs after ordinary input
or EOF and was reproduced in an actual PTY. The existing repeated-Ctrl-C test starts
with interruption during the read, which clears the input flag earlier and therefore
passes a different history.

The old native-password-processing hang is fixed: its actual-SRP/PTY falsifier now
returns130 without timeout or publication. Thirteen other fresh source/storage/
retirement histories passed. No product edit occurred during review.

This is the **second rejected PR gate** (first:pr-critic_r1.md). CONTRIBUTING §7.4
requires returning to description/traverse before another plan, not patching this
finding or automatically generating revision5. PR51 remains draft/unmerged. The
selected mitigation below will inform that upstream pass, not bypass it.

## Subject, provenance and scope

Head34907d42b7b1de1186e4b848eff4a50b2349e9ee, tree
9e9b562acbc1b1355277b69b71345ff8a36d156a, base
77f2f53eba8bdc6922127a3b9118bf17de4efabf; folded revision4.
Same warmed session, no subagent. Current-thread2026-10-16T12:53:53.496Z confirms
gpt-6-astra/xhigh. Renewed merge-check6314d33 is fidelity PASS, not soundness approval.

Read triage/description/folded plan/plan-critic/result/previous rejection and actual
published whole-feature diff. Current CLI, publisher and public documentation were
reread in full. Permanent tests, LoginFlow/StoredSession/native SDK/reader/owned
cleanup/getpass implementations remain in the same full warmed context; native
getpass restoration source was checked directly again for this finding. All106
verified product source hashes still match. No redundant full-suite repeat was
needed for unchanged code; new behavioral probes are below.

## Premise Inventory — ranked by waste if false

### P1 — the input flag represents all terminal resource cleanup

First dependent revision4 step1/3; waste is the input portion of the lifetime,
its phase tests and operator guarantees. Scheduled in full prebuild before product
promotion, but its input-restoration test sends the first signal during the read
and a second during restoration. That is **non-covering for a first signal after
ordinary input or EOF**, when _input remains true through getpass's own finally.

Cheapest covering earlier test: actual getpass/PTY with the first real SIGINT at
native restoration following Enter or EOF; bounded local execution, no account.
Now run: both fail, with echo disabled after main returns. The read-time first-
signal control passes. This is concrete ownership evidence, not a claim that
Python finally is universally safe or that a generic terminal framework is needed.

### P2 — stop intent survives active actions and retirement

First dependent step1/3. The full candidate preceded product edits. New13-case
crossings supplement it with errors/waits, authorization-only recovery, failed
close, storage failure, explicit retries and actual pending-task/async-generator
cleanup. They use real LoginFlow/SDK/native files and actual SIGINT, and pass with
source effects/bytes/cleanup observed. The old actual native-SRP falsifier also
passes. Neither success supplies the missing input-restoration behavior in P1.

### P3 — source completion and file effects remain separate

First dependent original conversion/publication steps; retained in revision4 step3.
Real source/native SQLite/ordinary-reader composition and file barriers were tested
before promotion. Fresh backup-barrier-failure plus stop preserves old bytes; a
post-mutation sync failure followed by a shutdown stop retains old backup and
reports uncertain publication with130. Repeated local save retries authenticate
only once. Mocked complete/file-success receipts are not the evidence used.

### P4 — qualification and ownership limits

Carry desc.md's supplemental live delivery/real-account2FA and nativePython3.7
limits unchanged. Synthetic replies cannot establish live Telegram behavior.
Trusted local POSIX/stopped readers, no hostile/concurrent-writer guarantee and
no bounded native computation/filesystem/disconnect latency remain explicit.
Those exclusions are not rated findings; terminal restoration within an actual
supported PTY is inside the command's stated contract.

## Restart Check

| Observed failure | Established mechanism | Current design result |
|---|---|---|
| Old Ctrl-C during executing authentication hangs | Re-entering run_until_complete on a done KeyboardInterrupt task | Fixed: persistent stop/cancel/consume path; old actual-SRP falsifier exits130 |
| Old waiting-state tests miss executing state | Different task phase at first signal | Expanded prebuild/permanent phase tests address that earlier omission |
| First signal during restoration leaves echo off | _input remains true while getpass executes its finally; the signal raises before native restore | Not addressed by clearing _input only on a prior signal or after getpass returns |
| Original backup-directory/optional-cache plan issues | Missing persistence barrier / optional account row assumed required | Retained publisher barrier and conditional copy remain verified |

## Inherited Lessons

The experiment ran before product promotion and actual signal-active SRP was used;
those earlier lessons were followed. New lesson: “input is active” is not the same
as “the terminal is awaiting bytes.” The opaque getpass call also contains terminal
acquisition and restoration. Protecting cleanup only after a prior interruption
misses ordinary-return and EOF cleanup. The next description/traverse must establish
who owns terminal state until restoration is observed, across every exit path.

Authentication is still not publication; in-flight effects remain possible and
later actions are blocked after stop. No evidence calls for rebuilding the existing
authentication/session/publisher layers or sharing this policy with the worker.

## R1 — first Ctrl-C during terminal restoration can leave echo disabled

**Risk**

After someone finishes entering a hidden phone number, code or password—or sends
EOF—the command must restore normal terminal input. If their first Ctrl-C arrives
while that restoration is happening, it can interrupt the restoration itself.
The command returns as interrupted while the terminal still has echo disabled.
Subsequent input can remain invisible unless the surrounding program or shell
repairs the terminal. The command's promised restoration therefore depends on
where the first signal lands, even though its repeated-signal case works.

In tgdata/login_cli.py:86–95, _TerminalRun.prompt keeps _input=True for the entire
_hidden/getpass call and clears it only in its outer finally. _signal at58–64 raises
KeyboardInterrupt whenever that flag is true. Python3.11.10 getpass.unix_getpass
restores terminal attributes in its own finally (installed getpass.py:75–80).
Following normal _raw_input return or EOFError, a first SIGINT before the restoration
termios.tcsetattr at79 raises out of that finally. The outer prompt finally only
clears the flag; it does not restore termios. The permanent phase_child input-repeat
case instead sends its first signal while reading, which already clears _input,
so its second signal during restoration cannot expose this path.

**Severity:** Medium
**Category:** Terminal resource ownership / interruption
**Impact:** command exits with altered terminal state; subsequent input may remain
invisible. A caller may independently restore it, but the command does not guarantee
its own documented cleanup. No credential disclosure or old-session loss was observed.
**NoobEng:** getpass is not just a blocking read. It disables echo, reads, then
restores echo before returning. An outer “inside input” flag cannot distinguish
those inner phases. Cleanup needs protection and resource ownership even when no
previous Ctrl-C occurred.
**Affected areas:** _TerminalRun.prompt/_signal, _hidden/getpass boundary,
revision4 step1/2/4 terminal ownership/acceptance, docs/terminal_login.md:140–144.

**Observed evidence** — pr-probes-r2/input-restore-result.json:

```text
normal_input: exit130, terminal_restored=false, echo_enabled=false, codes0
EOF:          exit130, terminal_restored=false, echo_enabled=false, codes0
read_stop:    exit130, terminal_restored=true,  echo_enabled=true,  codes0
```

The wrapper sends actual SIGINT at the native restore boundary, then would call
original tcsetattr; it supplies neither a fake getpass result nor fabricated terminal
state. Termios is observed after command return. The probe restores its own PTY
only after recording the failed state, so no test terminal is left altered.

### Mitigation — Quick
Document a terminal-recovery command and warn that cancellation near input return
may require caller cleanup, leaving the current input boundary unchanged.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust
Establish explicit ownership of the exact terminal descriptor and original modes
through the entire hidden-input lifetime. Restoration must execute under the
stop-only policy on normal return, EOF, input failure and first/repeated interruption,
and finish before ownership is released. Keep source admission closed after stop.
Qualify the chosen adapter with real PTYs/signals at acquisition/read/restore/return
and its failure paths before product work. Do not infer completion from an opaque
getpass call merely leaving its outer frame.
**Why this is robust:** closes the resource-ownership gap at the one private hidden-
input boundary without changing the existing authentication or file publisher.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* The private hidden-input adapter is the concrete resource owner
that must be established. Plain confirmations do not change terminal modes, and
the worker has a different input contract; no second equivalent consumer justifies
a shared framework. Explicit local ownership closes this instance with less extent
than a generic backend; a warning transfers cleanup to the operator. Selected on
merit, not external pressure. This informs the required description/traverse return
after the second rejection; it does not authorize a patch or automatic revision5.
*For future:* —

### Mitigation — Long-term
Build a reusable terminal-input backend using non-throwing signal/wakeup handling,
explicit descriptor/mode ownership and event-driven input for every CLI consumer.
**Why this is long term effective:** could centralize these guarantees if multiple
commands need the same terminal mode protocol. The worker's job input is not the
same hidden-input/restore lifetime; no second matching consumer is established.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Verification and review status

13 fresh crossings PASS; three real-terminal restoration histories expose two
failures and one passing control; original actual-SRP/PTY falsifier PASS. Scripts,
outputs and hashes are in pr-probes-r2/. No fixture corrections, product edits or
expectation weakening. The regression's outcome expectation changes from old hang
to revision4's specified130; the signal/native computation remains unchanged.

Recent immutable1,010 offline checks/34 suites, seven demos and installed-command
PASS still apply to this exact head, with3 live checks skipped. They did not cover
the new first-signal restoration branch. Issue steps6/7 must record this review's
completion and rejection honestly; they are not merge permission. The description/
traverse return required by the second rejection is the next development step.
