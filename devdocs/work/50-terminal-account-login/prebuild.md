---
model: gpt-6-astra
effort: xhigh
---
# #50 combined prebuild — PASS

Completed 2026-10-16T10:25:23Z before product edits. Python3.11.10/Telethon1.45.0.
Fourteen combined test groups passed, including eight actual PTY subprocess
scenarios. The candidate code lives only in this work folder; its exact hashes
are in prebuild-result.json and remained unchanged across both full runs.

Actual components: LoginFlow, StoredSession, native SQLiteSession and connection
retirement, ordinary ConnectionEngine verified reader, actual local file/link/
replace/sync operations, real getpass/PTY and first/repeated SIGINT. The source
transport is test41's controlled Service/Wire with actual SDK/TL serialization and
real SRP; sockets are forbidden. No production account or session was used.

Passed: first login, real SRP, missing access_hash, native reader restoration with
no extra SendCode, explicit replacement/default collision, stale/appeared target,
sidecar/symlink/type/noTTY refusal, local save retry, uncertain authorization check,
wait/unsupported/password_setup refusal, old bytes preserved at prepublication
barrier failures, retained old backup on post-replace sync failure, native commit/
close-failure retirement, safe output at DEBUG, unknown secret argument redaction,
getpass echo fallback refusal and output failure after known publication.

Eight PTY scenarios: plain login, password login, replacement confirmation, first
Ctrl-C at input, EOF at code input, first/repeated SIGINT during source/cleanup,
stop before publication, and stop after actual publication. Exit/contents/source
counts and absence of secret echo were asserted in the real child command.

## First attempt and fixture correction

Attempt1 passed11 groups and failed3. All three failures had the same fixture
cause: macOS tempfile paths used `/var/...`, while the candidate resolves the
same parent as `/private/var/...`. Fault hooks compared Path strings without
normalizing that alias, so the parent/replace hooks and during-publication SIGINT
hook never fired. The preflight-fault test then had no inputs because it expected
an earlier injected refusal; this was a consequence of the missed hook.

Corrected only `root=Path(out)` to `root=Path(out).resolve()` in the fixture. No
candidate code or acceptance assertion changed. Re-ran the complete suite, not
only the three failures:14/14 PASS. Attempt1 log/result and attempt2 log are both
preserved. Candidate hashes match across attempts:

The failed PTY transcript contains carriage returns. Its text rendering escapes
them as literal `\r` for clean diffs; prebuild-attempt-1.raw.json preserves the
exact original UTF-8 log string. This is evidence formatting only.

- candidate_login_cli.py:860dedd62bef5b3e13134245f05f6b7d198ebd4321489287dc63b9cc3a467c1f
- candidate_login_file.py:3b526f483d3f0c137ebc45023f2326710781000ec71af090ed83c1b10d001290

This establishes the local composition required by critic.md. It does not qualify
live Telegram delivery, real-account2FA, arbitrary filesystems/active readers or
physical power-loss behavior. Native Python3.7 execution is also unqualified.
The selected plan corrections can now be folded and the implementation promoted.
