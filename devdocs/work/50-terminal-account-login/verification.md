---
model: gpt-6-astra
effort: xhigh
---
# #50 revision 8 verification — PASS

Archive producteb1f564; byte-identical PR productb1d9dcc.
Python3.11.10 / Telethon1.45.0, native macOS terminal tests. No live login.

| Check | Observed result |
|---|---|
| Full prebuild before product changes | First complete run PASS, committed b0caa03 |
| Retained prebuild groups/scenarios | 23 groups;25 PTY;17 source/file;8 stop;14 publication-stop |
| Additional terminal/profile/control cases | 50 +20 PASS |
| Framing histories / real-component handoffs | 46 /7 PASS |
| Permanent smoke48 | 26 groups PASS, including all three additional matrices |
| Targeted15/17/32/41/48 | 100 checks /5 suites PASS |
| Full12–19/22–46 plus48 | 1,013 offline checks /34 suites PASS |
| Existing demos | 7 PASS |
| Compile / Python3.7 grammar | 111 /111 files PASS; native3.7 not run |
| Isolated installed command | Actual entry/native-SRP interruption, module/console help, headless refusal PASS |
| Candidate/product equality | Both product modules byte-identical to qualified candidates |
| PR-tree equivalence | All111 source hashes and complete product diff match |
| Live checks | 3 skipped, excluded from offline count |

The 123 new matrix histories run inside three of smoke48's26 groups; they are not
added again to the reported1,013 suite checks. The full runner records exits,
counts, durations and hashes and confirms source did not change during the run.
No product, candidate or expected-outcome correction was needed in verification.
Permanent-test extraction/packaging adaptations are listed in implementation.md
and verification-r8/promotion.json; behavioral assertions are retained.

## Evidence and reproduction

- prebuild-r8/result.json, result-attempt-1.json, attempt-1.txt and README.md:
  full experimental gate and its exact candidate/source hashes.
- verification-r8/evidence/targeted/result.json and evidence/full/result.json:
  five affected and34 full suites, with every suite/demo log beside each manifest.
- verification-r8/promotion.json: exact candidate/product hashes and retained ASTs.
- verification-r8/pr-equivalence.json: tested archive/PR equality and product-only paths.
- verification-r8/install-result.json, install-build.txt, installed-interruption.txt:
  isolated install with the actual generated console script and installed modules.

Commands, using /Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python:

```text
python devdocs/work/50-terminal-account-login/verification-r8/verify.py targeted
python devdocs/work/50-terminal-account-login/verification-r8/verify_install.py
python devdocs/work/50-terminal-account-login/verification-r8/verify.py full
```

Installed native-SRP output:

```text
PTY_PHASE native_srp terminal restored; exit130
INSTALLED_NATIVE_SRP_STOP_PASS
```

No active environment was changed. The offline setuptools managed install uses
separate temporary source/library/scripts, existing dependencies and no network.
Its source is the product tree, with no candidate overlay. Login tests forbid socket
connect/connect_ex; test12's full-suite proxy fixture uses local loopback only.

Native3.7, other-host terminal behavior, live code delivery/real-account2FA and
physical power-loss/arbitrary-writer filesystem behavior are unqualified. Existing
three live skips are intentional. #45/test47 remains separate. Renewed merge check
and fresh in-session PR critique are still required; PR51 remains draft.
