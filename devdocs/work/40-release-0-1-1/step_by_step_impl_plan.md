---
model: gpt-6-astra
effort: xhigh
---
# Gated0.1.1 publication — revision2

**Critic folded:**2026-10-15 — zero mitigations; required complete qualification PASS before adoption. Real wheel/sdist/install,914 offline checks/31 suites/7 demos pass with3 live skips. Tool setup corrections and exact manifests are retained in qualification.md/evidence. Steps and source scope unchanged.

### What is the task
Publish the already reviewed main product as0.1.1, proving source/tag/artifact identity before and after upload. Inputs: desc.md, triage340202a, completed main promotion05904d1 and prior0.1 release records. Reuse existing archive/product branches; no new branch or consumer deployment.

### Huge Hard Blockers
#### Planning Blockers
None OPEN. main05904d1 and dev7d9840f have identical product trees. setup.py parses the version from __init__, and the sole publish workflow triggers on GitHub release publication. PyPI0.1.1 and tagv0.1.1 are absent. No unknown release architecture is assumed.
#### Execution Blockers
No unavailable external prerequisite identified. Real build/test/install qualification gates adoption. Reviewed version and promotion merges gate tagging. Successful release-event CI/PyPI read-back gates completion. A vendor failure is observed and diagnosed; it is never replaced by a local success assertion.

### How this implementation moves toward desired state
Freeze the correct source, prepare a source-only candidate with three exact version substitutions, qualify real artifacts/full suites before adoption, then transport those exact bytes through reviewed dev/main PRs. A new annotated tag names the verified promoted main SHA. Publish once via existing CI, download actual results and compare them to that candidate.

### High-Level Summary
| Step | Change | Output |
|---|---|---|
| 1 | Qualify complete source/package candidate | Full tests, real wheel/sdist and isolated import proof |
| 2 | Adopt exact version/test edits and review version PR | Three-file product commit, reviewed dev merge |
| 3 | Review/promote exact product to main | Verified published main SHA/tree |
| 4 | Publish new pinned-main tag/release and verify PyPI | Actual downloaded artifacts/install and release closeout |

## Mandatory experiment before production adoption
After fresh critic-d, prepare the entire candidate from git archive of main05904d1 in a temporary directory. Change only `__version__ = "0.1"` to0.1.1 and the two exact __version__ assertions in suite42/43. Build wheel and sdist using the existing isolated build-tool environment; inspect all files/metadata and install the wheel into a new isolated target. Run all31 offline suites/7 demos with Telethon1.45 and missing config for optional live checks. Record hashes and logs, compile/parse Python3.7 grammar without claiming native3.7. A package/source mismatch disqualifies publication; do not remove new files or weaken expected parity. The exact version assertions change because the requested version changes, not to hide a failed feature test.

## Step1 — Complete candidate and real artifacts
### Proposed changes
Create source-only temporary archive, apply exactly the three substitutions, compare every tracked package/example source to frozen main with those transformations only. Reuse the prior artifact verifier with explicit root/version arguments. Verify exact package file set and bytes in both wheel/sdist, README/setup parity, Name/Version/Requires-Python/dependency-extra bounds and tgdata-worker entry point. Refuse unexpected session/config/env/work-folder/Duncan payloads. Record artifact SHA256s without assuming independently built ZIP/tar bytes are reproducible. Verify installation into a fresh target using existing qualified runtime dependencies (no upgrade of the user/consumer environment), actual module paths and installed worker --help. Confirm the three newly delivered APIs/defaults/heartbeat signatures. Run full source suites once and bind evidence to hashes.
### Output
Qualified candidate/source manifest, complete offline evidence and real wheel/sdist/install results.
### Safe in nature
False — validation must identify the exact release product; wrong-source acceptance is irreversible downstream.
### Peripheral concepts
setuptools/build discovery, version parsing, wheel/sdist metadata, installed import paths, worker entry point, existing source reviews.
### Hardness Lvl
3

## Step2 — Product adoption and dev PR
### Proposed changes
After complete PASS and fold, copy only the three candidate version/test edits onto the existing archive branch; commit product separately from evidence. Fast-forward existing product branch to current dev and cherry-pick only that product commit. Verify every candidate hash still matches. If dev moved, inspect the actual difference; never silently upgrade source. Write/commit/post merge-check, open version PR into dev with `Tracks #40` (not Closes; publication is unfinished), and fresh same-session critic-d over actual diff plus folded plan. Probe correct/mismatched package refusal, version/metadata parse and transport equality. Any Medium/High rejects under CONTRIBUTING. Merge with exact head SHA only after gates pass; verify merged tree equals candidate.
### Output
Reviewed exact0.1.1 product on dev; issue remains open.
### Safe in nature
False — changes externally observable version and must preserve reviewed source identity.
### Peripheral concepts
PR transport, archive separation, existing branch reuse, release tracker honesty.
### Hardness Lvl
2

## Step3 — Main promotion
### Proposed changes
Create dev→main PR on existing branches, compare real GitHub merge candidate with qualified full tree and source hashes, account for prior main-only merge metadata, and record/post promotion fidelity and fresh provenance critique. No novel code conflicts are permitted without inspection/review/testing. Merge with pinned dev head. Fetch published main and prove exact tree/parents; no redundant full suite on unchanged bytes. Keep all branches. Do not tag until this resulting main SHA is known and verified.
### Output
Exact qualified release source on main, ready for its new tag.
### Safe in nature
False — production source authority changes through reviewed promotion only.
### Peripheral concepts
Main ancestry, merge candidates, reviewed integration, version consistency.
### Hardness Lvl
2

## Step4 — One publication and observed read-back
### Proposed changes
Recheck PyPI0.1.1, tagv0.1.1 and GitHub release absence. If an existing matching publication appears, verify it instead of overwriting. Create an annotated v0.1.1 at the exact verified main SHA, push only that tag, and read back its peeled commit. Publish GitHub release with --verify-tag and reviewed notes covering albums/photo trails/heartbeat, opt-in behavior and SDK wait limits. No old tag is retargeted. The user already authorized publication; no redundant confirmation is needed.

Observe the matching release-event workflow by head SHA/tag and inspect failures if any. Read PyPI JSON for actual0.1.1 filenames/URLs/digests; download only those actual wheel/sdist files, verify advertised SHA256 and the complete candidate payload/metadata. Independently install the real published wheel into a fresh target and verify imports/API/signatures/version/worker help. Never claim completion from release creation alone. On ambiguous create/push/upload response, read tag/release/run/PyPI state before retrying. Do not rerun upload blindly if a version/file may already exist.

Archive final source/main/tag/workflow/PyPI/artifact/install evidence, update PRs/tracker and close#40 only after observed success. Preserve the original stale checkout/user edit, existing branches, old releases and live-validation deferrals. No ScrapeOps requirement/environment/deployment mutation.
### Output
Published and verified0.1.1 with correct exact-main source and durable provenance.
### Safe in nature
False — public version publication is irreversible; strict identity and read-back gates apply.
### Peripheral concepts
Immutable PyPI versions, annotated tag peel, GitHub release workflow, ambiguous replies, actual remote files, consumer isolation.
### Hardness Lvl
3
