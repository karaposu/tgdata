---
model: gpt-6-astra
effort: max
---
**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a live Telegram1.45 join/import produces a purported completion/pending
reply with materially different membership meaning, despite the installed schema
and documented operation semantics used here.
Affordable now: no — that remaining observation requires an explicitly authorized
account/group mutation; the prior read-only test authorization does not cover it.
All identified affordable local falsifiers were executed before this verdict:
eight fresh groups, including actual process exits, native SQLite refusal and SDK
request-state handling. No local experiment is left pending behind acceptance.

**Gate: ACCEPTED — 0 High, 0 Medium, 0 new Low.** Two inherited Stage3/4 Lows remain
consciously unchanged, described below. Date:2026-10-11.

## High-level summary

Subject: [PR25](https://github.com/karaposu/tgdata/pull/25)'s implemented product diff
`f15f1a8..4b4ae21` together with Stage5 plan revision2, landing on current devf15f1a8.
The published head when opened was5d76839; subsequent review artifacts do not alter
the product. This is a fresh soundness pass in the same warmed session, not a
subagent or repetition of the pre-implementation verdict. The merge check is the
separate fidelity record. No product correction was made during this review.

The implementation keeps authority, durable admission and outcome evidence separate
at the necessary boundaries. A status snapshot grants no later permission, a
committed charge can survive without a send, and a join result cannot certify
history access. Fresh probes found no uncharged enqueue, owner leakage, capacity
resurrection, fabricated success or cleanup-induced replacement in the examined
composition. The bounded adapter is sufficient; no wider quota/health framework is
needed to close an established defect.

Review source: complete product diff including test36; complete group domain,
join adapter, account operation, owned-health and join-ledger modules; relevant
complete factory/facade/read-budget and health-classification/evidence paths; actual
Telethon1.45 dispatch, join/import constructors/results, sender/result handling,
RequestState and session entity processing. Public docs, setup metadata, Stage5
triage/description/plan/critic/verification and historical lessons were compared.

## Premise Inventory — ranked by waste if false

### P1 — Admission is durable and remains attached to a new SDK attempt

**First dependent step:**2. **Waste if false:** adapter/facade and qualification,
steps2–4; a quota leak would invalidate the central joining guarantee.
**Test scheduled at:** prebuild cancellation experiment, then step4/6 public suites.
**Cheapest earlier test/cost:** actual SDK/SQLite composition before building,
seconds offline; it was run during the inquiry and required experiment. Fresh
review extends it with real process exits at uncommitted insertion, completed
commit and actual RequestState enqueue, plus native authorizer rejection and
post-commit/close faults.
**Coverage:** covering for this local composition. Reopened SQLite shows0/1/1
charges across those exits. Failed/cancelled claim completion never reaches the
sender; protocol repair retains the same RequestState/future and one admission.
Synthetic network replies are not evidence of remote deduplication or power-loss
durability, and neither is claimed. No build-before-unperformed-local-test gap remains.

### P2 — The verified owner and current policy control the mutation

**First dependent step:**2, consumed by3. **Waste if false:** the staged ownership
design would not protect this consumer; false accounting/health affects every join.
**Test scheduled at:** inquiry/earlier Stage1 proofs and delivered step4.
**Cheapest earlier test/cost:** delayed proof with changed identity/policy, seconds
offline. Existing product tests prove cached111/actual222 and changed-owner refusal.
**Coverage:** covering for actual facade/handle/ledger composition. New tests revoke
the cap from a second ledger while self proof is pending, force eight preflights
through two facade instances sharing one file, and cancel a held wrong-owner proof.
Results are0 sends after revocation/cancellation and exactly2 sends for a cap of2.
No test pretends a session filename or static user fixture alone authenticates a
live account; synthetic self responses exercise the real proof interpretation.

### P3 — Outcomes and health use the source evidence they claim

**First dependent step:**1/3. **Waste if false:** returned membership/pending values
or health could look correct while describing another request or account.
**Test scheduled at:** actual SDK probes before planning and public tests in4.
**Cheapest earlier test/cost:** decoded replies and sender-built error objects;
already performed, seconds offline. Fresh review combines proof RPC names with an
unrelated handled error and enclosing legacy observation, and fails actual request
serialization after admission. File/store reopen checks nested acknowledgment
metadata is not silently promoted to result/cache state.
**Coverage:** real request correlation, exception identity, health and cache paths.
All three misleading proof names remain original errors, with0 charges and0 health
events; serialization failure retains its original OSError and1 charge,0 enqueues.
The supplied server bytes cannot establish live membership. That frontier is P4.

### P4 — Vendor meaning and deployment conditions beyond local qualification

**First dependent step:**1's semantic interpretation and5's public claims.
**Waste if false:** any promise of actual membership/safe rates across untested
server/platform conditions would be wrong. The delivery does not make that promise.
**Test scheduled at:** no live mutation in this stage; separately authorized future
qualification. **Cheapest earlier test/cost:** an authorized live join on a designated
account/group; it changes membership and needs permission not supplied here.
**Coverage:** installed1.45/layer229 constructors and real local TL decoding, plus
primary method documentation for ordinary join/invite and special RPC meanings.
The freshly reopened method pages still show layer225; the newer Ok constructor
page was unavailable. Older web result shapes do not override installed source.
[channels.joinChannel](https://core.telegram.org/method/channels.joinChannel) and
[messages.importChatInvite](https://core.telegram.org/method/messages.importChatInvite)
support the operation/requested/already-member semantics; they do not qualify this
exact live composition. All scripted source outcomes are **non-covering for live
acceptance**. This limit is explicit in desc/plan/public docs, not a hidden passed gate.

Local file custody, accurate forward clock, SQLite/filesystem durability and
nonmalicious in-process callers remain the existing ledger/lifetime contract.
Native Python3.7 is untested;69-file grammar checks and labeled cancellation-hierarchy
fixtures are not represented as a native runtime run. Target execution is3.11.10/
Telethon1.45.0/SQLite3.45.3. No new unresolved planning or execution blocker was found.

## Restart Check

| Observed failure from the task history | Established mechanism | Current design/evidence |
|---|---|---|
| Event owner B but health summary owner A | Fresh event fed cache-owned legacy state | Merged owned context fixes the owner; this facade uses it without legacy fallback; test36 and cross-facade probes |
| Source error became a reference error | Old generic catch interpreted an SDK retry failure | Current resolver remains unchanged; zero-retry/last-error policy and narrow mapping preserve source exceptions |
| Missing/damaged allowance revived capacity | Old implicit repair/pruning semantics | Merged Stage4 ledger is used directly; real transaction/exit probes show retained or refused claims |
| Success-like RPC came from self proof | Error name was mistaken for mutation evidence | Exact original request identity in group_operations.py:405 and join_client.py:43; fresh nested-context probe records0 sends/0 success |
| Ok wrapper contained the wrong payload | TL field annotation was not runtime validation | Explicit seven-root Updates check and signed WebView fields; test36 malformed cases |
| Weak overlap test never interleaved | Ready futures completed in order | Held replies in public tests and eight deliberately blocked preflights in this review |

No cited failure is assigned to an unrelated layer. The old broad attempt is
historical evidence; it is not the active source baseline or a rejection of this stage.

## Inherited Lessons and ordering

- Cached labels are not authority: Stage1 proof was merged before Stage5; new proof
  is awaited at join_client.py:85 before any claim. Current policy is checked again
  by the actual transaction, not by trusting preflight remaining capacity.
- A helper invocation is not an attempt: SDK send/retry behavior was probed before
  building the adapter. The guard lies after resolution/cached waits and immediately
  before enqueue; process/serialization probes show conservative unused charges.
- An acknowledgment is not fresh metadata/read proof: step1 explicitly returns
  preflight metadata and step3 never asserts group recovery. File/store reopen
  probes confirm the cache boundary rather than inventing enrichment behavior.
- Local exceptions are not Telegram evidence: current owned observation and local
  error classes predate this consumer; native storage faults and nested unrelated
  exceptions generate no spurious source health facts here.
- Existing component tests do not qualify a new composition: the candidate prebuild
  experiment preceded edits; delivered44-group tests followed wiring; this review's
  probes call the actual public facade and sender adapter, not the prototype.
- More machinery does not imply safer mutation handling: no refund, reusable token,
  global request interception or health redesign is needed for the observed scope.
  A generic framework would enlarge the authority contract without closing a
  reproduced problem in this bounded consumer.

## Fresh execution evidence

Command: `python devdocs/work/7-group-operations/stage-5-joining/pr_review_probe.py`
using the project `.venv`, Telethon1.45.0. All eight groups completed on the first
run without a probe fix or product change. Source is [pr_review_probe.py](pr_review_probe.py);
raw output is [pr-review-probes.txt](evidence/pr-review-probes.txt). Representative
output excerpts below are exact; the full record includes the other subcases.

```json
{"probe": "process_boundaries", "result": [{"exit_at": "uncommitted", "return_code": 71, "persisted_charge": 0, "sdk_enqueue_observed": false}, {"exit_at": "committed", "return_code": 72, "persisted_charge": 1, "sdk_enqueue_observed": false}, {"exit_at": "enqueued", "return_code": 73, "persisted_charge": 1, "sdk_enqueue_observed": true}]}
{"probe": "policy_changed_during_proof", "result": {"observed_before": 2, "cap_at_claim": 0, "enqueued": 0, "charged": 0, "health_events": 0}}
{"probe": "different_facades_share_one_cap", "result": {"facades": 2, "held_preflights": 8, "joined": 2, "refused": 6, "enqueued": 2, "persisted_charge": 2}}
{"probe": "protocol_repair_retains_one_admission", "result": {"same_state": true, "same_future": true, "status": "joined", "application_sends": 1, "charged": 1}}
```

The other four groups record native commit denial, lost commit reply, close failure/
cancellation; actual serialization failure and wrong-origin RPCs; held wrong-owner
proof cancellation; and preflight-only metadata with file/store reopen. A native
SQLite authorizer supplies the before-commit refusal; the later exceptions are
explicit fault injections after real commit/close. Process exits are software-crash
tests, not power cuts. Protocol repair executes MTProtoSender's real bad-salt handler
on the same pending RequestState, without claiming a real packet exchange.

The existing **573 actual offline groups/3 live skips**,3 demos and export/69-file
checks remain applicable to unchanged product4b4ae21. Counts/ancestry were reconciled
in the merge check; the entire suite was not rerun merely to manufacture freshness.
The new probe source also compiles and passes Python3.7 grammar. Review changes are
confined to work artifacts. No account, login, message send or live join was used.

## Findings and consciously retained limits

No new High, Medium or Low defect established. In particular, losing allowance
without a send after a committed but failed claim return is the explicit conservative
contract, not a refund bug. Leaving unknown invite IDs unknown and exposing external
action requirements are honest results, not missing post-join workflows.

Inherited Stage3 Low: malformed ChatInviteAlready carrying a peer rather than an
entity can leak AttributeError before a join. It remains fail-closed and the existing
resolver is unchanged. Inherited Stage4 Low: floating expiry precision can briefly
yield a zero retry hint while admission still refuses. It grants no extra capacity.
These are recorded prior-stage limitations, consciously left under §7.3; neither
is promoted to a new rejection or silently patched in this review.

## Phase 3 — mitigation selection

There are no High/Medium proposals to select. No risk or wider class was invented
to populate the scaffold. The API's small consumer design survives this pass; no
re-plan, deprecation or product patch is warranted by the observed evidence.

## Gate disposition

Fresh §7.2 critique is **ACCEPTED** under §7.3. Commit and post this artifact onPR25,
then mark#7's Stage5 review step complete with its artifact/comment references.
Do not mark the issue closed or the stage merged. Merging still needs the user's
go-ahead; then exclude work/archaeology docs, verify the merged product, push dev and
retain the branch as the archive.

Model/effort were re-read at write time from the matching current-session turn context:
`gpt-6-astra`/`max`, `2026-10-11T01:51:41.282Z`, thread
`01a108f3-12f8-7ef2-bc82-745d4feb2a25`. Both review gates ran in-session and satisfy §9.
