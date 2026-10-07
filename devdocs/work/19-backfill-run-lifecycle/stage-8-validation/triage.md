---
model: gpt-6-astra
effort: max
---
# #19 Stage 8 triage

**Weight:** feature-heavy. **Priority:** existing P2.
This is a verification/integration stage of the feature, not a request for new lifecycle
semantics. Cross-operation/process/source/receiver boundaries can fail despite individual
stage tests. Gate D also consumes real account allowance under a fixed scope.

**Surfaced:** six public methods; real SQLite durable boundaries; exact pending/receipts;
terminal/control ordering; recovery/quiescence; source health ownership; configured
budget and actual SDK sends; independent oracle; receiver byte/snapshot custody; separate
daily/history progress; bounded traceable workers; whole-feature diff/finding/critic record.
See [surfacing](surfacing.md).

**Warm at `cb1297a` (2026-10-07):** same-session full lifecycle/facade/health/store model,
prior live gates and Stage 7 implementation retained. Actual public tests, settlement,
guard/receiver composition and large-fixture qualification refreshed. Archaeology is
unchanged. gpt-6-astra/max verified in session metadata; process guard present; current
issue titles read. #19 remains the existing task, with #18 prerequisites integrated
feature-only from `e9b5154`; paused #7 and later routing/worker issues remain separate.

**Traverse:** retain the completed lifecycle inquiry and Stage 1 contract. No new data
model/ownership choice is proposed. The selected test backend/receiver and instrumentation
are concrete implementations of the settled acceptance boundary; qualify the composition
before depending on it. A contradicted premise reopens its stage rather than being
patched silently or folded into a broader feature.

**Watch for:** coverage claims that count internal/synthetic tests as public/live;
lost replies treated as rollback; source death inferred from timeout; early/late ack
resetting pacing; local operations clearing source health; receiver markers preceding
durable bytes/snapshots; per-process caps mistaken for a stage-wide ceiling; oracle
drift; old receipts affecting successors; independent daily/history state advancing
together; aggregate issue boxes ticked before their actual evidence exists.

No runtime change is anticipated. Add focused combined tests and reproducible opt-in
Gate D tooling, then a scoped review-readiness audit against all stages. Large failures
stop under task-impl; only small nonarchitectural corrections are allowed. Publication
of completed feature-branch checkpoints/required issue updates is authorized; PR/merge
remain separate.
