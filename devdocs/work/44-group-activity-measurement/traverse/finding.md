---
status: active
model: gpt-6-astra
effort: xhigh
---
# Finding: bounded group activity and engagement measurement

## Question
What should tgdata's native activity measurement mean, and what evidence is needed to make its counts trustworthy? The goal is to replace repeated application code for reading a period's history and measuring it, without changing existing message batches or synchronization progress.

## Finding Summary
- Add one bounded measurement call using the existing verified-account operation.
- Return a separate versioned value containing raw observations, statistics and coverage information.
- Count ordinary Telegram messages, with service messages reported separately. Do not fold albums or photo trails.
- Keep missing counters and unknown authors explicit. A missing view count is not a measured zero.
- Only claim complete coverage after source-end or start-boundary evidence, with no uninterpretable message slots.
- Engagement counters are observed at collection time on messages published in the requested period. They do not measure engagement earned during that period.
- Prove raw paging, budget, heartbeat and cancellation composition with real SDK components before implementing the product path.

## Finding
The motivating audit script already produces useful group statistics, but some of its shortcuts obscure their meaning. Its view average excludes zeros, its unknown senders can become one fictional author, and its history cap can make a partial sample resemble a full period. These are examples of a broader problem: a number needs a defined population and evidence about how that population was collected.

The native call should accept a group, an expected numeric account ID, explicit aware start/end datetimes, a finite maximum number of examined source messages and an optional heartbeat. Normalize dates to UTC and use a half-open publication interval: include the start, exclude the end. Require a closed interval in the past or ending at invocation time; do not claim future coverage.

Use the established temporary-client operation to verify the account and apply its existing proxy, session, device, wait, budget and cleanup policies. Resolve the group through the existing lookup path. The measurement needs no joins, media downloads, profile fetch, database or acknowledgment protocol.

Read bounded raw history pages. The SDK's high-level iterator hides empty-message placeholders and response types needed to explain coverage. Telegram documents descending history order; validate that observed IDs and dates progress consistently. Seek conservatively around the end's whole-second wire representation, filter exact dates locally, and continue by message ID so equal timestamps are not skipped.

The source cap counts every returned slot, including service messages, empty placeholders and rows outside the requested window. Request limits must fit the remaining cap. A short page is not proof of the end. A sliced/channel result that exactly fills the cap remains limited unless the same accepted page supplies a start-boundary witness. Never fetch an extra uncharged page to manufacture completion.

Validate each page before accepting its observations. Unexpected peers, repeated IDs, invalid dates/counters and non-progressing order are protocol failures. Preserve previously accepted pages on later failures, but do not let an invalid half-page contaminate the statistics. Ordinary failures keep their original type; attach partial observations best effort. Cancellation and cleanup retain the existing operation's semantics, with no promise of durable result delivery.

The result must distinguish traversal evidence from counter availability. A complete visible-history scan can still contain messages without view or reaction counters. An empty placeholder makes message coverage incomplete because its date and contents cannot be established. Source counts are not sufficient completion evidence.

For ordinary messages, preserve message ID, publication date, observation time, sender kind/ID, album ID and optional views, reactions, forwards and replies. Preserve service observations separately. Distinct visible user IDs and channel-sender IDs are separate populations; unknown authors are counted as unknown messages. Do not infer unique people or readers.

Compute deterministic descriptive statistics from the retained observations: ordinary/service counts, distinct author populations, latest observed ordinary message, UTC daily counts and known-counter distributions. Every counter distribution names its known and missing populations and its sum, mean, median, minimum and maximum. With views `[0, unknown, 10]`, the known population has two values, sum10 and mean5.

UTC daily buckets include their exact overlap with the requested period. A rolling seven-day interval may touch eight calendar dates; that does not justify dividing daily unique-author counts by seven. Offer a plainly defined complete-window message rate per24 hours, with its duration denominator; leave it unavailable when coverage is incomplete. Do not add engagement scores or ambiguous average daily unique-user scalars.

Completeness refers to account-visible history observed during the collection interval. Multiple source requests cannot freeze concurrent edits, deletions, access changes or counter updates. The result reports collection times and never claims an atomic historical snapshot or recovery of deleted history.

## Next Actions
### MUST
- **What:** Write the qualified description and implementation plan with the value schema and stop/failure rules above. **Who:** task-impl. **Gate:** this inquiry is complete. **Why:** make caller behavior and acceptance cases reviewable before product edits.
- **What:** Run a combined real-component prebuild for source paging, half-open bounds, verified owner, budget, heartbeat, partial failure and cancellation. **Who:** task-impl plan/critic workflow. **Gate:** before product implementation. **Why:** a plausible contract is not proof that the SDK composition works.
- **What:** Implement, document and verify the selected contract against the current supported offline baseline. **Who:** task-impl. **Gate:** prebuild passes. **Why:** deliver the requested native feature with compatibility evidence.
### COULD
- **What:** Run bounded read-only comparison on an existing group. **Who:** implementation verification. **Gate:** an exclusive usable session and authoritative allowance are established. **Why:** add real visibility evidence. **Depends-on:** MUST “Implement, document and verify”; GATED until that work provides the public path.
### DEFERRED
- **What:** Public generic page streams, configurable analytics modes, persistent observations and sampling. **Gate:** a concrete additional caller requires their independent contract, including issue45 sampling. **Why (if revived):** reuse beyond the current fixed measurement surface.

## Reasoning
An unversioned extension to MessageBatch v1 was rejected because its exact-key validation and replay contracts do not permit extra counters. A v2 migration is possible but unnecessary here. Separate measurement values preserve compatibility and carry evidence the existing batch does not contain.

A caller-only summarizer and the existing iterator were rejected as the complete feature: neither supplies transparent source coverage. Internal pure arithmetic remains useful and keeps the result reproducible. A public raw-page stream was rejected for this delivery because it exposes lifetime and paging obligations that callers should not need.

A general analytics schema, formula language and configurable unit/timezone matrix were rejected because they enlarge the semantic surface without solving the identified problem. Fixed UTC raw-message statistics meet the request and remain reanalyzable through portable rows. Raw-only output was also rejected: it would omit the native reusable statistics the user requested.

A resumable measurement job engine and unlimited census were rejected because they add lifecycle and cost without producing an atomic snapshot. Reusing a shared persistent client was rejected because it risks the stale-account and mutable-policy problems already addressed by verified operations.

The selected assembly survives those objections: bounded raw capture retains evidence, an immutable value prevents drift, pure math explains populations, and existing operations preserve ownership. The useful parts of the remaining alternatives survive as explicit missingness, finite source work, observation timestamps, portable IDs and a narrow API. Page-atomic validation was retained to prevent malformed later replies from corrupting prior evidence.

## Open Questions
### Blocked
Live qualification requires establishing exclusive session use and a shared authoritative allowance. Local session filenames alone do not establish either. No live Telegram request was made during this inquiry.
### Refinement Triggers
Revisit the direct collector if Telethon exposes equivalent page/placeholder/end evidence without losing budget interception. Revisit UTC-only or raw-message-only statistics when a concrete caller requests a separately defined local-calendar or assembled-post population. Revisit schema portability when a consumer needs validated deserialization, rather than introducing it speculatively.
### Monitoring
During prebuild, a failure of conservative end seeking, monotone paging or actual-send budget interception invalidates the planned composition and must be resolved before product edits.

Evidence: current SDK1.45 `_MessagesIter`, current `message_batch.py`, `group_operations.py`, `account_operation.py`, `budget_client.py`, and audit `measure.py`; [Telegram history](https://core.telegram.org/method/messages.getHistory), [pagination offsets](https://core.telegram.org/api/offsets), [message fields](https://core.telegram.org/constructor/message). Detailed reasoning is retained in this inquiry's `docarchive/`; onward concept routes stay in `routelister.md` and `_route.md`.
