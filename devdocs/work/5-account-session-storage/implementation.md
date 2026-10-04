---
model: GPT-6 (Codex)
effort: unknown
---

# Implementation — issue #5

Continued on 2026-10-05 from `0162acd`, plan revision 2. The interrupted work
had left `tgdata/session_store.py` untracked; neither Step 2 wiring edit had
been applied. The five-step implementation plan is complete and verified.
Code, tests and user documentation are committed in `a0e0779`; this record and
the warming documents are kept in a separate documentation commit. This is
the initial checkpoint; the later PR review and regenerated implementation
are recorded below.

PR preparation: the maintainer specified a small SQLite-table example rather
than the initial dictionary example. `7a2f549` makes that documentation change.
The exact README class was executed with a temporary database and synthetic
session: save, reopen, exact key restoration, quoted account name and delete
all passed. Step 5 on GitHub #5 is now checked with the published commits.

## Changes

- Retained and completed `StoredSession`: opaque versioned persistence of the
  auth key, data centre, update states, group/channel cache and own identity;
  exclusion of message senders; deterministic ordering; unchanged-save elision;
  stale-login check; credential-free failure logs; optional delete and in-memory
  clones.
- Added `session_store=None` at the end of both constructors. The single
  connection factory selects a `StoredSession` only when a store is supplied.
  Persistent, pooled and short-lived connections keep their existing names.
  The default still passes the original name to Telethon's file session.
- Added the README store contract and example, constructor/factory docstrings,
  and the `test_17_session_store.py` smoke-test entry.
- Added twelve offline test groups covering the plan's scenarios, including
  an empty/falsey store, exact 64-bit access hashes, 500 excluded message
  senders, real disconnect/auth-key-save/log-out paths, first-login decisions,
  stale writers, optional deletion, mixed rows and health identity. The new
  suite refuses socket connections and uses synthetic credentials throughout.

## Implementation detail corrected during verification

The inherited decoder used permissive base64 decoding. A probe inserted
`auth_key = "!!!!"` into an otherwise valid stored record and printed:

```text
Malformed stored key accepted as a new session: True
```

That would violate the plan's requirement that damaged saved data never looks
like a first login. Decoding now validates both base64 layers and requires a
non-null auth key to contain 256 bytes. Empty, invalid and short encoded keys
are rejected before client construction. Parse errors also explicitly suppress
exception chaining with `from None`, as Step 1 specified. These cases are in
the failure test. The public format and store interface did not change.

The README explicitly states the existing concurrency boundary from critic
Risk 3: checking and saving are separate operations. This is not atomic
compare-and-set across processes; no richer store interface was added.

## Verification

Environment: project `.venv`, Python 3.11.10, Telethon 1.45.0, pandas 2.3.1.

| Suite | Executed and passed | Live checks skipped |
|---|---:|---:|
| `test_17_session_store` | 12 | 0 |
| `test_16_health_events` | 21 | 0 |
| `test_15_login_checks` | 11 | 0 |
| `test_14_flood_threshold` | 11 | 0 |
| `test_13_device_identity` | 5 | 1 |
| `test_12_proxy` | 5 | 2 |
| Total | 65 | 3 |

Commands: `.venv/bin/python -m tgdata.smoke_tests.<suite>`. For test_12 and
test_13, an explicit nonexistent config path inside a temporary directory was
passed, so their live checks skip without reading the account's real config.
The existing scripts count skips as successes in their final banner; the
table above separates them.

The first proxy run could not bind its localhost test server in the sandbox.
It was rerun with localhost access, and all five offline/loopback checks
passed. No live Telegram connection or login was attempted.

The three runtime modules and new test byte-compile. `git diff --check` passes.
The stricter decoder's tests were rerun after that correction; the existing
default-file regressions had already passed with the constructor wiring.

## Initial review boundaries

- Critic Low 7 remains accepted: the two connect-time save points are not
  exercised through Telethon's real `connect()` in this suite. Real disconnect
  and auth-key-save paths are exercised; login decisions use a stand-in.
- Live restoration with Telegram is unverified, as specified by the plan.
- The unrelated `devdocs/guides/group_discovery.md` edit is excluded from
  implementation and documentation commits.
- Merge-gate and PR-critic checkboxes are not complete. No merge or deployment
  is part of this implementation checkpoint.


## Regenerated implementation after the PR critique

PR #13's first review (`a6deab7`) found one Medium: an old client's logout
preserved a newer key during its save, then deleted it. Revision 3 was
regenerated (`cc665f4`), critiqued (`c663b4c`), and folded into revision 4
(`ab91f87`). Runtime/test/user-documentation changes are in `46aef9c`.

The adapter now uses `_may_mutate()` for both changed saves and optional
deletion. A stale or unreadable current record cannot be removed. The expanded
real-logout regression failed before this change and passes afterward.

The six suites were rerun on the final runtime code: 65 offline test groups
passed, 3 live checks skipped. The real-connect/restore/disconnect/logout
probe also passes; the old P4 failure is now asserted to preserve the newer
login. The exact SQLite example passed with two database connections, stale
real logout, reopen, exact-key restoration and ordinary owned deletion.
This probe exercises the actual connect-time saves, improving the initial
Low-7 evidence described above. No live Telegram operation was performed.

Final integration still needs the maintainer's go-ahead and §9 model-rule
disposition. The branch and its work documents remain the archive.

The repeated merge check and round-two PR critique now pass their respective
checks; see `merge-check.md` and `pr-critic.md`. The first rejected critique is
preserved in `pr-critic-round1.md`. No High or Medium remains in the final code
review. The feature is still unmerged pending the two maintainer decisions above.
