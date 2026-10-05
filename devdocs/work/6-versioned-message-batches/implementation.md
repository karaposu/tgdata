---
model: unknown
effort: unknown
---

# Revision 3 implementation and verification — #6

Completed the authorized re-plan/implementation cycle on 2026-10-05 on
`feat/6-versioned-message-batches`. Runtime/tests/public docs commit:
**`ce938a1fd0290cf590469800ce8541f4a9723e17`**. This work note is a separate
checkpoint. First-round records are intact under `history/round-1/` and in git.

## Pipeline and plan fidelity

The user requested CONTRIBUTING §7.4 after the first PR critique rejected
PR #15 with R1/R2 (two Mediums). Re-planning happened before runtime edits:
revision 3 at `e391cd6` regenerated file ownership/error boundaries using those
findings; the pre-plan protocol probe had seven passing observations. The
tailored critic prompt was committed at `c49d509`; the critic at `d82c663`
added cached-photo coverage and returned IMPLEMENT AS WRITTEN with no new
findings. Eight seam observations passed. Both original Robust mitigations were
already in the replacement plan; task-impl required no additional fold.

The seven steps were followed:

1. Retained the complete v1 value, codec, raw-reader/façade, guarded client,
   cursor and legacy contracts. A git comparison against `001f134` confirms
   `message_batch.py`, `batch_engine.py`, `tgdata.py`, exports, health, budget,
   connection and session code are unchanged.
2. Added `_local_io` and the private `_LocalFile` proxy in `batch_files.py`.
   Owned filesystem calls re-raise the same error from None; SDK write/flush
   calls also cross that boundary, while the SDK await does not.
3. Added one `_owned_stream`/`_cleanup` policy. Primary BaseException identity
   survives secondary teardown; close and unlink are attempted independently;
   the first cleanup-only failure is raised. Warning delivery is guarded and
   contains only operation/type. Close lookup occurs inside its guarded action.
4. Both publishers and existing-file verification use the same ownership policy.
   Output closes before non-replacing publication. Verification retains lstat,
   O_NOFOLLOW where available, fstat/inode checks and content verification while
   standard open owns descriptor handoff.
5. Retained the original 25 batch groups and added eight groups covering the
   native-I/O matrix, primary/secondary/cancellation, diagnostics and real causes.
   The unchanged first-gate probe now passes all eight observations.
6. Updated normative docs, README and smoke inventory. File cleanup is accurately
   best-effort if storage refuses it; incomplete public files and unsafe cursor
   progress remain prohibited.
7. Ran the required verification and committed this implementation separately
   from work notes. Repeated merge/PR reviews follow this checkpoint.

No architectural deviation or runtime failure correction was needed during
verification. All added tests passed on their first complete run. One local
composition detail was made explicit before that run: cleanup's close lookup
is deferred into the guarded action, so the action includes attribute access.
The new helper remains a file-ownership policy, not a storage/transaction
framework. The wire format/package/dependencies remain unchanged.

## Verification results

Project `.venv/bin/python`: Python 3.11.10, **Telethon 1.45.0**. No 1.33.1 run.
`compileall -q tgdata setup.py`, probe compilation and diff checks passed.

| Suite | Actual passed groups | Skipped |
|---|---:|---:|
| `test_19_message_batches` | 33 | 0 |
| `test_18_read_budget` | 28 | 0 |
| `test_17_session_store` | 12 | 0 |
| `test_16_health_events` | 21 | 0 |
| `test_15_login_checks` | 11 | 0 |
| `test_14_flood_threshold` | 11 | 0 |
| `test_13_device_identity` | 5 | 1 live |
| `test_12_proxy` | 5 offline/loopback | 2 live |
| `test_11_discover_groups` query-builder/empty-frame helpers | 2 | live helper not invoked |
| **Total** | **128** | **3 live checks** |

Run the named modules with `.venv/bin/python -m tgdata.smoke_tests.<name>`.
The 12/13 suites received `/private/tmp/tgdata6-replan-no-live.ini`, an explicit
nonexistent config, and localhost proxy tests had sandbox permission. Their
printed totals include skips (7/7 and 6/6); the table counts actual passes.
Historical live/manual scripts and real Telegram account config were not used.
All runners exited zero. The two no-network discovery helpers were awaited
directly and their booleans asserted.

Additional observations, separate from the 128 regression-group count:

- `probe_replan_seams.py`: **8/8**, actual SDK file-object dispatch and Python
  exception identity/chaining with supplied transport/I/O faults.
- Unchanged `probe_pr_review.py`: **8/8**, including both previously failing
  public reproductions. Exact repaired output:

```text
PASS local error context: error=FileExistsError, Telegram requests=0, health=[]
PASS cleanup error precedence: original=ChannelPrivateError, raised=ChannelPrivateError, same_object=True, cursor=101, temp_left=1
Result: 8 passed; 0 contract violations
```

The remaining private temp in the permission-denial probe is expected: storage
refuses unlink. Production preserves the primary failure and warns; only test
teardown restores permission so its private fixture can be deleted.

The eight new batch groups cover real path failure under incidental RPC context;
12 native local-I/O fault points; genuine SDK transport with explicit RPC cause;
primary RPC plus real unlink denial; simultaneous close/unlink plus failing
logging handlers (including a BaseException); actual task cancellation during
SDK download plus denied cleanup; cleanup-only media and manifest failures; and
verification read/close/outer-unlink precedence. Original exception identity,
health events, cursors, file contents/closed handles and warning privacy are
asserted. Existing golden/schema/replay/media/concurrency cases remain intact.

## Scope and next checks

Only `batch_files.py` changed in runtime code during this cycle. Shared health,
quota and client code were not weakened. The source of the two rejection
mechanisms is handled at the owning file operation/resource boundary.

The separate user guide checkpoint `b50561d` remains on the branch and outside
#6 integration. Its SHA-256 is unchanged:
`28daa77cd0a94e787f211f05405858327721fcdd275549e64b64f9e48389cedf`.
`duncan/` is not tracked or committed. All first-round records are archived;
the same PR #15 is retained.

Evidence remains offline: real SDK/client/file behavior with supplied Telegram
replies, not live-server, deployed-receiver or arbitrary-volume proof. Local
I/O remains synchronous, and deletion cannot succeed against filesystem refusal.
The next steps are the repeated fidelity check and fresh in-session PR critique.
No merge is performed by this checkpoint. Exact model/effort metadata remain
unavailable and CONTRIBUTING §9 stays explicitly unverified.
