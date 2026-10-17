---
model: gpt-6-astra
effort: xhigh
---
# #55 — accept pending-input terminal state

Same warmed session; triagec260fc2 and native baseline. GPT6 Astra/xhigh verified;
no subagent/new branch. Existing archive/product branches are reused per user.

## Problem Statement
The0.1.2 terminal CLI rejects PENDIN before starting LoginFlow because its positive
local-flag allowlist omits this legitimate kernel pending-input state. Normal login
through the older reader/Telethon prompts is a separate path. Existing native tests
incorrectly classify PENDIN as unsupported, preserving the defect through release.

## User Value Proposition
Operators can use tgdata-login from an otherwise supported terminal with PENDIN set,
while retaining hidden input, exact restoration, cancellation and source/file safety.

## Success Criteria
1. Allow PENDIN where available, while all other mode/control/foreground checks remain.
2. Actual CLI with initially set PENDIN supports plain and native2FA login/native-reader
   reopen, first interruption after normal/EOF input, code/password/replacement/retry
   prompts, physical Ctrl-C during rejected input and oversized-paste refusal.
3. PENDIN plus an unrelated unsupported local flag still refuses before source work
   or mode mutation. Exact original terminal settings and source/file outcomes are
   observed; no login value is supplied by a fake input helper.
4. Correct the old PENDIN-refusal test and retain all other terminal/CLI regressions.
   Full supported offline suites and seven demos pass. No live account login is needed.
5. Commit product/tests/docs separately from work evidence, reuse existing branches,
   and complete the requested merge check against current dev.

## Scope Boundaries
Private _terminal_input allowlist plus relevant tests/smoke documentation only.
No auth, native publication, signal driver, restore algorithm, dependency or API change.
No new branch, real login, main promotion, tag or release in this fix/merge-check run.
A0.1.3 release can follow the subsequent review/merge gates; version stays0.1.2 here.

## Priority Level
High: the installed CLI refuses affected normal macOS terminals before onboarding.
The fix is narrow; terminal safety still needs actual component regression evidence.

## Known Blockers
No planning blocker. Native refusal and three in-memory input/EOF/Ctrl-C controls are
observed. Complete candidate CLI/profile qualification remains an execution gate
before product adoption. Live/native3.7/other-host qualification remains separate.
