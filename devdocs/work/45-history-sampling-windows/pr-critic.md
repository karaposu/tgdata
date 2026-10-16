---
model: gpt-6-astra
effort: xhigh
---
**IMPLEMENT AS WRITTEN**

**PR gate: PASS — zero High, zero Medium, one Low.** The Low is informational
for this gate and is explicitly retained below; this is not a zero-findings review.

Falsifier: a native capture falsely reports a day complete or selection/reload
changes IDs under identical retained input and normalized policy, or real
owner/admission/cleanup composition loses the established outcome contract.
Affordable now: yes for the local composition; tested below before this verdict.
Live source visibility needs qualified session/allowance and remains untested.

## High-level summary

The capture/selection split holds. New source acquisition gives days bounded
opportunities; replay does not query Telegram or confer cursor authority. Fresh
probes found no native coverage, quota, selection, ownership or activity regression.
One nonblocking schema-hardening gap remains for manually constructed, correctly
rehashed input: accepted-page counts can exceed what the recorded row counts could
have produced. Ordinary corruption without a matching recomputed digest still refuses.

Review ran in the same warmed session, without a subagent, against published PR49:

- Base: `77f2f53eba8bdc6922127a3b9118bf17de4efabf`.
- Head: `559638a3624bcdba7684beb286e9c619144be455`.
- Tree: `baf22b05806b6220a2d2ae7c454016005f888f1f`.
- Plan: revision2 `step_by_step_impl_plan.md`, with the two selected plan corrections.
- Prompt: `pr-dynamic-critic-prompt.md`, committed before execution at30f83b5.

The published/local patches match after removing GitHub's different function-label
text in hunk headers; changed lines and file hashes match. Product sources were
hashed before/after probes and stayed unchanged. No finding was patched here.

## Premise Inventory — ordered by waste if false

### P1 — actual source composition can capture across days safely

First dependent step1 (common validator), then3/4; false composition wastes the
source path and public contract. Scheduled combined prebuild before product edits,
then suite47 and full verification. Eight combined groups passed at ac51fab before
20c6781. Fresh review used actual Telethon1.45 dispatch, decoded request/reply TL,
StoredSession, SQLite budget and cleanup with independently generated datasets.
Thirty-six histories checked per-day completeness against the available source
population, source caps, billed slots, ties and short pages. These cover client
composition; generated source replies are **non-covering for live server behavior**.

### P2 — retained input supports finite, exact local selection

First dependent step2; false arithmetic/replay would invalidate the value design.
Prebuild checked termination and raw-record canonical feasibility; permanent tests
then checked the public strict loader. Fresh review used a separate iterative
quota oracle for216 selections over36 captures, including zero/full/sparse cases,
and exact saved/reloaded output comparisons. Forty rehashed malformed-field cases
refused with the documented local error. Low1 identifies a remaining impossible
count combination; it does not invalidate retained native input or the selection
algorithm. No unrun affordable core arithmetic experiment remains.

### P3 — ownership and original outcomes survive multi-day reads

First dependent step3/4. Before-build real-component tests established expected
identity, allowance and cancellation composition; existing suites32/33/34/44 and
new47 cover refusals, storage failure, repeated cleanup cancellation and liveness.
Fresh concurrent222/333 operations preserved separate capture/event/budget owners,
including an original RPC error combined with disconnect failure. Cancellation
during metadata resolution emitted no history call or invented capture. No fake
client or invented budget decision supplied these outcomes.

### P4 — shared validation preserves activity behavior

First dependent step1. Prebuild compared the proposed extraction to the original.
The unchanged suite46 passes35/35. Fresh review compiled the original base _date/
_page functions and compared32 current/base outcomes, including exact exception
types/messages, malformed peers, duplicate IDs, missing slots, caps and boundaries.
All matched. Current activity projection and statistics remain independent of raw
content projection; no batch/progress schema changed.

### P5 — vendor and supported-runtime qualification

First dependent step3. Telegram documents descending history dates and before-date
seeking; its pagination contract explains exclusive ID continuation and filtering
after slicing. Reviewed primary references on2026-10-16:
[GetHistory](https://core.telegram.org/method/messages.getHistory) and
[pagination](https://core.telegram.org/api/offsets).

This supports the chosen wire contract, not live performance, visibility or a
snapshot guarantee. A live test requires an established exclusive session and
authoritative allowance, neither available for this run. Carry this declared
supplemental limit unchanged; do not re-derive it as a new finding or pretend the
source fixture closes it. Defaults3000/100 are caller policy, not empirically
validated recommendations. Native Python3.7 is unqualified; grammar checks and
Python3.11 execution are the reported evidence.

## Restart Check

The consumer's newest300-of599 failure came from stride1 followed by truncation.
Step2's finite quota/rank selection addresses it and permanent tests include both
endpoints. Fresh independent-oracle histories check the chosen policy, not the
consumer's buggy stride.

Earlier requested days missing from a newest-only capped acquisition cannot be
recovered by a better selector. Step3 gives independent day opportunities before
depth passes; capped fresh histories check complete-day populations separately.
There was no prior rejected #45 implementation to explain. This work addresses
the observed layer rather than replacing unrelated progress/pool infrastructure.

## Inherited Lessons

- Source work and selected count differ: separate call/slot caps were tested
  before step1, and per-day coverage is separate from eligibility/omission counts.
- A fresh query is not retained input: step2 hashes observed content/times and
  adds no selection clock;216 fresh replay comparisons match exactly.
- Raw messages are not proven complete albums: step2 declares raw units and known
  omissions; services are unselectable and no trail inference runs on sparse data.
- Selected IDs are not progress: no cursor/ack envelope or progress invocation
  appears in the source/value/facade path. Existing receipts are byte-unchanged.
- More code is not behavioral proof: the actual combined prebuild preceded all
  product work; the narrower fresh tests supplement that experiment and full suite.

## Low1 — saved page counts lack a necessary lower-bound check

**Risk**

A developer constructing or manually editing a saved capture can give it a
matching new checksum and claim that many pages were accepted without returning
any messages. The loader accepts that internally impossible accounting and exposes
it in the source summary. Normal reads cannot generate it, and ordinary file
corruption is still detected by the checksum. The gap affects validation of
externally reconstructed capture metadata, not the correctness of native samples.

In `tgdata/history_sample.py:140`, _validate checks scanned<=pages*100 but not the
necessary lower bound. Lines146–147 allow any positive pages with scanned0 when
end_reason is history_end. `probe_rehashed_impossible_page_counts` changes a valid
one-page empty capture to requests=pages=100, keeps scanned0/end_reasonhistory_end,
recomputes capture_id, then `HistoryCapture.from_json` accepts it with
coverage_complete=True. Native history_capture.py ends a bucket at its first empty
page, so100 zero-row accepted pages are unreachable.

**Severity:** Low
**Category:** Strict value validation / metadata consistency
**Impact:** misleading diagnostic source counts in deliberately reconstructed or
buggy third-party envelopes. No extra read, budget bypass, cursor advancement,
altered selected IDs or native false-completeness case was reproduced.
**NoobEng:** a checksum verifies consistency with the supplied bytes, not their
truth. The loader also validates structural evidence, but currently enforces only
the maximum number of rows possible across those pages. Every nonterminal accepted
page must have at least one row; at most the final history-end page can be empty.
**Affected areas:** HistoryCapture constructor/from_json and derived source summary;
no existing reader or stored native capture needs migration.
**Suggested follow-up:** enforce scanned>=pages for a non-history-end bucket and
scanned>=max(0,pages-1) for history_end, with public reload counterexamples. This
does not establish provenance; it only rejects provably impossible aggregate data.
The evidence does not justify a new generic validation framework.

## Fresh probe evidence

Command, using Python3.11.10/Telethon1.45.0:

```text
python devdocs/work/45-history-sampling-windows/pr-probes.py
```

Saved source/output: `pr-probes.py`, `pr-probes.txt`. Relevant output:

```text
32 base/current page results and exact exception texts match
metadata-stage cancellation: no invented capture or history send; cleanup PASS
40 rehashed malformed field variants refused with HistorySampleError
concurrent222/333 outcome, allowance and event ownership PASS
last-call completion and per-day unknown evidence PASS
36 wire histories; 216 independent selection/replay comparisons PASS
OBSERVED loader accepts rehashed100 accepted pages/zero slots/history_end as complete
Native collector stops on first empty page; valid native capture had1 page
wide window: 20454 buckets, 0.527s capture+selection, 3805081 bytes
8 fresh probe groups; 0 harness failures; one explicit loader observation
```

The observation probe intentionally demonstrates the accepted invalid envelope;
its successful execution is evidence for Low1, not evidence that the loader
refused it. Probes required no fixture correction, expectation weakening or
product changes. Wide-window timing is one local observation, not a latency SLA.

Exact PR-tree regression:1,018 offline checks/34 suites and seven demos PASS;
106 sources compile/Python3.7 grammar PASS; three live cases deliberately skipped.
Evidence is under `pr-verification/evidence/full/`. No extra dependency, migration,
media download, broad engine rewrite, source retry or logging of content is added.

## Phase 3 notes

Completed after Phase2 commit b874f7b. No High/Medium proposals require tier
selection. Low1 is consciously left for a focused validation follow-up: it requires
externally reconstructed data with a matching new digest, does not affect native
capture/selection, and the hash does not claim source authentication. Its small
local lower-bound check is recorded above; a broader validation framework has no
demonstrated additional consumer or justified reach. No product patch is folded
into this review and no unselected Medium/High mitigation is left ambiguous.

## Merge boundary

CONTRIBUTING§7.3 permits a PR with only Low findings. §9 is verified by current
thread metadata2026-10-16T09:18:35.538Z: gpt-6-astra/xhigh. This review does not
authorize merging or release; it records the quality gate for the user's decision.
