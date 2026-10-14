---
model: unknown
effort: unknown
---

# Triage — issue #29

**Weight:** feature-heavy.
**Surfaced:** message_batch.py, batch_engine.py, batch_files.py, sync_engine.py, sync_store.py, history_window.py, progress_facade.py, tgdata.py, backfill_engine.py, backfill_state.py, pool_result.py, pool_observation.py, examples/daily_continuation.py; ScrapeOps's collapse helper/fixtures; actual Telethon album event code and Telegram's message schema. Detailed identifiers/tags/coverage are in surfacing.md.
**Why heavy:** derived post identity and retained membership cross raw delivery, receiver acceptance, restart and media custody. Raw, daily and backfill consumers have different completion signals. Lost retained members after an acknowledged raw batch would be delayed data loss. #30 will depend on the resulting post representation.
**Watch for:** calling an album globally complete from a page boundary, a timeout, a changed grouped_id or a temporary history end; acknowledging source records before preserving their derived ownership; silent eviction or out-of-window lookahead; mutating hashed raw batches; dropping secondary captions; mixing chats, media modes or separate collections.

**Traverse:** required under CONTRIBUTING §5: a new representation/state structure that later work stands on, plus a delicate connection between raw delivery and receiver assembly. Inquiry location: traverse/. The question must distinguish membership evidence, closure policy and acknowledgment responsibility before a description or plan fixes an API.

**Prerequisites:** no separate prerequisite implementation is established yet. Existing MessageBatch and caller-owned durable receiver patterns are available. The inquiry must establish the home of assembly; a new generic persistence engine is not presumed necessary. Actual Telegram validation must test any source-completeness assumptions before dependent implementation.

**Scope readiness:** no prior desc, parked block or PR rejection exists for #29. The optional API preference and §9 model/effort question remain pending; preparation is continuing. Provisional API direction is a separate opt-in assembler. No product code has been written.
