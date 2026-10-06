---
model: gpt-6-astra
effort: max
---
# Fixed-window implementation record

Runtime/tests/public docs: e87754e1717dc06f2b5232f3cb4d776bf0932d81.
Parent daily delivery: d096442, verified at 0a9f824.
Branch: feat/18-daily-group-continuation.
Worktree: /private/tmp/tgdata-18-daily-group-continuation.

## Delivered

- Internal immutable UTC window validation and canonical saved timestamps.
- Optional start_date/end_date on get_message_batch; date-positioned first read,
  exact half-open filtering, exclusive-ID resume, and filtered-page continuation.
  Media is prepared only after membership in the interval is established.
- Optional explicit bounds or last_days on initialize_sync. Relative enrollment
  observes time once; repeat initialization loads first and retains saved dates.
  Conflicting query/seed/mode/input-form changes refuse rather than reset.
- Existing sync_group/replay/acknowledgment preserve the window. Strict pending
  validation rejects missing/out-of-window dates. Existing local error/partial
  result and media-verification paths remain authoritative.
- Daily records stay v1; window records use v2 in the same opaque backend protocol.
  No SQLite schema change. Status exposes immutable dates and relative input;
  daily status dictionary keys remain unchanged.
- Public examples/contracts and test23 with 22 offline behavioral groups.

## Plan execution

Triage cd111dd; description/probe 5c9b914; plan1 0e3e4a4; critic ac6bbfb.
The in-session critic returned IMPLEMENT AS WRITTEN with no selected mitigations.
All six steps were executed in order. No structural deviation or product-code
correction was needed during verification. Existing test expectations were unchanged.

The first test23 run passed22/22. Additional assertions then covered changing a
relative duration/input form and repeating relative setup after actual acknowledgment;
the same22 groups passed again. This strengthens the planned request-identity
coverage without changing behavior or existing expectations.

Two verification-environment/driver issues were resolved and are not hidden:
1. The proxy suite could not bind localhost under the default sandbox. It passed
   unchanged after a narrowly approved rerun with local socket access, using an
   explicitly nonexistent config to skip both live checks.
2. The temporary all-suite driver initially failed to await test11's two async
   helpers, printing a misleading pass before RuntimeWarnings. That initial result
   is not counted as evidence. Both helpers were actually awaited with sockets
   forbidden on the committed runtime and passed. The corrected invocation is in
   verification.md. No project source or expected assertion was changed for it.

## Boundaries and remaining work

This delivers fixed-window reads through the existing collection/ack contract.
Daily and historical collections of the same group use separate stores. It does
not add planned scheduling, pacing, named runs/re-arm or permanent completion state.
Those remain #18 follow-up work; the issue stays open.

The code has not been merged. Next gates are a combined merge-check, PR and fresh
in-session PR critique, accounting for both the daily and fixed-window documents.
Merge still requires the maintainer's go-ahead; work-folder documents remain on
this archive branch. The original #7 checkout and its untracked HANDOFF.md remain
unchanged, and no duncan path or ScrapeOps file was included.
