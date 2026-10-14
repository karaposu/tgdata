---
model: gpt-6-astra
effort: xhigh
---
# Triage — #30 optional photo-trail folding

**Weight:** feature-heavy.
**Surfaced:**18 identified items across consumer, value, reader, receiver, contracts/tests, source-progress, prior-evidence and process regions; full trace in surfacing.md/.json. Principal surfaces are MessageBatch, TelegramPost, AlbumReceiver, source receipts and the ScrapeOps folding/calling code.
**Why heavy:** heuristic attachment introduces a new relation between already identified Telegram posts. Late album members, batch partitioning, restart, original-record custody and caller acceptance can disagree silently. This is not merely moving a list helper into another package.
**Watch for:** folding anonymous/channel identities; treating any media as a photo; nonmonotone or missing time; changing captions/IDs; merging texts; using observation arrival order as source order; finalizing because a batch ended; dropping prior anchors after source ack; treating inferred grouping as Telegram fact; counting folded posts as folded messages; weakening #29's accepted-input confirmation contract.

**Traverse:** required by §5 for a new derived relation and the delicate connection between ongoing album observations, retained heuristic context and delivery acknowledgment. Establish the input/order/finality/retention contract before a description fixes its API. Preserve alternatives through articulation, then test the actual consumer assumptions and source/value seams.

**Prerequisites:** #29 merged in35c4362; its old blocked status is stale. #31 leases, #3 proxy checks and #17's two-account live gate are independent and remain outside this task. No new prerequisite implementation has yet been established. No lower-model work was used; §9 is verified for this turn.

**Scope readiness:** fresh task folder, no PARKED block, no prior description/plan and zero rejected PR critiques. User's explicit task-impl invocation authorizes the formal chain, branch, required commits/status updates and implementation/verification. Merge, release and consumer migration remain separate later actions.
