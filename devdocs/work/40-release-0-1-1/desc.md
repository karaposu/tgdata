---
model: gpt-6-astra
effort: xhigh
---
# Publish tgdata0.1.1

Session warmed at340202a against main05904d1 / dev7d9840f in the continuing feature/review/promotion session; triage.md records refreshed packaging/publication reads and verified GPT6 Astra/xhigh. Reuse existing archive/product branches; preserve the original stale checkout and its user version edit.

## Problem Statement
Album assembly, optional photo trails and batch heartbeats are reviewed and on main, but the current PyPI0.1 package predates them. The maintainer explicitly requested version0.1.1 and publication. A previous wrong-branch0.0.9 release demonstrates why changing a version in an old checkout is insufficient.

## User Value Proposition
Consumers can install one verified release containing the complete reviewed main product, including heartbeat support required by ScrapeOps's continuation watchdog. Publication has a traceable source/tag/package identity.

## Success Criteria
1. The candidate is main05904d1 with exactly __version__0.1→0.1.1 and the same expected-version update in the two existing export tests. No runtime behavior/dependency/workflow change.
2. Real wheel/sdist builds contain all expected package files with exact candidate bytes, correct0.1.1 metadata, README, Python/dependency bounds and worker entry point. Installation into an isolated target exposes the new APIs/heartbeat signatures and runs worker help without Telegram.
3. All31 supported offline suites and7 demos pass on Telethon1.45.0, with live skips reported. Complete package qualification precedes product adoption and publication; actual source hashes are recorded.
4. Version PR and fresh review pass into dev; promotion PR/review moves the exact qualified product to main. Tagv0.1.1 is new, annotated and pinned to that resulting main commit. Existing releases/tags are never moved or overwritten.
5. The GitHub release triggers the existing publish workflow. Completion requires the matching release-event run, actual PyPI0.1.1 files, verified advertised hashes and exact runtime/metadata parity, plus a fresh isolated install of the published wheel. Ambiguous mutation responses are read back before any retry.

## Scope Boundaries
No new features, CI redesign, SDK change, old-version yank, release-tag reuse or changes to running ScrapeOps. This publishes the reviewed library only. Work artifacts stay on the archive branch; product merges contain the three planned version/test edits. Deferred live account/pool validation remains deferred.

## Priority Level
High: deliver the reviewed updates as an installable package, especially the batch heartbeat. The small source edit does not reduce the rigor required for irreversible package publication.

## Known Blockers
No OPEN planning blocker. Build/install access, reviewed main promotion and actual vendor publication are execution conditions checked in sequence. PyPI0.1.1/tag availability was verified; recheck before irreversible publication. Vendor success cannot be certified before it happens and must be read back afterward.
