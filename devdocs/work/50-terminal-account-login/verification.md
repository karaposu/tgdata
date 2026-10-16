---
model: gpt-6-astra
effort: xhigh
---
# #50 revision4 verification — PASS

Product da890a1; identical PR head34907d4. Python3.11.10 / Telethon1.45.0.

| Check | Result |
|---|---|
| Complete prebuild before product changes | First run PASS:23 groups,25 actual PTY scenarios |
| Retained review/failure histories within prebuild | 17 PASS |
| Stop admission/completion/finalization phases | 8 PASS |
| Create/replace publication-stop combinations | 14 PASS |
| Permanent smoke48 | 23 passed;0 failed |
| Targeted15/17/32/41/48 | 97 checks /5 suites PASS |
| Full12–19/22–46 plus48 | 1,010 actual offline checks /34 suites PASS |
| Seven existing demos | PASS |
| Compile / Python3.7 grammar | 106 files PASS; native3.7 not run |
| Isolated installed command | Actual entry/native-SRP/PTY interruption, help, headless, isolated imports/hashes PASS |
| Exact PR-tree equivalence | All106 tested source hashes and product diff match |
| Live cases | 3 deliberate skips, excluded from offline count |

The CLI bytes equal the prebuild candidate:
8191362b69692824de82a3b70ac65a54103f79de29c1204b283d6bc1f8849d24.
Every permanent test function's AST equals its executed prebuild counterpart; only
candidate loading/root setup differs. The native publisher retains its previous
hash3b526f483d3f0c137ebc45023f2326710781000ec71af090ed83c1b10d001290.

## Evidence

prebuild-r4/result.json and attempt-1.txt preserve the complete candidate gate;
prebuild-r4/README.md describes components and phase coverage.
verification-r4/initial-test48.txt, evidence/targeted/result.json and
evidence/full/result.json preserve counts/exits/durations and source manifests.
Individual suite/demo logs sit beside their result JSONs. verify.py checks source
hashes before and after tests. pr-equivalence.json records the identical PR tree;
no unnecessary full-suite repeat was used for a byte-identical cherry-pick.

verification-r4/verify_install.py uses existing offline setuptools65.5 in temporary
source/lib/script directories. No wheel/build dependency was installed. Its
installed_probe.py runs the real generated console entry via runpy in an isolated
PTY child with controlled transport and actual native SRP, then verifies exit130,
terminal restoration and owned cleanup. Parent/child both assert imports from the
isolated library. installed-interruption.txt records:

```text
PTY_PHASE native_srp terminal restored; exit130
INSTALLED_NATIVE_SRP_STOP_PASS
```

Commands use /Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python:

```text
python devdocs/work/50-terminal-account-login/prebuild-r4/run.py
python -m tgdata.smoke_tests.test_48_terminal_login
python devdocs/work/50-terminal-account-login/verification-r4/verify.py targeted
python devdocs/work/50-terminal-account-login/verification-r4/verify_install.py
python devdocs/work/50-terminal-account-login/verification-r4/verify.py full
```

No verification failure or product correction occurred. The sole formatting
cleanup removed an unused extra EOF blank line from the extracted review_cases.py
work helper; executed combined-suite/candidate bytes and expectations did not change.
All tested changes are within the folded revision4 contract.

These are actual SDK/SRP/session/file/terminal tests with controlled source replies,
not live Telegram qualification. Network connection is forbidden in login tests;
full test12 uses its local loopback proxy fixture. Native3.7 execution and physical
power-loss/arbitrary-writer guarantees are not claimed. #45/test47 remains separate.
