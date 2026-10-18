---
model: gpt-6-astra
effort: xhigh
---
# Implementation stopped: source ownership starts too late

The candidate is not safe to publish. It was copied into the existing archive
checkout after a passing combined suite, but a further native verification exposed
an uncovered connection-creation boundary. The copied/staged product changes have
now been withdrawn. Exact candidate files remain committed at4a65f88 under
prebuild/candidate/, and the isolated executable candidate remains in /private/tmp/
tgdata-60-media-prebuild/candidate. No product commit, PR, merge or release was made.

## Reproduced failure
The public get_message_batch(download_concurrency=3) path receives FileMigrateError
and enters real Telethon1.45 _create_exported_sender. A native MTProtoSender connects
to a controlled transport and starts its real send/receive loops. The root client's
ExportAuthorization response is held. Cancellation then returns from the public read.

Observed BEFORE fixture cleanup:
- public task cancelled and ExportAuthorization future cancelled;
- newly created sender and transport still connected;
- native send and receive loop tasks still running;
- new sender absent from the original client's borrowed-sender cache;
- temporary files cleaned, showing file cleanup alone does not settle source work.

The fixture then disconnects the orphan to leave the test environment clean. That
cleanup is explicitly excluded from product success. No real account/socket/network
was used; actual sender connection/task lifecycle executes over a controlled wire.
Script, raw output and JSON are in prebuild/export_creation_probe.* and
export-creation-first.txt. The probe exits1 with its original ownership assertion.

## Why this is architectural
The plan records iterators after their creation and closes their assigned sender.
During export setup the new connection exists before _borrow_exported_sender returns;
the iterator still refers to the primary sender. Neither its finalizer nor normal
client-cache cleanup owns the new connection. Closing the gap requires changing
when and how source resources are registered and handed off, including direct SDK
sender admission during authorization. This is beyond a local name/call-site fix.

The task-impl Experiment FAIL and Verify gates require stopping, deprecating the
plan and recording the measured premise. No architectural patch was attempted.
No question to the user is needed: the previously unknown behavior is now observed.
Re-plan around creation-to-cache-transfer ownership, then fresh critique and a full
combined prebuild including this exact scenario. Existing windows, forwarding and
prefix tests may be reused after that contract is reviewed.

## Verification record, without hiding failures
Initial candidate:1,051 offline checks/35 suites/seven demos passed, three live skips;
38 new concurrency groups and a public CDN payload case passed. The native creation
probe demonstrates that this was incomplete coverage. Three earlier local corrections
are fully recorded in prebuild/corrections.md and are not the architectural failure.

After copying the exact candidate,643 affected checks/21 suites passed. The final
full run failed the existing35ms heartbeat test because it observed2 rather than3
wait ticks under parallel load. The unchanged31-test heartbeat suite then passed
standalone; no test expectation or product code was changed for that timing result.
All logs retained. This timing rerun does not close the independent ownership defect.

Current result: FAIL / implementation aborted, not a qualified feature. Package/main/
dev remain the published0.1.3 product. Original user checkout/version edit untouched.
