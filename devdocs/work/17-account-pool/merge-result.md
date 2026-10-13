---
model: gpt-6-astra
effort: max
status: MERGED_LIVE_E1_PENDING
---
# PR26 merged — #17 account routing and failover

User authorized the merge with “go” after being told that both review gates passed
and two-account live E1 remained pending. **Merged and pushed into dev as
c4e6eac89341b204b2749e9d15add578e0706965.** GitHub reports PR26 MERGED at
2026-10-13T19:51:34Z. Prior dev2ddb852 is the first parent; reviewed feature head6e500f9
is the second. The product remains byte-identical to reviewed007c2e4.

The isolated integration checkout is `/private/tmp/tgdata-26-merge-verification`.
The merge was conflict-free and contains exactly the23 reviewed product paths.
All devdocs match the pre-merge dev tree: feature work, inquiries and archaeology
remain on the retained feat/17-account-pool archive branch. Main checkout and other
issue worktrees were preserved. No runtime fix or plan change was made during merge.

## Merged-code verification

**750 executed offline groups and3 demos PASS;3 explicit live skips excluded.**
All27 supported suites12–19/22–40 ran on the archive-free integration checkout in one
complete attempt. Pool31:46/46, lifecycle39:48/48, outcomes40:25/25; worker37:33/33 and
worker38:25/25, including67 controlled worker subprocesses. No watchdog or failed test.
Missing configs explicitly disabled legacy live checks; test12 used owned loopback
proxy controls. No Telegram account, credentials or live allowance was used/reset.

Compile and Python3.7 grammar passed for88 Python files using Python3.11.10 and
Telethon1.45.0. No native3.7, real proxy/account visibility or two-account live claim.
All source/test/example hashes stayed unchanged, and executable P0 parity/35 promoted
function checks also passed through the unchanged implementation verifier.

[Complete run](evidence/merge-verification/attempt-1/summary.json),
[merge/tree/product audit](evidence/merge-verification/merge-audit.json), and
[reproduction adapter](probes/verify_merge.py). The evidence folder contains every
suite/demo log. The adapter changes only the verifier's source/output roots; it
retains all commands, assertions, parsers and test expectations.

The exact no-commit merge tree was tested before committing/pushing. Its23 product
hashes were checked against the reviewed diff before/after testing and again after
commit. Remote dev was refreshed and still matched the tested first parent immediately
before push. GitHub then recognized the PR as merged; local dev was fast-forwarded
without switching the user's checkout. The reviewed extra EOF blank line in
pool_observation.py was left unchanged; no formatting claim is inferred from test PASS.

## Remaining live qualification

**E1 remains OPEN. Issue17 stays open to track it; merging did not tick live step7.**
The existing-access implementation and review/merge gates are complete. The outstanding
service test still requires two approved logged-in accounts, one shared readable group
and their existing bounded allowance. User had selected one-account/offline-first;
merge approval does not manufacture those resources or complete the test.

Automatic joining remains outside the selected first delivery. No live account
operations or deployment occurred during this merge.

The feature archive retains this merge evidence in a subsequent work-only commit,
while dev remains at the product merge. Original checkout stays feat/7-group-operations
with its untracked HANDOFF.md/todo.md unchanged. Duncan and unrelated work were not staged.
