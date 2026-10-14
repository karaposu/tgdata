# Original issue #30 request

Captured before pipeline edits. Source: https://github.com/karaposu/tgdata/issues/30

Requested on 2026-10-14 for the tgdata backlog. The maintainer authorized creating GitHub issues; implementation has not started.

**Original request.**

> I think this can be still like an optional uh, thing in tgdata, you know, bc it is common ppl sending msg and then images etc. so it is generic enough i would say , dont u think?

**Requested capability.** Provide an optional helper that attaches a sender's loose, textless photos to their preceding logical post. A text post or Telegram album followed by additional photos is the motivating case. ScrapeOps already has a heuristic for this common posting pattern; tgdata could provide it generically so consumers do not each rebuild it.

**Proposed first scope, to qualify before implementation.**

- Off by default. Consumers explicitly enable it and select a time window; the existing consumer's 30-second setting is a starting point, not a Telegram guarantee.
- Same chat and positively identified same sender only. Anonymous or unknown authors must not be merged on a shared absence or channel identity.
- Attach actual photo-only follow-ups. A new message with text ends that sender's trail. Photos first, followed by text, remain outside the first delivery.
- Measure the gap from the previous attached photo; reject out-of-order or invalid timestamps and bound chain length, duration and retained state. Qualify how other senders' interleaved messages affect the trail; the existing consumer allows them.
- Reject replies whose relationship to the anchor cannot be established. Current raw batches contain the replied-to ID, not its author's identity. Do not silently perform additional Telegram requests to infer ownership.
- Preserve original messages, captions and media. Expose member IDs and observable heuristic provenance/counts with explicit units; avoid mutating caller-owned raw records or changing their hashes.

**Across batches and restarts.** An unfinished tail must survive a batch boundary without a premature fold or finalization. Qualification must specify checkpoints, replay/idempotency, acknowledgment coupling, end-of-history and quiet-window behavior, interruption, budget/window boundaries and restart. Grouping is an inference about intent and can be wrong; consumers need enough provenance to inspect or undo it.

**Reference consumer and corrections.** ScrapeOps `scrapeOps/engine/collapse.py` at `dc49db8` and its `tests/test_engine_smoke.py` provide useful compatibility fixtures: an album plus a loose photo, a following caption, interleaved senders, a long gap, a foreign reply and missing sender IDs. Despite its name, the current helper accepts any media-only post, mutates anchors, and works only on the supplied list. Its reply check accepts the anchor/member IDs, not arbitrary messages from the same author. These details are evidence to qualify, not a finished generic contract. Add photo-type, timestamp, bounds, cross-batch and restart/replay coverage before migration.

**Dependency:** #29 — establish deterministic album assembly and its post/provenance contract first, then qualify this optional heuristic on that foundation. #6 supplies raw messages; #18/#19 supply durable delivery. Classification, seeker-burst merging and business rules remain consumer work. Removing ScrapeOps's helper is a later adoption step after parity is demonstrated.

---
## Pipeline status

**Direction:** blocked — #29 must establish the album/post assembly contract first.
**Priority:** P3 — optional consumer convenience for the backlog; provisional until qualification.
**Path:** feature — labelled `enhancement`.
**Weight:** not decided yet; triage must assess it.
**Branch:** none yet.
**Docs:** none yet.
**Session warmth (step W):** not formally recorded for an implementation task. Filing inspected the current batch contract and ScrapeOps helper/fixtures; no pipeline artifact has been completed.

- [ ] **T — triage** — `/surfacing` → `triage.md`, then set weight.
- [ ] **0 — traverse** — when §5 requires it; otherwise record why it is unnecessary.
- [ ] **1 — desc** — qualify this request through `/task-desc` and preserve the original request.
- [ ] **2 — plan** — `/task-plan` → `plan.md`.
- [ ] **3 — critic** — `/critic-d` → `critic.md`.
- [ ] **4 — fold** — incorporate selected High/Medium mitigations into the plan.
- [ ] **5 — implement** — code, tests and documentation.
- [ ] **6 — merge gate** — `merge-check.md`, then PR.
- [ ] **7 — PR critic** — fresh `/critic-d` on the diff, committed and posted.

**To continue:** resolve the album dependency, read CONTRIBUTING.md and PROJECT_SPECIFICS.md, establish session warmth, and begin at triage. No branch, implementation, PR or consumer migration is authorized by this filing.

