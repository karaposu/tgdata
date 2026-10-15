---
model: gpt-6-astra
effort: xhigh
---
# Triage — #37

**Weight:** feature-heavy. **Surfaced:**22 items in surfacing-trace.json.
**Why heavy:** one callback crosses direct reads, daily/backfill preparation, pool-owned tasks and SDK requests. Wrong callback isolation could change health, cancellation or saved data; retries and budgets are separate policies.
**Watch for:** timer-only fake liveness; callbacks in background/concurrent tasks; swallowing real cancellation; callback text entering logs/health; forwarding None to old injected readers; new await boundaries around SDK enqueue; replay opening a client; hidden SDK waits confused with a heartbeat interval guarantee.

**Traverse:** not needed. This extends the established phase callback into existing readers; no new data model, persistence authority, retry policy or operation lifecycle is proposed. Real SDK probes qualify the notification seam before adoption. If that seam requires changing retry or ownership semantics, stop and revisit this decision.

**Matches:** #6, #18/#19 and #17 are delivered foundations; none promises batch heartbeat. #30/PR36 is independent. All17 open/closed issue titles read, relevant outcomes reviewed. New task#37, on the existing archive branch by explicit user instruction.
