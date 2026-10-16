# Revision4 full combined prebuild — PASS

Ran run.py using Python3.11.10 / Telethon1.45.0. First complete run passed:
23 groups;8 original plus17 new real-PTY scenarios;17 retained review histories;
8 command stop transitions;14 create/replace publication-stop combinations.
No fixture or candidate correction was needed. Product files remained unchanged.

Candidate CLI SHA256:8191362b69692824de82a3b70ac65a54103f79de29c1204b283d6bc1f8849d24.
result.json records candidate/test/product manifests before/after and18.619s elapsed.
attempt-1.txt contains complete results. No timeout kill counted as successful stop.

The combined_suite.py is the original smoke48 plus phase_cases.py and the test
body extracted into review_cases.py from the prior review's functional matrix.
It loads only candidate_login_cli.py in place of the product CLI; LoginFlow,
StoredSession, native SQLite/file publisher, account reader and SDK are real and
unchanged. functional_matrix.py preserves the adapted standalone source of those
17 histories; combined_suite.py executes their body in the complete run.

Actual PTYs/getpass/termios and process signals cover executing validation and
native SRP; connect/source/cleanup waits; completed exceptional futures; input EOF/
repeated interruption and exact terminal restoration; admission/completion and
final shutdown; create/replace before/after mutation, sync uncertainty and output/
cleanup crossing. Held cleanup proves repeated Ctrl-C waits until the owned release.
Native SRP proves the signal occurred while computation was active, then exits130
and leaves no published session, with owned source cleanup settled.

Completed source state may be known or uncertain after cancellation; the tests
retain actual source effects rather than asserting remote rollback. File effects
are independently checked. A deliberately failed retirement refuses publication;
fixture cleanup is explicit. Stale-callback identity checks supplement, rather than
replace, the real full-command histories.

No product edits, real Telegram connection, dependency change, release, native3.7
runtime or physical power-loss test occurred. This is the complete revision4
experimental gate, distinct from the earlier six phase-local planning probes.
