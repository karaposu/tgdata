# Branch: stepwise-login-ownership

## Source Input
Task-impl inquiry input; original user/issue request is preserved in ../source-input.md.
```text
For issue #8's phone → code → optional 2FA login, what state, ownership and completion contract should connect separate calls and the existing session store? Consider an in-memory flow versus restorable application-owned state, including retries, interruption, proxy/device continuity and publishing the finished credential.
```

## Articulation Reference
- File: articulate_simple.md
- Itemize count:1
- Per-item identifiers:I1
- Verdict:HIGH-PROCEED
- Flagged conditions:none

## Question
I1 literal statement: For issue #8's phone → code → optional 2FA login, what state, ownership and completion contract should connect separate calls and the existing session store? Consider an in-memory flow versus restorable application-owned state, including retries, interruption, proxy/device continuity and publishing the finished credential.

MQ1 identifications, retained:
Question: what kind of answer does this inquiry ask for?
Identified-ambiguities-list:
- A minimum contract for one live flow versus a restartable contract spanning independent calls.
- Description of available guarantees versus selection of which guarantees the first delivery should promise.
Implementation is the enclosing task; this inquiry asks for its behavioral foundation, not code.

MQ3 endpoints, retained:
Question: which action endpoint would satisfy the request?
Identified-ambiguities-list:
- One retained object supports phone/code/password over successive calls; stopping the process requires a fresh flow.
- An opaque unfinished state can be stored and restored between calls/worker handoff.
- A library-managed durable record also coordinates publication and retries around interrupted external calls.
- Final credential returned for explicit caller persistence versus automatic publication to a configured session store.
No-console interaction is an intrinsic bound in every reading.

## Goal
I1 Deconstruct tuple:
Tuple: (deliverable=behavioral foundation for the requested login implementation; kinds=state/owner/success/failure contract and scope/evidence boundaries; bounds=existing-account phone/code/optional-password flow integrated with current factory/session contracts). No late split: publication is part of the same login obligation.

WHY-axis alternatives:
- Enable a web page's natural multi-request interaction.
- Make server restarts/worker placement operationally tolerable.
- Avoid duplicate code delivery, hidden loss of a completed login or credential replacement.
These motives can coexist; their priority is not adjudicated here.

Context-needs (MQ2):
Question: what context is needed to establish that contract?
Identified-ambiguities-list:
- Verdict: whether unfinished-state persistence is required, and which caller/store boundary supplies it.
- Kinds: SDK auth/DC/challenge behavior; final session format; cancellation and uncertain remote outcomes; existing noninteractive readers; operational versus test-server evidence.
- Stance: a reusable library embedded in a web server versus a server that also owns workflow storage and coordination.
The same-session source/vendor knowledge is substrate, not an extra external lookup by articulation.

Exclusions and open boundaries (MQ4):
Question: which exclusions/bounds are known, and which remain open?
Identified-ambiguities-list:
- No console prompting; existing proxy/device/session contracts must apply.
- No implicit login-code request from ordinary scraping; login is deliberate.
- A library API is requested, not a web UI, account service or #17 live validation.
- Full support for signup, alternate delivery methods and recovery is not explicitly requested; the boundary between a supported next step and an unsupported challenge needs defining.
- No authority to merge is implied by implementation; real production code delivery/password input is a separate resource question.

## Considered Articulations
I1:
V1. Define an explicitly owned in-memory login flow whose calls require no console and whose completed credential is handed to the caller; a stopped process starts a new login deliberately.
V2. Define a login flow with secret opaque state that the application retains/restores between calls, and an explicit finished-session handoff; distinguish completed-step portability from interrupted-call certainty.
V3. Define a library-managed durable login record coordinating admission, challenge state and credential publication, with the necessary exclusive ownership and uncertain-write rules made explicit.

## Scope Check
Question covers goal. The inquiry addresses the broader pattern of separate authentication
calls and ownership, not only the historic persistent-client code-request incident.
The in-scope deliverable is a behavioral contract feeding #8, not production code here.
All MQ4 exclusions are retained in Goal; ordinary scraping, #17 live validation,
web UI/service construction and an unrequested merge remain outside this inquiry.
No layer commitment applies: this is a product contract inquiry, not a discipline rewrite.
