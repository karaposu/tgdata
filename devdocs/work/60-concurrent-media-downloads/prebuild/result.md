---
model: gpt-6-astra
effort: xhigh
---
# Combined native prebuild — qualification withdrawn

**Current gate: FAIL.** The later native exported-sender creation probe found a
connection and both native SDK loops still alive after public cancellation. The
sender was not yet in the client cache. Initial suite/CDN evidence below remains
historically true, but did not cover this creation boundary and is insufficient.
See ../verification/blocked.md. All adopted product changes were withdrawn.

Frozen devd8232d1, git-free candidate at /private/tmp/tgdata-60-media-prebuild/candidate.
Planrevision1 plus selected robust nested-scope mitigation; no product code changed
on the working branch. Exactly15 planned product/test/doc paths differ. Every tracked
candidate file has a SHA256 in manifest.json;113 tested Python sources are unchanged.

Complete35 offline suites:1,051 actual checks and seven demos PASS; three optional
live skips excluded. Python3.11.10 / Telethon1.45.0. Compile/3.7 grammar113 PASS;
this is not native3.7 or live Telegram proof. The38 new groups execute actual SDK
history/file/retry paths, native files, budgets, observer contexts and public delivery.
A separate public batch→SDK CDN redirect→helper→file probe verifies272 plaintext bytes,
real GetCdnFileRequest, helper cleanup, unchanged parent connection and copied zero-
wait/zero-retry policy. Controlled transport supplies responses only, not ownership.

Observed overlap: native file requests peak1 at default and3 when opted in, returned
batch bytes/identity equal across both. Out-of-order completion and a later saved file
do not cross an earlier failure. Daily failure replay/ack and pool cancellation capture
retain only complete prefixes. Cached/internal/propagated waits, source-refresh budget,
callbacks, repeated cancellation during actual exported-return state changes, CDN
creation cancellation, cleanup failure isolation and local file collision covered.

First25 new groups and existing batch33/heartbeat31 passed. Expanded35 groups found
two local corrections: missing wrapper on SDK-internal iterator close and a reuse
fixture using the deliberately uncached octet-stream extension. Both original failing
assertions stayed. A new queued-stop test then found a missing source-admission
cancellation checkpoint. Adding sleep0 before admission closes that existing contract;
assertion of one history request stays. Failed cases reran PASS before this full run.
All first outputs and corrections.md retained. No structural design repair, exception
contract relaxation, SDK version substitution or live-performance claim.

Fold Risk1 into planrevision2 now; adopt only exact15 candidate files. Subsequent
product verification and code/work commits remain required; merge/PR/release separate.
