# tgdata: what changed since 0.0.8

**Snapshot: 14 October 2026.** This compares published **0.0.8** with the merged
`dev` code at [`f927496`][current], including step-by-step login in PR #28.

Most of the planned implementation is complete. Nine of the original ten issues
are implemented and closed; **#3, proxy testing and exit-IP monitoring, remains
unimplemented**. The later daily/backfill proposal is complete. The account pool's
selected first delivery is merged, with two-account live validation still deferred.

**Merged code and a published release are different milestones.** At this snapshot,
PyPI still publishes `0.0.8`, and the merged code still declares that version too.
The features below describe the newer `dev` commit, not what installing the published
`0.0.8` package provides. A release must package the merged code and assign its new
version. This document does not choose that next version number.

## The baseline

The GitHub release is named [`v0.8`][baseline], but its package version is `0.0.8`.
The eight non-test Python modules in the published [0.0.8 wheel][pypi] match that
tag byte-for-byte. The comparison therefore uses a verified release baseline,
not the version string in an arbitrary working checkout.

Version 0.0.8 already supported message extraction, DataFrames, CSV/JSON exports,
incremental reads using `after_id`, media detection/downloads, polling, event
listeners and group discovery. Its discovery methods—`search_groups`,
`similar_groups`, `linked_groups` and `discover_groups`—are **existing features**.

The major expansion is the machinery around repeatable scraping: account policy,
explicit authentication, portable data, acknowledged progress, controlled history
runs, account selection and a process interface for another application.

## Before and after

| Area | Published 0.0.8 | Current merged `dev` |
|---|---|---|
| Proxy routing | No tgdata account-proxy configuration | One configured proxy applies to every library-created client, with optional mandatory-proxy enforcement |
| Device identity | SDK/machine defaults | Per-account device, app and language settings can be pinned |
| Authentication | Primarily interactive setup; the persistent path could prompt again | Headless readers refuse login; a separate phone/code/2FA API performs deliberate onboarding |
| Session storage | Normal Telethon session storage | Optional application-provided session store using opaque text |
| Account health | Errors/logs and basic connection checks | Structured health events, summaries and verified-account attribution for temporary operations |
| Read allowance | Per-call limits and pacing | Shared per-account rolling 24-hour budgets and configurable warm-up caps |
| Portable messages | DataFrames and general exports | Immutable, versioned `MessageBatch` objects with stable serialized identity |
| Media delivery | Existing media-download APIs | Batch downloads publish complete hash-named files and verify saved artifacts on replay |
| Daily continuation | Application tracks its own cursor | Stored pending batches, replay and explicit acknowledgment before advancing progress |
| Historical windows | Application supplies date limits | A historical collection can freeze “last N days” into permanent boundaries |
| Planned backfill | Application owns the run lifecycle | Durable runs with pacing, completion, controls, receipts and explicit recovery |
| Group operations | Existing discovery and read-time resolution | Account-verified lookup, access probes and deliberate joining with a separate join allowance |
| Multiple accounts | Connection pooling for one account | `AccountPool` selects among distinct accounts and performs bounded failover |
| External process use | Embed the Python library | `tgdata-worker` accepts explicit-account JSON-line jobs and returns structured results |

## 1. Consistent proxy and device settings — #1 and #2

Each account can have a proxy in its INI configuration. The common client factory
applies it to persistent connections, same-account pooled connections and temporary
operations, including login. SOCKS5, SOCKS4 and HTTP CONNECT are supported.

`require_proxy = true` refuses a missing proxy. Invalid configuration or a failed
proxy stops the connection; there is no automatic direct connection as a fallback.
Proxy support has an optional installation extra, `tgdata[proxy]`.

Device identity can be fixed with `device_model`, `system_version`, `app_version`,
`lang_code` and `system_lang_code`. `device_identity()` reports the effective values
and gives configuration lines for pinning them. Existing sessions pick up configured
identity settings on their next connection without another login.

**Practical difference:** moving an account between a laptop and a server no longer
requires inheriting each machine's device defaults, and routing policy applies
consistently across the library's clients. Proxy routing does not yet measure or
monitor the exit IP; that is the unfinished #3.

Details: [proxy configuration][proxy] and [device identity][device].

## 2. Login can be separate from scraping — #8 and the headless-login fix

Ordinary background reading no longer requests codes that nobody can enter. Under
the default policy, only a first login of a brand-new session at a terminal may
prompt. A logged-out session raises `AuthRequiredError`; applications can explicitly
set `interactive_login=False` to forbid prompts entirely.

The new `LoginFlow` supports independent calls to:

1. `start(phone)` to deliberately request a code.
2. `submit_code(code)` to submit it.
3. `submit_password(password)` when two-factor authentication is required.

The application can retain the object or privately save `export_state()` and restore
it between completed steps. Safe status describes the next action without exposing
credentials. Wrong input, waits, expired challenges, unsupported interactions and
uncertain outcomes remain distinguishable. `check_authorization()` checks whether
an interrupted login succeeded without sending another code.

Once complete, `session_data` supplies the credential in tgdata's session-store
format. The application saves it explicitly. Known progress survives later local
failure or cancellation; failed cleanup blocks another step or secret export until
the retained close is settled.

**Practical difference:** a web page can collect each input separately. Login is
an explicit application operation rather than a side effect of trying to scrape.
Completed-step restoration requires one owner using the latest private state;
it does not coordinate concurrent workers or guarantee replay after a mid-call crash.

Details: [step-by-step login][login]. Live Telegram login validation is still pending.

## 3. Sessions can live in application storage — #5

`TgData(..., session_store=store)` supports a caller-provided object with synchronous
`load(name)`, `save(name, opaque_text)` and optional `delete(name)` methods.

Store-backed sessions retain the login key, data centre, update state, group/channel
access information and the account's own identity rows. They do not build a cache of
message senders. The payload is opaque text; it is not Telethon's `StringSession`
format and should not be parsed by the application's database layer.

Load failures raise. Save failures are logged without credential contents and can
be retried at later save points. Older clients do not knowingly overwrite a different
login they did not load. That protection is not a distributed atomic-write protocol.
Encryption and access control belong to the store; its methods should return quickly.

**Practical difference:** applications can keep sessions in their own database
instead of depending on local `.session` files. File sessions remain available,
and existing files are not automatically migrated.

Details: [session storage][sessions].

## 4. Health is observable and tied to the correct account — #4 and #7

`health_callback` receives structured observations for waits, logout, bans,
restrictions, group-access refusals and observed recovery. Events identify the
account, operation, request or group involved, with relevant wait information.
`health_check()` also exposes a summary and checks actual authorization rather than
treating a connected socket as sufficient.

The staged group-operation work added verified numeric account ownership. A temporary
client using account B cannot assign its result to cached account A. The new
`get_account_health(account_id)` view belongs to these verified operations; it is
separate from the existing public-read health summary.

Recovery needs evidence relevant to the previous problem. Metadata lookup or a
successful identity check does not prove that a denied history read is now allowed.
Local file/storage failures do not become Telegram account-health failures.

**Practical difference:** applications can respond to a named condition instead of
guessing from log text. Plain `TgData` health reporting observes conditions; the
separate account pool supplies routing decisions. Health notifications are not a
durable audit log or a complete account-monitoring service.

Details: [health events][health] and [verified-operation health][owned-health].

## 5. Read budgets are enforced across account activity — #9

`ReadBudget` provides per-account policy and a shared SQLite ledger. The key is the
authenticated numeric Telegram account ID, independent of session names. Reusing
the same ledger on one host shares the allowance across cooperating readers.

The budget supports a rolling 24-hour cap, a zero cap to pause reads, and an explicit
warm-up curve. History, search, message-ID lookups and message re-fetches for media
can consume allowance. Metadata and downloading file bytes are different operations.

Capacity is reserved before a send. Successful responses settle the charge; failed,
cancelled or uncertain attempts retain their reservations. Retries require allowance
again. Exhaustion stops work with a structured error, retry information and available
partial results instead of silently discarding completed work.

**Practical difference:** several jobs cannot each treat the same account as having
a fresh daily allowance. Without a configured `read_budget`, ordinary `TgData` has
no added account quota. The account pool and worker require deliberately provisioned
read policies. Configured caps are application policy, not proven restriction-free
Telegram rates.

Details: [read budgets][read-budget].

## 6. Message batches have a stable delivery format — #6

`get_message_batch()` adds a portable alternative to the existing DataFrame API.
It reads oldest first, strictly after `after_id`, and returns an immutable
`MessageBatch` with:

- A versioned schema, canonical JSON and a deterministic `batch_id`.
- An exclusive input cursor and the last completely prepared message position.
- Explicit `limit`, `end` or `interrupted` stop reasons.
- Message, sender, reply, forward, album and media metadata within the documented
  projection. It is not a dump of every Telegram SDK field.

Identifier fields in the batch JSON use decimal strings to preserve large values.
A saved batch replays with the same identity. A new fetch may produce a different
observation, so receivers should also deduplicate messages by `(chat_id, message.id)`.

Optional media downloads publish complete files under content hashes, with size and
integrity checks. Original filenames are metadata rather than output paths. The
manifest and media files can be delivered separately, but the caller must retain
both when downloads were requested. Reference mode downloads no files.

**Practical difference:** a laptop, worker and receiver can exchange one defined
payload without depending on pandas or live SDK objects. Ordinary failures can carry
a completed prefix. Raw batch reads alone do not own a durable progress cursor or
promise a returned prefix on cancellation.

Details: [message batch v1][batches]. Existing DataFrame/export APIs remain available.

## 7. Daily continuation has durable acknowledgment — #18

Previously, an application passed its own `after_id` and decided when to save a new
cursor. Daily continuation now keeps an acknowledged position and at most one
pending batch per canonical group in a configured progress store.

The workflow is:

1. `initialize_sync()` deliberately enrolls the group at a known accepted position.
2. `sync_group()` prepares a bounded batch and saves it as pending, or replays the
   existing pending batch without another Telegram read.
3. The application's destination durably accepts the batch and required media.
4. `acknowledge_sync()` advances the saved position and clears the pending batch.

If an upload fails, the cursor has not advanced. If upload succeeded but acknowledgment
was lost, the same saved batch can be replayed. The receiver must recognize duplicates;
this is not an exactly-once transaction across Telegram and a remote database.

`SQLiteSyncStore` supplies local persistence, and a custom async backend can implement
opaque-text load plus atomic compare-and-swap. The application chooses storage and
schedules calls. Progress is tied to the canonical group, not a particular account
or laptop, but different accounts may see different history.

**Practical difference:** missing a day's scrape leaves work after the saved bookmark;
it does not silently replace the query with “the last 24 hours.” One active reader
per group/store remains the supported operating condition.

Details: [daily continuation][daily].

## 8. Historical windows stay fixed across restarts

A historical collection can use explicit timezone-aware dates or `last_days=N`.
Relative dates are resolved once and saved. Restarting tomorrow continues the same
window rather than shifting it forward and changing the job's meaning.

The interval is start-inclusive and end-exclusive. Message-ID continuation is still
used inside it, including when several messages share the same timestamp. Daily
and historical progress use separate collection namespaces/stores so their bookmarks
do not interfere.

**Practical difference:** “read these 30 days” is a stable collection request. Fixed
dates define the query; they do not freeze Telegram's contents or visibility. A fixed
window by itself is distinct from the managed run lifecycle below.

Details: [fixed historical windows][windows].

## 9. Backfill is a durable, controllable run — #19

The completed backfill lifecycle builds on batches, fixed windows and acknowledgments.
A run retains its identity, destination, accepted progress, pending delivery, pacing,
source-end evidence, operator controls and any unresolved attempt.

Public operations cover starting, status, preparing/replaying a bounded turn,
acknowledgment, pause/resume/cancel/abandon and explicit recovery. Important behavior:

- A matching creation retry recognizes the original request; it does not invent a
  new run. A deliberate successor has its own identity.
- Pending output replays locally without another read or new budget charge.
- A final nonempty batch remains owed until acknowledged. A failed or limit-sized
  read does not prove that the history is complete.
- Pause blocks new admissions while allowing admitted work to settle. Cancel can
  still leave data owed to the receiver; a late valid acknowledgment does not turn
  cancellation into completion.
- An uncertain attempt prevents another read until the previous reader has actually
  stopped and the caller performs the appropriate explicit recovery.
- Pacing survives restarts. A turn returns a wait for the caller's scheduler; the
  application can give daily work a turn between historical chunks.

Acknowledgment uses a delivery reference scoped to the run and destination, not just
a batch hash. Download replay verifies the retained files rather than fetching
replacement observations. The application owns receiver durability and scheduling.

**Practical difference:** a planned history job can be interrupted and resumed with
its meaning and delivery obligations intact. It no longer has to be represented as
one long scrape with an application-only “done” flag.

Details: [backfill runs][backfill]. The staged daily/backfill work included read-only
live validation; its final public Gate D passed on 7 October 2026 for the tested
source, SQLite backend and receiver composition.

## 10. Lookup, access checks and joining are explicit operations — #7

`lookup_group(target, account_id=...)` returns group details and qualified membership
information. `check_group_access(...)` returns `readable`, `denied` or `unprobed`;
when possible it performs a bounded history probe under the existing read allowance.
Looking up a group does not join it.

Each operation verifies the actual authenticated numeric account before group work,
preserves the configured connection policy and closes its temporary client. A stale
cached identity cannot authorize a different account. This was the prerequisite
foundation built during #7's staged implementation.

`join_group(...)` is a separate mutation and requires an explicit `JoinBudget` policy.
That SQLite ledger counts admitted attempts in a rolling 24-hour window. Failed or
uncertain admitted attempts are not refunded. Existing membership and known payment
requirements can be observed without a new join.

Join results distinguish `joined`, `already_joined`, `requested`, `payment_required`
and `interaction_required`. Requesting approval is not membership; membership is
not proof of readable history. Payments and bot interactions remain separate actions.

**Practical difference:** an application can inspect and onboard groups without
opening an unbounded raw client or mixing group lookup with membership changes.
This joining primitive does not add automatic joining to `AccountPool`.

Details: [group lookup/access][groups], [joining][joining] and [join allowance][join-budget].

## 11. An account pool can choose and recover — #17

`AccountPool` manages distinct, already logged-in accounts for groups they can already
read. This is separate from `TgData(connection_pool_size=...)`, which still represents
multiple connections for one account.

Selection considers saved health restrictions, group denials, available read budget,
configured warm-up eligibility and unresolved attempts. The `drain` strategy chooses
the first eligible account; `spread` prefers the largest remaining allowance.
Retries are bounded, and repair or uncertain attempts can require explicit rechecking
or recovery. If no account can proceed, `PoolUnavailable` supplies per-account reasons
and retry hints.

The pool supports raw batches and the daily/backfill interfaces. Its reads require
a caller-retained `PoolReadCapture`, which keeps complete available records accessible
through failures, cancellation and later application handling. A completed nonempty
prefix stops failover so its data can be handled first. A capture is not proof that
progress was durably saved or that a receiver acknowledged it.

The pool uses persistent routing/recovery state and exposes passive health observations
through `drain_health_events()`. It has one owning process/event loop and exclusive
session ownership; it is not a distributed pool coordinator.

**Practical difference:** reusable account selection and eligible failover can move
out of ScrapeOps or a web application's reading code. Automatic joining remains
deferred, and two-account live qualification still needs a second approved account.

Details: [account pools][pool].

## 12. Another application can run tgdata as a worker — #10

`tgdata-worker --config worker.json`, or `python -m tgdata.worker`, runs a resident
serial process using a versioned JSON-lines protocol on stdin/stdout.

Each job selects an account explicitly and can request `read_batch`, `lookup_group`,
`check_group_access` or `join_group`. The process emits readiness, health and terminal
result frames, including structured errors and completed partial batches when available.
Read jobs return reference-only media batches.

Startup uses an existing account inventory and budgets. Jobs cannot replace credentials,
proxy settings, paths or allowance. Stop signals and output failures have defined
behavior; failed cleanup stops the worker instead of letting it reuse a questionable
client. A missing terminal reply means completion is unknown, not that nothing happened.

**Practical difference:** the consuming app can use a managed subprocess instead of
embedding Telegram event-loop logic. The worker has no HTTP server, scheduler or
automatic account selection. Daily/backfill acknowledgments also remain outside this
worker protocol; use the library interfaces when those operations are needed.

Details: [worker protocol and examples][worker].

## Reliability changes across the existing APIs

These accompany the new capabilities rather than replacing the older read APIs:

- Per-request flood-wait thresholds now work through the configured client factory.
  Discovery handles the SDK's relevant wait-error family; some existing post-reading
  and dialog-sync paths still use native SDK sleeps.
- Headless login checks distinguish missing/revoked authentication from network or
  local failures and avoid repeated unsolicited code requests.
- Budget failures preserve available partial results and stop polling instead of
  automatically spending further allowance.
- Local file/storage errors keep their own meaning instead of inheriting an unrelated
  Telegram health verdict. Cleanup failures preserve the primary outcome where the
  operation's contract requires it.
- Temporary group operations, worker jobs, login flows and pool operations now have
  explicit account/lifetime rules. Cancellation does not imply remote rollback, a
  completed disconnect or an uncommitted database write.

## What remains the application's responsibility

| Responsibility | Current boundary |
|---|---|
| Groups and account inventory | The application chooses and provisions them |
| Schedule | The application decides when daily/history turns and worker jobs run |
| Permanent archive and uploads | The destination saves messages/media durably and deduplicates delivery |
| Business logic | Categorization, LLM extraction—including contact extraction—and product workflows stay in the consuming application |
| Storage deployment | The application protects credentials/content, chooses backends and preserves known state on restart |
| Account choice | Plain TgData/worker callers choose explicitly; AccountPool can choose within its registered inventory and policy |
| Concurrent machines | The application prevents overlapping source ownership; these features do not supply distributed leases |

tgdata can create and update its supported local SQLite state stores and write batch
artifacts when requested. That state is distinct from the application's permanent
message archive. Session, budget, progress and pool stores have separate contracts;
they are not interchangeable. Old edits and deletions remain outside the selected
synchronization scope.

## Migration and release notes

1. **Use the correct code baseline.** The features are in merged `dev` at `f927496`.
   A version-number edit in an older checkout does not include those changes.
   Installing published `0.0.8` does not supply them.
2. **Use Telethon 1.45.0 for this qualified feature set.** The dependency minimum
   rose from `>=1.33,<2.0` to `>=1.45,<2.0`; worker and pool adapters target 1.45.0.
   Supporting 1.33.1 was deliberately excluded. Add the proxy extra when needed.
3. **Existing simple callers can keep their APIs.** DataFrame reads, exports,
   discovery and file sessions remain. New stores, quotas and orchestration are
   explicit configuration. Headless login behavior is an intentional change.
4. **Provision persistent state deliberately.** Reuse budget history and known
   progress on restart. Use the documented reopen modes; do not recreate missing
   state as a shortcut past an error. Keep daily/history namespaces separate.
5. **Integrate acknowledgment with the receiver's durable save.** A successful read
   or upload request is not sufficient evidence that an external destination committed.
   Deduplicate by delivery identity and, where required, group/message identity.
6. **Use the final pool contract.** Earlier development examples without `capture=`
   or using an AccountPool health callback are obsolete. Plain TgData's callback
   remains supported; pool observations are drained explicitly.
7. **Respect representation and filesystem requirements.** Preserve decimal-string
   IDs in batch/worker JSON. Download-mode batch publication needs the documented
   complete-file/hard-link behavior; a manifest does not transfer its media for you.
8. **Treat release publication as a separate step.** Select the release version,
   package the intended merged code and follow the repository's release process.
   This comparison is not a release announcement.

Python `>=3.7` remains declared. The latest verification executed on Python 3.11.10
and checked Python 3.7 grammar; it did not run these features on native Python 3.7.

## Completion and remaining work

| Work | Status at this snapshot |
|---|---|
| Original issues #1, #2, #4, #5, #6, #7, #8, #9 and #10 | Implemented, merged and closed |
| #18 synchronization and #19 backfill lifecycle | Implemented, merged and closed; staged live validation completed within its recorded scope |
| [#3 proxy verification and exit-IP monitoring][issue3] | Open; implementation not started, previously deferred for lack of live test setup |
| [#17 account pool][issue17] | Selected first delivery merged; issue remains open for deferred two-account live validation |
| Automatic joining by the account pool | Deferred; standalone #7 joining primitives are available |
| Real Telegram login validation for #8 | Pending; #8's reviewed implementation is merged and closed |
| A new published package containing the complete set | Pending at this snapshot; PyPI's latest version is still 0.0.8 |
| Old draft PR #16 | Superseded by the completed staged #7 work; housekeeping, not missing functionality |

The actual merged tree passed **28 supported offline suites: 773 executed checks**,
with **three explicit live skips**, and all **five offline examples**. The final #8
review added **16 passing adversarial probe groups**. Daily/backfill also has separate
read-only live evidence; the pool and new login still have the qualifications listed
above. Passing offline tests does not establish every real account, proxy, receiver
or deployment environment. [Merged-code verification record][verification].

## Source references

Feature links above point to the exact compared `dev` commit, so this document
remains readable from an older checkout. Scope/status comes from the merged code,
public guides and current issue/PR records. Historical abandoned plans are not
counted as delivered features.

- [Published 0.0.8 metadata][pypi] and [release tag v0.8][baseline].
- [Current compared commit f927496][current] and [complete source comparison][comparison].
- Delivery PRs: [#11](https://github.com/karaposu/tgdata/pull/11),
  [#12](https://github.com/karaposu/tgdata/pull/12),
  [#13](https://github.com/karaposu/tgdata/pull/13),
  [#14](https://github.com/karaposu/tgdata/pull/14),
  [#15](https://github.com/karaposu/tgdata/pull/15),
  [#20](https://github.com/karaposu/tgdata/pull/20),
  [#21](https://github.com/karaposu/tgdata/pull/21),
  [#22](https://github.com/karaposu/tgdata/pull/22),
  [#23](https://github.com/karaposu/tgdata/pull/23),
  [#24](https://github.com/karaposu/tgdata/pull/24),
  [#25](https://github.com/karaposu/tgdata/pull/25),
  [#26](https://github.com/karaposu/tgdata/pull/26),
  [#27](https://github.com/karaposu/tgdata/pull/27) and
  [#28](https://github.com/karaposu/tgdata/pull/28). Proxy/device work predates those
  PRs and is recorded in [#1](https://github.com/karaposu/tgdata/issues/1) and
  [#2](https://github.com/karaposu/tgdata/issues/2).

[baseline]: https://github.com/karaposu/tgdata/tree/a10309367774e6412aabc83ed8e962331fe93df2
[current]: https://github.com/karaposu/tgdata/commit/f92749688b7d544da55249459c489164497d47ed
[comparison]: https://github.com/karaposu/tgdata/compare/a10309367774e6412aabc83ed8e962331fe93df2...f92749688b7d544da55249459c489164497d47ed
[pypi]: https://pypi.org/project/tgdata/0.0.8/
[proxy]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/README.md#connecting-through-a-proxy-optional
[device]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/README.md#a-fixed-device-identity-optional
[sessions]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/README.md#keeping-sessions-out-of-files
[login]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/stepwise_login.md
[health]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/README.md#account-health-events
[owned-health]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/account_operations.md#owned-health-composition-stage-2
[read-budget]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/README.md#per-account-read-budgets
[batches]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/message_batch_v1.md
[daily]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/daily_continuation.md
[windows]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/fixed_windows.md
[backfill]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/backfill_runs.md
[groups]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/group_operations.md
[joining]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/group_joining.md
[join-budget]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/join_budget.md
[pool]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/account_pool.md
[worker]: https://github.com/karaposu/tgdata/blob/f92749688b7d544da55249459c489164497d47ed/docs/worker.md
[issue3]: https://github.com/karaposu/tgdata/issues/3
[issue17]: https://github.com/karaposu/tgdata/issues/17
[verification]: https://github.com/karaposu/tgdata/blob/b7237c61d2011975d33701a5c9d0af32c02ce84f/devdocs/work/8-stepwise-login/merge-record.md
