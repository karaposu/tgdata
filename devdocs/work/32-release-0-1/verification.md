---
model: unknown
effort: unknown
---

# Candidate verification

PASS on 2026-10-14: qualified f927496 candidate with exact version 0.1 substitution. All28 supported suites12–19/22–41 completed under Python 3.11.10/Telethon 1.45.0;773 actual offline cases and 5 demos passed, 3 live skips excluded. Compilation and Python 3.7 grammar checks pass; native 3.7 execution and new live Telegram/login/failover qualification are not claimed.

Both real distributions contain 84 package Python files, including 37 runtime modules, matching the candidate exactly. Metadata, README, dependencies, optional proxy extra and worker entry point pass. Twine check passes for both. Isolated target install imports that target and exposes login/pool/batch/progress/group/budget APIs; installed worker --help succeeds. Existing merged source hashes match except the single version substitution.

Evidence below records the completed second full run and the initial sandbox-bind failure. The temporary verifier's UTF-8 payload decoder was corrected; no product/test assertion or source was weakened. Dist archive hashes describe the local build, not the future CI build: actual published payloads still require read-back. Python/OS build timestamps can change whole-file hashes; byte-level package equality and metadata are the release qualification.

Still pending: committed merge-check, PR/fresh critic, dev/main promotion, pinned v0.1 tag, observed workflow/PyPI publication and actual published-file checks.
