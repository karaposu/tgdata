---
model: gpt-6-astra
effort: xhigh
---
# #50 verification — PASS

Date: 2026-10-16. Product: `df7972828e2e608204a0043c391d895b51210389`.
Runtime: Python3.11.10, Telethon1.45.0.

| Check | Result |
|---|---|
| Full combined prebuild before product edits | 14 groups PASS, including8 actual PTY scenarios |
| New permanent suite48 | 18 passed;0 failed |
| Targeted15/17/32/41/48 | 92 checks in5 suites PASS |
| Full12–19/22–46 plus48 | 1,005 actual offline checks in34 suites PASS |
| Seven existing offline demos | PASS |
| Source compilation / Python3.7 grammar | 106 files PASS, including setup.py |
| Isolated installed tgdata-login | PASS: actual entry, isolated import, matching source, help and noTTY refusal |
| Live12/13 | 3 deliberate skips, excluded from1,005 |
| Diff whitespace / unchanged auth-reader scope | PASS |

The current dev baseline contains987 offline checks;18 new groups yield1,005.
Unmerged #45/test47 is not included in this branch or count. Native Python3.7
execution is not claimed by the grammar check. No live code delivery, real-account
2FA, physical power-loss or arbitrary-filesystem qualification is claimed.

## Evidence and commands

Using `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`:

```text
python -m tgdata.smoke_tests.test_48_terminal_login
python devdocs/work/50-terminal-account-login/verify.py targeted
python devdocs/work/50-terminal-account-login/verify_install.py
python devdocs/work/50-terminal-account-login/verify.py full
```

`evidence/targeted/result.json` and `evidence/full/result.json` retain individual
counts/exit codes/durations and source SHA256 manifests. The verifier hashes all
tested sources before and after execution. Individual logs sit beside the JSON.
`install-result.json` and `install-build.txt` record isolated package installation.
`prebuild.md`, both attempted full-run logs and result JSONs preserve the prebuild.

The new suite uses real LoginFlow, native SDK/SRP/session codecs, actual SQLite
files and the ordinary verified reader with test41's controlled source transport.
Sockets are forbidden. PTY subprocesses test hidden inputs, EOF, first/repeated
SIGINT and interruption on both sides of publication; signals target only those
synthetic child processes. Existing test12 uses a local loopback proxy fixture.
Missing configuration is supplied to live12/13.

## Corrections and limitations

No product verification failure occurred and no product code was changed to make
tests pass. Permanent suite48 passed on its first run, followed by targeted and
full PASS. Both product modules match the passing prebuild candidates byte for byte.

The earlier prebuild had three failures caused by one fixture path mismatch:
`/var` versus `/private/var` prevented its fault hooks from firing. Only fixture
path normalization changed; candidate hashes and expected outcomes did not. The
entire prebuild was rerun and passed. Its PTY carriage returns are escaped in the
text rendering while an exact JSON log string preserves the original evidence.

The isolated installer used existing setuptools65.5's managed install because
wheel/build were absent. No network or dependency change was needed. The installed
entry point was `tgdata.login_cli:main`, its modules matched the product SHA256s,
help exited0 and headless invocation exited2 before configuration/login.

Operator guarantees are bounded: local POSIX publication, a trusted destination
directory and stopped readers for replacement. A CLI-only marker would not
coordinate existing readers, so none is claimed. Uncertain publication retains
private recovery material and requires inspection rather than an automatic retry.
