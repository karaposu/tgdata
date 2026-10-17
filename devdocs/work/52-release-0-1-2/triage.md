---
model: gpt-6-astra
effort: xhigh
---
# #52 release triage

Maintainer authorizes tgdata0.1.2 publication. Heavy release maintenance: the source
edit is small, but main/tag/artifact identity and immutable upload cross boundaries.
Same warmed #43/#44/#45/#50 session. Current model/effort context2026-10-17T05:31:10.919Z
is gpt-6-astra/xhigh. No subagent; no missing AGENTS.md or PROJECT_SPECIFICS.md.

Refreshed full setup.py and publish workflow, CONTRIBUTING branch/release rules,
prior#40 description/plan/critic/artifact/install/provenance scripts and release
results. Reviewed current main→dev inventory and package-version references.
Runtime source already qualified/reviewed through PR47/48/51;#49 remains outside dev.

Bounded surface: (1) __init__.py/read_version and four exact version assertions,
(2) source-only git archive, wheel/sdist payload and installed command paths,
(3) reviewed dev/main PR transport, (4) annotated tag/release-event publisher,
(5) actual PyPI metadata/files/hashes and isolated installation, (6) archive tracking.
All six are confirmed in code/previous actual release evidence. No new auth/runtime
feature, external coordinator, dependency or workflow is proposed. Preserve user's
stale checkout/version edit, duncan, other branches/releases and live-test deferrals.

Only version-bearing product paths:tgdata/__init__.py and smoke suites42/43/45/46.
Publish workflow runs on release.published, builds via python -m build and uses the
existing PYPI_API_TOKEN secret (name/presence only inspected). Build tools are not in
the active runtime; use a separate temporary environment.0.1.2 PyPI/tag absence was
observed from public vendor metadata, not assumed. Future upload success is a later
observation, never a local qualification claim.

Traverse decision: not needed. Prior0.1/0.1.1 release procedures already established
the source/tag/package boundary and address the wrong-branch0.0.9 failure. Repeat
real qualification with current files and new entry points; do not repeat an inquiry
about a settled mechanism. No planning blocker. Execution gates are complete build/
full suite/install, reviewed transport, fresh version/tag absence and actual upload
read-back. Retain first failures and do not relax payload/metadata expectations.
