# tgdata backlog

Snapshot: 2026-10-08, after [PR #20](https://github.com/karaposu/tgdata/pull/20)
merged into `dev` at `95ed4c7`.

## The two later proposals

- **[#17 — Account pool with automatic recovery](https://github.com/karaposu/tgdata/issues/17).**
  Let tgdata choose an account that is healthy, has group access and has budget left,
  then switch accounts when one fails. Automatic joining could use a spare account.
  First delivery implemented on `feat/17-account-pool` in `964d082`: routing and
  failover for groups the accounts can already read. All 393 supported offline
  checks passed. Pending: merge check, PR, fresh PR critique and two-account live
  qualification. The user chose one account/offline testing first.
  Automatic joining is deferred; #7 stays paused.
- **[#18 — Group synchronization with acknowledged progress](https://github.com/karaposu/tgdata/issues/18).**
  Remember group progress, replay unfinished deliveries, and support daily reading
  plus historical backfill. Its daily/fixed-window foundations and
  [#19's eight-stage backfill lifecycle](https://github.com/karaposu/tgdata/issues/19)
  are now merged. The parent #18 issue remains open; its checklist needs to be
  reconciled with the completed merge.

## Other unfinished work

| Issue | Capability | Where we left it |
|---|---|---|
| [#3](https://github.com/karaposu/tgdata/issues/3) | Check proxy connectivity, exit IP changes and Telegram access | Deferred because live proxy testing was unavailable. |
| [#7](https://github.com/karaposu/tgdata/issues/7) | Look up groups, check access and join | Paused by the user after review exposed account/health ownership and error-handling problems. Do not resume automatically. |
| [#8](https://github.com/karaposu/tgdata/issues/8) | Phone → code → 2FA login through an API, without terminal prompts | Not started. Its old #5 dependency has been satisfied. |
| [#10](https://github.com/karaposu/tgdata/issues/10) | Run tgdata as a worker accepting reading jobs | Still waiting on #7; the other listed prerequisites are complete. |

## Completed

- #1 — account proxy routing.
- #2 — fixed device identity.
- #4 — account health events.
- #5 — pluggable session storage.
- #6 — stable, versioned message batches.
- #9 — per-account read budgets.
- #19 — durable backfill lifecycle, all eight stages and live Gates A–D; merged and closed.

Scheduling, account selection and permanent receiver storage remain caller-owned
in the merged daily/backfill APIs. #17 is the separate proposal to bring account
selection and failover into the library. Edits/deletions remain excluded; competing
readers are outside the selected synchronization scope.
