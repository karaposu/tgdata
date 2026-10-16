---
model: gpt-6-astra
effort: xhigh
---
# #50 implementation complete under revision 2

Product commit: `df7972828e2e608204a0043c391d895b51210389`.
Base: dev `77f2f53eba8bdc6922127a3b9118bf17de4efabf`.
Branch: `feat/50-terminal-account-login`.

The installed `tgdata-login --config CONFIG [--replace]` command and
`python -m tgdata.login_cli` share one terminal driver. It uses the existing
LoginFlow API, hides phone/code/password input, maintains one event loop and
separates source authentication from native session publication.

The file publisher prepares a private native SQLite candidate, verifies it locally,
refuses collisions/stale targets/sidecars and supports explicit replacement under
the stopped-reader precondition. Prior bytes are protected through replacement
until publication is confirmed. Uncertain publication retains recovery files;
cleanup or output failure does not erase known success. Local retry uses the same
completed credential and performs no new auth request.

## Plan completion

1. Destination/publication owner implemented in login_file.py, including explicit
   parent/backup sync barriers selected for critic Risk1.
2. Native completed-login conversion implemented with actual SDK APIs, own-ID0
   validation and optional account-cache preservation selected for Risk2. Native
   commit/close failures retire the underlying SQLite connection.
3. Terminal driver implemented in login_cli.py with eligible prompts, safe status/
   exit outcomes, explicit authorization-only checking and stop/cleanup ownership.
4. Installed console entry point, public guide and Authentication README added.
5. Permanent suite48 adds18 groups, including eight real PTY child scenarios;
   smoke README updated. Test47 remains assigned to unmerged #45.
6. New/targeted/full suites and isolated installed-command checks passed. Product
   and work records remain separate commits.

The two product modules are byte-identical to the complete prebuild candidate
that passed before product work. No product correction was required during
verification. The prebuild's one fixture-only path normalization and log rendering
are documented in prebuild.md; original evidence is preserved.

## Scope and deviations

No design deviation. The build environment had setuptools65.5 but no wheel/build
package, so installed-command verification used setuptools' offline managed install
in a temporary copy. It generated the actual entry point and verified isolated
imports and exact module bytes. No dependency was downloaded or installed into the
user's active environment.

LoginFlow, StoredSession, ConnectionEngine, TgData, package exports/version and
ordinary reader behavior are byte-unchanged from the base. No custom-store plugin,
durable CLI checkpoint, reader rotation lock, live Telegram login, ScrapeOps change,
version bump, PR, merge or release occurred. The command's supported publication
contract is local POSIX with a trusted directory and operator-coordinated readers.

## Review handoff

Next: merge check against triage, description, folded revision2 plan, critic and
actual product diff; product-only PR; fresh in-session critic-d review. Work-folder
documents stay on this archive branch. §9 gpt-6-astra/xhigh was verified for this
session. #45/PR49 is separate and still awaits its own merge decision.

The original checkout stays on its old branch with the user's uncommitted version
edit. That edit, duncan and unrelated guide files are not part of this delivery.
