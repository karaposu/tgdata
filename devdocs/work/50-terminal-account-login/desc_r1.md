---
model: gpt-6-astra
effort: xhigh
---
# #50 — Terminal account login

**Session warmth:** same warmed #43/#44/#45 session; base dev
77f2f53eba8bdc6922127a3b9118bf17de4efabf. LoginFlow, StoredSession, native
SQLite/MemorySession, terminal input, session naming/factory and login fixture
contracts refreshed. Existing ownership/health/budget context retained. Triage
77c1e85 is feature-heavy; full traverse concluded at15de8c2. No archaeology
refresh was necessary. PROJECT_SPECIFICS.md/AGENTS.md absent. Current-thread
metadata2026-10-16T09:35:25.016Z verifies gpt-6-astra/xhigh.

## Problem Statement

The existing LoginFlow API supports deliberate phone/code/optional password
authentication but does not provide an installed terminal command or publish a
reader session. A human operator currently needs application code around the API
or an application-specific login command. Its returned opaque StoredSession text
cannot simply be written as a native Telethon `.session` database.

## User Value Proposition

An operator runs one command with the reader's configuration, supplies the current
login inputs, and obtains a session the ordinary reader can reopen. Re-login is
explicit, failures preserve the prior credential where publication has not
occurred, and a failed local save can be retried without another code request.
ScrapeOps can later wrap this command rather than duplicate authentication.

## Success Criteria

1. An installed terminal entry point and module invocation use the same command
   path. They consume the ordinary reader configuration and show the resolved
   native session destination before a code is requested.
2. The command drives existing LoginFlow methods without changing their
   authentication, proxy/device, waiting, unsupported-response or cleanup rules.
   It owns one flow/event loop and prompts only at an eligible settled step.
3. Input is deliberate terminal interaction. Secrets are not accepted through
   command arguments or printed in output/logs. Password/code input never falls
   back to echo; EOF and Ctrl-C have explicit stop outcomes.
4. A completed and settled login is converted into a private native SQLite
   candidate using the existing codec and SDK APIs. The candidate preserves the
   actual key/DC and own identity needed by an ordinary reader. Local read-back
   and end-to-end reader authentication tests demonstrate reuse without prompting.
5. New-file publication refuses collisions. Existing-file replacement is opt-in
   and requires explicit operator confirmation of the destination/account and
   stopped readers. Symlinks, unsupported file types, SQLite sidecars and a target
   changed during the conversation refuse. These checks are not a global lock.
6. Before publication, a failure leaves the previous destination untouched.
   Replacement preserves prior bytes privately before switching. Confirmed
   publication, pre-publication failure and uncertain publication have distinct
   safe outcomes. Uncertainty retains recovery material; cleanup failure does not
   erase evidence or rewrite the original outcome.
7. A recoverable local preparation/save failure permits an explicit same-process
   retry using the retained completed credential, with no new SendCode or SignIn.
   Conflicts or uncertain publication do not silently broaden replacement
   authorization. No automatic restart, resend or remote replay is introduced.
8. Cancellation during source work settles owned cleanup before exit. Terminal
   interruption during publication cannot falsely claim the destination stayed
   unchanged after a possible write. Exit codes/messages distinguish operator
   stop, source refusal/failure, local publication failure and uncertainty.
9. A combined actual SDK/session/filesystem/TTY prebuild precedes product edits.
   Permanent tests cover first login, real SRP fixture, native reader reopen,
   create/replace/conflict/sidecar paths, save retry, secrecy, waits/unsupported
   responses, EOF/Ctrl-C, repeated cancellation and cleanup failures. Relevant and
   full offline baseline/demos pass; installed command behavior is tested too.

## Scope Boundaries

Initial CLI publication supports native file sessions on qualified local POSIX
filesystems with the required link/replace/sync behavior and a trusted directory.
Other platforms/filesystems must refuse unsupported publication capabilities
before authentication; no universal durability or hostile-directory guarantee.

Application-owned stores remain supported through the existing Python LoginFlow
and store API. No arbitrary CLI plugin loader, public generic session converter,
durable CLI checkpoint/recovery database or automatic reader-rotation system is
part of this delivery. No signup, QR/web login, proxy exit-IP check, background
automatic login, media read or ScrapeOps migration/deployment. No package version
bump, PR, merge or release in this task-impl run.

## Priority Level

Medium (P2). Removes duplicated manual onboarding work and makes re-login
predictable. It does not block the separate immediate production recovery path.

## Decisions and assumptions

The contract follows `traverse/finding.md`. File-first is the qualified initial
consumer; create-only is the default, with deliberate replacement under explicit
preconditions. Exact command spelling, exit values and publication mechanics are
plan decisions. [ASSUMPTION] operators can stop readers and control the local
destination directory; the command must not imply it can enforce external
process cooperation. The basic native conversion/link/backup probes passed;
they do not replace the combined prebuild.

## Known Blockers

No planning blocker or required offline execution blocker identified. Actual
combined publication/TTY composition must be proved before product edits, rather
than assumed from isolated probes. Live Telegram delivery/real-account 2FA needs
an explicitly authorized exclusive setup and remains supplemental, unperformed
qualification. Native Python3.7 runtime qualification is unavailable; syntax
compatibility and the supported Python3.11/Telethon1.45 run are reported separately.
