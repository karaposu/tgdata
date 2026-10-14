---
model: unknown
effort: unknown
---

# Release correction triage

Bug-light: the source change is `tgdata/__init__.py`'s version declaration. `setup.py` parses it rather than importing the package. All behavior is already merged and reviewed on dev at `f92749688b7d544da55249459c489164497d47ed`.

Read in this warmed session: the dirty original checkout/version diff, all open/closed issue titles, current remote branches and tags, the publishing workflow, setup.py, CONTRIBUTING §§6–9/12 and Appendix 2, the latest merged-code verifier/report, batch/daily/backfill code/contracts, and the original release run/PyPI artifact comparison. The first release changed metadata on a stale branch; it did not contain the completed updates. Scope includes source/artifact provenance, both required PRs, the new main tag, publication and read-back.

Affected interfaces: parsed distribution version, PyPI installation/version selection, GitHub release. No new Telegram behavior, API/schema/dependency change or consumer-environment update. Existing review and live-validation limits remain applicable.

No new traverse is required: the failure mechanism was demonstrated by the actual tag, release event, workflow run and all 18 old wheel runtime files. There is no unresolved architecture or ownership design in a one-field metadata correction. Packaging and vendor responses are tested at their actual execution boundaries.

Model/effort identity is not exposed by this runtime and is recorded as unknown; this report does not certify CONTRIBUTING §9 or replace the prior qualified feature reviews.
