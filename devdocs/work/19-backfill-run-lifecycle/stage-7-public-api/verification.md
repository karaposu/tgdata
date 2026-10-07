---
model: gpt-6-astra
effort: max
status: PASS
---
# Stage 7 verification

**PASS at product `17fccbc`: 342 actual supported offline checks.**
Telethon **1.45.0**, Python **3.11.10**. Three legacy live checks were explicitly
skipped, not counted as executed passes. No Telegram connection, real session/config
use or actual account-budget mutation was performed by this stage's verification.

[Structured results](verification-results.json), [final public suite](public-full-suite-results.txt),
[example output](example-results.txt), [prebuild primitive](prebuild-results.json).

| Suite | Actual passes | Explicit legacy live skips |
|---|---:|---:|
| 29 public API/example | 23 | 0 |
| 28 controls | 32 | 0 |
| 27 pacing/recovery | 32 | 0 |
| 26 completion | 16 | 0 |
| 25 delivery | 41 | 0 |
| 24 state | 23 | 0 |
| 23 windows | 22 | 0 |
| 22 daily continuation | 25 | 0 |
| 19 batches | 33 | 0 |
| 18 budgets | 28 | 0 |
| 17 sessions | 12 | 0 |
| 16 health | 21 | 0 |
| 15 login | 11 | 0 |
| 14 flood threshold | 11 | 0 |
| 13 identity | 5 | 1 |
| 12 proxy | 5 | 2 |
| 11 explicitly awaited helpers | 2 | 0 |
| **Total** | **342** | **3** |

The existing guard instrument passed 10/10. Daily example: four stored messages and
accepted through 104. New example: five unique records, three exact receipt snapshots,
historical completed at 104, daily cursor 105, zero replay source calls and separately
cancelled successor. Its completed repeated run performs zero source reads. All source
values in the example are explicitly synthetic; SQLite, processes and receiver commits
are actual. The public SDK fixtures use real Telethon with synthetic transport.

Compile passed; Python 3.7 grammar passed for 56 product/test/example files. This is
not a Python 3.7 runtime claim. Changed Markdown local links and whitespace checks
passed. All four qualified prebuild storage/receiver class ASTs exactly match the
final example. No internal engine/codec/helper became a package-root public API.

## Initial results and small corrections

1. The first new core run passed 17/18. Its health assertion looked up `method`, but
   the existing public event key is `call`. Corrected that test reference only.
   [Initial result](public-initial.txt).
2. The next run passed 17/18 because the same assertion spelled the verdict as the
   snapshot dictionary key `no_access`. The existing event constant is NO_ACCESS
   (`"no access"`). Corrected the test to that existing constant, preserving the
   expected one actual source event attributed to get_message_batch.
   [Intermediate result](public-intermediate.txt), [18/18 core result](public-core-results.txt).
3. The five example/receiver tests then passed on their first run, giving 23/23;
   [result](public-example-results.txt). The full suite repeated 23/23 after adding
   explicit fake API-hash exclusion assertions. The example passed first execution.

No runtime repair or behavior-expectation weakening occurred. The planned change to
public availability required updating only the staged absence assertions in tests
24/25/28; their existing state/receipt/health assertions were retained.

## Prebuild experiment and boundary coverage

The committed critic required actual SQLite namespace/receiver evidence before product
edits. All seven checks passed: isolated exact-text CAS; competing processes with one
winner; retained distinct snapshots despite a shared message ID; wrong receipt scope;
known file/schema refusal; receiver-commit exit/reopen and independent daily/history;
committed close-error recognition and primary-error preservation through cleanup.
See the experiment/result in [critic](critic.md). No fake supplied persistence behavior.

Public tests cover engine lifetime across overlap/control/recovery/close and forward
UTC movement, explicit required context, disabled/malformed input, no-send uncertain
admission, lost control reply, source exception ownership, local health preservation,
media failure, budget prefix and secondary persistence error, namespace refusal and
content/credential-free status/logging. The final example additionally tests real
receiver failures before commit and ambiguous post-commit close errors.

## Remaining validation

Gates A/B/C retain their exact historical product/source evidence; no source, budget,
health or state-machine behavior changed in Stage 7. Public composition is verified
offline here. **Stage 8 and mandatory live Gate D remain pending**, including public
flows against the selected real source/backend/receiver and review preparation. No
release, PR, protected merge, distributed-reader or deployment-readiness claim follows.
