---
model: gpt-6-astra
effort: xhigh
---
# #50 — Terminal account login

**Current contract:** upstream revision after two rejected PR reviews. The full
[terminal-ownership traverse](../../inquiries/2026-10-16_19-25__terminal-login-ownership/finding.md)
concluded at 47d3c99. The previous description is preserved in `desc_r1.md`.
Revision 4's plan and product remain historical evidence; do not resume that plan
unchanged. A new plan, fresh critique and full combined prebuild are pending.

**Session warmth:** same warmed #43/#44/#45/#50 session, base dev
77f2f53eba8bdc6922127a3b9118bf17de4efabf. LoginFlow, StoredSession, native SDK
sessions, reader identity, private publication, terminal input, signal/event-loop
behavior and CLI test contracts were read. Both rejected reviews and their probes
were consumed. Triage 77c1e85 remains feature-heavy. AGENTS.md and
PROJECT_SPECIFICS.md are absent. Current-thread metadata
2026-10-16T16:23:26.250Z verifies gpt-6-astra/xhigh.

## Problem Statement

LoginFlow already supports deliberate phone/code/optional-password authentication,
but users need an installed terminal command that saves a session ordinary tgdata
readers can reopen. Its opaque StoredSession text is not a native Telethon SQLite
`.session` file and cannot simply be written under that filename.

Two implementation reviews exposed an additional contract gap. A task result or
an outer “input is active” flag was treated as evidence that underlying work had
settled. The latest failure leaves terminal echo disabled when the first Ctrl-C
arrives during restoration after ordinary input or EOF. The command needs explicit
ownership of terminal input through restoration, alongside the existing separate
authentication and file-publication outcomes.

## User Value Proposition

An operator uses the reader's configuration, enters the current login inputs and
obtains a reusable session. Stopping does not require another keystroke or silently
leave terminal settings changed. Re-login is explicit; save failures preserve
truthful file outcomes and can permit local retry without another code request.
ScrapeOps can later wrap this command rather than duplicate authentication.

## Success Criteria

1. Installed and module invocations use the same command path and ordinary reader
   configuration. The resolved native destination is shown before requesting a code.
2. Existing LoginFlow owns authentication, proxy/device policy, waits, uncertain or
   unsupported responses and source cleanup. One flow/event loop serves the command;
   prompts and subsequent actions begin only at eligible, settled steps.
3. One private input owner retains the exact selected terminal and its original
   settings through acquisition, input, every exit path, restoration and release.
   It does not assume the selected terminal is stdin. A value reaches the next
   login action only after restoration is established.
4. EOF, normal input, input error and first/repeated Ctrl-C all have explicit
   outcomes. Stop ends the input wait without additional user input. SIGINT during
   command-owned work records stop intent without throwing through terminal
   acquisition/restoration. Repeated stops do not create competing cleanup owners.
5. An actual restoration failure releases no input value and admits no further
   login/save action. It reports a safe failure rather than claiming restoration
   succeeded. Arbitrary OS/device failure is not promised to be repairable.
6. Secret input never falls back to echo. Codes/passwords are not command arguments;
   credentials, codes, passwords and checkpoints do not appear in output/logs.
   Supported terminal contexts, encoding and input limits are explicit and tested.
7. Stop closes admission to new prompts, authentication actions and save attempts.
   An in-flight source action settles under its existing cleanup contract; stopping
   does not imply a remote request never happened. A final stop exit does not erase
   a known or uncertain publication outcome.
8. A completed, settled credential becomes a private native SQLite candidate through
   the existing codec/SDK APIs. Read-back and ordinary-reader authentication tests
   preserve the actual account, authorization key and data centre without prompting.
9. Creation refuses collisions. Replacement is opt-in and requires confirmation of
   the target/account with readers stopped. Symlinks, unsupported types, sidecars
   and a destination changed during the conversation refuse; these are conflict
   checks, not a lock on all readers.
10. Before publication, failures preserve the old destination. Replacement preserves
    prior bytes privately before switching. Pre-publication failure, confirmed
    publication and uncertainty remain distinct; uncertainty retains recovery
    material and cleanup errors do not overwrite the original outcome.
11. A recoverable local save failure permits explicit same-process retry with the
    completed credential, without another SendCode/SignIn. Conflicts and uncertain
    writes do not broaden replacement authorization or permit automatic replay.
12. A later full combined prebuild qualifies actual LoginFlow, native SDK sessions,
    publication, ordinary-reader reopen and terminal input before product edits.
    Tests cross normal/EOF/error exits with first/repeated stops and acquisition,
    mode-change, wait, restoration and release boundaries. Existing source/native
    SRP, publication, save-retry, secrecy and cleanup tests remain relevant.
    Permanent tests, installed-command checks, offline baseline and demos must pass;
    the inquiry's 22-case feasibility probe is not complete-candidate qualification.

## Scope Boundaries

The initial delivery is a deliberate local POSIX terminal command and native-file
publication on qualified trusted filesystems. Foreground/main-thread interaction
and the exact supported terminal contexts must be declared and tested. Unsupported
contexts must refuse safely before authentication. No universal terminal, filesystem
or process-cooperation guarantee is implied.

Keep LoginFlow, StoredSession conversion and native publication as separate
responsibilities. The preferred input direction is one private terminal owner with
nonthrowing stop intent and a controllable wait. This is a responsibility boundary,
not approval to promote the inquiry prototype or add a public terminal framework.

Custom-store users continue using the Python APIs. No CLI plugin loader, generic
session converter/supervisor, durable CLI resume, background input thread or
active-reader rotation is required. No signup, QR/web login, background automatic
login, proxy exit-IP check, media read or ScrapeOps migration/deployment.

This upstream pass changes the description and inquiry records only. Product
implementation, merge/release, version changes and real Telegram login are outside
this pass. Live tests remain separately authorized supplemental qualification.

## Priority Level

Medium (P2). Removes duplicated onboarding/re-login work. It is not a prerequisite
for the separate immediate downstream production recovery path.

## Decisions and Assumptions

Retain file-first publication, create-only by default and deliberate replacement
under the stated conditions. [ASSUMPTION] operators control the trusted directory
and can stop readers; the command must not claim to enforce their cooperation.
A helper process, guarded getpass reuse or create-only-only scope becomes relevant
only under the explicit revival conditions in the new finding.

No new planning blocker is established. Production input policy and complete
composition remain qualification obligations. Native Python 3.7 runtime testing
is unavailable; syntax compatibility is distinct from Python 3.11/Telethon 1.45
execution evidence. Live source delivery/real-account 2FA remain unperformed.
