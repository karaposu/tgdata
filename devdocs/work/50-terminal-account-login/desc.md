---
model: unknown
effort: unknown
---
# #50 — Terminal account login

**Current contract:** bounded input framing established by the
[streaming-input inquiry](../../inquiries/2026-10-16_20-49__bounded-terminal-input/finding.md)
at e2f5ab6. Earlier description preserved in desc_r2.md; original in desc_r1.md.
Revision6 remains DEPRECATED_step_by_step_impl_plan.md, with its failed experiment
in critic_r6_prebuild.md. Revision7 is based on this contract; fresh plan critique
and full combined prebuild remain pending. The inquiry prototype is not product code.

**Session warmth:** same retained #43/#44/#45/#50 context; dev77f2f53. LoginFlow,
SDK/SRP, session conversion, native publisher, reader, command lifecycle and full
prior test/review contracts retained; terminal/runtime/queue behavior refreshed with
primary source and native evidence. Feature-heavy triage77c1e85 still applies.
No AGENTS.md/PROJECT_SPECIFICS.md. Current-turn model/effort is unavailable; earlier
Astra/xhigh evidence does not verify this turn. §9 confirmation remains pending.

## Problem Statement

LoginFlow already implements phone/code/optional-password authentication without
publishing the configured session. Operators need an installed terminal command
that saves a native session ordinary readers can reopen. Its opaque StoredSession
text is not a Telethon SQLite `.session` file.

Earlier reviews exposed missing task/terminal settlement boundaries. Revision6's
prebuild then showed that canonical terminal input can withhold an oversized line,
so a post-read length check is never reached. Input needs its own bounded framing
and invalid-line completion contract, within the existing terminal owner.

## User Value Proposition

An operator uses the ordinary reader configuration, enters each requested login
value and obtains a reusable session. Oversized input is safely refused, Ctrl-C
remains responsive, and terminal state is restored before another action. Explicit
re-login and local save retry preserve truthful credential/file outcomes.

## Success Criteria

1. Installed/module invocations share the existing command path/configuration and
   show the resolved native destination before requesting a code.
2. Use existing LoginFlow authentication, proxy/device, wait, unsupported/uncertain
   outcome and cleanup semantics; one flow/event loop, no duplicate auth engine.
3. One private owner retains the selected controlling terminal and original modes.
   Supported context is validated before source work and at each prompt; no stdin
   fallback, echoed secret fallback or background input thread.
4. Input is observed incrementally. At most128 UTF-8 bytes are retained for a value,
   with strict decoding and no silent truncation/normalization. A finite paste beyond
   the kernel line limit reaches an explicit refusal without a timeout kill.
5. Oversize or unsupported-control input becomes permanently invalid for that line.
   Clear the candidate and discard the remainder while hidden through Enter, EOF or
   Ctrl-C. Editing cannot make the invalid suffix eligible for authentication.
   Missing newline may still wait, visibly rejected and cancellable; no new automatic
   whole-prompt deadline is implied.
6. Support the terminal's configured erase/clear-line controls before overflow;
   Unicode erase removes one scalar. Enter completes input; EOF stops without a
   partial value. Cursor/history, literal-next and other unsupported controls refuse
   instead of silently entering the password. All prompts use the same hidden path.
7. Discard queued input after hiding and before inviting a prompt, plus queued/
   already-read trailing input at retirement. A value is admitted only after exact
   restoration and descriptor release. The native canonical-mode transition must be
   settled while echo is still disabled; cleanup failures report safe fixed kinds,
   release no value and cannot be disguised as successful restoration.
8. First/repeated SIGINT records stop without throwing through owned input cleanup.
   Stop needs no additional input byte, prevents new prompt/auth/save admission and
   settles existing source work. It does not undo in-flight remote or file effects.
9. No codes/passwords as arguments; no credential, code, password or checkpoint in
   logs/output. Protect owned input and discard queued bytes; do not claim control
   over arbitrary future input after the command has returned.
10. Convert only completed/settled credentials into a private verified native SQLite
    candidate using existing codec/SDK APIs. An ordinary reader reopens the actual
    account/key/DC without another login prompt.
11. Creation refuses collisions. Replacement is explicit, confirms target/account and
    stopped readers, rejects symlink/type/sidecar/change conflicts and preserves prior
    bytes before switching. Pre-publication failure, confirmed save and uncertainty
    stay distinct; uncertainty retains recovery material.
12. Explicit local save retry uses the retained credential without another code/sign-in.
    Conflicts or uncertainty do not broaden replacement authorization. Cleanup failure
    does not overwrite an already observed source/publication outcome.
13. Fresh plan critique and a FULL combined candidate prebuild precede product edits.
    Retain source/SRP/file/stop/secrecy cases and add native size/fragmentation/partial-
    write/edit/EOF/invalid-remainder/queue/restore coverage.46 native inquiry cases and
    7 selected real handoffs establish the premise, not complete product readiness.

## Scope Boundaries

One deliberate local POSIX terminal command and native file publication on qualified
trusted filesystems. Main-thread/foreground terminal, explicit mode/control checks
and supported input policy; unsupported contexts refuse before authentication.
Native evidence is currently macOS/Python3.11/Telethon1.45. Broader runtime/host claims
require qualification; no universal terminal, durability or process-cooperation claim.

Keep the input module private, with basic editing rather than a general editor.
Retain LoginFlow, StoredSession bridge and LoginDestination. No CLI store plugin,
generic converter/supervisor, durable CLI resume, reader rotation, signup, QR/web
login, background auto-login, proxy exit-IP check or ScrapeOps migration/deployment.
Applications with different input/storage needs retain the existing Python APIs.

This pass establishes the contract and replacement plan only. No product edits,
merge, release, dependency/version change or real Telegram login. Later full
candidate qualification remains mandatory before implementation.

## Priority Level

Medium (P2). Removes duplicated onboarding/re-login work; not a prerequisite for
the separate immediate downstream production recovery path.

## Decisions and Assumptions

File-first, create-only default, deliberate replacement under stated preconditions.
[ASSUMPTION] operators control the trusted directory, stop readers and provide one
prompted input at a time; this command does not enforce external process cooperation.
A mature input backend, prompt timeout or producer framing protocol needs a concrete
consumer requirement before expanding this bounded interface.

## Known Blockers

### Canonical post-read overflow detection — CLOSED, false premise replaced
Revision6's5,000-byte-plus-newline case failed before a readable line existed.
The new inquiry establishes byte-observable bounded framing with partial-write
backpressure, invalid-line discard and exact staged restoration. Its final46 native
cases and7 real handoffs pass expected outcomes, including500,000 bytes plus newline.
No shortened value is admitted; persistent cleanup faults correctly remain failures.
Historical failure remains in critic_r6_prebuild.md and prebuild-r6/.

No open planning blocker identified. Complete production composition remains an
execution/qualification gate before product changes, not an assumed pass. Live
source delivery/real-account2FA requires an authorized exclusive setup; native3.7
runtime and current-turn §9 metadata verification remain unavailable/pending.
