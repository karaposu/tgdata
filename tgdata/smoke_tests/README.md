# Smoke Tests for TgData

This directory contains smoke tests for the TgData Telegram message extraction library.

## Test Coverage

### 1. **test_00_connection.py**
Tests basic connection functionality:
- Connection initialization
- Connecting to Telegram
- Authentication validation
- Session persistence

### 2. **test_01_list_group_chats.py**
Tests group listing functionality:
- Listing all accessible groups/channels
- Group metadata retrieval
- Group filtering and sorting

### 3. **test_02_get_message_count.py**
Tests message counting:
- Get total message count without fetching all messages
- Efficient count retrieval using Telethon's API

### 4. **test_03_get_all_messages.py**
Tests basic message retrieval:
- Fetching all messages from a group
- Message data structure validation
- Basic filtering and limits

### 5. **test_04_get_all_messages_in_batches.py**
Tests batch processing:
- Fetching messages in configurable batches
- CSV export with incremental writes
- Progress tracking
- Using `after_id` for incremental fetching

### 6. **test_06_advanced_features.py**
Tests advanced features:
- Connection pooling
- Progress tracking callbacks
- Date-based filtering
- Message caching behavior
- Metrics and logging
- Health checks and validation

### 7. **test_10_polling.py**
Tests polling and real-time features:
- Polling for new messages at intervals
- Real-time event handlers
- Error handling in polling
- Multiple handler registration

## Running Tests

### Run Individual Test:
```bash
# Basic tests
python -m tgdata.smoke_tests.test_00_connection
python -m tgdata.smoke_tests.test_01_list_group_chats
python -m tgdata.smoke_tests.test_02_get_message_count
python -m tgdata.smoke_tests.test_03_get_all_messages
python -m tgdata.smoke_tests.test_04_get_all_messages_in_batches

# Advanced tests
python -m tgdata.smoke_tests.test_06_advanced_features
python -m tgdata.smoke_tests.test_10_polling
```

### 8. **test_11_discover_groups.py**
Tests group discovery (`python -m tgdata.smoke_tests.test_11_discover_groups [config.ini]`):
- `build_search_queries` and the empty/unresolved frame shapes (no network)
- `search_groups`, `similar_groups`, `linked_groups` (unresolved, then resolved with a budget of 3)
- `discover_groups` with `found_callback`, `heartbeat` and the link-source cap
- a `get_messages` round-trip on a discovered room

Cost: about a dozen requests and three username resolutions on the live account. Do not scale it up.

### 9. **test_12_proxy.py**
Tests proxy support (`python -m tgdata.smoke_tests.test_12_proxy [config.ini]`):
- proxy URL parsing, masking, and the forms that are refused (no network)
- config loading: no key = direct, `require_proxy` refusal, inline comments, password kept out of `repr` (no network)
- every client (main and pool) is built with the proxy (no network)
- a dead proxy and a proxy that refuses the tunnel both FAIL; nothing falls back to a direct line (loopback only)
- a local SOCKS5 relay with a user name and password carries a full round trip to Telegram for a throwaway, never-logged-in session
- a real proxy from the config, when the config has a `proxy` key (pending a real proxy)

Items 3–6 need `pip install 'tgdata[proxy]'`. Item 6 reads only `api_id`/`api_hash` from the config; the account's own session is never opened.

### 10. **test_13_device_identity.py**
Tests the fixed device identity (`python -m tgdata.smoke_tests.test_13_device_identity [config.ini]`):
- no keys: Telethon's machine defaults, unchanged (no network)
- pinned keys presented as written: spaces kept, quotes and inline comments stripped, `lang_code` alone sets `system_lang_code` (no network)
- the use-and-close, persistent and pool clients all carry it — driven through the real code paths with a stand-in client that refuses to connect (no network)
- `device_identity()`: pasting its `config_lines` back pins exactly the same identity (no network)
- `health_check()` reports the presented identity (no network)
- Telegram accepts a connection presenting a pinned identity (throwaway session, no login)

Whether Telegram's active-sessions list *shows* the pinned values needs a logged-in account and is not checked here.

### 11. **test_16_health_events.py**
Tests account health events (`python -m tgdata.smoke_tests.test_16_health_events`) — entirely offline, no config needed:
- the verdict table, by Telegram's own error names, through tgdata's wrappers
- the event shape and its delivery: the same exception re-raised, the event first, a raising callback harmless
- Telethon's silent sleeps become events, per account and per call, with console output unchanged
- "ok" only on recovery; the summary in `health_check()["health"]`; the log mirror's levels
- polling stops on what retrying cannot fix; `validate_connection()` and `health_check()` find a logout Telethon's `get_me()` hides, and say why

Engine methods are replaced by stand-ins, and Telethon's real request code runs on a scripted connection.

### 12. **test_17_session_store.py**
Tests pluggable session storage (`python -m tgdata.smoke_tests.test_17_session_store`),
entirely offline with synthetic credentials and Telethon 1.45.0:
- file sessions remain the default; a supplied store serves persistent, pooled,
  and short-lived clients without creating `.session` files
- login keys, data centres, update states, and cached groups survive a restart;
  message senders are excluded and large access hashes remain exact
- disconnect and auth-key changes save; unchanged state is not written again
- load failures raise, save/delete failures are logged without credentials,
  and first-login rules still hold
- real Telethon log-out calls the optional delete method; stale clients cannot
  overwrite or delete a login already changed in the store, including when the
  current record cannot be read; mixed cache rows serialize
  deterministically; session copies stay in memory; health events keep their names

Socket connections are blocked by the test. Telegram replies and login prompts
are supplied by stand-ins; this does not verify a live login.

### 13. **test_18_read_budget.py**
Tests per-account read budgets (`python -m tgdata.smoke_tests.test_18_read_budget`),
entirely offline with synthetic credentials, temporary SQLite files and a
controlled clock:
- persistent policy, warm-up, rolling expiry, clock rollback, refunds and
  conservative failed/cancelled claims
- independent managers and four processes cannot spend the same allowance
- fresh authenticated identity, request-resolution delays, hidden retries,
  forward/reverse pages and resumed ID chunks through real Telethon code
- bounded request families, invoke wrappers, metadata batches, unsupported
  requests, oversized replies and storage failures
- partial fetch/search/media/discovery output, polling delivery and terminal
  stopping, local errors without invented account-health verdicts
- primary, pooled and short-lived clients share the guard; omitted budgets
  preserve existing behavior

The suite blocks socket connections. Scripted senders replace Telegram replies,
not the budget adapter or SDK request/iterator flow. Verified on Telethon 1.45.0
and 1.33.1; it does not establish live Telegram behavior or safe numeric quotas.

### 14. **test_19_message_batches.py**
Tests stable versioned batches (`python -m tgdata.smoke_tests.test_19_message_batches`),
entirely offline on **Telethon 1.45.0**, with synthetic credentials and real
temporary files:
- fixed golden JSON/hash, exact large IDs, UTC dates, nulls, senderless/service
  records and no sender enrichment
- immutable values, strict schema/hash validation, complete manifest save/reload
  and a receiver stand-in demonstrating replay after a lost acknowledgment
- bounded oldest-first reads, explicit groups, cursor limits, empty/end results,
  real read-budget exhaustion/resume and original exceptions with raw partials
- real SDK photo/document downloads, digest filenames, equal-content reuse,
  changed bytes, corrupt/symlink destinations, missing/truncated files,
  concurrent publication and cancellation cleanup
- implicit media-reference refreshes remain subject to the budget; local errors
  do not invent account-health verdicts; legacy DataFrame/media contracts remain
- native local I/O errors under incidental RPC context, including SDK stream
  writes/flushes, preserve their identity without false health events; actual
  transport causes still report correctly
- permission-denied cleanup, close/read double failures, cancellation,
  cleanup-only failures and raising logging handlers preserve the chosen error;
  secondary warning content is limited to operation/type

Socket connections are blocked. Scripted transport supplies Telegram replies;
the actual SDK iterator, downloader, budget guard and batch implementation run.
This does not establish live server behavior or a deployed receiver's guarantees.

### 15. **test_22_daily_continuation.py**

Tests durable daily continuation (`python -m tgdata.smoke_tests.test_22_daily_continuation`),
offline on Telethon **1.45.0**, with real SQLite, process exits and synthetic transport:
- explicit enrollment, immutable status, initial-position protection and exact group binding
- pending batches survive restart, replay without a client, and advance only on acknowledgment
- repeated/stale acknowledgments, storage conflicts, invalid/corrupt/missing state and schema
- real read-budget prefixes, original read errors, failed prefix persistence and cancellation
- enforced request overlap, source/mode mismatch and local operations without false health recovery
- actual downloaded media replay from another root and missing/corrupt/symlink refusal
- actual process termination before/after acknowledgment commit, lost receiver replies,
  SQLite cleanup precedence and an offline destination example

The example receiver demonstrates transactional duplicate handling; it does not verify
the deployed ScrapeOps destination. No Telegram sockets or real account configs are used.

### 16. **test_23_fixed_windows.py**

Tests fixed historical windows (`python -m tgdata.smoke_tests.test_23_fixed_windows`),
offline on Telethon **1.45.0** with the actual SDK, budget adapter and SQLite:
- UTC normalization, inclusive start/exclusive end, date seek and message-ID resume
- shared timestamps across pages/batches, full excluded pages, fractional boundaries
- media filtering, empty/end/limit results, real budget prefixes and read failures
- relative dates frozen across restart, repeat/conflicting initialization, uncertain commits
- exact pending replay and process exits during acknowledgment, independent daily/history stores
- unchanged v1 daily records and rejection of corrupt windows or out-of-window pending data

Synthetic transport supplies server replies; sockets are blocked and no real config
or Telegram account is used. No live server-selection or deployed receiver claim.

### Custom Test Scripts:
- **my_test.py** - Custom test script for specific scenarios

## Important Notes

1. **Authentication Required**: Live tests require valid Telegram credentials in `config.ini`.
   The offline login, flood-threshold, health-event, session-store, read-budget and message-batch suites use
   synthetic credentials. Proxy and device-identity suites also contain live checks.

2. **Non-Destructive**: Tests only read data, they don't send messages or modify groups

3. **Rate Limits**: Tests respect Telegram's rate limits with appropriate delays

4. **Real Data**: Tests work with your actual Telegram groups, so results vary based on your account

## Configuration

Create a `config.ini` file in the project root:

```ini
[Telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_file = YOUR_USERNAME
phone = YOUR_PHONE_NUMBER
```

## Expected Results

Each test will show:
- ✓ for passed tests
- ✗ for failed tests
- Test-specific output (message counts, group names, etc.)

Tests are designed to be informative, showing real data from your Telegram account while validating the library's functionality.

### Test 24: backfill state (Stage 2, offline)

```bash
python -m tgdata.smoke_tests.test_24_backfill_state
```

Exercises immutable creation/reference/status values, strict lifecycle snapshots,
SQLite start/reopen/CAS and actual before/after-commit process exits. Unknown retries,
stale predecessors, malformed state, uncertain results, local-error privacy and legacy
state isolation are covered. Existing-only store reopening and conservative sub-microsecond
pacing representation are included. No Telegram/config/login is used. Snapshot fixtures
for later lifecycle facts do not test their unimplemented transitions; no live gate passes.

### Test 25: backfill delivery (Stage 3, offline)

```bash
python -m tgdata.smoke_tests.test_25_backfill_delivery
```

Exercises durable source admission, exact restart/replay, complete delivery references,
atomic acknowledgment, preserved failure prefixes and cancellation. Real SQLite
process exits surround publication/ack commits; a real receiver transaction exercises
a lost acceptance reply. The actual SDK iterator, budget and artifact paths use
synthetic transport. Media relocation/corruption/removal, control-state preservation,
equal hashes across runs, counter/clock edges and local health isolation are covered.
No account/login/network is used. Future control/recovery snapshots are labeled fixtures;
positive timing eligibility and the next live gate remain their later stages.


### Test 26: backfill completion (Stage 4, offline)

```bash
python -m tgdata.smoke_tests.test_26_backfill_completion
```

Exercises empty/final completion, declared fresh/imported scope, failed full-batch
follow-up and confirmed ambiguous writes. The real SQLite matrix includes exceptions
and malformed replies before/after commit, absent/old/newer/corrupt/unreadable read-back,
no-send admission uncertainty, cancellation and original source-prefix exceptions.
Owned processes exit immediately before/after actual create/publication/empty-completion/
final-ack commits. Reopen checks owed work, unresolved attempts and durable completion.
Sockets are blocked; source replies are synthetic through Telethon 1.45.0. Seeded
operator states test preservation only; live Gate B is a separate required execution.


### Test 27: backfill pacing and recovery (Stage 5, offline)

```bash
python -m tgdata.smoke_tests.test_27_backfill_pacing
```

Exercises positive/zero/sub-microsecond pacing, independent UTC/monotonic evidence,
early/late acknowledgment, restart and nonblocking waits. Actual recovery methods
check quiescence and exact run/attempt/command/control identity, preserve known ends
or create one conservative unknown-end interval, and recognize lost replies without
refreshing it. Real SQLite process exits surround recovery commits; concurrent recovery,
newer attempts, wrong/stale context, clock failures and original error provenance are
covered. Actual SDK/budget code uses synthetic transport to verify prefixes, indefinite/
expired hints, account changes and retained cancelled charges. Sockets are blocked.
A short real elapsed-time case is local evidence; it does not pass live Gate C.
