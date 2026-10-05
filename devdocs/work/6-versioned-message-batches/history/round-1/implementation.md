---
model: unknown
effort: unknown
---

# Implementation and verification — #6

Completed 2026-10-05 on `feat/6-versioned-message-batches`, based on `dev` at
`d39a4df275bacf51f814b6a0b281c227d4d17f93`.

Code, tests and public documentation are committed separately as
**`001f1345fbca9b73f9f94614f2d66fa80c35222c`**. This report is the work-folder
checkpoint; work documents remain on the feature branch at merge.

## Plan fidelity

Implemented all six steps of `step_by_step_impl_plan.md`, revision 1
(`f19299f`). The critic (`e19c8ca`) returned IMPLEMENT AS WRITTEN with
0 High / 0 Medium / 0 Low findings, so task-impl skipped Fold as instructed.
No planning or execution blocker remains for this implementation checkpoint.

| Step | Delivered |
|---|---|
| 1 | `tgdata/message_batch.py`: immutable v1 value, strict field/type/cursor/media validation, canonical JSON and verified SHA-256 payload identity; independent copied accessors and offline reload. |
| 2 | `tgdata/batch_files.py`: private temporary output, complete-byte hashing/size checks, non-replacing hard-link publication, verified existing files and cancellation cleanup; manifest save through the same mechanism. |
| 3 | `tgdata/batch_engine.py`: bounded oldest-first raw reads, explicit canonical group, senderless/service preservation, cached sender metadata only, requested media completion and original exceptions with a completed-prefix batch. |
| 4 | Additive `TgData.get_message_batch`, shared ConnectionEngine and health wrapper, public value/error exports; corrected the stale pandas dependency comment. |
| 5 | Normative `docs/message_batch_v1.md`, README usage, smoke README entry and 25 offline test groups in `test_19_message_batches.py`. |
| 6 | Compilation, new suite, full supported offline regression set, diff checks, separate implementation/work-note commits and issue checkpoint publication. |

No architectural deviation. One boundary detail makes the planned maximum
cursor valid: after resolving the group, `after_id == 2147483647` returns an
empty `end` batch without invoking the SDK reverse iterator, which otherwise
increments its offset beyond signed int32. The transport fixture serializes
real outgoing requests to exercise wire-width constraints.

The user's target is **Telethon 1.45.0 only**. This implementation/verification
did not run 1.33.1 or add compatibility work for it. Historical pre-steering
observations in earlier artifacts remain truthful history. The dependency
range/package version was not changed; this is not a release or a compatibility
certification for other SDK versions.

## Verification

Interpreter: project `.venv/bin/python`, Python 3.11.10, Telethon 1.45.0.
Compilation: `.venv/bin/python -m compileall -q tgdata setup.py` passed.
`git diff --check` and the staged diff check passed.

| Suite | Actual passed groups | Skipped |
|---|---:|---:|
| `test_19_message_batches` | 25 | 0 |
| `test_18_read_budget` | 28 | 0 |
| `test_17_session_store` | 12 | 0 |
| `test_16_health_events` | 21 | 0 |
| `test_15_login_checks` | 11 | 0 |
| `test_14_flood_threshold` | 11 | 0 |
| `test_13_device_identity` | 5 | 1 live |
| `test_12_proxy` | 5 offline/loopback | 2 live |
| `test_11_discover_groups`: query builder and empty/unresolved frames only | 2 | Live helper not invoked |
| **Total** | **120** | **3 live checks** |

The 12/13 runners count skips in their printed totals (7/7 and 6/6); the table
separates actual passes. Both received the explicit nonexistent config
`/private/tmp/tgdata6-no-live-config.ini`. Proxy checks 4/5 exercised localhost
refusal paths with sandbox permission. No Telegram account config was loaded,
and historical live/manual scripts were not run.

Run each named module above with `.venv/bin/python -m tgdata.smoke_tests.<name>`;
pass the nonexistent config to 12/13. The two discovery helpers were awaited
directly and their boolean results asserted. All final runners exited zero.

The new suite verifies actual SDK request/iterator/download flow with a scripted
transport and blocked sockets. It includes:

- an independently fixed canonical JSON/hash fixture, large signed IDs, Unicode,
  UTC/null handling, senderless/service messages and no enrichment calls;
- immutable copies, malformed/duplicate/nonfinite/version/hash rejection,
  strict record/cursor/mode/blob constraints and save/reload identity;
- 205 ordered records across 100/100/5 request bounds; empty/end/exact-limit
  results; maximum cursor and pre-connection input checks; source/peer rejection;
- real budget exhaustion, empty/nonempty raw partials and resume without
  skipping completed records; original transport/RPC exceptions and health
  reporting; malformed record failure after a valid prefix;
- actual SDK Document, Photo, cached-photo and progressive-photo downloads,
  exact bytes/digests, equal-content reuse, root independence, changed content,
  unsupported media references and metadata filenames that never become paths;
- missing/truncated output both before and after a completed record, corrupt
  files, symlink/directory destinations, manifest corruption, 24 competing
  publishers and cancellation during the SDK's second file chunk;
- both SDK file-reference refresh errors blocked by real budget admission,
  without a false account-health event or cursor advancement;
- saved replay after a lost acknowledgment through a receiver stand-in and
  unchanged legacy DataFrame/media filename contracts.

Golden payload identity:
`0080da8c922378798db91cd36476d57bc4ea02f5cadb140fb23e650b77e9e614`.

## Corrections made during verification

The first new-suite run passed 20/25 groups. Four local test-setup mistakes
accounted for all five failing groups; production code required no correction:

1. The username fixture wrongly expected `GetChannelsRequest` in addition to
   username resolution. The real 1.45.0 `get_entity` source and a recording probe
   show that `ResolveUsernameRequest` returns the entity directly. Corrected the
   erroneous request-name expectation; the exact golden bytes and no-enrichment
   assertions remain.
2. Two file tests compared `/var/...` fixture Paths against the publisher's
   resolved `/private/var/...` Paths on macOS. Resolved the fixture directory
   once so both denote the same path. Content, integrity and no-leftover
   requirements are unchanged.
3. The health assertion used nonexistent field `operation`; the existing event
   contract names it `call`. Corrected that field reference.
4. The legacy media test passed nonexistent keyword `download_dir`; the existing
   API names it `output_dir`. Corrected that call site; retained the expected
   `<chat_id>_<message_id>.png` filename and byte assertions.

The corrected suite passed 25/25. Added both empty/nonempty-prefix cases to the
missing/truncated-media group and reran the final suite: 25/25 again. No schema,
cursor, file-integrity or golden expectation was relaxed.

Two regression invocations initially used wrong module names
(`test_14_full_fetch`, `test_15_auth`) and exited with module-not-found. Corrected
the commands to the actual modules listed in the table; both passed 11/11.
No regression source changes were needed.

## Boundaries and remaining workflow

The evidence is offline. Scripted replies do not establish live Telegram's
history selection, a deployed receiver's atomic deduplication, deployment-volume
hard-link support or power-loss behavior. Local hashing/publication is synchronous
I/O as documented. A saved snapshot replays identically; a fresh fetch is a new
observation. The API does not advance durable caller cursors or provide a receiver.

The unrelated `devdocs/guides/group_discovery.md` edit was preserved and excluded.
Its SHA-256 remains
`28daa77cd0a94e787f211f05405858327721fcdd275549e64b64f9e48389cedf`.
The unrelated untracked `duncan/` directory was also left outside the commits.

Next: CONTRIBUTING step 6, `merge-check.md` comparing the actual diff with
triage/description/plan/critic and issue status, then the PR into `dev`; step 7
is a fresh in-session PR critique with probes. No PR, merge or deployment is
performed by this implementation checkpoint. Exact active model/effort metadata
are unavailable and remain `unknown`; **CONTRIBUTING §9 compliance must be
flagged at the merge gate, not certified here**.
