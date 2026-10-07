---
model: gpt-6-astra
effort: max
gate: A
verdict: PASS
date: 2026-10-07
---
# Gate A — frozen scope, source compatibility and real persistence

**PASS for the Gate A foundation scope.** Seven real-source comparisons matched their
independent ID/date/media expectations. Actual SDK pages were crossed. Two controlled
local interruptions around real reads preserved failure/cancellation semantics and
charges. Real SQLite state tests passed again. Stage 3 is unblocked, not implemented.

The prior BLOCKED report is retained in commit `23ceab5`. This report records the later
user-authorized login and live execution; Stage 2's original offline receipts remain
historical offline evidence.

## Revisions and context

- Product code/tests: `1425fd7870b62859b9b1d78701fb347ca9aaf40a`, unchanged during this gate.
  #18 foundations remain integrated only on this feature branch via `5d0789e`.
- Instrument correction: `e644655`, work-folder tools only. Executed `live_probe.py`
  SHA-256: `a9d772b6ed6589e7fb6c556f5bf5da2d60a032230b81056226ff9b9d79580f54`.
- Python 3.11.10, Telethon **1.45.0**, package imported from the #19 worktree.
- The user selected the project config/session and confirmed no other scrapers or
  existing budget database. The same account was freshly verified in each source
  driver; its numeric identity and credentials are omitted from published evidence.
- After `AUTH_KEY_UNREGISTERED`, the user explicitly requested login. It ran in a local
  Terminal with hidden code/password input, outside agent tool outputs. The configured
  session now contains the restored login. No credentials are in the evidence.
- Existing sources selected by the user: `arenda_stambul1` (`-1004478311025`) and, for
  pagination, `programlama_sohbet` (`-1001139574198`). No message, media upload,
  invitation, join or membership change was used to manufacture a fixture.
- Model/effort verified in session metadata: `gpt-6-astra` / `max`.

## Allowance, storage and independent expectations

A persistent test ledger was configured for 5,000 message reads after fresh account
verification and the user's confirmation that no other reader/ledger exists. It was
never reset or increased. Final charged usage is **1,118**, including a conservative
nine-slot reservation for a refused send. Source workers ran sequentially and shared
that ledger. Metadata and requested file bytes are recorded separately.

Qualification allowed at most five direct 100-slot history requests, five-second
spacing and 180 seconds. Normal comparisons had caps of 100 RPCs, ten history requests,
1,000 requested slots and 180 seconds, with five-second spacing between caller batches.
Reference cases allowed zero media bytes; selected-photo cases allowed at most 4 MiB
of requested chunks. MTProto handshake/housekeeping is not counted as application RPCs.

Each lifecycle case used a separate real SQLite state file/collection. State was
created locally and reopened by a different process. Start retry/status used a forbidden
clock. Every diagnostic scan left the complete lifecycle row unchanged; no preparation,
acknowledgment or progress transition was simulated.

Expected results were frozen **before** tested reads through separate direct descending
`GetHistory` calls, not `get_message_batch`, its ascending iterator or its date filter.
The smaller group's 46 visible records reached ID 1. The larger capture obtained 500
records over five descending pages, with witnesses older and newer than the selected
350-record interval. Completeness is scoped to those observed account views and
intervals, not an immutable/global Telegram archive. The independent path shares
Telethon's transport/TL decoder; it independently checks traversal, selection, ordering
and batching, not that decoder.

The relative run was enrolled at `2026-10-07T06:04:44.170536Z`, with a ten-day window
ending at that saved instant. Its independent snapshot began afterward, at
`2026-10-07T06:04:52.173593Z`. Reopen/retry and real reads preserved those exact dates.
The media reference came from direct SDK byte download before the batch/blob test;
its SHA-256 and byte length were frozen independently of that wrapper.

## Actual observations

| Case | Expected / observed | Result |
|---|---:|---|
| Explicit boundaries, timestamp ties and ID gaps | 45 / 45 | Five batches; `limit, limit, limit, limit, end`; MATCH |
| Exact full batch and follow-up | 9 / 9 | First `limit`, then `end`; MATCH |
| Empty historical interval | 0 / 0 | `end`, no media request; MATCH |
| Imported origin at ID 34 | 16 / 16 | Declared tail only; `limit, limit, end`; MATCH |
| Relative window after process restart | 46 / 46 | Same saved run/dates, five batches; MATCH |
| Imported, subsecond-bounded photo | 1 / 1 | Exact ID/date and independent 173,837-byte photo hash; MATCH |
| Actual SDK pagination | 350 / 350 | Six history requests, three caller batches; MATCH |

The photo SHA-256 was
`ee515f404f8e760679cfa72d55d832a599309fc0ca1035d9acf7c719b7b6c984`.
Only included media was downloaded. All seven comparisons had zero missing IDs,
unexpected IDs, date mismatches and media mismatches, and unchanged lifecycle state.

The larger window was `[2026-09-14T17:25:09Z, 2026-10-06T11:28:33Z)`, caller batch size
120. Normal SDK page sizing was retained. Actual iterator/page pairs were
`(1,1),(1,2),(2,1),(2,2),(3,1),(3,2)`; repeated small first pages were not counted as
pagination. The independent capture contained both date-boundary witnesses.

## Controlled interruptions and storage

- **LIVE source + INJECTED cancellation:** after a real five-record response arrived
  and was charged, a local barrier withheld it from the caller. Cancellation propagated,
  the five-record charge remained and lifecycle state did not change. This characterizes
  an answered read, not an unknown network outcome or Stage 5 recovery.
- **LIVE full prefix + INJECTED refusal:** after a real nine-record `limit` batch, the
  next history send was refused. No additional history request reached the sender.
  The exception contained an empty `interrupted` partial result, never a successful
  `end`. The existing budget retained its conservative nine-slot reservation.
- **LOCAL/INJECTED actual SQLite:** test_24 passed **23/23** again, including actual
  process exits before/after creation commit, committed cleanup error, exact CAS,
  uncertain/lost replies, frozen dates, conflicts, absence and corrupt-state refusal.
  These are process-crash observations, not power-loss certification.
- Instrument checks passed **10/10** with sockets blocked. Changed Python compiled
  and passed Python 3.7 AST grammar checks; no Python 3.7 runtime claim. The original
  198-group Stage 2 sweep remains a separate receipt and was not counted as rerun here.

## Findings and corrections

1. Authentication was initially missing. Qualification stopped before history; the
   user requested and completed local login. No automatic code-request loop ran.
2. Real Telethon startup attempted account-wide `GetDifference` despite updates being
   disabled. The guard refused it before send. Earlier synthetic reader tests did not
   exercise actual SDK `connect()` startup.
3. Restoring saved state alone was insufficient when saved state was empty. The final
   diagnostic startup hook restores real state or initializes from actual self/state
   metadata without the difference call. Authentication responses, history iteration,
   budget admission and fresh account verification remain real. A regression now runs
   actual SDK connect with missing, zero and populated saved state. Passive receive
   loops are outside that synthetic sender model: an initial test stalled there, was
   stopped, and those unrelated loops were made idle before all ten checks passed.
4. The first supplied username resolved to a user, so no history was read from it.
   The replacement group's 46 records could not cover a full SDK page; the user supplied
   a larger existing group. No seeded messages or weakened assertion replaced that case.

No product implementation or expected result was weakened. The correction is local
instrumentation enforcing the original selected-source policy. Per-scan verdicts remain
INCONCLUSIVE by design; **this manual aggregate review** closes the gate only after
all required evidence is present.

## Evidence and handoff

[Observations](gate-a-evidence/observations.json) include frozen expectations, source
IDs/dates, hashes and actual RPC/page observations, with account identity redacted.
[Evidence notes](gate-a-evidence/README.md) describe archived execution recipes and
private originals. State/tool logs are included. No credentials, session/budget/state
databases, message bodies, sender identities or downloaded photos are committed.

This covers Gate A foundation portions of C01–C05, C12–C14, C37 and C40–C44. Later
preparation, delivery, completion, pacing, controls, recovery and public integration
remain unimplemented/unrun. No skipped critical live assertion counts as a pass.

**Next: Stage 3 — prepare, retain, replay and acknowledge one exact batch.** Gates B–D
remain pending. Changes invalidating these reader/store/tool assumptions reopen the
affected evidence. Gate A PASS does not approve a PR, merge, release or another backend.
