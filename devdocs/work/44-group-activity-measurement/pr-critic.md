---
model: gpt-6-astra
effort: xhigh
---
**IMPLEMENT AS WRITTEN**

**Gate: PASS — 0 High, 0 Medium, 0 Low findings.**

Falsifier: a real authenticated history trace obeying the documented input contract
loses an in-window message while this result claims complete, or a supported
runtime trace changes owner/charge/error/cancellation semantics. Local attempts to
produce these outcomes were executed below and did not reproduce a defect.
Affordable now: no unresolved local experiment remains — the inexpensive local
falsifiers all ran. Further live server qualification requires exclusive session
ownership and an authoritative allowance, neither established for this review.

## High-level summary
Fresh in-session critic-d review of **PR48's implemented diff plus revision2 plan**,
after PR publication. No subagent, no assumption that the earlier plan critic or
merge check proves soundness. The seven-file public diff and relevant implementations
were read in full; unchanged factory/session/health context retained from the same
warmed session, with owned-operation, budget, heartbeat, group resolution and
window interfaces refreshed. Model/effort verified from current-thread metadata
at2026-10-16T06:06:16.393Z: gpt-6-astra/xhigh, satisfying §9.

Subject: PR head `b479e5f3cf0304865b055ebd271f187cf60848b3`, base
`490cf5f4aaf682a1ed9fcf8c680be56f2ec14c92`, tree
`64a002ef820bba2f6c3a5842c238a3827e1eabf7`. Archive product1855c87 has identical
product contents. Published diff matches the local diff after normalizing GitHub's
different hunk-context labels; added/removed/context content and blob IDs match.

Nine new probe groups exercised eighteen fresh histories through the public API,
real Telethon1.45 dispatch/TL decoding, StoredSession and SQLite allowance machinery.
All passed on the first probe run. Scripts/output: `pr_probes.py`, `pr-probes.txt`,
`pr-probe-results.json`. Source packet contents are synthetic; the source-side
offset model tests reader composition, not live server behavior.

## Premise Inventory — by consequence if false
### 1. Source coverage and pagination
First dependent plan steps1–2; false premise would undermine result meaning and
collector design. Earlier test scheduled before productstep1; original combined
prebuild passed, but did not substitute for this review. Fresh cheapest test:
eight independently selected window/cap histories over a400-message source model
with gapped IDs, equal-second timestamps and variable short pages, using actual
SDK-encoded replies and the real public operation. PASS: all complete results
equal the independently selected full population; cap-only results withhold the
rate and completion claim. Unknown-row/boundary history also stays incomplete.

Source anchor: [GetHistory](https://core.telegram.org/method/messages.getHistory)
documents descending dates and before-date selection. [Offsets](https://core.telegram.org/api/offsets)
defines ID continuation after the offset item and separates post-slice filters.
Current SDK1.45 iterator corroborates full/empty response termination and warns
against treating a short page as end. The new collector avoids min/max filtering,
checks observed order, preserves unknown slots and never promises a snapshot.
Non-covering evidence: synthetic responses do not prove actual live visibility;
that limitation is retained rather than converted into a test PASS.

### 2. Owner, allowance and outcome composition
First dependent steps2–3; false premise could misbill accounts or erase primary
outcomes. Scheduled prebuild and implementation suites covered baseline behavior.
Fresh tests cover two concurrent owners on one facade with stale cached identity,
late allowance refusal, a settlement failure after a successful page, and caller
cancellation from final-page progress. Actual public path/SDK/SQLite/cleanup
observed; only source packets and the explicitly injected settlement fault are
supplied. All PASS, no product or policy change. Named source faults preserve
accepted prefixes and original exceptions; cancellation remains cancellation.

### 3. Populations, dates and counter interpretation
First dependent step1; incorrect denominator would silently mislead comparisons.
Fresh independent arithmetic fixture covers three UTC dates, repeated user IDs,
a same-numeric-ID channel sender, an unknown author, a service message, zeros,
missing counters, an even-duration message rate, paid/custom reaction totals and
a negative signed64-bit album ID. Exact expected values pass. The
[reaction constructor](https://core.telegram.org/constructor/messageReactions)
describes min as absence of current-user detail, not absence of aggregate counts;
the code preserves the supplied aggregate. No unique-reactor, audience-growth or
accrued-in-window interpretation is inferred.

### 4. Compatibility, complexity and runtime
First dependent steps1/3; package or complexity defects could affect existing
callers. Static comparison confirms no existing batch/progress/owned lifecycle/
budget/heartbeat implementation diff. setup.py still discovers the tgdata package;
exports are additive, version0.1.1 and dependencies unchanged. Statistics groups
messages once and emits day buckets once; exact counter medians are the only sorts.
The exact PR tree passed the full supported baseline before publication and all
102 source hashes still match after fresh probes. Python3.7 grammar passes; native
3.7 execution and other SDK versions remain outside this qualification.

## Restart Check
The downstream reader's hidden cap is addressed by explicit stop/coverage evidence;
the fresh exact-cap history verifies the distinction. Zero-excluding truthiness is
replaced by known-value aggregation and the fresh oracle retains0. Unknown senders
no longer become a fictional distinct user; repeated user/channel/unknown fields
are independently checked. No earlier rejected #44 PR exists. These fixes address
the observed measurement layer, without rebuilding storage or scheduling.

## Inherited Lessons
Iterator exhaustion is insufficient evidence: raw source pages/unknowns are kept,
with no short-page end rule; validated by the offset and unknown probes.
Counters now are not engagement accrued during the publication window: separate
publication/observation times and explicit cohort definitions are preserved.
Cached account identity is not billing authority: concurrent owner probe observes
charges1/1 for222/333 and0 for cached111. More test cases are not live validation:
all reports retain the explicit synthetic/live distinction. Cleanup must not turn
cancellation into success: cancellation at the final progress boundary discards
the return, settles disconnect and retains the already-completed source charge.

## Fresh probe evidence
Selected exact output (the complete eighteen histories are in pr-probes.txt):
```text
PASS offset_oracle_500000_164 {"complete": false, "expected_full": 164, "messages": 164, "requests": 6, "scanned": 164}
PASS offset_oracle_500000_200 {"complete": true, "expected_full": 164, "messages": 164, "requests": 6, "scanned": 200}
PASS aggregate_oracle {"ordinary": 4, "reactions_sum": 2147483650, "services": 1, "views_sum": 14}
PASS foreign_unknown_page_atomic {"accepted": 1, "charged": 3}
PASS budget_late_refusal {"accepted": 2, "source_requests": 1}
PASS settlement_fault {"accepted": 1, "reserved": 2}
PASS parallel_owners {"charges": [1, 1], "owners": [222, 333]}
PASS cancel_at_final_progress {"charged": 1, "disconnected": true, "result_delivered": false}
9 groups / 18 fresh histories PASS; no live Telegram
```
Additional histories verify a preview invite makes zero history calls; already/peek
invites use one read and expose only a hashed token label; an unavailable row before
a later boundary never enables complete-window rates. The full suite separately
covers malformed counters/order, primitive input validation, callback isolation,
source RPC health, waits, original-error annotation refusal and repeated cleanup
cancellation. There is no new helper faking owner verification or budget settlement.

## Findings and mitigation selection
No actionable finding. Phase3 has no Medium/High mitigation tiers to select;
no product change or generalized infrastructure is proposed. The documented
limitations are deliberate scope boundaries, not disguised merge blockers:
visible-history observations rather than snapshots, raw rather than assembled
message populations, UTC buckets, finite source work, best-effort exception
metadata and no auto-resume/archive. Billed attempts can exceed accepted observation
counts after failures; docs explicitly direct callers to ReadBudget for that ledger.

## Verification and review disposition
Exact PR tree:987 offline checks across33 suites and seven demos PASS; three live
cases skipped and excluded from987.102 sources compile and pass Python3.7 grammar
on Python3.11.10/Telethon1.45.0. New review probes:9 groups/18 histories PASS with
sockets and login forbidden. No live Telegram call, login code, join, release or
deployment occurred. No credentials or original-checkout changes are included.

CONTRIBUTING §7.3 threshold is satisfied. Commit and post this review, mark PR48
ready, and retain both branches. Merge still requires the maintainer's go-ahead;
this review request does not itself perform a merge.
