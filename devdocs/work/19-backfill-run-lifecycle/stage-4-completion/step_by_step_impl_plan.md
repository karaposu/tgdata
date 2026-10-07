---
model: gpt-6-astra
effort: max
revision: 2
---
# Stage 4 — completion and authoritative write confirmation

**Critic folded:** 2026-10-07 — 0 content mitigations; required prebuild experiment
ran before Step 1 and PASSED (4 checks). No implementation steps changed or added.
202 requested live history slots count toward the 1500-slot Stage 4 cap; full Gate B
still runs on the final product. See [critic](critic.md) and [receipt](prebuild-results.json).

Baseline: `62d5f60`, Stage 3 product `3140dcd`. Inputs: [desc](desc.md),
[contract](../contract.md), [staged plan](../staged-plan.md), [Gate A](../validation/gate-a.md).
No PARKED or rejected PR-critic artifact exists in this scoped task.

### What is the task

Finish the existing completion path's audit and add bounded confirmation of ambiguous
storage replies. Prove the actual internal source/state/receiver flow at Gate B before
pacing/recovery is built. Retain existing one-reader, scoped receipt and custody rules.

### Huge Hard Blockers

#### Planning Blockers

None identified. The strict aggregate already represents every required completion
fact. No operation, schema or ownership decision is missing. The proposed single
read-back confirmation is deliberately conservative and does not promise recognition
of arbitrary later states. Raw source foundations already passed Gate A.

#### Execution Blockers

None currently OPEN. Live steps require the selected account session, existing
read-only group visibility and remaining allowance in the same authoritative ledger.
Those are available from Gate A but rechecked during live qualification; a failure
gates Steps 4–5 and Stage 5 of #19, without faking a PASS. No policy reset/increase,
new account or unapproved group may stand in for those inputs.

### How this implementation moves toward desired state

Keep the existing closure and receipt recognition. Centralize only the common CAS
reply boundary: one attempted write, and on a non-cancellation ambiguous result one
validated authoritative load. Exact candidate-state equality confirms the attempted
transition. Anything else remains unconfirmed; never retry a write blindly or infer
rollback. Admission opts out of successful reconciliation: no ambiguous admission
result can turn into a source send. Existing explicit status/retry methods handle
retained effects after restart or concurrent subsequent mutations.

### High-Level Summary

| Step | Description | Expected output |
|---|---|---|
| 1 | Confirm exact committed snapshots after ambiguous replies | One bounded helper, wired create/publish/ack; no admission widening |
| 2 | Completion and uncertainty regression matrix | test_26, real SQLite/process exits; intentional existing-test updates |
| 3 | Update staged usage, run relevant and full offline suites | Verified product/code/tests/docs commit |
| 4 | Freeze independent live oracle and Gate B instrument | Guarded real source, durable receiver, bounded crash workers |
| 5 | Execute Gate B and publish accurate handoff | Evidence, verdict, work-doc commit/push, #19 status |

## Design constraints

- `_BackfillState` canonical JSON equality includes full namespace, run/generation,
  request/window, accepted cursor, pending hash/payload, exhaustion, attempt, receipts,
  timing, control and state revision. Never match a bare hash/cursor or strip fields.
- A helper over `_backend('compare_and_swap', ...)` accepts a strict bool reply.
  False remains known conflict with existing bounded operation-specific reloads.
  Exception or nonbool is ambiguous. Cancellation propagates immediately, from None;
  do not mask it with reconciliation I/O.
- After ordinary ambiguity, load at most once and validate through `_load`. If its
  canonical snapshot equals the attempted next snapshot, return confirmed success.
  Otherwise re-raise the original sanitized storage error, from None. Read-back
  outage is unknown; malformed/wrong-scope data raises StateError rather than success.
  No second CAS, clock read, source call or receiver operation occurs here.
- Admission uses the same write plumbing with confirmation disabled. Preserve its
  current error/no-send behavior whether it committed or not; the durable marker
  blocks future reads until explicit recovery (Stage 5). Keep all cancellation paths.
- A newer compatible control/receipt snapshot may retain the effect but fail strict
  equality. That is intentionally conservative, not a claim of rollback. The caller
  can inspect status or use existing retained same-request/same-receipt recognition.
  Do not return old candidate data as current, invent a broad partial-effect matcher,
  or overwrite newer state to make equality true.
- Ordinary source exceptions still re-raise the identical error after confirmed
  prefix settlement. If read-back cannot confirm it, local error retains `read_error`
  separately and never inherits a Telegram health verdict.
- No state schema/version or public facade/value changes. `_complete_if_fulfilled`
  remains the only shared terminal predicate; adjust its stale staging comment.
- A start confirmed by exact read-back returns `applied=True` (the submitted candidate
  is durably present); a later retained request retry remains `applied=False`. This is
  confirmation of the effect, not proof that this process was the unique writer.

## Step 1 — Exact read-back confirmation

### Proposed changes

In `tgdata/backfill_engine.py`, add the shared narrow CAS helper with the constraints
above. Route `_write` and `start` through it. `_admit` explicitly disables successful
read-back reconciliation. Leave completion transitions, strict validation and existing
CAS-conflict rebasing intact. Clarify module/start/closure comments.

### Output

Ambiguous non-admission writes can finish successfully only after validated identical
state is actually read. Unconfirmed state never prompts an automatic replacement write.

### Safe in nature

False — changes whether existing post-commit failures return success.

### Peripheral concepts

Durability, strict canonical state, error provenance, cancellation, source admission.

### Hardness Lvl

4/5.

## Step 2 — Completion and uncertainty matrix

### Proposed changes

Add `tgdata/smoke_tests/test_26_backfill_completion.py` using existing SDK fixtures,
actual SQLite, actual engine and network denial. Reuse test_25 helpers where useful.
Test create/publication/empty-end/final-ack exceptions and nonbool replies before/after
commit; exact read-back uses one additional load/no clock/no second write. A false CAS
keeps current semantics. Read-back absent/old/moved-on/outage/corrupt/wrong-scope states
never fabricate success. Check newer control and retained receipt via explicit retry.

Cover empty and nonempty final scopes, exact-full limit followed by empty end, failed
follow-up after accepted full batch, origin/window on reopened completion, no-account
and budget prefixes, last receipt with newer pending, equal hashes/wrong-run receipt,
and seeded cancellation/pause precedence. Existing coverage may be cited/reused rather
than copied. Exercise real source failures during prefix publication: committed close
error returns the original source exception; unresolved save keeps separate provenance.
Cancellation before/after write and during read-back remains cancellation, never end.

Run owned subprocesses exiting immediately before/after actual SQLite commits for
creation, pending publication, **empty completion** and **final acknowledgment**.
Reopen with create=False, reader/clock forbidden as applicable. Before empty commit,
attempt stays unresolved; after, complete. Before final ack, pending remains owed;
after, one accepted receipt and completion. A real receiver commits before ack;
replay/retry adds no repeated destination effect. This is process durability, not
simulated power-loss/filesystem certification.

Update test_24/test_25 assertions only for explicitly planned post-commit ordinary
error confirmation. Preserve negative precommit, cancellation, health and identity
expectations. No test expectations are relaxed to repair unexpected failures.

### Output

Executable cases distinguish accepted/owed/unknown/complete across actual commit boundaries.

### Safe in nature

True — disposable offline test artifacts only.

### Peripheral concepts

SDK end semantics, receipt scope, imported coverage, media acceptance, subprocess exit.

### Hardness Lvl

4/5.

## Step 3 — Usage and supported offline verification

### Proposed changes

Update `docs/backfill_state.md`, relevant README staged references and smoke-test
README with exact confirmation/unknown behavior and completed Stage 4 scope. Do not
preclaim Gate B. Run compile, AST Python-3.7 grammar compatibility, test_26 then the
supported offline modules 25,24,23,22,19,18,17,16,15,14,13,12 and explicit two test_11
helpers. Legacy live cases remain explicit skips; actual runtime is Python 3.11.10 /
Telethon 1.45.0. Run existing Gate A instrument checks and daily demo. Commit product
code/tests/public docs separately from work-folder evidence, no PR/protected merge.

### Output

Verified product checkpoint with exact pass/skip counts and any local corrections recorded.

### Safe in nature

True — documentation and verification only; commit feature branch only.

### Peripheral concepts

Backward compatibility, import paths, Python/SDK support, honest staged availability.

### Hardness Lvl

2/5.

## Step 4 — Gate B oracle and actual receiver instrument

### Proposed changes

Keep `live_probe.py`'s pinned guard/startup workaround unchanged. Create Gate B driver
and receiver under the issue work folder, private data under a new mode-700 temp root.
Use existing config/session and `account-read-budget.sqlite3`; verify the actual
account each connection and read its existing policy/charges. No reset/configure calls.

Requalify the small group's complete visible interval with direct descending history
RPCs independent of `get_message_batch`/prepare, and selected photo via direct SDK
bytes hashing. Freeze ID/date/boundary/media manifest before tested scans. The oracle
shares SDK decoder/transport but not selection/traversal logic; state that limitation.
Use the larger approved group if needed for a genuine interrupted multi-page prefix,
with an independently complete bounded interval. Reuse qualified Gate A bounds only
after current-view checks; drift makes that case INCONCLUSIVE, not a rewritten oracle.

Receiver: real SQLite FULL-synchronous transactions; unique full DeliveryRef receipt;
unique group/message key and stable payload; required blobs copied and flushed/verified
before receipt/message commit, directory synced where supported. Repeated delivery and
overlap cannot repeat effects. Capture canonical pending payload hash before crash and
compare exact replay, separately from the independent source selection oracle. No raw
message bodies, sender metadata, credentials, sessions or budget files in published docs.

Workers are sequential and owned. Offline restart/replay/status/ack must construct no
Telegram client; block sockets to prove it. Test process exits at actual SQLite commits
using the same method as offline tests. Confirm child exits before replay. No source
worker is assumed dead from time alone; leave unresolved attempts untouched.

Caps per small scan: <=12 history requests, <=1000 requested slots, <=4MiB media,
180 seconds; external spacing >=5 seconds between live source turns and oracle pages.
Global Stage 4 live cap <=1500 requested message slots (within existing policy), no
concurrent source sessions. Stop on guard/budget/auth/flood failures; do not spend more
to conceal them. A controlled prefix case may locally refuse the second actual send;
keep real budget admission/charges intact. This is INJECTED local failure, not a claim
of naturally occurring server failure. Any simpler prebuild probe counts against caps.

### Output

Frozen independent oracle, auditable source guard, actual local receiver and crash controls.

### Safe in nature

False — bounded real external reads consume account allowance; existing authorization applies.

### Peripheral concepts

Fixture drift, source evidence, source budgets, media custody, repeat-safe receiver, privacy.

### Hardness Lvl

4/5.

## Step 5 — Run Gate B, record and hand off

### Proposed changes

Execute required cases from live-validation §6: sequential overlapping collections;
empty, nonempty final, exact-full-follow-up and imported scopes; wrong-run receipts;
completed reopen; post-publication and post-receiver crashes; actual before/after-final
ack and empty-completion crashes; failed full-batch follow-up; useful interrupted prefix;
unresolved-attempt refusal. Reopened paths spend no new source requests/allowance.

Compare accepted IDs/dates/media with frozen oracle, accepted cursor/pending/terminal
state and real receiver receipts/effect counts. Save sanitized observations and explicit
LIVE/INJECTED/LOCAL classifications. Record `validation/gate-b.md` PASS only if every
required assertion has evidence and regressions pass; otherwise FAIL/BLOCKED/INCONCLUSIVE
with retained failing records and stop before Stage 5. Reopen Gate A if source meaning
changed. No later stage implementation is authorized by this scoped run.

Update assumptions, acceptance-matrix coverage, root handoff/staged plan/contract
availability and Stage 4 implementation/verification notes. Commit work notes separately;
push only #19 feature branch; update issue status/comment preserving raw request. Its
body is near the size limit: use links/short replacements and a completion comment, not
another long append. Report exact code/evidence revisions, tests, gate and remaining work.

### Output

Reviewable Stage 4 checkpoint and an evidence-backed Gate B verdict.

### Safe in nature

False — real bounded reads and deliberate local process interruptions.

### Peripheral concepts

Stage gates, actual receiver durability, retained uncertainty, GitHub pipeline status.

### Hardness Lvl

4/5.
