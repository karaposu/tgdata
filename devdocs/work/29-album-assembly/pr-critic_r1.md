---
model: gpt-6-astra
effort: xhigh
---
**DO NOT IMPLEMENT — MEANING GAP**

Falsifier: —

**Gate: REJECTED — one Medium finding, reproduced in three histories.**

## High-level summary

A successfully accepted raw input is not guaranteed to be replayable under the same policy. The receiver identifies an existing acceptance marker, but reassembles the current expanded posts under fresh-work limits before using that marker. First acceptance, immediate retry and retry after later membership growth therefore have different admission costs. This contradicts the promised lost-ack recovery even when every saved post is valid and loadable.

This is a narrow missing contract between bounded new assembly and confirming an already accepted delivery. It does not establish that stable post identity, retained members or caller-owned storage are the wrong architecture. The revised plan must settle that contract before specifying the receiver's replay path and its return values. Raising a constant or adding a catch would leave the premise unresolved.

Reviewed in this same warm session, without subagents, against the actual published PR35 product head `19d421f1465961f90ab8a1036bd285425c2b90ad` and target `e5cdad77ff6af41f21503fc43fe3180d5213a41e`, together with folded plan revision2. All seven published product files and93 Python sources match the verified archive tree. The clean PR branch's37 existing album tests pass. Fresh probes executed eight histories: five controls passed and three counterexamples reproduced one underlying finding. The previous810-check regression result remains valid but did not exercise these boundary combinations.

## Premise Inventory

### P1 — Accepted input remains replayable with unchanged policy

**Premise:** preserving valid post snapshots and propagating identical limits through reload is sufficient for receiver acceptance to be retryable after a lost acknowledgment.
**First dependent step:**2, with the resource accounting contract fixed in step1.
**Waste if false:** the receiver replay/return contract, bound-focused tests and recovery guidance in steps2–4 need re-planning; the pure representation can remain.
**Test scheduled at:** the combined prebuild and step3 tested replay and limits separately, including raised member limits, but did not test initial acceptance versus exact replay at an unchanged boundary or replay of several posts after one grew.
**Cheapest earlier test:** real AlbumReceiver accept→reopen→accept with identical input/policy at the byte boundary; real SyncEngine retains the exact pending input to expose acknowledgment consequences. Local, seconds, no access dependency.
**Coverage/result:** fresh probes now reproduce failure at an explicit4640-byte policy and the default16MiB policy. A third history reproduces the same mismatch using a member-count bound after later growth. Raising the bound is a positive control, not a repair. Existing always-spacious replay fixtures are non-covering for this premise. No fake receiver or storage supplies the result.

### P2 — Immutable observed data can be independent of source receipt identity

**Premise:** canonical post observations can preserve every observed member while raw delivery identity/cursors remain unchanged.
**First dependent step:**1.
**Waste if false:** value/combiner architecture would change.
**Test scheduled at:** prebuild and suite42.
**Cheapest earlier test:** actual SDK-derived records with multiple logical posts, partition permutations, different raw stop reasons and equal album IDs in other chats.
**Coverage/result:** fresh mixed-post permutations (six orders, four posts, six members), raw-stop-reason control and cross-chat/collection controls passed. Existing SDK/window/media/source tests also cover the composition. No additional source-completeness promise is made, so synthetic observations are not being used to prove unseen Telegram membership.

### P3 — Known receiver state and uncertain commits preserve data safely

**Premise:** strict reopening and transactions distinguish absent keys from lost state, and a lost response after commit can be recovered without resetting data.
**First dependent step:**2.
**Waste if false:** storage integration changes.
**Test scheduled at:** prebuild and suite42.
**Cheapest earlier test:** actual missing-file/collection/schema checks, a real SQLite trigger abort after post writes, and actual successful commit followed by injected close failure.
**Coverage/result:** fresh controls passed. No file was silently created; data and marker rolled back together; committed data survived failed close and replay with adequate headroom. These results isolate R1 from data loss, bad JSON or broken SQLite transactions.

## Restart Check

| Observed failure | Established mechanism | Design element / gap |
|---|---|---|
| Reference consumer loses secondary caption in its returned summary | Earlier actual-helper probe; every member can carry text | New value retains all member records; fresh mixed-caption controls pass |
| Reference helper aliases equal group IDs across chats | Earlier actual-helper probe; grouping key omitted chat | New post key includes chat; fresh wrong-chat prior refusal passes |
| First receiver acceptance succeeds but lost-ack replay refuses | Fresh real receiver + SyncEngine probe; prior JSON is charged on replay in addition to raw/output | **Gap:** accepted-input recognition is evaluated only after fresh assembly admission |
| Previously accepted multi-post input refuses after another post grows | Fresh SQLite history; replay returns today's larger projections and exceeds aggregate member cap | **Gap:** receipt confirmation is coupled to the size of a new projection |

## Inherited Lessons

| Lesson | Observed ordering / result |
|---|---|
| Saving data before ack must enable restart replay | Commit ordering is correct, but duplicate confirmation can fail afterward under unchanged bounds; R1 |
| Source data is not an acknowledgment receipt | collect uses a normal confirmed raw delivery; its refusal leaves the original source pending/cursor unchanged |
| Raising limits must also work on reload | Selected original Risk1 propagation is implemented; each saved post loads successfully in the failing history, so propagation alone is insufficient |
| More reading does not establish complete album membership | No new source reads or completeness assertion in assembly; fresh controls preserve unconfirmed membership |
| Real-component prebuild must precede adoption | It ran before production and its hashes match; its history set omitted the joint replay/admission boundary |

## R1 — A successful acceptance can strand its own replay

**Risk**

A collector can save a batch successfully, lose the acknowledgment and then be unable to confirm that same saved batch after restarting. Nothing is corrupt and no setting changed. The retry now counts the already saved post as extra work and can exceed the limit that allowed the original save. The saved reading position remains stuck until the caller changes policy or uses a different recovery path. Retrying older input after another post grows can fail for the same reason.

In `examples/album_assembly.py:155–162`, AlbumReceiver.accept reads the collection-scoped marker, loads current posts and calls assemble_albums before branching on `received`. `tgdata/album.py:212–215` adds every prior post's bytes, `:242–244` adds the output again, and `:228–230` bounds the current combined member count. Thus a first acceptance costing `raw + output` can commit while its identical replay costing `raw + prior + output` refuses. For older accepted multi-post input, today's grown prior changes the returned member count too. `examples/album_assembly.py:185–186` then raises before acknowledge_sync; actual SyncEngine leaves the saved pending batch and old cursor intact. This follows the plan's accounting formula, so it is a design-contract gap rather than an implementation deviation.

**Severity:** Medium.
**Category:** Recovery contract / resource admission / replay liveness.
**Impact:** routine lost-ack recovery can stall a successfully stored delivery, including with default settings. Data remains durable; no data loss or extra Telegram read was observed. Manual bound increases can recover the reproduced cases, which limits severity but does not satisfy unchanged-policy retry semantics.
**NoobEng:** being able to reload one saved post proves its format and individual size are valid. It does not prove the receiver can afford a second merge of the raw input plus all current prior/output values. Confirmation of a committed input needs a contract that stays valid after the state changes caused by that input—and after permitted later updates.
**Affected areas:** receiver accept/replay, pure assembler bound policy as used by that receiver, daily/backfill receiver guidance and tests. Raw source serialization, source acknowledgment implementations, account health and budget charging are unchanged.

### Reproduced evidence

Command (against the published product-only checkout):

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python \
  devdocs/work/29-album-assembly/pr-probes.py /private/tmp/tgdata-29-album-pr
```

- **Two-message album + actual daily pending store:** first cost4640, policy4640; acceptance commits. Reopen with identical policy loads the saved post. Exact pending replay costs6990 and raises `AlbumAssemblyError: max_bytes exceeded`. One receiver marker remains; source cursor0, pending=true, source reads1. Raising policy to6990 allows the same replay/ack through cursor2.
- **Default policy:**1300 singleton records,4096 text characters each, all valid raw input. First acceptance costs11,669,628 bytes and commits under16,777,216. Identical replay costs17,679,914 and raises max_bytes. All1300 posts and the acceptance marker remain stored.
- **Later growth:** with max_members3, a raw input containing a two-member album plus one singleton commits. A later input grows the album to three members and also commits. Replaying the old input now wants four output members and raises max_members under the same policy. Raising policy to4 confirms the unchanged input.

These are three manifestations of one missing replay invariant, not three independent findings. The serialized accounting formula explains the failures exactly; documenting that formula does not reconcile it with the promised acceptance/recovery contract.

### Required contract before another plan

Define separately what admits **new assembly work** and what confirms an **already accepted raw input**. Establish an observable invariant: any input the receiver successfully accepts remains confirmable under the unchanged receiver policy after restart and permitted later post growth, without silent trimming, skipped integrity checks or fabricated source receipts. Specify what the replay returns when current post projections are larger than the original delivery.

Then re-plan the receiver path, corresponding bound checks, recovery tests and documentation around that invariant. The pure immutable post representation and source APIs need not be replaced on the evidence available. No mitigation tiers are selected here: critic-d's meaning-gap procedure requires settling the contract first, and CONTRIBUTING §7.4 prohibits patching a rejected PR in place.

## Other checks and review limits

Five fresh control histories passed: mixed-post partition ordering, malformed saved values and incidental RPC context, successful commit followed by failed close, raw/chat/collection identity separation, and strict reopen/atomic rollback. Their JSON output is preserved in pr-probes.json and pr-probes.txt. Five malformed inputs were rejected without content exposure; local AlbumAssemblyError remained neutral under a real ChannelPrivateError context. No extra finding is claimed for memory overhead beyond the documented serialized-work policy, arbitrary external deletion, incompatible fresh observations or stronger live completeness semantics.

The published suite42 passed37/37 unchanged; prior full verification records810 offline checks and6 demos with3 live skips. Package exports and automatic module discovery are additive. No product code was edited during this review. This is local SDK/storage/source-engine evidence, not a live Telegram or physical power-loss test.

## Procedure and next step

Phase1's fresh prompt is pr-dynamic-critic-prompt.md. Phase2 produced this same-session review and actual probes. Phase2.5 applies: rename the folded revision2 plan to `DEPRECATED_step_by_step_impl_plan.md`, record the unresolved acceptance/replay contract in desc.md and keep plan.md as a clear historical pointer. The original preimplementation critic.md remains intact. Phase3 is intentionally not run for a meaning-gap verdict.

This is #29's first rejected PR critique. **Next: revision3 re-planning**, using this finding and the established counterexamples; settle the receiver contract before committing new implementation steps. CONTRIBUTING §7.4: “When the PR critic rejects, the branch does not get its findings fixed one by one. It goes back to step 2 and re-plans.” After revised implementation, renew both merge check and fresh PR critique.

**Independent merge prerequisite:** §9 model/effort remains unconfirmed. It is not counted as a code finding and is not waived. PR35 remains draft and must not merge in its current state.

**Provenance verified retrospectively, 2026-10-14:** local active-thread turn records and matching commit outputs establish GPT 6 Astra / xhigh for this artifact. Earlier unknown/pending wording records what was known at the time; see [§9 verification](model-effort-verification.md).
