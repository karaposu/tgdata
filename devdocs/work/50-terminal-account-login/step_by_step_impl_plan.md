---
model: gpt-6-astra
effort: xhigh
---
# #50 implementation plan — revision 2

**Critic folded:** 2026-10-16T10:25:23Z —2 robust mitigations,3 steps changed(1,2,5),0 added.
Combined prebuild PASS before product work:14 groups including8 actual PTY cases.

### What is the task

Provide a deliberate installed terminal login command that reuses LoginFlow and
publishes a native session the ordinary configured reader can reopen. Treat
authentication, private candidate preparation and local publication as distinct
outcomes, preserving old credentials and avoiding extra code requests on save retry.
Basis: desc.md and the concluded traverse at15de8c2, dev77f2f53, Telethon1.45.0.

### Huge Hard Blockers

#### Planning Blockers
None identified. The existing flow/session/reader contracts and local primitives
are reachable and inspected. Isolated actual-component probes established basic
conversion, native reader reuse, private backup and non-echo fallback refusal.
The combined publication/TTY experiment below remains mandatory before product
work; no claim that the isolated probes establish its composition.

#### Execution Blockers
None for required offline implementation. Live delivery/real-account2FA requires
explicitly authorized exclusive setup, which is unavailable and is supplemental
qualification outside this run. Native Python3.7 is also unavailable; grammar
checking is reported separately from Python3.11 execution.

### How this implementation moves toward desired state

Add a private file publisher and a terminal adapter; reuse LoginFlow, StoredSession,
SQLiteSession and the configured session-name policy. No LoginFlow behavior change,
new store framework, persistent checkpoint database or reader rotation protocol.
The command's safe outcomes preserve the distinction between a failed preparation
and a publication whose durability is uncertain.

### High-Level Summary

| Step | Description | Output |
|---|---|---|
| 1 | Define native destination and publication lifetime | Private file owner, collision/replacement checks and outcomes |
| 2 | Prepare a reusable native credential | Closed verified SQLite candidate from a completed LoginFlow |
| 3 | Drive the terminal conversation | One loop, eligible prompts, cleanup/interrupt and local save retry |
| 4 | Install and document the command | Console/module invocation and operator guide |
| 5 | Test the real composition | Offline smoke48 plus terminal and package checks |
| 6 | Verify and record implementation | Separate product/work commits, pushed branch and issue state |

## Mandatory combined prebuild before step 1

Build a work-folder-only prototype of the chosen command driver and publication
lifetime. Use actual LoginFlow, StoredSession, SQLiteSession, ordinary configured
ConnectionEngine reader and the existing controlled-wire Service/Wire from test41.
Do not replace flow, native session or cleanup with stand-ins returning success.
Source packets may be synthetic; they do not qualify live Telegram behavior.

Include actual terminal subprocess/PTY behavior: hidden input, first Ctrl-C while
waiting for input, first/repeated SIGINT during an async source action and cleanup,
and a stop requested during synchronous publication. Source signals must target
the owned synthetic child process, not the user's terminal or a real reader.

Passing composition: one phone/code and real-SRP path creates a private native
candidate; ordinary reader restores the authenticated ID/key/DC without a new
code; default collision and stale/sidecar targets refuse; pre-publication faults
preserve old bytes; private backup survives a post-mutation sync fault; outcomes
distinguish publication uncertainty; explicit preparation/save retry performs no
additional auth call; EOF/Ctrl-C settle cleanup and never turn into false success.
Also exercise SQLite commit/close failures so no connection outlives candidate
cleanup, secret-free output at DEBUG level, and getpass warning refusal.

Disqualifying result: actual loop/TTY/filesystem/session composition cannot support
these outcomes within the two-module design after fixture-only corrections. Then
do not patch around it in product code: record the meaning gap and return to the
description. Candidate mechanics or behavioral tests must not be supplied by fake
success-returning provider helpers.

## Step 1 — destination owner and explicit publication outcome

### Proposed changes

Add private `tgdata/login_file.py`. A destination owner retains the resolved path,
initial absence or regular-file snapshot, replacement intent and one private
per-attempt staging directory. A small safe outcome records status, destination,
account ID, safe error kind and recovery directory when material must remain;
no credential/error text is included. It is private, not a general receipt API.

Resolve session_file exactly as the existing cached configuration does: explicit
session_file, then legacy username, then telegram_session. Append `.session` only
if absent, as SQLiteSession does. Relative names are relative to the invoking
working directory, matching the reader; do not silently reinterpret tilde relative
to HOME or change the config. Resolve/check the existing parent directory and
display the absolute destination. Parent must exist. Reject non-POSIX/unsupported
link/replace/sync capabilities before source work; qualify trusted local POSIX
filesystems only. No hostile-directory or network-filesystem guarantee.

Preflight never opens the existing destination through SQLite (constructor may
upgrade it). Use lstat/nofollow reading for a regular nonsymlink file, snapshot
dev/inode/size/mtime_ns plus streamed SHA256. Reject any destination `-wal`, `-shm`
or `-journal`, including dangling symlinks, rather than delete/recover them.
Default refuses an existing destination before authentication; `--replace` only
permits an explicitly confirmed replacement. An initially absent path stays a
no-clobber creation even when --replace was supplied.

Create staging under the destination's parent with mode0700. Candidate/backup
names contain no secret input. Establish actual write/link/directory-sync support
using owned empty probe files before requesting a code, then remove those probes.
[folded: Risk1, robust] Sync the destination parent immediately after creating the
private directory, before authentication/publication, so its recovery name is part
of the persistence ordering. Before replacing, sync the prior file's bytes through
the verified backup, then sync the private directory containing that link. Only
after these barriers may replacement be attempted. The post-replace parent sync
remains the success barrier. Failure of a prior barrier cannot proceed to replace.
All operations stay on the same filesystem. A parent identity change or stale
destination snapshot refuses later publication; such checks are detection, not
proof that external readers are idle. The operator owns stopping all readers.

Publish a closed/synced/verified candidate only. Recheck parent, destination and
sidecars immediately before the mutation. Creation uses `os.link(candidate,dest)`
so an appeared file cannot be overwritten. Replacement first hardlinks the old
regular file to `previous.session` in the private directory, verifies it still
matches the original snapshot and syncs that directory before `os.replace`.
Do not use ctime/link-count equality as the post-backup check: creating the owned
backup link changes those attributes without changing old content.

Before any attempted destination mutation, failures are `not_published`; old bytes
are unchanged and explicit local retry may be offered for recoverable preparation
I/O. Destination conflicts refuse without refreshing the original authorization
snapshot. Once a mutation is attempted, an exception that cannot establish its
effect is `publication_uncertain`: retain staging/backup and stop, with no blind
retry or rollback. After mutation and destination-parent sync succeed, outcome is
`published`. Success cleanup removes the candidate's extra link, backup and private
directory; cleanup failure warns with a safe recovery path but never changes the
known publication outcome. On uncertainty, preserve recovery files. No source
request belongs in this module.

### Output
One private owner of preflight, preserved old bytes, publication evidence and cleanup.
### Safe in nature
False — changes secret-bearing filesystem state when explicitly invoked.
### Peripheral concepts
SQLite sidecars, no-clobber link, replace visibility, directory sync, reader quiescence,
safe error reporting, trusted local paths.
### Hardness Lvl
5

## Step 2 — completed-login to native SQLite candidate

### Proposed changes

In login_file.py, consume a settled `flow.session_data` and safe authenticated ID;
the command checks complete/no action_required/no cleanup_pending first. Decode
through StoredSession with a private in-memory store, never parse its JSON in the
command. Validate that auth key/DC and own identity agree with completion.

Create a new candidate file with exclusive creation and mode0600 inside the private
directory. Instantiate SQLiteSession on that path, use native set_dc/auth_key/
takeout_id and set_update_state methods. Reconstruct the own-ID0 marker and actual
account's input-peer row through process_entities on a list of TL input peers.
[folded: Risk2, robust] The own-ID0 marker must match completion. The separate
actual-account row is optional: copy/validate it only when present, never invent
a missing access hash, and compare optional presence during read-back. A completed
LoginFlow without access_hash must still yield a reusable native reader session.
This isolated flow holds own identity, not an arbitrary reader's full group cache;
do not advertise generic session conversion. Preserve available update states.

Save and close before publishing. Native SQLiteSession.close may fail on commit
before it closes its connection: guarantee final local connection retirement, using
the actual retained sqlite3 connection as a last cleanup path if native close fails,
without masking the original preparation error. No partially prepared candidate
is eligible for publication. Retain only owned paths and do not remove an open
candidate while a live writer still owns it.

Reopen the candidate through native SQLiteSession, verify auth key/DC/own identity
and update states against the decoded source, then close and fsync its bytes.
Read-back is local format verification, not a new Telegram authorization claim.
An ordinary reader's actual authorization is covered by the combined/permanent
integration tests. On retry, use the same completed credential and a fresh candidate;
cleanup of a failed candidate cannot destroy the old destination or primary error.

### Output
A closed private native credential that the normal reader can restore.
### Safe in nature
False — credential conversion and local persistence must preserve exact identity/key.
### Peripheral concepts
StoredSession codec, SQLiteSession schema/lifecycle, own entity rows, update states,
commit/close failure, credential secrecy.
### Hardness Lvl
4

## Step 3 — terminal conversation and interruption ownership

### Proposed changes

Add `tgdata/login_cli.py` with `main(argv=None)` returning process exit status and
`if __name__ == '__main__': raise SystemExit(main())`. Interface:
`tgdata-login --config CONFIG [--replace]`; config defaults to config.ini. No phone,
code, password, credential or checkpoint command-line options. Refuse nonterminal
stdin before flow/source work. Require the main thread for signal handling.

Use one private event loop for the command's full lifetime. Construct LoginFlow
with that loop selected; obtain its cached effective configuration for destination
resolution without duplicating config parsing. The ordinary LoginFlow module and
reader entry points remain unchanged. Input is synchronous between settled async
actions. Use getpass for code/password (and phone to avoid terminal disclosure),
with GetPassWarning promoted to refusal; no echo fallback and no background stdin
thread. Confirmation input contains no secret. Validate prompt step from status.

The step driver creates one task, runs it on the retained loop, and on first or
repeated KeyboardInterrupt cancels/drains that task until its owned cleanup has
settled. Preserve caller stop as exit130. Finally retry pending flow cleanup once
if needed without starting new source actions; report cleanup failure safely and
retain original stop/error precedence. Shut down owned loop tasks/async generators
before closing the loop. No new bounded disconnect-timeout promise.

Drive phone→code→password only as status permits. Invalid phone/code/password
permits correcting the same step, never a code resend. Wait prints retry_after and
exits; restart_required/unsupported/action_required exits explicitly. A complete
status with password_setup is not a silently successful CLI login. On uncertain
source outcome, offer one explicit authorization-only check using
check_authorization; it never replays the previous input. If still uncertain or
restart_required, stop. Known complete authorization can be published only after
cleanup is settled; safe status is authoritative even when a source attempt also
reported an error, and the error kind is displayed rather than hidden.

Show the resolved target before first code request. Before publishing a replacement,
show authenticated numeric ID and destination and require affirmative confirmation
that all readers are stopped and this replacement is intended. No automatic yes
flag. A denied confirmation stops without changing the target. For creation, show
the authenticated ID and destination before publishing without a second permission
prompt; it was the command's explicit purpose.

Preparation/save errors known to be pre-publication may offer an explicit retry
while retaining flow.session_data; no source auth method is called on that retry.
Conflicts and publication_uncertain stop for inspection, keeping recovery paths as
specified. EOF is an operator stop. Safe statuses:0 saved;2 usage/config/TTY or
preflight refusal;3 login wait/unsupported/source failure;4 known-unpublished save
failure;5 publication uncertainty;130 interrupted. Local errors show type/kind,
never arbitrary exception text or traceback. Display paths with escaped controls.

During synchronous publication, temporarily defer SIGINT into a local stop flag
rather than allowing KeyboardInterrupt between namespace mutation and outcome
recording. Restore the previous handler in finally. Deliver a pending stop only
after recording/reporting the known publication outcome; a saved session followed
by stop is described as saved, with exit130, not “unchanged.” A second SIGINT during
this short local section remains a pending stop, not a new storage operation.
Other failures are conservatively classified by the publisher. This is no SIGKILL
or universal power-loss recovery promise.

### Output
A deliberate terminal adapter with truthful source/storage outcomes and one owner.
### Safe in nature
False — starts authentication only on explicit command invocation and publishes secrets.
### Peripheral concepts
LoginFlow loop binding/status, getpass, SIGINT/EOF, source cleanup, local retry,
safe output, publication uncertainty.
### Hardness Lvl
5

## Step 4 — installed entry point and operator documentation

### Proposed changes

Add `tgdata-login=tgdata.login_cli:main` beside tgdata-worker in setup.py. No version
bump, dependency change or new exports in tgdata.__init__.py. Add
docs/terminal_login.md and link from README Authentication. Explain first login,
re-login with --replace, session path/CWD semantics, stopped readers, sidecar
refusal, supported local POSIX environment, private files/backup retention, safe
exit codes and the difference between known save and publication uncertainty.

Document in-process save retry, explicit auth-only checking, no durable command
resume, no auto-resend, and custom-store use through the existing Python API.
Keep source live qualification distinct from synthetic-wire tests. No ScrapeOps
code/environment changes, release or running-reader action.

### Output
An installed command and complete operator guide for its bounded guarantees.
### Safe in nature
False — package entry points and public Authentication guidance change.
### Peripheral concepts
setuptools console scripts, module entry, current file/store docs, CLI compatibility.
### Hardness Lvl
2

## Step 5 — permanent actual-component tests

### Proposed changes

Add `tgdata/smoke_tests/test_48_terminal_login.py`; number47 remains assigned to
unmerged #45 and is not imported/cherry-picked. Use actual LoginFlow/native SDK/SRP,
StoredSession, SQLiteSession and ordinary ConnectionEngine consumer with controlled
wire replies. Extend fixture use locally without changing test41's no-created-file
assertions: CLI output belongs in a separate temporary directory. Sockets forbidden.

Cover successful first login and2FA, installed/module entry, config path precedence,
relative CWD behavior, hidden secret input and redacted output, invalid inputs,
wait/expired/unsupported/password_setup, uncertain check without resend, source
errors/cleanup, noTTY refusal before source, EOF, first/repeated Ctrl-C and pending
stop during actual publication. Use real PTYs/subprocess signals for terminal
claims; input stubs supplement rather than replace them.

File cases: native reopen same account/key/DC/own row; mode0600/private0700;
existing refusal before SendCode; explicit replacement with confirmation; rejection
of symlink/type/sidecar/stale target; appeared-file race; commit/close/fsync/link/
replace failures; private old bytes preserved before mutation and retained on
uncertainty; cleanup warnings cannot reverse success; local retry never sends a
second code or SignIn. Tests must assert actual old/new contents and outcome, not
only helper call order. No test expectation weakening.

Add smoke README entry. Check an isolated built/installed package entry point
using existing offline build dependencies, never install into the user's active
environment or contact PyPI. Assert imported path is the isolated installation.

[folded: Risk1 and Risk2, robust] Trace and fault every pre-replacement persistence
barrier and retain old bytes on refusal; test missing access_hash through actual
LoginFlow, native candidate and ordinary reader. Do not present syscall-order
fault tests as physical power-loss qualification.

### Output
Permanent CLI/persistence/lifecycle regression and installation evidence.
### Safe in nature
True — tests/docs additive, existing fixture contracts unchanged.
### Peripheral concepts
real wire fixture41, PTY/signal behavior, filesystem fault injection, isolated packaging.
### Hardness Lvl
4

## Step 6 — verification, commits and issue status

### Proposed changes

Compile/check Python3.7 grammar, run new48 plus relevant15/17/32/41, then all
supported12–19/22–46 plus48 (34 suites on this base) and seven demos. Supply missing
configuration to live12/13; local loopback fixture may need socket permission.
Use Python3.11.10/Telethon1.45.0. Baseline987 actual offline checks plus new tests;
three live cases remain deliberately skipped. Record isolated install checks and
every allowed local verification correction; architectural failure stops the run.

Review actual unchanged LoginFlow/session/reader behavior and source hashes. Commit
product/tests/public docs together; work evidence separately. Push linked branch;
update #50 through step5 with committed evidence. Leave merge-check/PR/fresh critique
for the user's next request. Preserve original checkout/version edit, #45 PR49,
duncan and unrelated guide files. No release, merge or live login.

### Output
Verified implementation and honest committed/pushed handoff for later review.
### Safe in nature
False — publishes implementation and workflow records after required checks.
### Peripheral concepts
supported suite baseline, package test isolation, GitHub pipeline, archived work records.
### Hardness Lvl
3
