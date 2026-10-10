---
model: gpt-6-astra
effort: max
---
# Stage 2 revision 4 verification — 2026-10-10

**Result: PASS.** Product `c6451bb`, folded plan `aee7211`, base dev/Stage1
`53306df`, branch `feat/7-account-health-ownership`. Implementation is complete.
Later review checkpoints: merge fidelity PASS `fd655a5`, fresh PR ACCEPTED `9e0b4e5`;
see merge-check.md and pr-critic.md. PR22 is ready, not merged. No live
Telegram action, login or membership change. This is not PR or merge approval.

The first product's verification is preserved byte-for-byte in
`archive/round-1/verification.md`, checked against b9a8a5d. Its 424 passes describe
rejected product3d59455, not acceptance of this rework. The original rejecting PR critique and probes are preserved under archive/round-1;
there is one distinct Stage2 rejection. A later review owns the root PR filenames.

## Executed plan and critique

Fresh revision3 critic `d9eefbe` found one Medium: mutable caller batch input could
invent a successful action after awaiting. The selected robust mitigation captures
immutable logical keys before awaiting in the existing client wrapper. The required
real-SDK exception-carrier experiment passed at `d2dd499` before implementation;
revision4 folded the mitigation in `aee7211`. No second critique of that fold ran.

1. Added sender-built regressions before production edits. Synthetic decoded replies
   enter real MTProtoSender.send, RequestState and result/error construction using
   the actual request emitted by the factory's policy. The eight initial acceptance
   cases produced the expected **0/8 red baseline** against the rejected product.
2. Unified owned failure/success keys through seven known envelopes and generated
   namespaces. Captured immutable keys plus observation/client binding before the
   SDK await. Lazy/custom input is not consumed; partial batches add no success.
3. Stored the current restricted action and required its later success under the
   existing owner, method, ordering, valid-handle and no-self-recovery guards.
4. Replaced ambient retained-error lists with neutral metadata on the originating
   error, explicit causes and SDK RPC members. New RPCs take precedence over older
   neutral context; diagnostic classification and polling decisions stay intact.
5. Completed integrated cases and documentation for namespace keys, refused-action
   recovery, forwarding, immutable evidence and notification arrival order.
6. Ran the complete supported offline regression set, demos, syntax and scope checks;
   committed code/tests/product docs together, with these work notes separately.

Runtime rework touches only owned_health.py, health.py and the existing
_AnswerEvidence wrapper in connection_engine.py. Stage1, budget admission and facade
interfaces are unchanged by this rework. No request registry, sender layer, global
health migration or delivery queue was introduced.

## Measured verification

Python **3.11.10**, Telethon **1.45.0**. Interpreter:
`/Users/ns/Desktop/projects/telegram-group-scraper/.venv/bin/python`.
Commands run from `/private/tmp/tgdata-7-stage2-health-ownership`.

Suite commands use `python -m tgdata.smoke_tests.<module>`. Suites12/13 receive
`/private/tmp/tgdata-stage2-deliberately-missing.ini`, verified absent; their live
cases skip without reading credentials. Suite12 uses normal escalation for a local
refusing/dead proxy. No Telegram connection is made by those local proxy cases.

| Suite | Actual passes | Live skips |
|---|---:|---:|
| 12 proxy | 5 | 2 |
| 13 device identity | 5 | 1 |
| 14 flood threshold | 11 | 0 |
| 15 login checks | 11 | 0 |
| 16 legacy health | 21 | 0 |
| 17 session store | 12 | 0 |
| 18 read budget | 28 | 0 |
| 19 message batches | 33 | 0 |
| 22 daily continuation | 25 | 0 |
| 23 fixed windows | 22 | 0 |
| 24 backfill state | 23 | 0 |
| 25 backfill delivery | 41 | 0 |
| 26 backfill completion | 16 | 0 |
| 27 pacing | 32 | 0 |
| 28 controls | 32 | 0 |
| 29 public backfill | 23 | 0 |
| 30 backfill integration | 15 | 0 |
| 32 Stage1 operation | 28 | 0 |
| 33 owned health | 62 | 0 |
| **Total** | **445** | **3** |

All final suite processes exited0. Suite12 prints7/7 and suite13 prints6/6 because
those runners include skips; the actual total subtracts their three live skips.
No blanket pytest, older live-oriented tests, unmerged #17 suite31 or Telethon1.33.1
run. Suites16/32 were run once on the final runtime, then omitted from the remaining
parallel regression batch. Suite33's core eight passed after runtime changes and
its full 62-case run passed after the remaining planned tests were added.

Suite33 retains 41 existing cases and adds 21. Existing owned-key assertions adopt
namespaced spelling as explicitly planned; legacy assertions are unchanged. Added
cases cover sender-built wrapped errors, separate namespaces, envelope boundaries,
mutable lists, lazy/custom input, invalid evidence bindings, restriction replacement,
missing keys, same-call/older-operation refusal, self verification and budget refusal,
fresh legacy errors, child-task forwarding, explicit-cause rethrow, implicit context,
SDK MultiError leaves/partial success and harmless metadata failures/cycles.
Critical transport cases use real error construction; malformed metadata and observer
faults deliberately retain direct synthetic unit fixtures. Sockets are forbidden.

- `compile()` and `ast.parse(..., feature_version=(3, 7))`: **63/63** Python files
  under tgdata/ and examples/. This checks grammar, not execution on Python3.7.
- `python examples/daily_continuation.py --demo`: exit0; lost acknowledgment replay
  used the same batch without a new source read; 4 messages, acknowledged through104.
- `python examples/backfill_runs.py --demo --directory <temporary> --new`: exit0;
  accepted-batch replay after simulated process exit; completed, 5 unique messages,
  3 source reads, 0 replay reads.
- Same backfill command without `--new`: exit0, completed with **0 source reads**.
- Product `git diff --cached --check`: clean; seven intended files only.

Local logs, machine-readable suite/demo results and syntax results are retained at
`/private/tmp/tgdata7-stage2-r4-verification/`. This document is the durable result
record; temporary log retention is not a repository guarantee. Expected injected
callback/cleanup/observer-failure diagnostics are not test failures.

## Corrections and deviations

No runtime fix was required after the final verification runs; no architectural
change departed from revision4. Before production edits, the explicit-cause red
case was strengthened to rethrow outside its handler, where implicit context cannot
hide the defect. Its expected zero legacy events remained unchanged. The intentional
pre-change red run is planned evidence, not a final-verification failure.

The product commit contains the three planned runtime files, suite33 and the three
planned product documents. Work notes are separate. Original checkout remains on
feat/7-group-operations with its pre-existing untracked HANDOFF.md and todo.md.
No duncan, stray guide edit, old broad revision3 or unmerged #17 was staged or changed.

## Limits and next gates

This is still the Stage2 foundation: existing public reads keep legacy health;
group lookup/access and joining are later stages. Private callers keep individual
TLRequest objects stable during a call; group access confirmation still requires
semantic interpretation of an actual result. No durable/FIFO callback contract.
Tests establish local SDK/asyncio/SQLite composition, not live server permission
or frozen-account behavior.

At implementation completion, the next gates were renewed merge fidelity and a
fresh same-session PR critique on the final product diff and plan. They subsequently
passed at fd655a5 and9e0b4e5, with no runtime changes. Merge now needs the user's
explicit go-ahead. Any future Medium/High rejects under CONTRIBUTING §7.3–7.4. Keep work docs out of dev and retain the branch.
Frontmatter retains the previously observed same-session Astra/max provenance;
the archived merge check records its original timestamp, not a new selector reading.
