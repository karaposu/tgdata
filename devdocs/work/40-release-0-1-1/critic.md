---
model: gpt-6-astra
effort: xhigh
---
**REORDER — TEST BEFORE BUILD**

Falsifier: the actual0.1.1 wheel/sdist or installed package omits/differs from the frozen reviewed source, exposes the wrong version/API, or fails the complete offline qualification after only the three intended version substitutions.
Affordable now: yes — local source archive, real packaging backend, full suites and isolated installation; no upload or live account required.

Experiment: construct the full candidate from main05904d1; change only the version declaration and two exact expected-version assertions. Build wheel/sdist; verify complete payload/metadata/README/entry point against candidate bytes; install the real wheel into an isolated target and check current APIs, heartbeat signatures and worker help. Run all31 offline suites and7 demos on Telethon1.45.0, with missing-config live skips and subprocess watchdogs. Record all hashes/results before adoption.
Cost: local build/test/install work; installed build tools and qualified runtime are available.
Must precede: production adoption in Step2, any version merge/tag/publication.
Disqualifying result: correct source cannot produce/install the required package without runtime/packaging redesign, missing files must be excused, or feature expectations must be relaxed to accept the candidate.
Passing result: both actual packages contain the exact source and expected0.1.1 metadata, isolated import/CLI works, all named suites pass and source remains unchanged. Then record result, fold, adopt exact edits and continue reviewed promotion/publication.

Result: PASS — actual wheel/sdist each contain all90 expected Python package files (40 runtime modules) with exact source/metadata; isolated0.1.1 import/102 exports/7 heartbeat signatures/worker help pass.914 offline checks across31 suites and7 demos passed;3 explicit live skips.2026-10-15. Build-environment corrections retained in qualification.md; no source or expected parity was weakened.

## Summary
The plan uses the correct authority: reviewed main source, then exact candidate bytes, reviewed PR transport and a pinned-main tag. The version/test substitutions are explicit and do not alter runtime behavior. No actionable High/Medium/Low defect is established. Actual artifact qualification is still needed before adoption, and actual vendor publication remains a later observation rather than a local assumption.

## Premise Inventory

**P1 — Real distributions contain the complete product.** First dependent step2; wasted if false: version PR/promotion/release and consumer expectations. Scheduled test: complete candidate before adoption. Cheapest earlier test is the named real backend/wheel/sdist/install experiment. Prior0.1 checks supply a proven procedure, not coverage for newly added modules. Manifest completeness/bytes and actual import paths must pass now.

**P2 — Version-only edits preserve qualified behavior.** First dependent step2; waste if false: release source requires a different review. Scheduled/cheapest test: exact all-source comparison allowing only the declared substitutions, followed by full31-suite run. The two0.1 assertions were found in actual source and intentionally change with the requested public version; no failed feature expectation is being rewritten. Existing main914-check evidence applies to unchanged behavior but the candidate's actual run closes the new version observation.

**P3 — The exact qualified source becomes tag authority.** First dependent step3/4; waste if false: wrong code under an immutable version. Scheduled checks: actual GitHub merge refs and published tree, then annotated tag peel before release. Cheapest earlier documentary checks are current main/dev equality and actual workflow source, already read. Those do not certify future merge/tag state; the ordered read-back gates do.

**P4 — Vendor publication succeeds and serves the expected bytes.** First dependent irreversible action: release publication. Scheduled test: matching release-event workflow and actual PyPI JSON/files/digests/install immediately afterward. No honest earlier test can prove a future upload response; local builds or scripted responses are non-covering.0.1.1/tag absence was checked and will be rechecked. Ambiguous replies require read-back, not repeated upload. Completion remains gated until actual success.

No OPEN planning blocker. No unavailable credentials/permission assumption is needed: the existing workflow published0.1 successfully and is still configured; failure of the requested real run will be observed rather than predeclared impossible.

## Restart and inherited lessons
The actual0.0.9 incident came from tagging an older feature checkout with a new version. Frozen main05904d1, source-only candidate, exact runtime/package manifests, reviewed main promotion and explicit tag SHA address that established mechanism. The original checkout/version edit is excluded. An existing version/tag is never replaced. As in0.1, the release tracker must stay open through vendor read-back; Tracks#40 prevents premature auto-close during version promotion. Deferred live account tests and consumer deployment do not become claims of this release.

## Findings and Phase3
Zero High/Medium/Low; no mitigation selection or plan deprecation. The complete real-component experiment is required before adoption. No workflow redesign, dependency change, broader runtime work or new branch is justified. After PASS follow the existing plan and observe real publication through completion.
