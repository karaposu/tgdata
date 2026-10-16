---
model: unknown
effort: unknown
---
# #50 implementation plan — revision 6

**Critic folded:** 2026-10-16T20:18:38.182284+03:00 — 1 selected robust mitigation (2 steps changed, 0 added). Full combined prebuild remains PENDING; no product clearance.

Based on revised desc.md dbe9d97 and traverse finding 47d3c99, with both rejected
PR reviews as inputs. Revision 4 is preserved in step_by_step_impl_plan_r4.md.
Two rejected PR reviews exist; the required upstream return is complete. This is
a new plan from that contract, not resumption of revision 4 or a third PR review.

Same warmed session; no subagent. Source, SDK, native sessions, reader, publisher,
terminal and previous review/prebuild contracts retained and refreshed. Dev remains
77f2f53; product PR51 remains34907d4. Prior session proof records Astra/xhigh; this
turn's model/effort is not exposed by reachable current metadata, so frontmatter
is unknown and current-turn §9 verification remains pending rather than invented.

### What is the task

Provide one deliberate terminal login command whose input remains owned until its
terminal settings are restored, while preserving existing LoginFlow authentication
and native session publication. A stop request prevents new work without pretending
that source effects or file writes have been reversed. The requested work in this
turn ends after the new plan, fresh critique and complete prebuild; product steps
below describe the later implementation and are not authorized by the prebuild alone.

### Huge Hard Blockers

#### Planning Blockers

None identified. Native inquiry observations establish local input-owner feasibility:
terminal state outlives an fd, getpass can select a different terminal from stdin,
and a nonthrowing handler alone cannot wake a blocking read. The full candidate
composition is still an experimental premise, tested before product edits below.
It is reachable work, not an inaccessible planning blocker.

#### Execution Blockers

- **What must happen:** authorized exclusive account setup for supplemental live
  delivery/real-account 2FA. **Who:** maintainer. **Blocks:** optional live portion of
  step 5 only. **Status:** OPEN; not needed for the required offline gate.
- **What must happen:** available native Python 3.7 runtime if that execution claim
  is needed. **Who:** environment owner. **Blocks:** optional runtime qualification
  in step 5. **Status:** OPEN; syntax compatibility is reported separately.
- **What must happen:** verify current-turn model/effort under CONTRIBUTING §9.
  **Who:** session metadata/UI. **Blocks:** final merge clearance, not offline
  behavioral measurements; no compliant current-turn model is claimed. **Status:** OPEN.

### How this implementation moves toward desired state

Replace opaque getpass/input ownership with one private, bounded terminal reader.
The command's existing sticky stop and async action owner remain; its signal handler
stops throwing into input. Preserve LoginFlow, StoredSession conversion,
LoginDestination and their independent source/file outcomes. Prove all of these
in one candidate run under work docs before promoting any product bytes.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Specify the private input contract and build its experimental composition | Complete candidate under work docs only |
| 2 | Fresh critique, selection/fold and full combined prebuild | Recorded pass/fail with unchanged product hashes |
| 3 | Promote only the qualified candidate | Private terminal module and CLI integration |
| 4 | Make failures permanent tests and document support | Regression coverage and terminal guide |
| 5 | Verify and return to review | Product/work commits and renewed review handoff |

## Step 1 — private terminal input and command integration candidate

### Proposed changes

Create experimental candidate_terminal_input.py and candidate_login_cli.py only in
prebuild-r6/. Their future product locations are tgdata/_terminal_input.py and
tgdata/login_cli.py. Keep the module private; no new exports, dependency, public
terminal API or changes to LoginFlow/login_file.py. Candidate loading must substitute
both modules while all source/session/file/ordinary-reader components remain real.

The terminal reader opens its own nonblocking `/dev/tty` descriptor with NOCTTY,
validates it and closes only its own fd. Never infer terminal identity from stdin.
Preserve the command's main-thread, terminal-stdin and no-running-loop refusals.
Before any source request, preflight controlling-terminal availability, foreground
process ownership and supported modes; repeat validation at each prompt. No getpass
fallback, stdin fallback or background input thread. Help/import must still work
where termios is unavailable; operational preflight safely refuses there.

Initial input policy: canonical terminal line editing, ISIG enabled, CR-to-LF input
mapping and no conflicting CR/LF conversion, UTF-8 strict decoding.
[folded: R1, robust] Reject ISTRIP and IUCLC when available at both preflight and
every prompt, before mutation/source work; do not silently normalize user settings. Limit each
phone/code/password/confirmation line to128 UTF-8 bytes excluding newline; require
PC_MAX_CANON to exceed the130-byte observation buffer, otherwise refuse before auth.
Observe overflow rather than truncate. Read up to130 bytes so a128-byte line plus
newline succeeds and a129-byte line cannot be silently accepted. Empty read or a
canonical EOF-delimited fragment without newline stops without releasing a value.
Invalid encoding/oversize input safely fails this command attempt; it does not
silently modify a password or submit partial input. Tests include exact boundary,
oversize and input exceeding the kernel queue capacity. Longer passwords continue
to use the Python LoginFlow API; this CLI limit must be explicit in documentation.

Capture original termios settings before any mode mutation. Inside a restoration
scope, clear ECHO and ECHONL, apply with TCSANOW, read back to verify hidden/canonical
modes, then display the prompt. All prompts, including confirmations, use this same
hidden reader. Preserve kernel editing; no custom editor. A finite select wait
(50ms) plus nonblocking os.read checks stop before/after waiting and before value
admission. No extra keystroke is needed to stop. This is not a bound on native
filesystem/SDK cleanup or OS calls.

Always settle a possibly applied mode change, including a tcsetattr that took effect
and then raised. Discard queued input while hidden with TCIFLUSH, restore the exact
original settings with TCSANOW and compare tcgetattr. Restoration must still run if
flush fails. Close the owned descriptor once; do not retry an uncertain close and
risk a reused fd. Any flush/restoration/readback/close failure prevents value release
and reports only a fixed safe error kind. Real restoration failure is reported, not
claimed repaired. No value may be returned from inside the protected read scope.

In _TerminalRun remove the _input flag and exception-raising SIGINT branch.
_signal only records persistent stop and requests at most one cancellation of the
registered source action. prompt passes a stop predicate to _hidden/_confirm,
checks before/after them and never owns terminal cleanup itself. _hidden and _confirm
call the private reader; confirmation comparison remains unchanged. Input stop/EOF
maps to the existing130 outcome after cleanup; terminal failures are safely reported
independently even when stop selects130. Late stop cannot erase saved/uncertain files.
Preflight runs inside the command owner before constructing source/destination work.

Retain actual completed-task consumption, exact action registration and stale-callback
checks, explicit retirement, one event loop, existing cleanup and signal-handler
restoration. No new auth/save is admitted after stop. In-flight source effects remain
known/uncertain according to LoginFlow; no remote rollback claim or automatic replay.

### Output
Complete experimental input/CLI candidate plus declared support and effect boundaries.
### Safe in nature
True — work-folder candidate and synthetic terminals only; no product changes.
### Peripheral concepts
Controlling terminal, foreground ownership, termios, canonical input, UTF-8, source
cancellation, safe diagnostics, separate publication outcomes.
### Hardness Lvl
5

## Step 2 — fresh critic, fold and full combined prebuild

### Proposed changes

Run fresh in-session critic-d on revision5 against the revised description, both
rejections and actual code. Preserve critic_r3.md/dynamic_critic_prompt_r3.md. Selected R1 is folded
into revision6; revision5 is preserved. No re-critique of the fold is required. A meaning gap follows
the skill's deprecation/stop procedure. This written fold does not qualify code.

The critic's real-component experiment precedes all product edits. Candidate work
is experimental only. One combined runner must execute the whole retained r4 suite
and the added terminal matrix, with socket connect/connect_ex forbidden, real
LoginFlow/Telethon1.45/SRP/StoredSession/SQLite/reader/publisher, actual PTYs and real
SIGINT. Controlled test41 transport supplies source replies only; input mocks are
non-covering for terminal behavior. Retain pure source/file tests that inject input
values, and identify them honestly. Record exact candidate/harness/product hashes.

Required coverage in that same run:
- Prior23 groups,17 review histories,8 stop transitions,14 publication-stop crossings,
  and25 real-terminal scenarios, adapting only removed helper seams. Preserve all
  behavioral assertions; a getpass-fallback unit test is replaced by actual no-
  controlling-terminal/refusal and hidden-input evidence. Confirmation repeated
  signals must occur during real restoration, not caught KeyboardInterrupt.
- Full CLI phone/code/password/replacement/retry prompts: first signal before native
  restoration after normal input and after EOF, plus repeated read/restore signals.
  Assert exact terminal settings, no next source/save, correct prior file bytes,
  owned wire/task cleanup and original handler restoration.
- Terminal acquisition/snapshot/mode apply (before/after effect), wait/read completion,
  flush, restore/readback, close and prompt-output failures. Inject restoration failure
  with/without stop: assert no input action/publication, safe error and observed dirty
  modes; harness repairs its own terminal only after recording the failure.
- Actual selected controlling terminal differs from tty stdin; observe only the
  selected terminal's changes and exact restoration of both. Reject no controlling
  terminal, background process, noncanonical/unsupported mapping before source work.
- Normal/Unicode/editing, exact128-byte input,129-byte input, kernel-overflow input,
  invalid UTF-8, empty/partial EOF, typeahead discarded, and no echo/secret diagnostics.
  [folded: R1, robust] Actual ISTRIP initially and introduced after the phone action
  must refuse before any next source request; test available IUCLC validation too.
- Complete successful login/native reader reopen, actual2FA and executing-SRP stop;
  create and replacement; local retry without reauthentication; saved/uncertain
  publication plus late stop; all previous source/file failure histories.

Passing result: all required observations pass in one full run; no product source
changes; no timeout kill counts as successful stop. The inquiry's isolated22cases
and targeted probes cannot substitute. A candidate contract failure is a failed
experiment, not permission to tune the plan around it. Preserve failures and stop
for the skill's meaning-gap procedure. A demonstrated harness-only error may be
corrected with failed evidence retained, unchanged assertions and a full rerun.

### Output
Fresh critique, revision6 fold and complete pass/fail artifact before implementation.
### Safe in nature
True — controlled component experiments and documentation only.
### Peripheral concepts
Premise inventory, restart/inherited-lesson checks, real-component evidence,
synthetic terminals, immutable manifests, secrecy and durable-file observations.
### Hardness Lvl
5

## Step 3 — promote the qualified input boundary

### Proposed changes

Only after the full prebuild passes and implementation is requested, promote exact
candidate bytes to tgdata/_terminal_input.py and tgdata/login_cli.py. Preserve the
existing native publisher/bridge, configuration precedence, CWD/literal tilde naming,
create-only default, replacement confirmation/stopped-reader precondition, sidecar/
symlink/conflict checks, private backups and durability barriers. Keep local retry
and confirmed/uncertain outcomes. No public LoginFlow/reader/store change.

### Output
Product code matching the qualified candidate; no unrelated layer rewritten.
### Safe in nature
False — changes installed command input, signal and cleanup behavior.
### Peripheral concepts
Native session compatibility, existing proxy/device policy, package discovery,
source/file separation and operator replacement authorization.
### Hardness Lvl
4

## Step 4 — permanent coverage and operator documentation

### Proposed changes

Promote behavioral prebuild cases into smoke48 with reusable test-only PTY helpers.
Preserve both rejection witnesses and explicit phase markers. Timeouts fail, actual
source/file/terminal outcomes decide, injected irreparable failures stay failures.
Update docs/terminal_login.md and smoke README with supported POSIX contexts, hidden
confirmations,128-byte UTF-8 limit, EOF/stop, input flushing and truthful restoration
failure. Explain cooperative source cleanup and separate saved/uncertain outcomes.
No universal shutdown-time or live qualification claim.

### Output
Regression tests and public guidance matching the observed supported behavior.
### Safe in nature
True — tests/docs only; no live login.
### Peripheral concepts
PTY test isolation, secrets, input support policy, entry-point behavior.
### Hardness Lvl
4

## Step 5 — verification and review handoff

### Proposed changes

After implementation compile/3.7 grammar-check, run smoke48 and affected15/17/32/41,
then the full supported offline suite and seven demos. Reconcile inventory with dev;
#45/test47/PR49 remain separate today. Current unchanged baseline:1,010 checks in34
suites, three live skips. Verify isolated installed/module entry points and native-
SRP stop without altering the active environment. Live/native3.7 claims remain gated.
Commit product/tests/public docs together and work records separately; preserve
archive and product-only branches. Update the same draft PR51 only with product
commits. Renewed merge check and fresh in-session PR critique remain required.
Three rejected PR reviews would trigger task-impl decomposition, not another patch.
Merge requires go-ahead; no release/version/deployment or unrelated checkout edits.

### Output
Verified product and traceable review handoff; no implicit merge clearance.
### Safe in nature
False — later code publication and externally visible review updates.
### Peripheral concepts
Full regression/install verification, archive/product separation, issue honesty,
§9 metadata, repeated-rejection guard and preserved unrelated user work.
### Hardness Lvl
3
