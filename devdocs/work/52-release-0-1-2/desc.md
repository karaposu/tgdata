---
model: gpt-6-astra
effort: xhigh
---
# Publish tgdata0.1.2

Same warmed session; triage4c803b4. Source authority: reviewed devbbc0fd6,
main2e6edf2; no base drift. Existing archive/product branches reused. §9 verified
GPT6 Astra/xhigh. No subagent or unrelated checkout change.

## Problem Statement
PyPI0.1.1 predates merged richer profiles(#43), activity measurement(#44) and terminal
login(#50). The maintainer explicitly requests0.1.2 publication. The earlier0.0.9
incident showed that tagging a stale feature checkout publishes the wrong code.

## User Value Proposition
Install the complete reviewed library from PyPI with traceable source/main/tag/
artifact identity and the new tgdata-login command, without copying repo files.

## Success Criteria
1. Candidate is devbbc0fd6 with exactly five0.1.1→0.1.2 substitutions: package
   __version__ plus existing assertions in smoke42/43/45/46. No other behavior change.
2. Source-only complete candidate passes34 offline suites/seven demos with Telethon
   1.45.0; live skips remain explicit. Both wheel/sdist contain every expected Python
   file with exact bytes, correct metadata/dependencies/extras/README and both commands.
3. Actual wheel installs into a new isolated target; all exports/new APIs, heartbeat
   defaults, worker/login help/headless and real installed native-SRP stop work.
4. Reviewed version PR into dev and dev→main promotion carry exact qualified bytes,
   with work docs excluded. New annotated v0.1.2 names the verified main merge.
5. Existing release workflow succeeds; actual PyPI0.1.2 files are non-yanked, their
   advertised hashes/content match, and a fresh installed published wheel passes.
   Tracker52 closes only after observed publication/read-back, not version adoption.

## Scope Boundaries
No new feature, SDK/dependency/workflow change, tag reuse/retarget, prior-release
yank, live login or ScrapeOps deployment. PR49/history sampling remains excluded.
Preserve original user's checkout/version edit and both branches. Native3.7,
other-host/live Telegram limitations stay explicit; syntax checks are not live proof.

## Priority Level
High: deliver the explicitly requested installable reviewed library. Publication is
immutable, so the small source delta still requires full provenance qualification.

## Known Blockers
No OPEN planning blocker. Actual complete artifact/install qualification gates
adoption; reviewed main and fresh tag/version availability gate publication; actual
workflow/PyPI read-back gates completion. Existing build-tool environment and publish
secret name are available; their past success does not promise this run's success.
