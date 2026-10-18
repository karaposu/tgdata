---
model: gpt-6-astra
effort: xhigh
---
# Triage — issue60

**Weight:** feature-heavy. Two readers and daily/backfill/pool consumers; out-of-order
work crosses durable prefix, file publication, cancellation, source policy and task-
scoped health/heartbeat. Wrongness can silently skip messages or leave writes running.
**Baseline:** archivec3950c6, product matches current devd8232d1 / main4c47c86.
No new branch: retain feat/50-terminal-account-login archive and existing product
transport. No old user checkout edit or other issue enters this work.
**Warming:** retained same-session source/session/progress knowledge; refreshed whole
batch engine/file/heartbeat/budget/pool-source/lifecycle/observation/sync modules,
legacy reader, real SDK _call/download/exported/CDN paths and public consumer seams.
Full heartbeat integration tests read. Broader unchanged system context retained from
prior#7/#17/#18/#37 work. Current thread2026-10-18T05:12:43.389Z confirms
GPT6 Astra/xhigh. No subagent. No AGENTS.md/PROJECT_SPECIFICS.md in this checkout.

**Surfaced:** see surfacing.md. Default1 must bypass concurrency machinery. Current
legacy per-message handlers swallow ordinary download errors; batch preparation fails
with ordered complete prefix. These contracts differ and cannot be unified casually.
SDK can sleep before/inside _call; downloads use _call directly and may export senders
or create CDN clients. Batch heartbeat and ambient health deliberately reject inherited
background-task attribution. Budget is charged at real sender admission; file-reference
refresh may read messages even when file bytes themselves cost zero allowance.

**Watch for:** unbounded queued records despite a semaphore, cursor past an unfinished
message, speculative tasks surviving callbacks/cancellation, delayed observer ownership,
SDK waits hidden from the coordinator, missing cleanup of native exported resources,
policy mutation affecting shared clients, rate backoff that changes pool no-wait policy.
**Traverse decision:** required (§5 delicate connection/new scheduling structure).
Question: what bounded ownership/completion/wait contract lets optional parallel media
coexist with existing ordered delivery and source policy without a general scheduler?
No planning blocker declared from unread code: resolve frontier through reading/probes.
No live benchmark has run; implementation can be qualified offline, performance remains
an explicitly separate bounded read-only validation without promised multiplier.
