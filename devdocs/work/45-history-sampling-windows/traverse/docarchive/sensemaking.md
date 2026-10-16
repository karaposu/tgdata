---
model: gpt-6-astra
effort: xhigh
---
# Sensemaking — #45

## User Input
_branch.md: qualify #45 history sampling across days over all four considered articulations before implementation.

## SV1 — baseline
A native helper should fix the consumer's599/300 stride defect and provide reading material distributed across days. It initially appears to be an arithmetic selection added to the existing bounded reader.

## Phase 1 — cognitive anchors
**Constraints:** fixed aware time bounds; bounded source work and selected output; preserved identities/text/dates; reproducibility on identical captured input/configuration; existing ownership/budget/heartbeat and raw progress compatibility. These come from issue45, not a default analytics methodology.
**Insights:** selecting evenly from a newest-only capped capture cannot recover older days; #44's value deliberately omits text; missing source observations and intentionally omitted sample members are different; empty source responses still cost requests even when they return zero messages.
**Structural points:** acquisition chooses what can be observed; selection chooses which captured observations to show; replay needs the captured content or a retained authoritative reference to it; album/trail helpers describe observed originals and cannot prove global membership.
**Foundational principles:** no sample implies a population census; same captured facts plus the same selection decisions should produce the same IDs; no omitted record advances a source receipt; text/policy callback failure must not become a Telegram account verdict.
**Meaning nodes:** requested day, captured observation, eligible message, selected message, incomplete bucket, observed album. These are domain/user terms, not a new scheduler or storage abstraction.
H4/H5 checks: “sampling across days” is not just a new name for taking every Nth row.599/300 illustrates temporal concentration, not the entire failure class.

## SV2 — anchor-informed understanding
Acquisition distribution is part of sampling usefulness. A bounded selector alone cannot promise coverage of dates absent from its input. The contract needs to distinguish source coverage, local eligibility and output omission, and must make the captured input available for reproducibility without promising unchanged Telegram queries.

## Phase 2 — perspectives
| Perspective | Anchor or uncomfortable consequence |
|---|---|
| Technical | GetHistory permits independent before-date seeks; raw page types/placeholders expose evidence the iterator discards. Reusing batch envelopes would also import cursor semantics. |
| Human | A sample from one busy recent day is poor reading material for a two-week request even when its incomplete flag is honest. A sparse older day should be able to contribute. |
| Strategic | Capture/reselection can support later analysis without a permanent archive; #46 discovery state remains a different operation. |
| Risk/failure | A live predicate may have side effects or fail after source work; replaying arbitrary code does not establish identical eligibility. Partial captured content must remain separate from selected output. |
| Resource | Many empty days can produce many requests while returning zero messages. A message-count bound alone does not bound per-day source invocation cost. |
| Ethical/systemic | Day-balanced examples are intentionally disproportionate to traffic; they must not imply frequency estimates or representative demographic/content percentages. |
| Definitional/internal | A complete capture may yield a deliberately small sample. A complete selection from a partial capture is not a complete history observation. Album membership remains unconfirmed even when all captured members are selected. |
| Calibration/phase | No evidence supports a universal ideal sample size or statistically representative strategy. A named deterministic reading heuristic with explicit limits is testable now; live server visibility remains conditional. |

Frame-exit completeness fires for inherited “capture”, “complete” and “post” meanings across these layers. Existence enumeration: raw captured records, durable sync/backfill deliveries, caller-retained pool captures, activity observations, album originals and inferred photo-trail groups. Role assessment: only captured content/evidence is needed here; durable receipts remain owned by their existing operations. Strong counter: sampling should reuse sync acknowledgments to avoid repeated reads. Structural test: deliberate omission is not durable acceptance of every source record, so a sampling decision cannot authorize that acknowledgment. Scope exclusion survives. Residual: local retention is still necessary for replay; locate it in a portable caller-owned value, not a new database/scheduler. “Post” retains its observed-membership meaning; sparse sampling cannot fabricate full album or inferred trail context.

H1/H2/H3/H7 checks: variants cover both acquisition and selection, raw and assembled units, local and live behavior. The question's goal is useful bounded reading, not unbiased statistical estimation. No calibration on live traffic distributions is claimed.

## SV3 — multi-perspective understanding
This is a bounded acquisition-and-selection contract. It has independent cost, source-evidence and selection-evidence dimensions. The strongest new risks are starving older days, unbounded empty-day requests, callback nondeterminism and accidental interpretation of sparse samples as complete posts or receipts.

## Phase 3 — ambiguity collapse
Entries state strongest counter, structural test, confidence, resolution/fixed/excluded meaning, dependencies and model change.

1. **Spread across days.** Counter: collect newest messages once, then divide captured days equally. Test: with more recent-day traffic than the source cap, no older candidate ever enters the selector; arithmetic cannot create it. HIGH. Fix acquisition breadth as a first-class obligation for a native source sampler; exclude promising period distribution from a newest-only prefix. Source scheduling and per-day evidence depend on this. Selection alone is no longer the whole feature.
2. **Bounded source work.** Counter: returned-message count alone bounds expense. Test:100 empty day queries return0 messages; they still create100 RPCs. HIGH. Fix an explicit request-work bound in addition to returned/retained message bounds, or an equivalent conservative requested-slot bound. Exclude unlimited retry/bucket loops justified by zero returns. Admission and failure accounting depend on this; cost has more than one unit.
3. **Reproducible.** Counter: same dates and seed should reproduce a fresh query. Test: deleted/edited/newly visible messages change the candidate set and ranking. HIGH. Fix identical captured content plus normalized policy/eligibility as the replay domain; exclude stable fresh-query promises. Serialization and pure selection depend on it; source query identity differs from observation identity.
4. **Captured input.** Counter: the returned selected IDs alone suffice for reselection. Test: omitted text cannot be tested against a later caller eligibility rule; additional IDs/counters cannot reconstruct it. HIGH. Fix access to portable captured content for the replay path; leave whether via separate API or retained result component open. Exclude claiming reselection from only selected rows. Value/API design depends on this.
5. **Eligibility.** Counter: a predicate object is the same configuration, so rerunning it is deterministic. Test: it may read a clock, mutable external state or an LLM. HIGH. Fix explicit decisions as replay input; a predicate may be convenience only with its outcomes captured, or run outside the library over retained content. Exclude reusing its name/identity as evidence of determinism. Failure isolation and portable policy follow from this. Code and decisions become distinct.
6. **Sampling unit.** Counter: raw messages and human posts are interchangeable. Test: one album has several message IDs/captions; photo trails additionally infer intent. HIGH for distinction, LOW for initial unit choice. Fix explicit unit and known omission/membership disclosure; exclude silently claiming logical posts from arbitrary raw rows. Keep raw sampling and atomic observed-post sampling as design alternatives; do not change #29/#30 semantics.
7. **Complete.** Counter: filling sample_size proves success for every requested date. Test: selected output can be full while some buckets are unvisited or capped; a complete source capture can also have many deliberate omissions. HIGH. Fix separate source/bucket coverage and selection counts/omissions; exclude one overloaded success flag. Rates/representativeness claims remain out. Runtime coverage must be decided from actual request/page evidence, not quota satisfaction.
8. **Day fairness.** Counter: proportional-to-traffic allocation is the obvious default. Test: the consumer asks for reading across days, and proportional allocation lets a busy day consume nearly every slot. HIGH against treating the default as a universal statistical rule; LOW among precise deterministic reading heuristics. Fix explicit allocation/tie rules and sparse-day redistribution; keep exact strategy for innovation. Day boundaries use fixed UTC initially to match existing windows; callers retain dates for other analysis.
9. **Reuse.** Counter: #44's result can simply be sampled. Test: ActivityMessage contains no text and introduces engagement populations irrelevant to content selection. HIGH against direct result reuse; LOW between a small shared source seam and a separate bounded source path. Fix reuse of established owner/budget/liveness and source evidence rules, not mandatory reuse of the summary value. No broad engine rewrite is yet justified.
10. **599/300 scope.** Counter: adjust stride calculation and the task is done. Test: even perfect rank spacing across599 rows cannot repair missing older days or explain service/album omissions. HIGH. Fix the broader temporal selection contract; exclude a local arithmetic-only patch as full delivery. The example remains a mandatory acceptance case, not an entire model.

All load-bearing concepts were tested against external-default and user-language concerns. Requested-day membership is determined by exact UTC half-open bounds; source completion by page/boundary evidence; eligibility by explicit row decisions; sample omissions by comparison to the captured eligible population. No runtime classification is left merely named. No earlier Sensemaking artifact exists for this inquiry.

## SV4 — clarified understanding
The native acquisition path must give dates a deliberate opportunity under finite work limits; the local selector must be reproducible over known captured input. Raw source evidence, eligibility decisions and selected output remain separate facts. Atomic post selection is still a design option; post membership cannot become globally complete by sampling.

## Phase 4 / SV5 — reduced freedom
Fixed: explicit closed publication window, UTC days, finite source request/message work and output, retained content for replay, deterministic decisions, qualified coverage, no progress/ack mutation and existing verified lifecycle. Eliminated: newest-prefix-as-period-sample, returned-count-only work bound, fresh-query reproducibility, predicate identity as deterministic input, inferred complete albums and archive/scheduler requirements. Remaining choices: public capture/reselection surface, source day allocation, rank strategy, initial raw/post unit, and the smallest source reuse seam. These are bounded implementation design choices rather than external blockers.

## Phase 5 / SV6 — stabilized model
Treat sampling as two explicit transformations: obtain bounded dated content/evidence across requested days, then select from that captured material under a versioned deterministic policy. Preserve enough input and decisions for exact local reselection, and report what was never observed separately from what was deliberately omitted. Reuse the current verified account/admission/cleanup foundation; do not let sampling create receipts or silently reinterpret albums/trails.

SV1's stride helper has become a precise acquisition/selection contract because missing days and replay inputs cannot be repaired by arithmetic. The model settles without layered exceptions: the independent evidence dimensions explain the difficult cases. Telemetry: five anchor types, eight perspectives plus frame-exit assessment,10 ambiguities resolved/narrowed, five explicit design choices retained. Six failure modes checked; no status-quo protection or unsupported statistical claim. Manual structure: SV1–6 and all required phases present,7/7. PROCEED to Decomposition.
