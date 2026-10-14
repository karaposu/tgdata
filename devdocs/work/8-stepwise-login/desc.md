---
model: gpt-6-astra
effort: max
---
# #8 — explicit step-by-step account login

## Problem Statement
tgdata deliberately refuses unattended login in its reading APIs, but has no explicit
phone → code → optional two-factor password interface for a web application. Holding
the SDK's interactive startup open across HTTP requests would lose challenge state on
restart and can confuse remote authentication with later client initialization.

## User Value Proposition
An application can ask for each input separately, display a safe next-step status,
retain private login progress and save the finished session through its existing #5
store. Every call uses the configured proxy/device policy without console input.

## Success Criteria
1. Explicit start/code/password operations authenticate an existing account; nothing
   in ordinary reading, worker or pool startup acquires permission to send a code.
2. Wrong input, expired challenge, waits, unsupported interaction and uncertain
   network results are distinguishable; no automatic resend or broad auth retry.
3. One caller-owned flow retains observed challenge/authorization and actual key/DC
   through caller cancellation or later failure; owned disconnect settles before
   admission reopens. Failed cleanup blocks new steps until explicitly settled.
4. A versioned opaque private checkpoint restores a settled flow under matching
   config, including the frozen effective device settings. Codes/passwords are never
   retained in it. Local overlap is refused; the application serializes latest-state
   use across workers. Mid-call process death is not exactly-once recovery.
5. Final session text actually reloads through StoredSession and the common client
   factory. It is explicitly saved by the application; SDK save hooks do not claim
   durable publication. Beginning login never loads/replaces an existing session slot.
6. Safe status/repr/errors/native auth diagnostics contain no phone, input secret,
   challenge hash or key. Configuration errors are similarly redacted. Auth flow
   failures remain neutral to ordinary account-health tracking.
7. The complete native Telethon1.45/SRP/session/lifetime candidate passes before
   production implementation; focused and full supported offline suites then pass.

## Scope Boundaries
Existing accounts using ordinary app/SMS/voice codes and optional 2FA password.
Unsupported server interaction is explicit; no signup, payment, QR, recovery,
password changes, bot login, automatic resend or new web UI/server. No cross-worker
lease service, distributed transactions, automatic final-store write or file store
creation. No exit-IP validation or unrelated #17 two-account testing.

## Assumptions and qualification
[ASSUMPTION] Completed-step opaque restoration is the stated working default while
the optional persistence preference remains unanswered; callers may simply retain
the flow in memory. No user-confirmed crash-recovery guarantee is inferred.

Offline tests qualify installed SDK composition, with controlled wire replies.
Live Telegram delivery/acceptance requires an explicitly authorized account/test-DC
setup and is not claimed by the offline implementation. This task requests building
the API, not sending real codes or changing a real account without setup.

## Known Blockers
None identified for planning or offline implementation. Five SDK boundary probes
support the contract; the full candidate gate is still pending, not waived.

## Priority Level
Medium (issue P3). It enables web onboarding now that #5 is merged, while existing
authenticated scraping already works. Credential/lifetime consequences warrant the
feature-heavy process despite the deliberately small public surface.

## Foundation
[Traverse finding](traverse/finding.md), source-input.md and triage.md at dev base
c4e6eac. No prior #8 plan/rejected PR. Implementation scope excludes PR/merge.

## Session warmth record
The implementation session retained the preceding #17 review/merge and #18 closeout
context and refreshed the factory, session store, account-operation lifetime,
configuration, public consumers, login tests and installed Telethon1.45 auth paths
at ancestor c4e6eac89341b204b2749e9d15add578e0706965. Triage a481e32 records those
reads; the full traverse is archived beside its finding. GPT-6 Astra/max verified.
This direct record was added during the merge check to make §4.2 explicit; it does
not claim a new warm-up or change the description's implementation contract.

## Review checkpoint
The prebuild mentioned above subsequently passed in1a234b0, followed by product
877d29d and full verification b76f1f6. On2026-10-14 the user authorized merge check,
PR publication and fresh PR critique. Merge itself remains a later decision.
