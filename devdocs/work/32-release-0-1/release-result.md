---
model: unknown
effort: unknown
---

# tgdata 0.1 published and verified

Completed on 2026-10-14. Version PR #33 merged into dev as e5cdad77ff6af41f21503fc43fe3180d5213a41e; promotion PR #34 merged into main as **1ddfb4ec7d43a05e36f464646fd4f867e5076c0c**. The annotated v0.1 tag peels to that exact main commit. The actual main tree and all 91 recorded source hashes match the qualified candidate.

[GitHub release](https://github.com/karaposu/tgdata/releases/tag/v0.1) published at 07:57:21Z. [Publishing run 38531759612](https://github.com/karaposu/tgdata/actions/runs/38531759612) succeeded from the release event with head SHA 1ddfb4e and branch v0.1. Build and publish both succeeded. No completion was inferred from release creation alone.

[PyPI 0.1](https://pypi.org/project/tgdata/0.1/) contains two non-yanked files, downloaded after publication and verified against their advertised SHA256s:

- Wheel: cc2e95a341ea51f393487d7b81d58f7b9ae31a081a504e92b2e85ae5311f10b3; uploaded 07:57:45.928008Z.
- Sdist: 0a0ebfaf6e7e79c61711ad2aeb0781f7075b833b2bd5cf748d97aec7cb9e9aee; uploaded 07:57:47.416752Z.

Both real published distributions contain all 84 expected Python package files, including 37 runtime modules, with exact candidate bytes. Their version, dependency bounds/extra, Python floor, README and worker entry point pass. The actual published wheel installs into a fresh isolated target, imports the current public login/pool/batch/progress/budget APIs and runs the installed worker --help. No running consumer environment was changed.

The single completed qualification run passed 773 executed offline checks in 28 suites and five demos; three live skips are excluded. Earlier sandbox/decoder harness failures remain recorded. Native Python 3.7, live onboarding and two-account failover are not newly qualified by this release. New proposals 29–31 and automatic pool joining are excluded.

GitHub automatically closed #17/#32 on promotion because earlier closing keywords reached main. Both were reopened: #17 must stay open for its deferred two-account gate; #32 could close only after this actual publication/read-back. The release tracker is now ready to close as completed.

## Workspace handoff

The maintainer's original checkout remains on feat/7-group-operations at a47ba80 with the local 0.1 version edit preserved. That checkout remains old source despite its version declaration. Product release and future release tags use main, not that archive branch. Work-folder records stay on fix/32-release-0-1 and are excluded from dev/main; old branches and local notes are retained. Version 0.0.9 has not been retargeted, replaced or yanked. ScrapeOps has not been installed/upgraded by this release operation.
