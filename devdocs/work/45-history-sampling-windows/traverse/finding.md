---
status: active
model: gpt-6-astra
effort: xhigh
---
# Finding: reproducible history samples across days

## Question
How should #45 provide bounded message samples spread across a requested period, while keeping the original content, explaining incomplete reads and preserving the library's existing account and progress contracts?

## Finding Summary
- Provide two actions: capture bounded content across UTC days, then select locally from that immutable capture.
- Give unresolved days a turn before reading another page from the same busy day.
- Bound both returned source messages and logical history requests. Empty responses still consume requests.
- Select raw messages using equal-day allocation and deterministic rank spacing. A small sample is reading material, not a representative population estimate.
- Make topic eligibility an explicit set of captured message IDs. Caller predicates run outside live source work.
- Report source gaps separately from deliberate sample omissions, including known omitted album members.
- Share only raw page validation with #44; preserve the existing activity, batch, album, trail and acknowledgment contracts.
- Prove the complete SDK/owner/budget/capture composition before product implementation.

## Finding
The downstream audit wants roughly300 messages across the requested days. Its current stride calculation takes only the newest300 when599 candidates exist. Correcting that arithmetic helps, but does not solve the whole problem: if a single busy recent day exhausts the source cap, older days never reach the selector.

The native feature therefore needs deliberate acquisition across days. `TgData.capture_group_history` should return a `HistoryCapture` containing bounded original content and source evidence. The caller can keep that value in memory or save its portable JSON. tgdata does not create a permanent archive or a new progress store.

`capture.sample(size=300, eligible_ids=None)` should be a pure local operation returning a separate `HistorySample`. The sample contains selected bodies and policy/coverage/omission metadata, rather than secretly carrying every captured body. A retained capture can be loaded and selected again without another Telegram request.

This two-action boundary makes reproducibility precise. The same captured content and normalized selection decisions produce the same selected IDs. Repeating a Telegram query after edits, deletion or changed visibility is a new observation and may produce a different sample.

Use explicit timezone-aware start/end dates, normalized to a fixed UTC interval that includes start and excludes end. Require the end not to be in the future. Split the interval into its intersecting UTC calendar days, retaining the exact exposure of partial boundary days.

Read newest first within each day, using the source's before-date seek and exclusive message-ID continuation. In each round, give each unresolved day at most one page. Request limits fit both the remaining message capacity and a fair share for the remaining visits in that round, with at most100 slots per page. Quiet days release capacity for later rounds instead of permanently stranding it.

When the remaining request/message capacity cannot give every day a turn, visit an evenly spaced subset of the active days. This cannot guarantee that every requested day contributes, but it avoids silently choosing only the newest dates. All unvisited and unfinished days remain visible in the result.

A separate logical history-request cap is necessary. A returned-message cap does not stop hundreds of queries over empty days. Existing account allowance remains a separate authority: it reserves the actual request bound before send and may refuse it. No quota is created, reset or silently enlarged.

Use the raw page evidence already established by #44: response shape, matching peer, monotone IDs/dates, empty placeholders and genuine end/start witnesses. A short nonempty slice is not an end witness. Validate a page before accepting its content. A message ID repeated across day captures with conflicting placement/content must refuse rather than silently replace an earlier observation.

Keep source completeness distinct from selection completeness. An unavailable placeholder leaves its day incomplete because its date/content cannot be established. A capped or unvisited day cannot become complete because the requested sample size was filled. Conversely, a complete source capture may intentionally omit most messages from its sample.

The first selection policy uses ordinary raw messages, with services excluded from eligibility. Divide the requested output fairly among nonempty eligible days, redistributing spare capacity from sparse days. Spread remainder choices across days rather than always favoring the first date. Within a day, order by publication date then numeric ID and choose evenly spaced ranks.

For k selections from n ordered candidates, when k is at least2 select ranks `floor(j*(n-1)/(k-1))` for j from0 through k-1. For one selection use `floor((n-1)/2)`. The599/300 example then includes ranks0 and598, not just0 through299. A local probe checked size, uniqueness and bounds for3160 n/k combinations; this is arithmetic evidence, not proof of source behavior.

The selector should accept explicit eligible IDs belonging to ordinary messages in the capture. None means all ordinary captured messages; an empty set means none. A caller can run any topic predicate over retained text and pass the resulting IDs. If that predicate fails, the capture is still available and no live client is held. The library does not claim that a predicate object's identity makes its output deterministic.

Raw-message units must be explicit. Albums retain their original grouping IDs, and the sample reports which captured members of a selected album were included or omitted. It must not describe arbitrary selected members as a complete logical post. Global album membership remains unconfirmed, even when all captured members are selected. Do not run photo-trail inference on sparse sample rows; that inference depends on original context which sampling may have omitted.

Reuse the existing raw-record serializer and validator where useful, without importing the MessageBatch envelope's cursor meaning. The new capture/sample values have no acknowledgment or continuation authority. Sampling must never call daily/backfill prepare or acknowledge operations.

The shared source seam should be small: response/vector validation, peer/ID/date order, unknown-slot accounting and boundary evidence, with separate internal projections for activity counters and sampled content. There is no reason to replace the existing batch or progress engines. Preserve #44 behavior with parity tests when extracting that common code.

Captured values need bounded, strict reload validation. A hash identifies serialized observations; it does not prove they came from Telegram. Derived totals/coverage must agree with bucket facts, records must agree with their day/group, and duplicate/conflicting IDs must refuse. A missing or corrupt input is an error, never an instruction to create a new empty capture.

Source failures and cancellation propagate with their original outcome. When possible, attach accepted capture evidence to the error after target resolution. Cleanup preserves the existing cancellation rules, including the documented limit that later cleanup cancellation can supersede exception metadata. This feature adds no durable delivery promise.

## Next Actions
### MUST
- **What:** Qualify the description and exact schema/algorithm/limits in a five-section description and implementation plan. **Who:** task-impl. **Gate:** this inquiry is concluded. **Why:** make the source/selection boundaries and acceptance cases reviewable.
- **What:** Run a combined prebuild on real SDK/codec/SQLite/verified-operation components, including day seeks, shared validation parity, content capture, replay, quota and cancellation. **Who:** task-impl's plan critic/experiment workflow. **Gate:** before any product step. **Why:** reject an impossible composition before implementation.
- **What:** Implement and verify the qualified source and pure-selection contracts. **Who:** task-impl. **Gate:** selected plan mitigations folded and combined prebuild passed. **Why:** deliver useful native sampling without changing current readers or progress.
### COULD
- **What:** Compare a bounded sample against a real group's visible dated content. **Who:** verification. **Gate:** exclusive session ownership and authoritative allowance established. **Why:** strengthen live visibility evidence. **Depends-on:** MUST “Implement and verify”; GATED until the public path exists.
### DEFERRED
- **What:** Atomic observed-post sampling, alternate timezones, random/proportional strategies or a convenience predicate API. **Gate:** a concrete caller requires that separately defined unit/policy. **Why (if revived):** broaden useful sampling while preserving explicit member/cost/determinism rules.

## Reasoning
A selected-only result was rejected as the sole replay input because it cannot recover omitted text. A permanent archive was rejected because caller-owned immutable values satisfy retention without adding storage ownership and recovery.

A single newest-first window scan was rejected as the native acquisition default: one busy day can hide the rest of the period before selection begins. A pure MessageBatch helper alone was rejected for the same missing source behavior, although raw-record validation and pure local selection remain useful parts of the chosen design.

A generic scheduling engine and wholesale reader refactor were rejected because they expand compatibility risk without improving this fixed contract. The narrow shared page validator provides the actual reusable mechanism. A strategy registry was rejected because no current caller requires several competing allocation policies.

Atomic album/post sampling was rejected as the initial default because a small raw-message bound may not fit one observed album, and complete observed membership is different from complete source membership. Explicit raw units and known omission reports meet the present request; whole observed units need their own size and underfill rules.

Removing the request cap was rejected because empty days consume calls without consuming returned-message capacity. Running arbitrary predicates inside source acquisition was rejected as an implicit reproducibility promise; explicit eligible IDs preserve caller flexibility without retaining executable code.

The surviving combination makes acquisition breadth, retained evidence and pure selection independently testable. Equal-day examples are intentionally different from traffic-weighted population statistics, and the public contract must say so. Strict saved-evidence consistency, page-atomic acceptance and existing owner/cleanup policies address the composition risks without a new orchestration layer.

## Open Questions
### Blocked
Live qualification lacks established exclusive session use and an authoritative allowance. No live Telegram call was made during this inquiry. This does not block the required offline implementation.
### Monitoring
The combined prebuild must reject a mismatch between proposed shared validation and existing activity behavior, unsupported raw-record projection, skipped equal-second boundary messages, incorrect budget charging or lost primary cancellation/failure.
### Refinement Triggers
Revisit raw-unit-only selection when a caller requires whole observed posts under explicit unit/member caps. Revisit the two-action API when a concrete caller cannot retain captured input; any convenience wrapper must preserve the same evidence rather than weaken replay semantics.

Source: issue45; current batch/value, activity, album/trail, ownership/budget/heartbeat code at dev77f2f53; downstream measure.py/how_to_search.md; SDK1.45 message iterator. Full reasoning is archived in docarchive/. The route-map and concept index remain at the inquiry root.
