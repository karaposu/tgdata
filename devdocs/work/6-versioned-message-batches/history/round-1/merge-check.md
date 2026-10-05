---
model: unknown
effort: unknown
---

# Merge check — issue #6

**Fidelity verdict: PASS. Ready to open the PR; the fresh PR critic remains
required. CONTRIBUTING §9 model/effort compliance is unverified and must be
explicitly considered by the merger. This is not merge authorization.**

Reviewed in the same warmed session, 2026-10-05. Base: refreshed `origin/dev`
at `d39a4df275bacf51f814b6a0b281c227d4d17f93`. Reviewed branch head:
`b50561d4c9c46b4c09da46279f730b76d9e9d302`; feature implementation:
`001f1345fbca9b73f9f94614f2d66fa80c35222c`. Read triage, description, revision-1
plan, pre-implementation critic, implementation report and actual diff together.
No subagent or cold-session review.

## 0 — Warmth and weight

`desc.md` records the full-codebase #5/#9 context, merged-tree review at
`d39a4df`, refreshed #6 record/export/SDK reads and completed traverse at
`c7f7e1e`. Both commits are ancestors of this head, checked with
`git merge-base --is-ancestor`. Triage `7fe270c` is present and classifies this
as feature-heavy; GitHub #6 carries `enhancement`, `heavy` and
`open to implement`. This matches the new public wire contract, cursor/media
completion coupling and downstream consumer #10.

## 0b — Scope versus triage

All runtime changes occupy surfaced boundaries: raw records, public reader,
media files, shared connections/budgets/health, package exports, tests and docs.
The new filenames `message_batch.py`, `batch_files.py`, `batch_engine.py`,
`test_19_message_batches.py` and `docs/message_batch_v1.md` are the concrete
components selected by the subsequent plan for those boundaries. They do not
introduce an unsurfaced service, transport, database, login path or receiver.

The only additional existing file is `devdocs/guides/group_discovery.md`.
The user explicitly requested committing remaining changes, then explicitly
excluded `duncan/`. Commit `b50561d` checkpoints the pre-existing one-line guide
edit exactly as supplied. It is unrelated to #6 and should remain in the archive
branch rather than being integrated with this feature. No `duncan/` files are
tracked or committed. The feature-heavy weight remains appropriate.

## 1 — Implementation versus plan

1. **Value and schema:** `message_batch.py` implements the exact envelope,
   required record/media/blob fields, decimal ID ranges, canonical UTC dates,
   null rules, ordering and cursor constraints. Its canonical UTF-8 payload
   excludes `batch_id` for hashing and includes it for serialization. Reload
   validates version/hash; copied accessors preserve immutable stored JSON.
2. **Complete publication:** `batch_files.py` writes private temporary files,
   flushes/fsyncs, hashes in bounded chunks, checks known source size and
   publishes without replacing a destination. Existing entries must be regular
   nonsymlink files with the expected bytes. Manifest save verifies full-file
   contents independently from payload identity. Temporary cleanup uses finally.
3. **Raw reader:** `batch_engine.py` uses the existing ConnectionEngine session,
   entity/dialog fallback and SDK reverse iterator. It rejects nongroups,
   checks peers, projects directly from raw messages/cached senders, prepares
   requested media and appends only complete validated records. Ordinary
   failures retain their exception object and carry the complete prefix.
4. **Integration:** the façade constructs one BatchEngine with its existing
   ConnectionEngine; the public method uses `_reported('group_id')`. Package
   exports are additive. No existing MessageEngine, connection, budget,
   health, session, export or database implementation changes.
5. **Documentation and tests:** the normative v1 document covers schema,
   canonical encoding, modes, stop reasons, omissions, failure handling,
   media-root semantics and caller acknowledgment order. README and smoke
   inventory entries exist. The 25-group test suite implements the planned
   golden/schema, raw-reader, budget, exception, file/replay and compatibility
   checks through actual 1.45.0 SDK flows with supplied transport replies.
6. **Verification/commits:** implementation `001f134` and report `2a41379`
   are separate commits. The report records every local test-fixture/command
   correction. Current runtime, tests and public docs are byte-for-byte
   unchanged from the verified implementation (`git diff --exit-code 001f134
   HEAD -- tgdata setup.py README.md docs/message_batch_v1.md`).

Named details/deviations:

- The maximum signed-int32 cursor returns empty/end after entity resolution
  without a history request. This fulfills the planned cursor range while
  avoiding the SDK reverse iterator's offset increment overflow; it is tested
  and was named in the implementation commit/report.
- Revision 1 remains the live plan. The critic selected no mitigations and
  task-impl explicitly says to skip Fold for IMPLEMENT AS WRITTEN; there is no
  fabricated revision 2 or unaddressed finding.
- `setup.py` corrects the planned stale pandas comment and adds an EOF newline.
  No dependency/version change or 1.33.1 verification was added.
- The separate user-requested guide checkpoint changes what is now committed,
  not the implementation scope or runtime. Its exclusion at integration is
  explicit above and below; implementation.md remains a historical record of
  the earlier checkpoint when the guide was still uncommitted.

## 2 — Does the plan still make sense?

Yes. The explicit raw value bypasses the presentation conversion that can drop
senderless records. The value, file publisher and reader retain separate roles;
the reader advances at completion, while the caller owns durable acknowledgment
and cursor state. Saved replay is correctly distinguished from re-fetching
mutable history. No full Telegram archive, complete-album, deployed receiver or
exactly-once effect claim emerged during implementation.

Known boundaries remain explicit: actual SDK behavior is exercised with
synthetic replies; live server selection is unverified. File publication is
tested on this local filesystem, not every deployment volume. Hashing/fsync
are synchronous local I/O. These are unchanged scope boundaries rather than
unresolved implementation steps hidden by the test totals.

## 3 — Were critic findings answered?

`critic.md` at `e19c8ca` has **0 High / 0 Medium / 0 Low** and verdict
IMPLEMENT AS WRITTEN. There are no selected mitigations or consciously deferred
Lows to map. Its five premises map to the implementation's SDK/ordering,
file-output, concurrent-publication, codec/golden and shared-control tests.
No live-server or external-receiver claim is inferred from those stand-ins.
The fresh PR critic will judge soundness independently of this fidelity result.

## 4 — Is issue #6's status honest?

At this check, T/0/1/2/3/4/5 are checked and each is backed by the ancestry
verified artifacts `7fe270c`, `c7f7e1e`, `9928658`, `f19299f`, `e19c8ca`,
`001f134` and `2a41379`. The no-fold decision is stated. Steps 6 and 7 remain
unchecked; they must be updated only after their artifacts are committed and
their PR actions complete. The issue retains the original request and
Telethon 1.45.0 target. The continuation text will record the guide checkpoint
and explicit duncan exclusion with the step-6 update.

Verification evidence: **120 actual offline/loopback groups passed; three live
checks skipped**, with compilation and diff checks passing. The 12/13 printed
totals include their skips; implementation.md separates them correctly. A
read-only comparison confirms the tested code is still the code under review.

## Integration requirements and model flag

Keep the feature branch as the archive. At a later authorized merge into `dev`,
exclude `devdocs/work/6-versioned-message-batches/`, any archaeology refresh,
and the unrelated guide delta from `b50561d`; retain public `docs/` and README
changes. Run the required merged-code checks before pushing. Closing #6 on
`dev` may require the manual issue close used for #5/#9.

CONTRIBUTING §9 requires Fable 5.1/max or GPT 6 Astra/xhigh for this feature
workflow. The active exact model ID/effort are not exposed here; artifacts
truthfully record `unknown`. This fidelity pass cannot certify that rule.
The user has authorized review and PR creation; merge remains a later explicit
decision after the fresh critique and consideration of this flag.
