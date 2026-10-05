---
model: unknown
effort: unknown
---

# Merge result — issue #6 / PR #15

The user explicitly authorized the merge after the accepted second review.
PR #15 is **MERGED** into `dev` at
**`45bab7172621f576fa5e4b3265f87ec20da04fd5`**, pushed and recognized by
GitHub on 2026-10-05 at 15:24:18 UTC.

Parents: previous dev `d39a4df275bacf51f814b6a0b281c227d4d17f93` and reviewed
feature head `b021d2930dcd409956e12a727615542d9f07fe9e`. The merge was prepared
in an isolated dev worktree with `--no-ff --no-commit`, its archive-only paths
restored to dev's versions, then committed, tested and pushed in that order.

Exactly ten intended paths changed: README, the public v1 contract, setup.py's
comment, package exports, the façade, three batch modules, test_19 and the
smoke inventory. Git comparison confirms runtime/tests/public docs match the
reviewed feature head. `devdocs/work/`, archaeology and the unrelated guide
delta are unchanged from the previous dev tree. `duncan/` is not committed.

## Merged-code verification

Tests imported `tgdata` and its file module from the isolated merged worktree,
not the feature checkout. Dependencies used the existing project Python 3.11.10
environment with **Telethon 1.45.0**, explicitly asserted before the suites.
Compilation and merged diff checks passed; every runner exited zero.

| Check | Actual passes | Live skips |
|---|---:|---:|
| Message batches (19) | 33 | 0 |
| Read budgets (18) | 28 | 0 |
| Session store (17) | 12 | 0 |
| Health events (16) | 21 | 0 |
| Login checks (15) | 11 | 0 |
| Flood threshold (14) | 11 | 0 |
| Device identity (13) | 5 | 1 |
| Proxy (12), including loopback refusal paths | 5 | 2 |
| Discovery (11), two no-network helpers only | 2 | live helper not invoked |
| **Total** | **128** | **3** |

The 12/13 commands received a nonexistent config within the merge worktree.
Their printed 7/7 and 6/6 totals include skips; actual pass counts are separated
above. No live account/session config or 1.33.1 test run was used. The archive-only
probe files were not copied into dev; their earlier results remain in the
implementation and second PR critique records.

## Archive and closure

`feat/6-versioned-message-batches` is retained as the reasoning archive, including
the original rejected gate, the replacement plan, accepted reviews and this
post-merge record. The unrelated user guide checkpoint stays there. Issue #6
is closed manually because the target is `dev`, rather than relying on default-
branch automatic closure. The temporary merge worktree is removed after success.

The user authorized merging after the §9 model/effort metadata flag was disclosed.
Those metadata remain unverified; this result does not retroactively certify
them. Both technical gates accepted the revision. Live Telegram, arbitrary
deployment storage and a deployed receiver remain outside the offline evidence.
