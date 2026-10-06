# Gate A instrument usage

This is an instrument for the [live validation procedure](../live-validation.md),
not an automatic acceptance test of the whole gate. Read-only existing-group scope
remains fixed. Actual account/config, group, oracle and approved limits are still unset.
The example JSON deliberately refuses preflight until its placeholders are replaced
and its independent complete-history oracle is established. Its numeric limits are
illustrative, not an approved traffic allowance or Telegram-safe recommendation.

1. Select the actual account/config label and existing canonical group. Prepare an
   isolated Stage 2 run locally using `BackfillStartRequest`/`BackfillEngine.start`.
   Keep the request before submission and persist the returned RunRef. For a relative
   run, freeze its dates first, then independently enumerate that exact saved scope.
2. Copy `probe-manifest.example.json` to a local input file. Use the actual request and
   RunRef portable dictionaries. Set its exact saved UTC window. Supply a complete
   ordered ID/date oracle from a separate client/export/manual enumeration of existing
   visible history. Do not populate it by calling the reader under test.
3. Each oracle message has exactly `id` (canonical decimal string), `date` (canonical
   UTC microsecond timestamp) and `blob`. `blob=null` means no downloaded artifact is
   expected for that row. In download mode provide `{sha256, size}` for every row that
   should produce a blob, using independently known bytes/hashes. Unknown media is not
   silently accepted as verified. Reference mode has null blobs and zero media allowance.
4. Qualify the actual SDK/caller page boundaries and required empty/full/date/media cases
   before source calls. One scan need not cover all of them; use separately qualified
   existing intervals/runs without changing a saved run's intent. Missing cases remain
   blocked/inconclusive. Never seed messages or modify group membership.

Offline preflight (no account/config is read):

```bash
python devdocs/work/19-backfill-run-lifecycle/live_probe.py \
  --manifest /path/to/qualified-manifest.json \
  --state /path/to/existing-backfill-state.sqlite3 \
  --output /path/to/new-preflight-report.json
```

Explicit live diagnostic, after the actual resources and allowance are established:

```bash
python devdocs/work/19-backfill-run-lifecycle/live_probe.py --live \
  --manifest /path/to/qualified-manifest.json \
  --state /path/to/existing-backfill-state.sqlite3 \
  --config /path/to/selected-account.ini \
  --budget /path/to/existing-authoritative-budget.sqlite3 \
  --output /path/to/new-live-report.json
```

Add `--media /path/to/disposable-artifacts` only for a download-mode run. Config and
budget files must already exist; the account policy must already be configured. The
tool never configures/reset limits, creates login codes or chooses another account.
The existing proxy and actual budget adapter remain in the call path. A test cap may
only further restrict an account's authoritative allowance. A request stopped by the
instrument after a budget reservation can retain its conservative charge; do not reset
usage to erase it. The report records before/after observed usage separately from sends.

The selected group must be resolvable from the authenticated client's existing entity
context. Unrelated dialog discovery/username traversal, writes, joins and unknown RPCs
are refused. Unsupported cached-entity/media-DC flows are a stopped/inconclusive probe,
not permission to broaden source access or bypass the guard. Read-only metadata and
SDK media authorization on another DC are allowed only within the selected media mode.
The instrument disables updates for its connection before connect; it does not change
account settings. Telethon 1.45.0 private send/page seams are deliberately pinned.

Limits bound RPCs through the instrumented client call path, actual SDK history sends
including retries, requested message slots, requested file-chunk bytes and total scan
time. MTProto handshake/housekeeping/packet retransmissions are not counted as those
application requests. The trace records real SDK iterator/page identities; repeated
retries of one page do not constitute a page crossing. Report fields contain IDs,
counts, types, timestamps and hashes, not message bodies, credentials or raw exceptions.

The diagnostic scan advances only a local comparison cursor. It never calls lifecycle
prepare/ack or changes saved run progress. It verifies the state text is unchanged.
A `MATCH` means the scanned IDs/dates/blobs match this oracle, **not** that Gate A passed.
Even a matching scan reports `INCONCLUSIVE` for the whole gate until independent oracle
review, other required cases, persistence receipts and source-interruption observations
are assembled and reviewed. Output files are created exclusively and never overwritten.

Exit 0 means offline preflight succeeded or the individual scan matched with no recorded
operational error and unchanged lifecycle state. It never means whole-gate PASS. Exit 2
means blocked, incomplete, mismatching or failed reporting. A failure with requested live
mode may have source activity; the tool never labels that unknown activity as “no live
connection.” Preserve the actual trace and requalify uncertain observations.

Offline instrument checks:

```bash
python devdocs/work/19-backfill-run-lifecycle/stage-2-state/probe_checks.py
```

They exercise real SQLite, the real Telethon iterator, budget adapter and request types
with synthetic transport and blocked sockets. They are LOCAL/INJECTED evidence only.
