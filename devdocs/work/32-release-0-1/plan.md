---
model: unknown
effort: unknown
revision: 2
---

# Gated 0.1 publication

Revision 2 records the completed real-component qualification before product adoption. Critic selected no remedies; the steps and scope are unchanged. Real wheel/sdist, isolated installation,773 offline checks and 5 demos passed, with 3 live skips excluded. Version substitution remains the only product change.

1. Freeze current dev f927496 and the user's final version 0.1; inventory remote tags/releases and PyPI. Create the issue-linked branch/worktree without using the stale checkout as source.
2. Qualify a temporary candidate from a git archive of the frozen base, changing exactly the version line to 0.1. Run the real packaging backend, full offline verifier and isolated installation. Compare every runtime/test/example source byte with the recorded merged baseline (only the exact version substitution is allowed). Inspect both wheel/sdist, metadata, dependency declarations and worker entry point. Failure stops the release.
3. Critique/fold the release plan. Adopt the qualified one-line change on the branch. Commit product separately from work artifacts. Keep the linked branch as archive and publish a clean product PR head containing only the version commit.
4. Run fidelity check and publish the version PR into dev. Execute fresh critic-d on actual PR diff plus this plan; probe version parsing, source/artifact parity and refusal of old artifacts. Post committed checks/review. Merge only after passing, matching the reviewed head SHA.
5. Publish the dev-to-main release PR. Check exact qualified tree parity, prior feature review evidence and explicit live limits; review this promotion without inventing new behavior. Merge with expected dev head SHA. Verify main contains the qualified source and excludes this work folder.
6. Create a new annotated v0.1 tag at the exact promoted main commit, push only that tag, and create the GitHub release with reviewed notes and --verify-tag. Never retarget v0.0.9 or overwrite an existing0.1 release/tag. Publishing triggers the existing PyPI workflow.
7. Observe the matching release-event workflow and PyPI0.1. Download the actual wheel/sdist, verify their advertised SHA256s and exact runtime contents, metadata and entry point. If replies are missing/ambiguous, read back the release/tag/run/version before retrying. A failed upload is not completion.
8. Archive final evidence and update/close #32 after actual publication. Preserve branch history and user work. Carry the already-satisfied version edit onto released main for a safe workspace handoff if Git can do so without conflicts; otherwise retain it and report the checkout state.

No product workflow redesign, dependency change or Telegram request is part of this plan. Packaging checks precede commits/merges/publication; existing deferred live gates stay deferred.
