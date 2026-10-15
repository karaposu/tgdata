---
model: gpt-6-astra
effort: xhigh
---
# #43 merge verification — PASS

The maintainer explicitly authorized merging after both review gates passed.
[PR47](https://github.com/karaposu/tgdata/pull/47) merged into dev at
`490cf5f4aaf682a1ed9fcf8c680be56f2ec14c92`, confirmed by GitHub at
2026-10-15T19:41:00Z. No branch was deleted.

## Reviewed and tested identities
- Previous dev: abd1f577c928cc22c08cdbd9580c2d916e98c64b.
- Reviewed product-only PR head:72f51313214a318d59eb9fc43e652ae64bf67159.
- Isolated local merge candidate:adc0c86980de3a8d5c8e99043fc1e5054badf1e0.
- Candidate and published merge tree:e2fe693be8f39932dd28f2f7912012616fc3178f.
- Archive branch:feat/43-richer-group-profiles; PR branch:
  feat/43-richer-group-profiles-pr. Both remote branches were verified retained.

The candidate was made by an actual no-fast-forward merge of the reviewed head
onto the unchanged dev base, without conflicts. Full tests ran before publication.
The PR head/base were checked again immediately before gh pr merge with an exact
head-commit guard. After publication, fetched dev's actual merge has the expected
two parents and the **identical entire Git tree**. All100 Python SHA256 values
also match the merge-test manifest. See merge-parity.json.

## Tests on the merge candidate
**952 actual offline checks across32 suites, all7 demos PASS;3 live skips.**
All100 Python sources compile and pass Python3.7 grammar checks on actual
Python3.11.10 / Telethon1.45.0. Native Python3.7 is not claimed.
Evidence: evidence/merge-candidate/result.json and individual logs.
The existing driver was copied to verify_merge.py only to take the merge root
and keep this run's output separate; suite selection/assertions are unchanged.

This run enabled local loopback for the existing proxy tests. Explicitly missing
config paths kept all live checks disabled. No fixture/product correction was
needed; every selected suite passed in this merge run. No real account login,
join, Telegram permission qualification or account-budget change was performed.

## Preservation and closeout
Only the eight reviewed product/test/public-doc paths changed from dev.
Dev's devdocs/work and archaeology trees are unchanged. The original user's
feat/7-group-operations checkout still has its existing tgdata/__init__.py edit;
it was neither committed nor overwritten.

Main remains2e6edf2a3b2c016f9fea4a43b5edffd25fc9cf8e and version remains0.1.1.
No release, tag, PyPI publication or consumer deployment was performed.
Current-turn model/effort verified as gpt-6-astra/xhigh
(2026-10-15T19:37:26.609Z). Reviews remain f7f88b6 (merge fidelity) and afb7428
(fresh critic accepted,0 High/Medium/Low;13 groups/29 fresh probe cases).

#43 is complete on dev and may be closed manually because the default branch is
main. #44/#45/#46 remain separate requests; this merge starts none of them.
