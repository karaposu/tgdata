---
model: unknown
effort: unknown
---

# Articulation — group lookup, access checks and joining

## User Input

`$task-impl o [**\#7 — group lookup, access checks and joining**](<https://github.com/karaposu/tgdata/issues/7>).`

The referenced issue is preserved verbatim in `source-input.md`. Its request:
three operations through ephemeral_client — look up name/handle/type, check an
account's access, and join by invite link or handle with an account join limit.
Its examples describe ready versus needs-to-join group handling.

## Itemize

Count: **1**. Identifier: **G1** — implement issue #7's short-lived group
operations with account join limiting. The three verbs are one coupled feature:
they share the target/account/lifecycle and readiness vocabulary. Treating the
quota or joining outcome as an unrelated task would discard that coupling.

## G1 — Per-item bundle

### MQ1 — verdict axis

**Question:** What kind of answer is being requested?

**Answer — explicit-empty:** the user explicitly invokes task-impl for
implementation through its planning, critique and verification chain. No
advice-versus-implementation ambiguity is perceived.

### MQ2 — context-need axis

**Question:** What contextual preparation is needed to frame this implementation?

**Answer — identified-ambiguities-list:**
- **Verdict/preparation:** existing ephemeral/auth/session behavior versus a
  new lifecycle; installed SDK outcomes versus older API descriptions;
  empirical versus merely inferred meanings of membership, read access and
  join acknowledgment; what can be established offline.
- **Kinds:** metadata and result/error shapes; group identifier and invite
  forms; account join-limit unit, time window, storage and concurrency domain;
  optional versus mandatory explicit configuration; interaction with #9's
  independent read allowance and #4's health events.
- **Stance:** thin convenience methods versus a durable account-operation
  boundary for future worker #10; direct-call simplicity versus explicit
  incomplete/uncertain outcomes for automation. Both are readings to retain.

### MQ3 — intent axis (WHAT)

**Question:** Which action endpoints can “lookup, check access and join” denote?

**Answer — identified-ambiguities-list:**
- **W1:** resolve a known group entity versus also return an unjoined invite
  preview whose group ID may not be available.
- **W2:** report membership versus prove readable history versus report the
  ability/action needed to become readable; public read access and membership
  need not denote the same endpoint.
- **W3:** return completed membership only versus distinguish already joined,
  pending approval, web-view interaction and uncertain transport outcomes.
- **W4:** limit successful membership changes versus logical API calls versus
  actual join sends/retries; cap one process lifetime versus a persisted window.
- **W5:** use current group conventions versus introduce explicit portable
  result data that a later worker can relay without SDK objects.

### MQ4 — boundary axis

**Question:** What exclusions or boundary openness are carried by the session?

**Answer — identified-ambiguities-list:**
- **B1:** explicit target Telethon 1.45.0; no additional 1.33.1 work.
- **B2:** `duncan/` is explicitly excluded from commits; the prior issue's
  unrelated guide checkpoint stays archived. #3 proxy testing remains deferred.
- **B3:** this request builds the library feature; no live target/account join
  was specified. Offline verification versus later live acceptance must remain
  distinguishable. The existing separate merge go-ahead boundary still applies.
- **B4:** support for describing paid/web-view/pending outcomes versus actually
  completing those external workflows is not specified; neither is a worker,
  receiver or noninteractive account-login implementation requested by #7.

### MQA

**Reconcile:** MQ2's result/admission preparation and MQ3 W1–W5 share two joint
axes: **what each result proves** and **where account admission is authoritative**.
Retain all named options on both axes. MQ4 B4 and W3 overlap on whether to
describe or complete an interaction; surface that boundary without selecting
one. The explicit SDK/commit/merge constraints are unchanged.

### Deconstruct

Tuple: **deliverable** = implemented and verified tgdata feature;
**kinds** = description, plan, critic/fold decisions, code, offline tests and
public documentation; **bounds** = the three ephemeral group operations and
their account join limit, using the existing account controls. No separate
deliverable/type forces a late Itemize split.

### MultiDepth

**Literal-statement:** “group lookup, access checks and joining.”

**Identified-purpose-motivation-ambiguities (WHY):**
- **Y1:** reduce repeated caller glue versus establish a trustworthy capability
  boundary for worker #10.
- **Y2:** make account/group readiness visible versus contain unintended or
  repeated membership changes and operational account pressure.
- **Y3:** convenience for short human-triggered actions versus explicit state
  suitable for unattended callers. These motivations can coexist.

### Considered articulations

None of these is selected by articulation:

1. **A1 — convenience reading:** implement three short-lived convenience
   methods over existing group metadata/access behavior, with a caller-configured
   per-account limit and familiar result shapes.
2. **A2 — read-capability reading:** implement lookup (including invite preview),
   an actual account read-access check, and separately admitted joins with
   explicit results suitable for “ready / needs join” decisions.
3. **A3 — membership reading:** implement membership-focused lookup/check/join,
   with distinct already-joined, requested and interaction outcomes, and a limit
   defined over membership changes rather than conflating them with reads.
4. **A4 — worker-boundary reading:** implement the same three ephemeral calls
   with portable result/error data and persistent account admission covering
   actual join attempts/retries, while exposing incomplete outcomes for a later
   orchestrator rather than building that worker here.

Each preserves the requested feature deliverable, spans W1–W5/Y1–Y3, stays
within the warm substrate and retains B1–B4. The variants do not choose a
specific window, numeric quota, storage API or implementation sequence.

## Self-assessment

Single light pass: premature split, late split, MQ extension, missing operation,
missing MQ2 preparation/kinds/stance, 2-shape violation, WHAT/WHY conflation and
variant drift **did not fire**. All four MQ questions/answer shapes, MQA, tuple,
literal statement, WHY list and four variants are present. No additional
clarification or planning machinery was run inside articulation.

**Verdict: HIGH-PROCEED.** One item; four considered articulations; no flagged
operational condition. This verdict concerns framing completeness, not a
selection among its readings.
