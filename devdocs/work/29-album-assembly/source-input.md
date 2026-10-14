# Source request — issue #29

## User invocation

$task-impl |  |  |  |
|---|---|---|
| #29 — Album assembly across batches | P2 | Not started; ready for qualification |

Follow-up: continue

## Issue captured at task start

Requested on 2026-10-14 for the tgdata backlog. The maintainer authorized creating GitHub issues; implementation has not started.

**Request.** Telegram albums should be available as one logical post with their captions and media, even when their members arrive in different SDK pages or bounded message batches. This is reusable Telegram behavior currently handled in ScrapeOps. Consumers should not accidentally process the caption and the remaining album photos as unrelated posts.

**Current foundation.** #6 provides immutable MessageBatch v1 records with `grouped_id`. Its [published contract](https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/message_batch_v1.md) explicitly permits albums to cross batch boundaries and does not promise complete albums. [Telegram documents the grouping field](https://core.telegram.org/constructor/message). This is a new capability, not missing work from #6.

**Requested behavior and boundaries.**

- Assemble members using the canonical chat ID and Telegram album ID. Preserve all original message IDs, captions, ordering and media references, including albums with more than one nonempty caption.
- Retain an unfinished album across calls. Define its behavior when a batch limit, fixed historical window, exhausted budget, cancellation or source failure interrupts assembly.
- Make incomplete or unconfirmed membership explicit. Do not exceed read allowances or leave the requested time window merely to claim a complete album.
- Preserve raw MessageBatch v1 records, hashes, continuation and acknowledgment semantics. Qualify a derived post representation or explicitly version any public format change before implementation.
- Keep the library generic: classification, contact extraction, listing rules and uploads remain consumer concerns.

**Questions for qualification.** Decide whether the public capability is an assembler, optional whole-album delivery, or both; how completion is established; and how retained members survive restart, replay and lost acknowledgment without being emitted twice or discarded. Bound retained state and any lookahead. A batch boundary or temporary end of visible history alone must not silently become proof of completeness.

Useful acceptance examples include an album spanning two batches, a caption outside the first batch, multiple captions, identical album IDs in different chats, interruption followed by restart/replay, and an album intersecting a fixed window or read allowance. Include real Telegram validation of the chosen completeness assumptions before depending on them.

**Reference consumer.** ScrapeOps `scrapeOps/engine/collapse.py` at `dc49db8` is a useful fixture source. Its current helper only groups the supplied rows, keys albums without the chat ID, and selects one caption; these assumptions should be qualified rather than copied unchanged. Consumer migration is later work after the library contract and adapter parity are verified.

**Related:** #6 (raw batches), #18/#19 (daily/backfill delivery), and #30 (optional photo-trail folding, dependent on this foundation). Album membership comes from Telegram; photo-trail attachment requires a distinct heuristic.

---
## Pipeline status

**Direction:** open to implement — ready for qualification; filing accepts no implementation design.
**Priority:** P2 — prevents fragmented posts in daily scraping; provisional until qualification.
**Path:** feature — labelled `enhancement`.
**Weight:** not decided yet; triage must assess it.
**Branch:** none yet.
**Docs:** none yet.
**Session warmth (step W):** not formally recorded for an implementation task. Filing inspected current dev at `f927496`, the batch/progress contracts, the ScrapeOps helper and all existing issue titles; no pipeline artifact has been completed.

- [ ] **T — triage** — `/surfacing` → `triage.md`, then set weight.
- [ ] **0 — traverse** — when §5 requires it; otherwise record why it is unnecessary.
- [ ] **1 — desc** — qualify this request through `/task-desc` and preserve the original request.
- [ ] **2 — plan** — `/task-plan` → `plan.md`.
- [ ] **3 — critic** — `/critic-d` → `critic.md`.
- [ ] **4 — fold** — incorporate selected High/Medium mitigations into the plan.
- [ ] **5 — implement** — code, tests and documentation.
- [ ] **6 — merge gate** — `merge-check.md`, then PR.
- [ ] **7 — PR critic** — fresh `/critic-d` on the diff, committed and posted.

**To continue:** read CONTRIBUTING.md and PROJECT_SPECIFICS.md, establish session warmth, and begin at triage. No branch, implementation, PR or release is authorized by this filing.


