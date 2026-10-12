---
model: gpt-6-astra
effort: max
---
# Revision4 combined prebuild — PASS

2026-10-12. The complete Step1/critic experiment passed: **82 groups and67
controlled Python subprocesses**, with both frozen candidate functions installed
together. This is the previously pending combined gate, not a sum of the earlier
narrow probes. Product remains6ee146c; no runtime/test/public-doc file was changed.

## Candidate and execution identity

Candidate, source fingerprints and initial runner were committed **before execution**
at `2cc9995`. Both candidate files remain byte-identical to that checkpoint:

- `probes/revision4_candidate_serve.py` SHA256
  `7b5258e255960ac67c4b3143d4e9b7c7dd983bc6844d3392fd10a39e890c7b96`
- `probes/revision4_candidate_diagnostics.py` SHA256
  `74ef82a6fb672fdbf8bd2bd2f94a31eb5a8a195a5c1077e16a822ba61c94b0aa`

`probes/revision4_fingerprint.json` pins13 relevant product/fixture source files,
the20 canonical auth names, Python3.11.10 and Telethon1.45.0. Each subprocess validates
the fingerprints, installs both candidates, and records their identities separately
from transport activity. End-of-run checks also verify the source files unchanged.
Functions are compiled in memory with the unchanged worker/protocol helper globals.

Run with the project Python from this worktree:

```bash
python devdocs/work/10-reading-jobs/probes/revision4_prebuild.py
```

Final runner SHA256:
`8e04f26d56a699afba1c2c8ad531f423def4eb790facd51c22538bc0e0070db4`

Full output is `probes/revision4_prebuild.txt`; machine-readable groups/details are
`probes/revision4_prebuild_result.json`. This runner targets the rejected product
snapshot and deliberately refuses changed source. After implementation, use the
permanent suites and implementation verification; do not rerun this as if it were
a portable test for arbitrary future code.

## Coverage against the mandatory matrix

| Matrix / controls | Groups | Subprocesses | Observed |
|---|---:|---:|---|
| Quiet, held native disconnect, before creation, publication, held finalization — both stop signals | 10 | 10 | Exits130/143, retained cleanup/restoration, no successor source; creation cases use0 clients/claims |
| Repeated caller cancellation while native cleanup is held | 1 | 1 | Real Task cancelled twice; process retains one disconnect until release; charge2 retained; exit3 |
| Empty inventory/EOF and seven invalid startup forms | 2 | 8 | Source-free readiness/refusal; exits0/2; no session/client on refused startup |
| Existing operation, framing, identity/store and raw-pipe controls | 10 | 14 | All four jobs, two accounts, exact Node query ID, prefixes/health, local refusals, EOF, broken output and undrained pressure |
| Cleanup failure after success, body failure, setup failure, internal SDK cancellation and partial-source failure | 5 | 5 | Original outcome/prefix retained; one failed disconnect attempt; no second account; exit3; remaining tasks settled |
| Six SDK error variants across all four worker verbs | 24 | 24 | Unknown401/406 text absent; generic403 and three known auth reasons/flags preserved; no group work/claim |
| Delivery-error projection and four fatal-encoder variants | 5 | 5 | Shared projector omits unknown text, retains known names and explicit omission; no false success |
| Existing core source/protocol regressions under the same candidate context | 25 | 0 | Actual SDK/SQLite, ownership, budgets, bounded resolution, hashes, observer isolation, cancellation and size/drop behavior |
| **Total** | **82** | **67** | **All passed** |

The67 count is controlled Python subprocesses (including explicit fatal-encoder
controls); the Node consumer check is separate. The25 core groups run in the parent
event loop with both candidate functions installed. Source execution is always the
actual Worker/SDK implementation, not fabricated Worker return values.

The child has no polling/file-watcher helper. The parent observes traces and sends
OS signals. Native disconnect and finalization are held with an Event, released by
an explicit parent command only after cleanup/settlement entry is observed and a
repeat signal has left the child waiting. Direct caller cancellation uses a
separate test command that cancels the real owning Task; it is not a public worker
signal API. Quiet cases observe long selector waits without incidental wake-up.

Both snapshots are active for normal and failed jobs, startup/EOF, output pressure,
cleanup faults and diagnostic tests. Every completed child checks owned signal and
logging restoration; loop-close instrumentation verifies zero pending Tasks and a
closed loop. Unexpected stderr must be empty. Source request/cleanup traces remain
visible independently of provenance and lifecycle bookkeeping.

## Comparison with the critic's pass/fail definition

- **Progress without unrelated timers:** quiet SIGINT/SIGTERM and held-cleanup
  histories pass with explicit loop wake-up and no child polling assistance.
- **Stopped publication performs no source:** both before-create and after-create/
  before-return cases pass with zero clients, read claims and join claims.
- **Cleanup retained:** repeat signals and repeat caller cancellation do not
  abandon the actual SDK attempt. Final settlement also survives first/repeat stops.
- **Raw output stops:** a broken reader exits3; undrained output pressure exits130/
  143 without reader drain or final flush. The queued second account is untouched.
- **Original outcomes survive unsafe cleanup:** a100-message prefix/FloodWait7200
  retains charge200; success/body/setup/internal-disconnect-cancel controls retain
  the appropriate outcome. Failed disconnect is recorded as failure, never described
  as a successful connection close; the process stops and settles remaining tasks.
- **Unknown diagnostics absent:** real TL error decoding and actual jobs exercise
  unknown401/406, ordinary403, AUTH_KEY_UNREGISTERED, SESSION_REVOKED and
  USER_DEACTIVATED_BAN. All four verbs and secondary diagnostic paths share the rule.
- **Same architecture:** no extra timer, queue, router, transport framework, public
  error hierarchy, live action or new quota mechanism was needed.

No disqualifying mechanism result was observed in the completed matrix.

## Initial harness correction, retained

The first attempt stopped after13 passing groups because the reused source-only
trace assertion saw a newly added candidate-fingerprint row at ready. That was
bookkeeping, not client/request activity. The initial output and machine result
are retained as `revision4_prebuild-harness.txt` and
`revision4_prebuild-harness-result.json`.

The correction separates provenance/lifecycle observations into evidence.jsonl
and leaves trace.jsonl with the original client/request/cleanup meaning. The
existing assertions and product/fixture source files were not changed, and the
frozen candidate fingerprints did not change. The full matrix was then rerun and
passed. This was an inconclusive harness failure, not a failed candidate premise
silently patched into success.

## Result and remaining work

**Result: PASS.** This discharges the REORDER experiment and completes revision4
Step1. The review/fold need not run again merely because the experiment passed.
The next work is Step2 onward: integrate the tested phase policy and diagnostic
vocabulary, make the histories permanent without work-folder dependencies, run
the full offline/package verification, then renew merge check and PR critique.

This result qualifies the frozen candidate on Python3.11.10 / Telethon1.45.0 /
SQLite3.45.3 and macOS/POSIX. Synthetic transport supplies Telegram replies/faults;
the Worker, SDK, budgets, native cleanup, OS signals and pipes are real. No live
Telegram permission, safe-rate, proxy, native Windows/older Python or cross-process
session-sharing qualification is claimed. Product6ee146c still contains the original
two Medium defects until integration. PR27 remains draft, and #10 remains open.

The current prebuild turn's metadata records GPT-6 Astra/max at
2026-10-12T08:33:08.175Z. Work is in-session; no delegated agents or unrelated edits.
