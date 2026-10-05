---
model: unknown
effort: unknown
---

# Per-account read budgets — issue #9

> Warmth: this session read the full codebase before #5 and verified the merged
> runtime at `af593fc`. For #9 it additionally read Telethon's request loop,
> message/ID/dialog iterators and iterator base, and ran the pagination and
> multi-process SQLite probes in this folder. Triage is feature-heavy. The
> historical `devdocs/scoped/9` heartbeat proposal is a different task.

**Source:** GitHub #9 and the maintainer's request to run task-impl. Related
work: #5 has landed; #6's versioned batches and #10's worker remain separate.

## Problem Statement

Each tgdata fetch can be paced, but multiple jobs and connections can read an
unlimited combined number of messages for the same account. A per-connection
counter cannot survive restarts or coordinate jobs. Counting output rows is
also too late: Telethon has already fetched an entire page before tgdata
filters or converts its messages.

## User Value Proposition

An application configures an account's allowance once. Every explicit message
reader built through tgdata's shared client factory then spends from the same
allowance, including pooled and short-lived connections. A caller requesting
2,000 messages from an account whose current allowance is 300 stops after at
most that allowance and receives a clear budget status and retry time. Already
processed results remain recoverable. Tests can deliberately configure larger
limits for their own accounts without changing the library's safeguards.

## Success Criteria

1. **Opt-in and identity.** Supplying a read budget enables enforcement;
   omitting it preserves current behavior. Accounting uses Telegram's actual
   account ID, not the session-file name, pool suffix, username or label.
   An enabled budget with missing account policy or unknown account identity
   refuses message pulls instead of silently becoming unlimited.
2. **One durable allowance.** Jobs using the same budget database and account
   share usage, including independent processes. Usage and warm-up age survive
   client restarts. Concurrent claims cannot each spend the same remaining
   allowance. No storage transaction remains open during network I/O.
3. **Count retrieval, not presentation.** Count message slots returned by
   explicit history/search/message-ID requests, including repeats, service or
   empty placeholders, messages later filtered out, and internal re-fetches.
   Protect before dispatch using the request's bound. Successful replies can
   release unused reserved capacity. Failed, cancelled or crashed calls keep
   their reservation conservatively until it ages out.
4. **Window and warm-up.** [ASSUMPTION] Use a rolling 24-hour allowance, avoiding
   a double allowance at a fixed reset boundary. Warm-up uses completed
   24-hour days since a persisted start time; first configuration defaults to
   now and callers may supply the known start. Explicit policy updates preserve
   usage and the existing start unless a new start is explicitly supplied.
   A backward clock does not make spent capacity available again.
5. **Paging remains correct.** Reduce a history/search page before Telethon
   calculates its offsets, including oldest-first and after-ID reads. A quota
   race may stop a request, but must not skip messages by changing an offset
   window. ID lookups retain positional meaning; they are not silently
   truncated to masquerade as missing messages.
6. **Every supported reader participates.** History fetch, search, polling,
   discovery link-mining, counts that fetch a message, and media metadata
   lookups use the guard. A script using a tgdata-created client's message
   APIs also reaches it. Unsupported unbounded message-returning requests or
   batched/wrapped message requests fail closed when a budget is enabled.
7. **Stop and report.** Exhaustion has a distinct exception carrying account,
   requested capacity, limit/usage/remaining and the earliest retry time (or
   that a policy change is needed). Bulk tgdata operations attach their
   already processed partial result. Polling stops instead of retrying every
   interval for hours. Budget errors are local policy/storage signals, not
   fabricated Telegram account-health verdicts.
8. **Storage failure is closed.** A failed budget read/write prevents further
   message dispatch. A failure settling a completed request leaves its full
   reservation charged. Budget storage contains counters/policies and account
   IDs, never login keys or message contents.
9. **Offline evidence.** Test window expiry, warm-up, restart, reconfiguration,
   clock rollback, cancellation/failure, simultaneous claims, and actual
   Telethon pagination/request control flow with scripted replies. Run the
   supported offline regression suites with live checks disabled. These tests
   verify enforcement, not that a configured rate is safe for Telegram.
10. **Documented contract.** Explain configuration, what consumes allowance,
    shared storage, conservative reservations, partial results, retry timing,
    and unchanged behavior without a budget.

## Scope Boundaries

- [ASSUMPTION] The allowance covers explicit message pulls. User/group/dialog
  metadata (including incidental dialog previews), downloads of file bytes,
  unsolicited real-time updates and their transport recovery are outside this
  message allowance. Discovery searches/recommendations stay metadata;
  reading posts to mine links is charged.
- [ASSUMPTION] A SQLite database supplied by the application is the initial
  durable coordinator. Callers on separate hosts or separate databases are
  not coordinated. A remote quota backend is not part of this issue.
- The boundary is clients created by tgdata with that budget. This is not a
  sandbox against code constructing another Telegram client, changing policy
  deliberately, opening a different ledger or bypassing private internals.
- No claim about Telegram-safe numeric limits. Limits and warm-up schedules
  are application policy; examples are illustrative.
- No automatic sleeping until the next allowance, account selection, worker,
  proxy test, stepwise login, message-batch schema or message archive.
- No change to the session-store protocol, credential serialization, default
  file sessions or successful DataFrame/media return types. Standard-library
  SQLite suffices; no new mandatory dependency is required.

## Priority Level

**Medium — P2.** It belongs before later stress testing and the worker because
it gives every supported reader a shared, explicit ceiling.

## Known Blockers

None open for implementation. The accounting/window/storage choices above
are explicit assumptions to be assessed by the plan critic. Verification is
offline; live Telegram behavior and safe real-world quotas are not established.
