---
model: gpt-6-astra
effort: max
---
# #8 merged into dev

**PR:** https://github.com/karaposu/tgdata/pull/28
**Merge:** f92749688b7d544da55249459c489164497d47ed
**Merged at:**2026-10-14T05:36:14Z (GitHub confirmation).
**Authorization:** the user's “go ahead” after both review gates passed.

The merge has parents c4e6eac89341b204b2749e9d15add578e0706965 (dev) and
99ea00123c98218cb47e8f391ef00c8add162fea (reviewed feature head). It adds exactly
the eight reviewed product paths. All78 #8 work/evidence paths were excluded from
the merged tree; dev's existing work/archaeology content was preserved. The feature
branch remains the archive. No force push, branch deletion or main-checkout switch.

## Merged-code verification — PASS before push
Executed in `/private/tmp/tgdata-28-merge-verification` at the actual merge commit,
with package import location asserted under that checkout. `verify_merge.py`
reuses the full verifier against that tree and stores evidence under
`merged-verification/`; no work documents need to ship in dev to run the product.

-28 supported suites passed:773 executed offline cases,3 explicit legacy live skips.
-All5 offline examples passed, including the new login and existing worker examples.
-Compile, package imports, Python3.7 grammar, candidate byte parity and factory AST
  parity passed on Python3.11.10 / Telethon1.45.0.
-Reviewed product tree parity and archive exclusion were asserted before and after
  verification. Source hashes remained unchanged; merged worktree was clean.
-All33 child jobs finished without a watchdog timeout. Full logs/results are in
  merged-verification/result.json and sibling logs.

After verification, pushed the two-parent merge to dev without force. GitHub reports
PR28 MERGED at this exact commit; local dev was advanced by compare-and-swap from
the verified old base. The original checkout remains feat/7-group-operations with
its untracked HANDOFF.md/todo.md; unrelated/duncan work is untouched.

## Qualification that remains open
Live Telegram code delivery and real-account2FA acceptance were not run. The merged
guide states that limit. No real code/password was requested or production credential
replaced during verification. Native Python3.7 and physical proxy exit-IP checks
are not claimed. #17's two-account live validation remains separately deferred.

Issue8 can close as completed for the reviewed implementation. Any later live
qualification should retain these distinctions and use an explicitly authorized
account/setup; it is not an instruction to log in automatically now.
