---
model: unknown
effort: unknown
---
**IMPLEMENT AS WRITTEN**

Falsifier: an exact committed input with intact original records and unchanged policy cannot be confirmed after restart/growth without rebuilding views; or successful confirmation accepts different original data or advances the wrong source obligation.
Affordable now: yes — actual local receiver/SQLite/source-engine probes, no external account or deployment. **Executed: PASS.** No identified affordable premise test remains scheduled after adoption or unrun as a condition of this verdict.

**PR soundness gate: PASS — zero High, zero Medium, zero Low findings.** §9 model/effort verification remains an independent unresolved merge prerequisite; keep PR35 draft and unmerged.

## High-level summary

Revision4 addresses the first rejection by changing what durable acceptance depends on. The receiver stores immutable original records once. A repeat of an accepted input verifies those records directly; it no longer computes or returns today's potentially larger album. Current content remains available through a separate bounded view read. New input still pays the original admission costs, and changed accepted data is refused.

Fresh same-session critic-d review on2026-10-14, without subagents: complete PR35 diff `e5cdad77ff6af41f21503fc43fe3180d5213a41e...7a49bd9dd0b109ccd64aa7140bd8d88168382f90` plus plan.md/canonical revision4. All seven changed files were read in full alongside the description, both plan-critique generations, first rejection, implementation evidence and relevant raw/source interfaces. The renewed merge-check is committed at528ce74. This soundness verdict is independent of that fidelity result.

Twelve fresh probe groups passed. One group exercised18 deterministic randomized histories with576 acceptance calls and576 zero-write confirmations across two chats and two collections. Other groups test exact replay versus a different raw hash at the same boundary; Unicode/NUL/case-separated destinations; original-record integrity scope; real committed write with a lost response; equal content through two real source engines; actual SQLite commit contention/rollback; read snapshots during external corruption; three competing processes; mixed conflict rollback; indexed query plans; and cancellation between destination commit and source ack.

## Premise Inventory

### P1 — Confirmation depends on the fixed original input

**Premise:** canonical immutable member rows plus a scoped marker allow exact confirmation independently of future post size, without trusting the marker alone.
**First dependent step:** receiver steps1–2, with consumers/docs in3–4.
**Waste if false:** normalization, confirmation API and recovery guidance would need another design; increasing limits would not close the contract.
**Test scheduled at:** mandatory complete prebuild before adoption, permanent suite42, and this fresh review.
**Cheapest earlier test:** actual accept→growth→reopen→confirm at unchanged byte/member bounds, forbidding assembly/view/stat calls and DML. Already performed before adoption; fresh probe groups additionally separate same records under a new raw hash, integrity limited to original records, and interleaved overlapping partitions.
**Coverage/result:** permanent small-byte/default16MiB/multi-post-growth failures now pass. Fresh cap5096 case rejects a different input hash as new work while exact accepted input confirms unchanged.576 guarded confirmations succeed after random overlap/growth. Changed original records refuse; corruption outside the original input does not incorrectly become a dependency of its confirmation. No fake receiver/storage result supplies this behavior.

### P2 — Destination and source obligations stay separate

**Premise:** successful None-return acceptance can support both existing source protocols without treating a post revision or destination marker as a source receipt.
**First dependent step:**2/3.
**Waste if false:** caller integration and acknowledgment guidance would change.
**Test scheduled at:** prebuild with real daily/backfill engines; permanent tests; fresh equal-content and cancellation histories.
**Cheapest earlier test:** actual SQLite-backed engines prepare the same content, store it once, then settle each original receipt independently. Executed now; both source reads remain distinct, one destination marker covers identical content, and acknowledging daily does not move backfill.
**Coverage/result:** PASS. Lost receiver commit response and cancellation after a real receiver commit leave daily cursor0/pending intact; exact normal replay settles to1 without another source read. Source replies are synthetic SDK-derived observations, not live Telegram evidence. The explicit cancellation checkpoint models cancellation before the caller sends ack; it does not claim to qualify every internal source-store cancellation interleaving, whose implementation is unchanged.

### P3 — SQLite supplies the required local transaction/snapshot behavior

**Premise:** exact-key indexed reads, scoped records/markers and transaction boundaries prevent partial acceptance or stale materialized views, and uncertain success can be confirmed.
**First dependent step:**1.
**Waste if false:** receiver storage/read protocol would change.
**Test scheduled at:** full prebuild and new actual SQLite probes.
**Cheapest earlier test:** hold a real read transaction so writer commit fails; start competing processes; mutate a WAL database between metadata and payload reads. All executed.
**Coverage/result:** PASS. Busy commit rolls back new member/marker and succeeds after lock release. Three barrier-synchronized processes report successful transaction changes `[0, 0, 51]`:50 original rows and one marker exactly once. A view sees its consistent old snapshot during external corruption; next view and confirmation refuse. EXPLAIN QUERY PLAN uses indexed SEARCH for original-member, post and marker lookups. Six distinct destination names, including composed/decomposed Unicode and an embedded NUL, remain separate. Prior schema2/v1/index/collation qualification is retained. Actual SQLite operations provide the observations; injected exceptions exercise uncertainty rather than simulate successful durability. Physical power loss and arbitrary external rollback repair are outside the documented contract.

### P4 — Post identity preserves observations without claiming unseen membership

**Premise:** the pure format preserves supplied records/captions and chat-qualified identity across partitions without changing raw source state.
**First dependent step:**original core step1, unchanged by revision4.
**Waste if false:** public derived format would change.
**Test scheduled at:** original actual SDK prebuild,57-case candidate, and fresh mixed histories.
**Cheapest earlier test:** compare accumulated receiver content to one-shot actual core output and independent raw row/marker counts across chats, destinations and orderings. Executed; all18 histories retain48 distinct members each and equal canonical post bytes.
**Coverage/result:** PASS. The core remains byte-identical to the first reviewed version and is covered by SDK serialization/iteration/media tests. This does not qualify global album completeness; the feature deliberately does not infer it. No untested vendor completeness behavior is a premise of the shipped API.

## Restart Check

| Observed failure | Established mechanism | Response and observed result |
|---|---|---|
| First small-byte acceptance could strand exact retry | Rebuilding charged raw+prior+output before marker recognition | Separate indexed original-record confirmation; permanent boundary test and fresh5096-byte/hash control pass |
| Default16MiB accepted1300-message input failed on retry | Same additional prior charge at the default policy | Permanent default-limit regression passes; immutable confirmation has no post-wide cost |
| Old multi-post replay failed after album growth | Return content grew past original aggregate member cap | None-return confirmation; separate bounded view; permanent later larger-policy test and fresh randomized growth pass |
| Raised limits were lost on reload in the original plan | Receiver load used defaults | Explicit selected policy on view/assembly;10001-member test retained; stricter view policy remains an intentional refusal |
| Implementation verification found case-insensitive collection aliasing | SQLite predicates inherited column NOCASE despite BINARY indexes | Explicit BINARY comparisons; permanent foreign-column-collation test and fresh namespace/query-plan controls pass |

Every failure has an established mechanism and matching response. There is no evidence that this revision rebuilt the wrong layer. This round does not add a rejection, so §7.4's second-rejection return to description/traverse is not triggered.

## Inherited Lessons

| Lesson | Satisfying sequence or evidence |
|---|---|
| Loadable views do not imply retryable acceptance | Contract split before r3/r4; three old counterexamples mandatory before adoption; fresh new-hash control keeps the distinction honest |
| A marker alone is not data integrity | Original-row comparisons precede successful confirmation; fresh corrupted-original refusal and zero-write guards |
| More targeted probes do not replace full composition | Complete57-case candidate and13 related suites/demo passed before adoption; final830 checks precede this review |
| Available raw data is not source acknowledgment authority | Original source receipts retained; equal-content two-engine probe settles independently; no partial-result receipt invented |
| More reads cannot establish complete membership | No new fetch/lookahead; all album observations remain unconfirmed; source call counts unchanged on replay |
| Scope and limits must remain explicit | Pure core unchanged; new admission, original-input confirmation and view policy documented/tested separately |

## Fresh execution evidence

Command from the archive worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python \
  devdocs/work/29-album-assembly/pr-probes-r2.py /private/tmp/tgdata-29-album-pr
```

Actual output is preserved in pr-probes-r2.txt and structured pr-probes-r2.json. All12 groups PASS, Python3.11.10, product head7a49bd9. Socket connections are forbidden in parent and child processes. Source hashes for all93 Python files match before and after execution.

Selected observations:

```text
mixed_histories: seeds18, accept_calls576, zero_write_confirmations576
new_hash_boundary: cap5096, new_hash_refused=true, original_confirmed=true
equal_content_two_sources: source_reads2, independent_original_receipts2, receiver_markers1
actual_busy_commit: partial_data_or_marker=false, retry_succeeds=true
process_competition: actual_changes[0,0,51], members50, markers1
cancellation_after_commit: cancellation_preserved=true, source_reads1, recovery_cursor1
```

Two initial probe-harness errors were retained as pr-probes-r2-harness-initial.py/.json/.txt. The backfill status call incorrectly passed a chat integer instead of its required BackfillRunRef. The cross-process harness retried accept contention but not constructor contention, despite documented timeout0 behavior. Corrected the probe to use the original delivery's run reference and retry known SQLite lock refusal at opening, then synchronize all opened processes on a barrier. No product code or expected safety property changed. The entire corrected12-group run passed; failed initial results are not hidden or counted as code findings.

## Architecture, compatibility and limits of this review

No additional runtime framework, source lifecycle, cache or generic coordinator is introduced. Canonical rows replace embedded mutable post snapshots; the existing SQLite example owns persistence and the library core remains pure. Adding a second authoritative snapshot/archive would increase state without addressing another observed requirement. Schema2 and None-return acceptance are explicit changes to an unmerged example, with strict known-v1 refusal; no public raw/progress format or package version changes.

Public exports are additive and package discovery includes the new module. All89 pre-existing Python files except __init__ remain unchanged against dev; account health, budgets, source/pool/worker behavior and dependencies are not rewritten. Pure assembly refuses conflicting observations rather than inventing an edit policy. README's in-memory illustration is expressly for a new collection; durable guidance uses commit-before-ack and warns against resetting known lost state.

The existing exact-tree regression evidence remains830 executed offline checks across29 suites,6 demos and3 explicit live skips, with57 suite42 cases. This review did not unnecessarily rerun all unchanged suites; fresh93-source hash parity links that evidence to this exact PR head. Compile/Python3.7 grammar checks are inherited; native3.7 execution is not claimed. Neither these checks nor synthetic source fixtures establish live Telegram completeness, production deployment, distributed ownership, storage repair or hardware durability. Those are not promises of this diff and are not invented findings.

## Findings and Phase3 selection

No High, Medium or Low code finding was identified. Phase2 is complete. Phase3 was then performed: with no mitigation proposals, the selection set is empty; no phase was skipped and no tier was selected merely to add work. No product edits were made during review.

The original first rejection is preserved in pr-critic_r1.md, its prompt in pr-dynamic-critic-prompt_r1.md, and its eight original histories in pr-probes.*. The current plan critic remains critic.md. This review's prompt is pr-dynamic-critic-prompt.md; its actual evidence is pr-probes-r2.*.

**Next prerequisite:** verify CONTRIBUTING §9 model/effort before a merge decision. It remains unknown, is not a code finding, and is not certified by this pass. Commit/post this result, update #29's6–7 gates with the actual outcomes, keep PR35 draft, and wait for merge authorization. No merge, release or running ScrapeOps change is part of this review.
