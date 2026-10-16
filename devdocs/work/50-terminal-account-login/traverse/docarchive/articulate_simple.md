# Articulation — terminal account login

## User Input
`$task-impl Created #50 — Add a terminal login command that saves a reusable account session, priority P2.`

Substrate: issue50's complete request, completed #8/#5 contracts, triage and current warmed code context. This frames the publication question; it does not choose an implementation.

## Itemize
Count:1. I1 — Add a terminal login command that saves a reusable account session.
Prompts, authentication and saving are parts of the same requested end-to-end outcome; no independent migration/release item is implied.

## I1 — Meta-questions
**MQ1 — What kind of ask is this?**
Identified-ambiguities-list: initial delivery breadth (a focused native-file command / a common command supporting file and application stores); success authority (authorization observed plus explicit save / also reader reopen verification).

**MQ2 — What context does the answer require?**
Identified-ambiguities-list:
- Verdict axis: which publication/durability boundary preserves old credentials; whether ordinary readers consume the output unchanged.
- Kinds axis: destination naming, StoredSession versus SQLite representation, existing-reader ownership, terminal cancellation, packaging and test seams.
- Stance axis: bounded local operator tool versus extensible store integration; deliberate re-login versus resumable authentication workflow. Existing live authentication remains separate evidence.

**MQ3 — What action endpoint is intended?**
Identified-ambiguities-list: create a new compatible file; deliberately replace an existing file; publish to a caller's store; resume a settled flow or retry saving within the same command. The relation among these endpoints is open, not permission to expand all at once.

**MQ4 — What is excluded by the user/context?**
Identified-ambiguities-list (exclusions from issue50): replace LoginFlow; background automatic login/resend; account signup/QR/web auth; proxy exit-IP checking; ScrapeOps orchestration or immediate downstream migration; production login merely from filing; release/merge inside task-impl. Unsupported API actions remain unsupported.

**MQA — reconcile.**
MQ1 breadth, MQ2 stance and MQ3 destination endpoints share the delivery-scope axis. Preserve all options while preventing “small wrapper” from silently meaning either no publication guarantee or an arbitrary store-plugin framework. Success evidence and interruption recovery are separate axes.

## Deconstruct
(deliverable: implemented terminal onboarding/re-login capability;
kinds: installed command, compatible persisted session, tests, caller guide and workflow records;
bounds: existing auth/session contracts, explicit terminal action, old usable destination preserved on pre-publication failure).
No late split: tests/docs/publication are required parts of the same deliverable.

## MultiDepth
Literal-statement: “Add a terminal login command that saves a reusable account session.”
Identified-purpose-motivation-ambiguities (WHY): easier manual onboarding; reliable recovery after logout; reducing duplicate ScrapeOps authentication code; avoiding loss of a working credential. Operational convenience and credential integrity may emphasize different initial scopes.

## Considered articulations
1. Deliver a terminal command that publishes a native file session for existing configured readers, supporting deliberate replacement after readers are stopped.
2. Deliver one command with explicitly qualified file and application-store publication destinations, retaining the same LoginFlow.
3. Deliver a command that creates a new native destination and refuses existing destinations; re-login switches readers to the new file rather than overwriting.
4. Deliver a checkpoint-aware terminal workflow that separates authentication from retryable publication and supports continuing settled login/save work without another code request.

All four preserve the requested command/session outcome; each spans the identified destination, replacement or recovery axis. None commits to a spelling, plugin system, overwrite mechanism or new auth flow.

## Telemetry and self-check
One item;4 MQs,1 reconciliation,1 tuple,2 MultiDepth outputs,4 variants. All9 LAYER1 modes not fired: no spurious split, missing operation, extra axis, missing preparation/kinds/stance, 2-shape commitment, WHAT/WHY conflation or variant drift. Single lightweight pass; no external investigation during articulation. Layer2 is an over-time audit, not asserted absent.
**HIGH-PROCEED**
