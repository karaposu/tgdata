---
model: unknown
effort: unknown
---

# Release tgdata 0.1

## Problem Statement

PyPI 0.0.9 contains the old feature branch at a47ba80. The user's latest request is to publish exactly 0.1 with all completed, reviewed updates. Current dev is f927496; main is f411c9c. The original checkout has only a local 0.1 version edit and must not be used as the build source.

## User Value Proposition

Consumers can install the completed session, budget, batch, progress, backfill, group, pool, worker and stepwise-login features from PyPI using one correct release.

## Success Criteria

The candidate is current dev with exactly the version declaration changed to 0.1. Real wheel/sdist builds contain every expected Python module and matching bytes, correct metadata/dependencies and the worker entry point. All 28 supported offline suites and five demos pass under Telethon 1.45.0 with live checks explicitly skipped. The package installs in an isolated target and exposes the expected public APIs. Version/source PR review passes, dev is promoted to main through a PR, and tag v0.1 names the exact promoted main commit. The actual published wheel/sdist are downloaded, their PyPI hashes verified and their runtime contents compared with the qualified candidate. Completion requires observed publication, not merely a successful local build or release creation.

## Scope Boundaries

Only the version declaration changes product code. Existing behavior/reviews are inherited by byte equality with f927496; no new feature soundness or live Telegram claim is made. New proposals29–31, new CI architecture, yanking0.0.9 and changes to the running ScrapeOps environment are excluded. Work-folder artifacts remain on the archive branch, outside dev/main product merges. Preserve the user's edit and archive; the final workspace handoff may carry that same version edit onto released main without discarding it.

## Priority Level

P1: replace the stale-code release. Bug-light implementation, with stricter artifact/source checks because publication is irreversible.

## Known Blockers

No open planning blocker. Execution preconditions are the real build/install verification, successful reviewed PR merges, availability of version 0.1 and observed vendor publication. An ambiguous mutation response must be read back before retrying; do not replace an existing tag/version.

## Session warmth

See triage.md. The reviewed base is f927496, the branch ancestor. Model/effort unknown is explicit; this operational release record makes no §9 model certification.
