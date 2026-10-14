---
status: active
model: gpt-6-astra
effort: xhigh
---
# Finding: assemble observed albums at the receiver

## Question

How should tgdata turn Telegram album members arriving in separate bounded message batches into one logical post, while preserving existing reading limits, saved progress and acknowledgments?

The goal is a reusable, implemented library capability. ScrapeOps motivates the work, but application classification, uploads and photo-trail guesses remain separate.

## Finding Summary

- Add an opt-in, pure assembler over existing MessageBatch values. It returns immutable post observations; it does not read Telegram or acknowledge anything.
- Identify an album by its chat and Telegram grouping ID. Retain every original member, including every caption and media reference.
- Merge new members into the caller's saved prior observation. Require an explicit prior lookup result for every affected post, so an omitted argument cannot silently erase history.
- Keep global album membership unconfirmed. A batch boundary, history end or successful database commit does not prove that all members have been seen.
- Demonstrate durable use with a small SQLite receiver example. It explicitly creates a new collection or strictly reopens a known one, then commits posts and input recognition before the caller acknowledges the original raw delivery.
- The design is qualified. The actual assembler still needs a reviewed plan, combined real-component prebuild and implementation tests.

## Finding

An album caption can arrive in one batch and its remaining photos in another. The raw reader already preserves Telegram's grouping ID, but its limits deliberately count individual messages. Changing those limits to chase the rest of an album would affect budgets, fixed windows and existing saved delivery hashes.

The new operation should therefore consume the raw batches already returned. It combines records with the same chat and grouping ID into one stable logical entity. A later observation updates that entity's content revision instead of inventing another post. Ungrouped messages remain separate entities keyed by chat and message ID.

Every member remains available in its original form. A convenient display caption cannot replace the source records: Telegram permits captions on individual media, and the inspected ScrapeOps helper otherwise keeps only the first returned caption. Large grouping IDs remain exact decimal strings.

The operation needs the prior observation for each affected identity. Callers supply an exact mapping: a saved post when present, or explicit None when a successful authoritative lookup found no such post. Missing entries, invalid saved values, incompatible media modes, conflicting observations of the same member and configured resource limits cause refusal. The operation must not partially mutate supplied values or silently trim members.

This requirement does not make tgdata the owner of permanent scraped content. The caller chooses its database or other durable storage. The library supplies portable immutable values and a deterministic combining operation. It does not hold all historical posts in an internal cache.

The SQLite example makes that caller contract concrete. Creation is explicit. Normal reopening requires the expected file, schema and named collection to exist. A missing collection is different from a missing individual post: only the latter can mean a new logical post. Backend errors must propagate instead of becoming an empty prior value.

For acceptance, the receiver opens a write transaction, reads the current observations, combines the new input, and commits the resulting posts together with an input marker scoped to the selected collection. Loading current values inside that transaction prevents stale blind replacement. The same raw batch delivered to two collections requires acceptance in both.

The caller then acknowledges the original source delivery. Daily continuation uses its original batch ID; backfill uses its full delivery reference. A post ID or post revision is neither of those receipts. Likewise, captured data attached to an exception does not by itself prove that a durable source delivery is pending. The example must obtain a normal delivery or confirmed pending replay before acknowledging.

A crash before receiver commit leaves the input unaccepted. A crash after commit but before source acknowledgment leaves recoverable observations; retry merges against the current saved state. A reply lost after a commit does not justify resetting storage or undoing the write. The combined prebuild must exercise these histories with the new candidate code.

An album observation remains explicitly unconfirmed even after durable acceptance. Scoped history can omit members, and the raw interface carries no expected album size. The helper neither fetches outside the requested scope nor guesses completeness from consecutive IDs, time, maximum media count or the next different grouping ID.

Downloaded media has separate custody. Saving JSON preserves references, not bytes deleted from a download directory. The first receiver example can use reference-only batches and document the caller's blob-retention obligation for downloaded media.

Eight checks against actual SQLite and SQLiteSyncStore confirm strict reopening, authoritative absence, conditional writes, atomic data/receipt rollback, reopening committed data, collection separation and transaction exclusion. They establish the available storage seam. They do not establish that an unbuilt assembler works, certify storage-device power failure or prove Telegram history completeness.

## Next Actions

### MUST

- **What:** Specify public post serialization, exact prior-input contract, error behavior and adjustable count/byte limits in the feature description and plan. **Who:** task-desc/task-plan in this work folder. **Gate:** before production edits. **Why:** make the qualified contract reviewable and testable.
- **What:** Review the plan and run a combined prebuild using the actual candidate, Telethon serialization, MessageBatch, SQLite receiver and existing daily/backfill engines. **Who:** task-impl/critic-d. **Gate:** before production step1. **Why:** check representation and restart assumptions in their real composition.
- **What:** Implement the qualified value, assembler, receiver example, documentation and tests; run the full existing offline suite. **Who:** task-impl. **Gate:** after the plan and prebuild pass. **Why:** deliver the requested capability without changing raw delivery behavior.

### COULD

- **What:** Validate a later ScrapeOps adapter against the existing consumer fixtures. **Who:** a separately authorized consumer task. **Gate:** after the library API and tests exist. **Why:** preserve consumer counts and caption expectations during adoption. **Depends-on:** MUST item “Implement the qualified value, assembler, receiver example, documentation and tests”. This COULD is GATED.

### DEFERRED

- **What:** A source-aware API promising stronger album readiness. **Gate:** a concrete caller requests that guarantee and an actual source mechanism can establish it. **Why (if revived):** support final-emission workflows without guessing membership.
- **What:** Rebuild projections from a retained raw archive. **Gate:** an actual indexed archive contract is supplied. **Why (if revived):** reuse an existing application's authoritative content storage.

## Reasoning

The immutable observed-post value survives because it preserves both stable identity and all observed content. The pure required-prior combiner survives because it makes retention an explicit input without adding source operations. The strict receiver example survives because it gives those values a durable owner. Combined qualification survives because it can test those actual seams without pretending scripted Telegram replies prove universal server behavior.

Fragment-only output was rejected: it leaves callers solving the original cross-batch grouping problem. Removing the persistence example was rejected because it hides the restart obligation that can lose already-acknowledged members. Relying only on old suites was rejected because they never call the new operation. These are the substantive rejected candidates across both iterations.

A permanent mutable assembler cache could work only with another durable lifecycle. The receiver already owns accepted content, so that lifecycle adds no required guarantee here. Rich envelopes mixing source receipts with post data also couple identities that have different scopes. Whole-scope buffering needs bounds tied to an entire history, making it a specialized export alternative rather than the default daily path.

The first inquiry iteration left receiver reopening implicit. The second resolved it by separating explicit provisioning, validated collection opening and individual-key absence. That refinement retained the small assembler architecture and used actual existing storage behavior as evidence. No new source engine or progress schema is needed.

## Open Questions

### Monitoring

The combined prebuild must establish actual candidate behavior before implementation adoption. Public API names and policy defaults belong in the description/plan. Current model/effort metadata is unavailable; the factual question remains pending and must not be certified without an answer.

### Refinement Triggers

Revisit the observation API if the user requires one irreversible final post rather than stable entity updates. Revisit conflict refusal if edit/deletion reconciliation becomes an explicit requirement. Qualify actual Telegram behavior before introducing any new source-completeness assumption. No live Telegram claim is made for this pure observed-data contract.

**Provenance verified retrospectively, 2026-10-14:** local active-thread turn records and matching commit outputs establish GPT 6 Astra / xhigh for this artifact. Earlier unknown/pending wording records what was known at the time; see [§9 verification](../model-effort-verification.md).
