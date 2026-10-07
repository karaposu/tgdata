---
model: gpt-6-astra
effort: max
---
# Stage 5 source input

User request, verbatim:

> $task-impl stage 5

The user supplied the task-impl skill in full. Execute desc → plan → critic-d →
experiment/fold where required → implement → verify, with formal artifact checkpoints.

Resolve Stage 5 of issue #19: 5.1 saved attempt-based pacing/readiness; 5.2 existing
source restriction observations and actual-send authority; 5.3 explicit exact-attempt
recovery; 5.4 clock/pacing-anchor tests. Gate B passed at the previous handoff.
Stage 6 controls and mandatory live Gate C follow later; this scope does not build them.

Entry: feat/19-backfill-run-lifecycle at 246a187; product b1f6495. Working tree clean.
Stages 1–4 and Gates A/B are complete, pushed and reflected on #19. No scoped PARKED
block or rejected PR critic exists. User constraints persist: Telethon 1.45.0 only,
one source reader per group, no source edits/deletions, no account routing/scheduler,
no #7/duncan work, no PR/protected merge. Caller owns receiver, account and worker lifetime.

Existing live authorization and resources remain recorded for later Gate C: the two
approved read-only groups, selected session and unchanged authoritative ledger. Its
last Gate B usage was 2202/5000. Do not reset/reconfigure it. Gate B's unknown attempts
remain private and unresolved; local validation may use disposable copies, preserving
the original gate evidence. Stage 5 itself requires no new Telegram traffic.
