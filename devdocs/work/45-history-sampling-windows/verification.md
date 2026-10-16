---
model: gpt-6-astra
effort: xhigh
---
# #45 verification — PASS

Date: 2026-10-16. Product commit: `20c6781ae7229e36054e5c89ba5735dfb8f0f904`.
Runtime: Python3.11.10, Telethon1.45.0.

| Check | Result |
|---|---|
| Combined prebuild before product edits | 8 groups PASS; see prebuild.md/txt |
| New suite47 after fixture correction | 31 passed;0 failed |
| Targeted23/32/33/34/42/43/44/46/47 | 368 checks in9 suites PASS |
| Full12–19 and22–47 | 1,018 actual offline checks in34 suites PASS |
| Seven existing offline demos | PASS |
| Source compilation | 106 files PASS |
| Python3.7 grammar | 106 files PASS; native3.7 runtime not tested |
| Live cases12/13 | 3 deliberately skipped, excluded from offline count |
| Diff whitespace and scope | PASS |

The previous baseline was987 offline checks; suite47 adds31. Tests46 were not
edited: all35 activity checks still pass after extracting structural validation.
The verifier records source SHA256 values and asserts that tested sources did
not change during each run. Full and targeted JSON reports contain individual
exit codes/counts/durations and source manifests; logs sit beside those reports.

## Commands and evidence

Using `/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`:

```text
python -m tgdata.smoke_tests.test_47_history_sampling
python devdocs/work/45-history-sampling-windows/verify.py targeted
python devdocs/work/45-history-sampling-windows/verify.py full
git diff --check
```

- `evidence/first-test47.txt`: initial30/31 run and fixture assertion failure.
- `evidence/corrected-test47.txt`: corrected31/31 run.
- `evidence/targeted/result.json`:9 suites/368 checks, all PASS.
- `evidence/full/result.json`:34 suites/1,018 offline checks,7 demos,3 live skips.

The full run required socket permission only for the existing local loopback
proxy fixture. Missing configuration was deliberately supplied to live12/13.
Suite47 forbids sockets/login and uses real Telethon dispatch/TL decode,
StoredSession, verified owner checks and SQLite ReadBudget; only source replies
are synthetic. No Telegram login or live history was requested. Exclusive live
session ownership/authoritative allowance remains unqualified, so no live sampling
claim is made.

## Verification corrections

The first suite47 run failed its photo/document size assertion. Inspection of
Telethon1.45.0 constructor signatures showed that positional arguments to
MessageMediaPhoto/MessageMediaDocument were interpreted as boolean flags, leaving
the asset absent. Corrected only those fixture calls to `photo=photo` and
`document=document`. The expected media sizes and all acceptance assertions were
unchanged. Re-ran the entire failed suite, then targeted and full verification;
all passed. No product code or architectural change arose from this failure.

The staged whitespace check also found one extra blank line at the end of the
work-folder verifier. Removed it and repeated that check; executable logic and
the tested product sources were unchanged.

## Acceptance evidence

- 599 retained ordinary messages select300 spanning first/last; canonical reload
  and normalized eligibility reproduce exact output. No source calls follow cleanup.
- 60-day sparse history captures599 useful messages and selects300 in fewer than
  1000 returned slots and at most100 logical calls; the prebuild records660 slots
  and66 calls. Quiet days retain opportunity beside a busy day.
- Tiny/no-spare-call budgets, empty days, partial UTC intersections, fractional
  endpoints, equal timestamps and source placeholders preserve explicit evidence.
- All-zero/full/partial quota combinations terminate with exact conservation and
  capacity bounds; sparse redistribution is exercised through the public API.
- Services remain retained but unselectable; raw albums disclose omitted observed
  members; text/media references survive without implicit download or enrichment.
- Malformed JSON, duplicate keys, byte limits, changed hashes and rehashed
  contradictory evidence refuse. Getters are detached and values immutable.
- Original RPC/local/settlement errors and accepted earlier days survive. Invalid
  pages never partly enter a capture. Refused annotation preserves the original.
- CachedA/expectedB/actualB proceeds asB; wrong expected identity refuses; budget
  and late identity checks remain effective. Local errors do not become health events.
- Stalled reads emit no fake beats. Cancellation remains cancellation, repeated
  cleanup cancellation waits for disconnect, and cleanup errors preserve precedence.

No batch/progress/assembly/session policy implementation changed. No downstream
project, PyPI version, main/dev branch, tag, running scraper or deployment changed.
