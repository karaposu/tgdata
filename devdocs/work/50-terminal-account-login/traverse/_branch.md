# Branch: terminal account login publication

## Source Input
```text
$task-impl Created #50 — Add a terminal login command that saves a reusable account session, priority P2.
```
Substrate: complete issue50 request and same-session code/triage. Inquiry lives in
the issue work folder per CONTRIBUTING; display ID2026-10-16_12-40__terminal-account-login.

## Articulation Reference
- File: articulate_simple.md
- Itemize count:1; identifier:I1
- Verdict:HIGH-PROCEED; flagged conditions:none

## Question
I1: “Add a terminal login command that saves a reusable account session.”
From MQ1: is the initial delivery a focused native-file command or a common
command with file/application-store destinations, and does success mean observed
authorization plus explicit save or also reader reopen verification?
From MQ3: endpoints remain open—new compatible file, deliberate replacement,
caller-store publication, settled-flow resume or same-command save retry.
What contract connects the existing flow to those supported destinations without
invalidating either side's ownership, interruption and persistence rules?

## Goal
Derived from Deconstruct: implemented terminal onboarding/re-login capability,
with installed command, reusable persisted session, tests, caller guide and
workflow records; constrained by existing auth/session contracts, explicit operator
action and preservation of the old usable destination before publication.

WHY alternatives from MultiDepth: easier onboarding, reliable logout recovery,
less duplicate ScrapeOps code and preservation of working credentials. No one
motivation is silently substituted for the others.

MQ2 context needs: verdict axis—safe publication/durability boundary and unchanged
reader consumption; kinds axis—destination naming, opaque/native representations,
reader ownership, terminal cancellation, packaging/test seams; stance axis—bounded
local tool versus extensible store integration, deliberate re-login versus
resumable workflow. Live qualification is distinct from local correctness.

MQ4 exclusions: replacing LoginFlow; background auto-login/resend; signup/QR/web
authentication; proxy exit-IP checking; ScrapeOps orchestration/immediate migration;
production login merely because the issue is filed; release/merge in task-impl.
Unsupported API interactions must not silently become supported terminal actions.

## Considered Articulations
I1 variants, copied from Rephrase without selecting:
1. Deliver a terminal command that publishes a native file session for existing configured readers, supporting deliberate replacement after readers are stopped.
2. Deliver one command with explicitly qualified file and application-store publication destinations, retaining the same LoginFlow.
3. Deliver a command that creates a new native destination and refuses existing destinations; re-login switches readers to the new file rather than overwriting.
4. Deliver a checkpoint-aware terminal workflow that separates authentication from retryable publication and supports continuing settled login/save work without another code request.

## Scope Check
Question covers goal. Include publication success/failure semantics and reader
compatibility for whichever endpoints survive; exclude the MQ4 list above.
Address the general local login/publication pattern, with ScrapeOps as a motivating
consumer, not a production system to modify during this inquiry.
No discipline/framework rewrite or synthesis of multiple prior inquiries is
requested, so Layer Commitment and Synthesis Trigger are not applicable.

## Derivation audit
Item1 retained; MQ1–MQ4 all retained; MQ2 verdict/kinds/stance and WHY alternatives
retained; four variants copied; all exclusions retained. No selection introduced.
