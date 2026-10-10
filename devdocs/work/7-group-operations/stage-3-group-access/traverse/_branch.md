# Branch: Stage3 group lookup and access contract

## Source Input

```text
$task-impl |  |  |  |
|---|---|---|
| 3. Group lookup and access checks | Resolve a group’s details and check whether the account can access it. | Next; not started |
```

## Articulation Reference

- File: docarchive/articulate_simple.md, read in full before this derivation.
- Itemize count:1; identifier:I1.
- Verdict: HIGH-PROCEED; flagged conditions:none.

## Question

I1 literal statement: “Resolve a group’s details and check whether the account can
access it.” The following MQ content is copied through without selecting a reading.

**MQ1 — What is the user asking for?**
Answer: **explicit-empty**. The requested mode is implementation via task-impl,
not a proposal-only or merge instruction. Within this runner the immediate product
is the framing for that implementation; the later pipeline still owes code/tests/docs.

**MQ3 — What action endpoint does “details/access” mean?**
Answer: **identified-ambiguities-list**:
- minimal known group metadata versus metadata that can honestly represent an
  invite preview with missing identity and a temporary expiry;
- resolving metadata, observing membership, or actually obtaining a bounded
  history response as the meaning of “can access”;
- returning a negative/unknown observation versus raising an operational failure
  when no conclusive access observation is available;
- compatibility with current GroupInfo-style consumers versus a separate qualified
  result containing the verified account and uncertainty.

## Goal

From I1 Deconstruct:

(deliverable: Stage3 implementation contract feeding the requested feature;
kinds: explicit lookup/access behavior and return/error boundaries, then code,
tests and product documentation through task-impl;
bounds: one named account's short-lived read-only group operations on merged dev,
Telethon1.45.0; no joining/allowance or legacy-system rebuild.)

From I1 MultiDepth - onboarding/displaying a group's real details versus deciding whether to schedule
  a daily scrape;
- reducing consumer glue versus preventing a misleading “ready” decision;
- delivering the first user-facing part of #7 versus establishing a result contract
  that later joining can consume without reopening the merged foundations.-axis (retained as ambiguities):

- onboarding/displaying a group's real details versus deciding whether to schedule
  a daily scrape;
- reducing consumer glue versus preventing a misleading “ready” decision;
- delivering the first user-facing part of #7 versus establishing a result contract
  that later joining can consume without reopening the merged foundations.

From I1 MQ2, including all verdict/kinds/stance context needs:

**MQ2 — What context is needed that the statement does not supply?**
Answer: **identified-ambiguities-list**:
- verdict: which existing boundaries can be consumed unchanged, and which part of
  the old combined approach was rejected versus superseded by Stages1/2;
- kinds: accepted references (handle/link/known numeric peer), group versus user
  entities, invite preview versus full entity, optional identity/metadata, result
  representation, budgeted history and the operational error vocabulary;
- stance: an observed read-only result for the named authenticated account versus
  a general prediction of membership/permissions or future scraping success.

From I1 MQ4, preserving the exclusions:

**MQ4 — What is explicitly outside this delivery?**
Answer: **identified-ambiguities-list** (extrinsic bounds from the staged session):
- Stage4 join allowance and Stage5 joining, including implicit joins during lookup;
- rebuilding merged account ownership/lifetime or broadly migrating legacy health;
- account routing, scheduling, new storage backends, login UX and live Telegram
  mutation in this run;
- Telethon1.33 compatibility work, committing duncan/unrelated guide edits, merging
  or deploying this stage before later review and user authorization.

## Considered Articulations

I1 — Resolve a group's details and check whether the account can access it.

1. **Metadata availability:** implement the paired read-only operations around
   fresh metadata availability, preserving a compact GroupInfo-like view for
   callers that mainly need group discovery/onboarding.
2. **Membership eligibility:** implement group details plus account membership and
   preview qualifications as the access observation, retaining unknown identity
   where an invite reveals less than a full group.
3. **Observed history access:** implement separate metadata lookup and bounded
   read observation for a verified account, distinguishing unknown evidence and
   operational failure so callers can decide whether to scrape.

These are candidate readings, not selected architectures. Each keeps the paired
Stage3 deliverable, spans the identified evidence/representation ambiguity, stays
within the session substrate, and excludes joining/allowance/routing.

## Scope Check

Question covers goal. IN: the paired read-only Stage3 contract and enough current
SDK/code evidence to feed its requested implementation. OUT: the MQ4 exclusions
above, including joins/allowance/routing and reimplementation of merged foundations.
The parent task-impl still owns description, plan, critique, implementation and tests.
Specific-versus-pattern: address the general group-reference/access evidence pattern;
prior PR16 failures are examples to guard against, not the only cases to solve.
No cognitive-discipline rewrite or consolidation of prior inquiry outputs is requested;
merged code is a constraint, not an invitation to synthesize a new global architecture.
