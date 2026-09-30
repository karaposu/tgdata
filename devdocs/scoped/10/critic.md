---
model: claude-fable-5-1
effort: max
---

# Critique — Issue 10, group discovery in tgdata

Plan: `step_by_step_impl_plan.md` · Desc: `desc.md` · Prompt: `dynamic_critic_prompt.md` · Date: 2026-09-30

## Verdict: REORDER — TEST BEFORE BUILD

**Status 2026-09-30, later the same day: the experiment was run and PASSED** (result block below). The plan proceeds as critiqued — treat this as **IMPLEMENT AFTER FOLDING THESE IN**: fold the `selected` proposals of risks 1, 2, 3 and 5 into the plan; risk 4 is downgraded by the observation.

```
Falsifier: from the configured account, through tgdata's own persistent session, send one
           global search for a title known to exist, one recommendations request for a
           channel the account follows, then get_messages(limit=1) by BARE id on a returned
           room the account is NOT a member of. Search returning no chats for a known title,
           or that fetch raising GroupAccessError / ValueError, flips this to DO NOT
           IMPLEMENT: the row contract (step 2) and the engine (step 4) would be rebuilt
           around retained entities or an AccessHash column, not adjusted.
Affordable now: yes — about five read-only requests, under one minute, from the account
           already configured in config.ini. Needs the user's OK to use their personal
           account, which is the same consent step 6 already waits for.
```

```
Experiment: run devdocs/scoped/10/probe_discovery.py from the repo root with .venv/bin/python.
            It opens TgData("config.ini"), picks a broadcast channel the account follows,
            asks Telegram for its recommendations (up to three seeds), runs one global search
            for that channel's own title, prints for every returned room its type, min flag,
            whether an access hash came back, and participants_count, then fetches one
            message by bare id from a returned room the account is NOT in, through the
            normal fetch path, and reports whether a dialog sync was needed.
Cost:       ≈5 requests, read-only, under one minute; the user's personal account.
Must precede: step 4 — the engine. (Steps 1–3 are cheap and premise-free; they may proceed.)
Disqualifying result: the search returns zero chats for a title that exists, OR the
            non-member fetch by bare id fails (GroupAccessError, ValueError, or the log
            shows "syncing dialogs" followed by failure). Either means discovered rooms are
            not usable by id, and steps 2, 4, 5 and 7 are rewritten around a different row
            contract.
Passing result: at least one search hit; the non-member fetch returns a row with no dialog
            sync in the log; recommendations return a list for at least one seed — an
            EMPTY list with no error is not disqualifying, it downgrades similar_groups'
            documentation to "may return nothing on a non-Premium account" (a docs change).
            The probe also reports whether participants_count is present on results, which
            settles risk 4 below.
```

```
Experiment result (2026-09-30, account @karaposu via flatmir-scrapeops/scrapeOps/sessions/config.ini,
session propertybot_scrape, tgdata 0.0.7 source + Telethon 1.40.0; run beside the live
`scrapeOps.cli loop` on the same session file — no lock error, no prompt; exit 0):
  [0] authorized; the account has Telegram PREMIUM — so [1] is the Premium yield, and the
      "~10 per seed on a normal account" figure stays an unobserved claim in the docs.
  [1] GetChannelRecommendationsRequest(@turkey_insider) -> messages.Chats with 64 channels,
      every one non-min, with an access hash and a participants_count.
  [2] contacts.SearchRequest('Turkey Insider • Новости Турции') -> 1 chat (itself);
      SearchRequest('Анталия') -> 17 chats + 1 user: broadcast channels AND megagroups
      (broadcast=False, megagroup=True), all with participants_count.
  [3] 82 objects: 81 Channel, 0 Chat, 1 Forbidden (the skip rule in step 4 is needed),
      min=0, participants_count present on 81 of 81.
  [4] get_messages(group_id=1171979348, limit=1) on a NON-member room returned 1 row with
      no "syncing dialogs" line in the log: the cache premise (P1) holds in this composition.
Verdict on the experiment: PASSING. Nothing disqualifying was observed.
```

The plan is alive and may now be implemented. Nothing here is renamed; the plan is not edited by the critic. The mitigations below are ready for the plan to absorb.

## Preconditions (declared execution blockers, carried unchanged)

- **Live smoke test on a real account.** `search_groups` and `similar_groups` send global-search and recommendation requests from the configured personal account; a burst can earn that account a flood wait. The user runs the smoke test, or approves it being run, with the query count kept small. Blocks step 6 (running it; writing it is not blocked). Status: OPEN.
- **Releasing 0.0.8 to PyPI** is a GitHub release the user creates (`.github/workflows/python-publish.yml`). Blocks no step. Status: OPEN.

## High-level summary

The plan's shape is right: a fourth engine beside the message engine, the `list_groups` row contract reused, the two flood lessons from the finder turned into code, nothing existing touched. Its four documentary premises were genuinely closed by reading Telethon's source, and two more checked here hold as well (a `Channel` object passed between rounds costs no lookup; `Dialog.is_channel` matches the plan's parity claim). What it has not done is *observe* Telegram from this account through this composition before writing the engine that depends on it. Every vendor premise is tested at step 6, after step 4; a five-request probe settles them now, so the verdict is REORDER rather than the usual "fold these in".

Beyond the ordering, five findings need to be absorbed before step 4 is written:

1. **High — `discover_groups(mine_links=True)` has no budget.** It mines links from *every* room found and resolves every username by default. The finder capped both at 200 for a reason; a naive caller here would send thousands of the one request that earned that account 8- and 21-hour blocks. The codebase already has the convention for this (`DEFAULT_FETCH_LIMIT` plus a warning); the plan does not apply it.
2. **High — a dropped connection loses the whole run.** Only flood waits are survivable. A laptop lid closed forty minutes into a two-hour session block raises through and discards every row found. The finder lost 487 rooms exactly this way on 2026-09-08 and added a reconnect gate and checkpoints; the plan carries neither, and there is no way to receive rows as they are found.
3. **Medium — the resolution guard mutates the shared client.** The plan chose a per-call flood threshold precisely to avoid touching the persistent client's state, then sets `client.flood_sleep_threshold = 0` around every resolution. A real-time handler or a concurrent fetch on the same client that hits a wait inside that window raises instead of sleeping. A mutation-free version exists using the session cache and the same per-call path. Three other paths (`get_entity(peer)`, the dialog-sync fallback, `iter_messages`) still sleep silently up to 60 s, which the desc's "make the wait visible" rule forbids.
4. **Low after the experiment — `ParticipantsCount` is present on discovered rows.** The TL schema marks it optional and the finder fetches counts separately, so the critique expected an empty column; the probe observed the field on 81 of 81 objects from both search and recommendations. The parity promise stands. One sentence in the README ("present when Telegram includes it, which it did on every result observed") is all that remains; the opt-in below is not needed now.
5. **Medium — step 4 is under-specified for its hardness.** The internal signatures the four operations share, `ChatsSlice` handling, whether seeds are pre-seeded into the dedup set, the exact shape of an unresolved link row, and `_frame`'s dtypes on empty input are all left to the implementer — and each is a place where the code could quietly break a promise the README makes.

Trivia grouped under one Low item: dedup by bare id versus marked id, `t.me/boost/<name>` links dropped, private cross-engine coupling, the dependency floor forcing upgrades on consumers pinned below 1.33, seeds surfacing as their own "finds", and where the new exports go in `__init__.py`.

## Premise Inventory

Ranked by waste-if-false. Every premise below has the same cheapest earlier test — the probe named in the verdict — and every one is scheduled after its first dependent step, which is what makes the verdict REORDER. The rule is applied on P1; the others ride on the same experiment.

### P1 — A discovered room is fetchable by bare id through the normal fetch path, with no dialog sync
- **Premise:** rooms returned by `contacts.SearchRequest` and `channels.GetChannelRecommendationsRequest` are written into the SQLite session with a usable access hash, so `MessageEngine.fetch_messages(group_id=<bare id>)` resolves them without `_entity_after_dialog_sync` and without `GroupAccessError`.
- **First dependent step:** 2 — the row contract carries `GroupID` only, no access hash and no retained entity.
- **Waste if false:** steps 2, 4, 5 and 7 rewritten around an `AccessHash` column or retained entity objects — roughly the whole day of work the plan estimates.
- **Test scheduled at:** step 6, item 6 (the round-trip fetch), after the engine exists.
- **Cheapest earlier test:** the probe's final step — one `get_messages(limit=1)` by bare id on a returned room the account is not in. One request. Affordable now.
- **Coverage:** documentary only in this repo: `telethon/client/users.py` `_call` runs `session.process_entities(result)` (lines 83, 93), and `sessions/memory.py` stores only entities that are not `min` and carry a non-zero access hash (lines 106–113). The finder's `link_mine` calls `client.get_entity(row["id"])` on ids that came from search and it works in production — **covering for the mechanism on another account and another client configuration, not for this composition**. Nothing in this repo has ever run the calls.

### P2 — Global search returns rooms for name queries from this account
- **Premise:** `contacts.SearchRequest(q, limit)` returns `Channel`/`Chat` objects in `.chats` for queries that match a room's name or username.
- **First dependent step:** 4.
- **Waste if false:** most of steps 4–7 — search is two of the four methods and the whole point of the query helper.
- **Test scheduled at:** step 6, item 2.
- **Cheapest earlier test:** the probe's one search. One request.
- **Coverage:** the finder's production runs (682 and 1,287 queries per market) — covering for the vendor in general and account-independent; **non-covering for this composition** (per-call `flood_sleep_threshold=0` through `ConnectionEngine.session()`), which the probe supplies.

### P3 — Recommendations yield something on this account
- **Premise:** `channels.GetChannelRecommendationsRequest(channel=…)` returns "~10 per seed on a normal account, ~100 with Premium" (the plan's own hedge, lifted from the finder's docs).
- **First dependent step:** 4 (the `similar_groups` third of the engine).
- **Waste if false:** the similar-rounds code, its smoke test and its README paragraphs — about a third of step 4 and a slice of 6 and 7. Not a rewrite: the other two methods stand.
- **Test scheduled at:** step 6, item 3, which already concedes "a megagroup seed may legitimately return zero rows" — i.e. the test cannot fail.
- **Cheapest earlier test:** the probe's recommendations call on up to three broadcast-channel seeds. One to three requests.
- **Coverage:** the finder's Istanbul run "collected over 2,000 rooms from the similar-channels phase alone" from four seeds in two rounds — arithmetic that fits ~100 recommendations per seed far better than ~10, i.e. **a Premium account; non-covering for the account configured here.** An empty result on a non-Premium account is a documentation downgrade, not a disqualifier.

### P4 — `ParticipantsCount` carries a value on discovered rows
- **Premise:** implied, not stated: the README will promise "the `list_groups` columns", and in `list_groups` that column is usually populated because dialogs carry it.
- **First dependent step:** 7 (the promise) and, in meaning, 2 (the contract).
- **Waste if false:** small — a docs correction or the opt-in in risk 4. Listed because the plan tests columns for *presence*, never for *values*.
- **Test scheduled at:** never.
- **Cheapest earlier test:** the probe prints `participants_count` for every returned object. Zero extra requests.
- **Coverage:** none. `types.Channel.participants_count` is `Optional[int]` (flag 17) and the finder reads member counts from `GetFullChannelRequest`, never from search results — strong evidence the field is absent here.

### P5 — Every flood wait surfaces to the heartbeat
- **Premise:** sending raw requests with `flood_sleep_threshold=0` makes Telethon raise every `FloodWaitError` instead of sleeping silently.
- **First dependent step:** 4.
- **Waste if false:** the `_request` helper and the "waits obeyed exactly with heartbeat ticks" promise.
- **Test scheduled at:** never — step 6 cannot force a wait.
- **Cheapest earlier test:** none that is cheap; forcing a wait means abusing the account. Argued acceptable: the mechanism is fully visible in `users.py` `_call` (the per-call parameter at line 29–38, the raise-above-threshold at 121–123, and the pre-check that re-raises a remembered wait at 52–57 without sending). Documentary, CLOSED.
- **Coverage:** code reading only. Non-covering by nature; acceptable.

### P6 — A `Channel` object carried between rounds costs no lookup
- **Premise:** passing a `Channel` from a previous response as `channel=` to the recommendations request resolves locally.
- **First dependent step:** 4.
- **Waste if false:** round two would re-resolve every name — the exact behaviour that earned the finder's account its 21-hour block.
- **Test scheduled at:** never explicitly.
- **Cheapest earlier test:** confirmed by reading during this critique: the generated request's `resolve()` calls `client.get_input_entity(self.channel)`, and `get_input_entity` short-circuits any TL object through `utils.get_input_peer` (users.py lines 418–420) before touching the session or the network. CLOSED.
- **Coverage:** the finder does exactly this in production; documentary confirmation above.

**Rule applied:** P1–P4 each have a cheapest earlier test (the probe) that is affordable now and is scheduled after the first dependent step. Verdict: REORDER. P1 ranks first and defines the disqualifying result.

**After the experiment (2026-09-30):** P1 CLOSED — a non-member room fetched by bare id with no dialog sync. P2 CLOSED — 17 chats for one city-name query, channels and megagroups alike. P3 CLOSED for a Premium account (64 recommendations from one seed); the non-Premium yield remains unobserved and stays a hedge in the documentation, not a premise any step depends on. P4 CLOSED in the plan's favour — `participants_count` was present on 81 of 81 returned objects, so the parity promise holds as written. P5 and P6 unchanged (documentary).

## Restart Check

Not applicable. The plan exists to add a missing capability and remove duplication in a consumer; it does not cite a failure, incident or abandoned attempt as its reason for existing. The finder's incidents are lessons, handled below.

## Inherited Lessons

`desc.md` carries four numbered lessons from the finder's account blocks. One row each: the lesson, and the step in the plan's ordering that satisfies it.

| Lesson | Satisfied by | Assessment |
|---|---|---|
| 1. Username resolution is punished hardest; round two must reuse the objects round one returned, never look them up by name | Step 4 — `similar_groups` carries `next_layer` as objects; `_resolve` passes entities through untouched | Satisfied in the sequence, and P6 confirms it costs no lookup. |
| 2. Never sleep on a resolution; drop the threshold so Telethon raises, abandon the mined tail on the first wait | Step 4 — `_resolve` with the threshold at zero; link resolution stops on the first `FloodWaitError` | Satisfied in effect; the *mechanism* (mutating the shared client) is risk 3. And `discover_groups(resolve_links=True)` with unbounded mining (risk 1) invites exactly the request volume the lesson warns about, so the lesson is honoured per request and violated in aggregate. |
| 3. Obey a wait exactly, never retry early, and make it visible | Step 4 — `_request` sends with a per-call threshold of zero and sleeps in ten-second beating slices | Satisfied for the two raw requests. Not satisfied for `client.get_entity(peer)`, `get_dialogs()` in the dialog-sync fallback and `iter_messages` in link mining, which keep Telethon's silent 60-second sleep (risk 3). |
| 4. Results seed the session cache, so a later fetch by id needs no dialog sync | Relied on at step 2, tested at step 6 | Disclosed, not closed — this is P1 and the REORDER experiment. |

---

## Risk 1 — `discover_groups(mine_links=True)` has no budget: unbounded mining sources and username resolutions

**Risk**

*Plain.* The library is getting a "find me groups" feature that works in three stages: ask Telegram for channels similar to a few starting ones, run name searches, and then read the recent posts of every group found so far to collect links to yet more groups. That third stage has no ceiling. If the first two stages find two thousand groups, the third reads a hundred posts from each of the two thousand and then asks Telegram to look up every group name those posts link to, one lookup per name. Looking up a name is the single action Telegram rate-limits most harshly on personal accounts: the reference tool this feature is copied from got its account blocked from lookups for eight hours one day and twenty-one hours the next, at a few hundred lookups. Someone who switches the link stage on with the defaults, on a broad search, walks straight into that block without knowing it was possible.

*Precise.* In `step_by_step_impl_plan.md` step 4, *discover* mines "links from every room found so far with `resolve=resolve_links`", and step 5's facade sets `resolve_links: bool = True`. Neither `discover_groups` nor `linked_groups` takes a cap on the number of source rooms or on the number of `contacts.ResolveUsernameRequest` calls; the only stop is the first `FloodWaitError` in `_resolve`. With N rooms found, link mining costs N `iter_messages` requests (100 posts each) plus one resolution per new username — for the finder's Istanbul run that would have been 2,000+ mining requests and thousands of resolutions. The finder bounds exactly this with `LINKMINE_ROOMS_CAP = 200` and `LIST_MINED_CAP = 200` and mines only from rooms that passed its checks. tgdata's own convention for an open-ended walk is `DEFAULT_FETCH_LIMIT = 750` with a logged warning (`message_engine.py` lines 22–25, 329–335); the plan does not apply it here. Trigger: any `discover_groups(..., mine_links=True)` on more than a few dozen found rooms.

**Severity** — High
**Category** — Unbounded operation / Account safety
**Impact** — Multi-hour runs the caller did not intend; hundreds of resolution requests in one session; a flood block on username lookups lasting hours to a day, which also degrades every later `get_messages("@name")` on that account; `DiscoveryInterrupted` raised deep into a run.
**NoobEng** — Telegram's rate limits are per request type and cumulative. Search requests are cheap-ish; resolving a username to an id is the expensive one, and the penalty grows with volume rather than arriving at a fixed line. A discovery pipeline therefore needs a *budget* on resolutions as a first-class parameter, the way the fetch path has a message cap. `resolve=False` on the link stage costs nothing (it returns the usernames as text); resolution should be something the caller opts into, bounded.
**Affected areas** — `discovery_engine.discover_groups`, `linked_groups`; indirectly every later username-based call on the same account (`get_messages`, `search_messages`, `get_message_count` with an `@name`).

#### Mitigation — Quick
Keep `mine_links=False` as the default and add a docstring warning that mining and resolution are unbounded; leave the caps to the caller.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Apply the codebase's existing convention. Add `link_sources: int = 50` and `max_resolve: int = 100` to `discover_groups`, and `max_resolve: int = 100` to `linked_groups`; make `resolve_links` default `False` in `discover_groups` (usernames come back as text; the caller resolves the ones it keeps, or passes `resolve_links=True` knowingly). Mining sources are the first `link_sources` rooms in discovery order (similar first, so the seeds' neighbourhood is mined before search noise). When either cap truncates, log a WARNING in the exact voice of the 750-message warning ("stopped at the N-room link-mining bound; pass link_sources=… to mine more"). Count resolutions across the whole `discover_groups` call, not per method.
**Why this is robust:** a naive caller cannot send thousands of resolutions by accident; the caps are explicit integers with a logged reason, which is how tgdata already handles open-ended walks; the finder's proven numbers (200/200) become defaults a consumer can lift.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Class check: the only other bounded walk today is `fetch_messages`' `DEFAULT_FETCH_LIMIT`, and one shared budget across the two would be fake reach — fetch counts messages, discovery counts rooms and resolutions, with no common unit. Robust reuses the existing convention inside the one new file: highest reach per unit of extent.
*For future:* —

#### Mitigation — Long-term
A `RequestBudget` object (max requests, max resolutions, max wall-clock) passed through every paced operation — `search_groups`, `similar_groups`, `linked_groups`, `discover_groups`, and later the per-room measurement calls of the planned `get_group_stats` — that stops cleanly with partial results and reports what it spent. **This is better in the future context only:** once measurement lands (one `GetFullChannelRequest` per room, the finder's `measure()`), a single budget across discovery *and* measurement is what a consumer actually needs; today it would be one caller's parameter object for four methods.
**Why this is long term effective:** every future paced request stream inherits one budget semantics instead of each method growing its own cap parameters.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* The right shape once measurement lands (`get_group_stats`, one full-channel request per room) and discovery and measurement share one account's rate-limit headroom. Revisit in that issue; the caps above survive it as the budget's defaults.

---

## Risk 2 — A dropped connection loses the whole run; nothing survives except flood waits

**Risk**

*Plain.* A full discovery run sends well over a thousand requests, two seconds apart, for an hour or two, on a laptop. The plan protects the run against one thing: Telegram telling it to wait, in which case it waits and carries on, or gives up while handing back everything found so far. It does not protect against the connection dropping — the lid closing, Wi-Fi changing, the socket timing out — which is the far more common way a two-hour laptop job dies. In that case the error passes straight through and every group found in the last hour is discarded; the caller gets an exception and an empty hand. The tool this feature is copied from lost 487 measured rooms exactly this way and then grew a reconnect gate and a save-every-100-rooms checkpoint; the plan carries neither and offers no way to receive results as they arrive.

*Precise.* `DiscoveryEngine._request` (plan step 4) catches only `FloodWaitError`. `ConnectionError`, `OSError`, `asyncio.TimeoutError` and `asyncio.IncompleteReadError` — Telethon's transport failures, which `find_rooms.py` enumerates as `NET_ERRORS` — propagate out of `discover_groups`, and the `rows` list accumulated inside `async with self.connection_engine.session()` is lost. `ConnectionEngine._ensure_connected` runs only in `get_client()`, i.e. when `session()` is entered, never mid-block, and the persistent client is built with Telethon's default `connection_retries=5`, after which it stops reconnecting on its own. `MessageEngine.fetch_messages` has the same exposure (`message_engine.py` lines 367–369: `except Exception: raise`), mitigated there only for callers that pass `batch_callback`; discovery offers no streaming callback at all. Trigger: any transport failure during a long `discover_groups`, most likely a sleeping laptop.

**Severity** — High
**Category** — Resilience / Data loss
**Impact** — An hour or more of paced requests wasted and repeated on the next run (re-spending the account's rate-limit headroom); a caller that has to wrap the whole call in its own checkpointing to be safe, which is the duplication the feature exists to remove.
**NoobEng** — The persistent client here is a long-lived asyncio socket. Telethon reconnects a fixed number of times on its own and then raises on the next request. Nothing in the library resumes a *logical* operation across that gap: the message engine resumes across flood waits by remembering the last message id, but a network error is re-raised. Discovery is idempotent per request (a query can simply be re-sent), so "wait until `get_me()` works again, then retry the same request" is both safe and cheap — and the finder already wrote that loop (`wait_for_network`).
**Affected areas** — `discovery_engine` (all four operations); the same class of exposure exists in `message_engine.fetch_messages` for callers without `batch_callback`.

#### Mitigation — Quick
Wrap the body of `discover_groups` in `try/except Exception` and re-raise as `DiscoveryInterrupted(found=<partial frame>, retry_after=0)`, so at least nothing found is lost. No reconnect, no retry.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
In the engine: catch `NET_ERRORS = (ConnectionError, OSError, asyncio.TimeoutError, asyncio.IncompleteReadError)` inside `_request` and around the `iter_messages` loop; on one, enter a beating wait loop — every 30 s try `client.connect()` if not connected, then `client.get_me()`; beat `"reconnecting <n>min"`; give up after a `max_offline` parameter (default the same 3600 s as `max_flood_wait`) by raising `DiscoveryInterrupted` with `.found` — then retry the *same* request, which is idempotent. Add `found_callback: Optional[Callable[[dict], Awaitable | None]]` to the four methods, invoked once per new room as it is discovered, mirroring `batch_callback`, so a caller can persist as it goes and a lost run costs nothing.
**Why this is robust:** it is the finder's `wait_for_network` — the fix that ended the 2026-09-08 loss — placed where the requests are made; every failure mode ends either in a resumed run or in an exception that still carries the rows; the callback removes the all-or-nothing shape entirely.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* A class exists (`fetch_messages` carries the same exposure), but the size and delicacy gates decide: the class fix edits fetch's resume loop, which `scoped/9` is about to rework, and cannot be verified without the network. Smallest change that closes the instance now, and the callback removes the all-or-nothing shape. Robust survives the later class fix — its loop would simply call the shared method.
*For future:* —

#### Mitigation — Long-term
A `ConnectionEngine.wait_until_connected(heartbeat=None, max_offline=…)` method — the beating reconnect loop in the one place that owns the client — used by both engines, and `NET_ERRORS` handling added to `fetch_messages`'s retry loop so a long fetch resumes from `last_seen_id` after a drop the same way it resumes after a flood wait. **Better in the future context only:** `scoped/9` is about to touch that very loop (heartbeat coverage), and doing both edits in one pass avoids reworking the resume logic twice.
**Why this is long term effective:** transport recovery becomes one policy for every long operation the library will ever run — fetch, discovery, and the planned measurement — instead of each engine carrying its own loop.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Do it together with `scoped/9`'s work on `fetch_messages`' retry loop: add `NET_ERRORS` handling there, lift the reconnect wait into `ConnectionEngine.wait_until_connected`, then point the discovery engine at it. Future improvement, not a prerequisite — the robust loop above is not thrown away by it.

---

## Risk 3 — The resolution guard mutates the shared client, and three paths still sleep silently

**Risk**

*Plain.* The library keeps one long-lived connection to Telegram that everything shares: fetching messages, listening for new messages in real time, polling, and now discovery. Telegram sometimes answers a request with "wait N seconds"; the connection has a setting that decides whether to sleep through short waits quietly or to raise an error. Discovery needs that setting at "raise immediately" for one particular request type, so it flips the shared setting to zero, makes the request, and flips it back. During that window, anything *else* using the same connection — a real-time handler reacting to a new message, another task fetching history — that happens to hit a wait now gets an error instead of a quiet pause, and that error is the one the plan itself said it wanted to avoid by using a per-request setting. Separately, three of discovery's own steps still use the quiet-pause behaviour, so a wait there is invisible to the caller's watchdog, contradicting the design rule that every wait must be seen.

*Precise.* Plan step 4, `_resolve`: `old = client.flood_sleep_threshold; client.flood_sleep_threshold = 0; … finally: client.flood_sleep_threshold = old` around `client.get_input_entity(ref)`. The client is `ConnectionEngine._primary_client`, shared by `TgData.run_with_event_loop` handlers (`events.NewMessage` → `event.get_sender()` etc.), `poll_for_messages`, and any concurrent `get_messages` task; `users.py` `_call` reads `self.flood_sleep_threshold` at line 37–38 for every request without a per-call value, so a wait raised for *their* request during the window propagates as `FloodWaitError` where they expected a sleep. The plan's own step 4 justified the per-call parameter as avoiding exactly this race. Meanwhile `client.get_entity(peer)` (the `GetChannelsRequest` after resolution), `client.get_dialogs()` inside `MessageEngine._entity_after_dialog_sync`, and `client.iter_messages` in link mining all run with the default threshold (60 s), so a wait of up to a minute is slept with no `beat` — the desc's "make the wait visible" rule (lesson 3) is violated on those paths. Trigger for the race: discovery and any other consumer of the client active at the same instant; for the silent sleeps: any flood wait ≤ 60 s on those three request types.

**Severity** — Medium
**Category** — Concurrency / Shared state / Observability
**Impact** — Unhandled `FloodWaitError` inside a user's real-time handler (swallowed and logged by `_register_pending_handlers`' safe wrapper, so the event is lost) or inside a concurrent fetch (which then counts it as a flood interruption against `MAX_FLOOD_RETRIES`); silent one-minute stalls that a heartbeat watchdog reads as a hang.
**NoobEng** — Telethon has a client-wide `flood_sleep_threshold` and a per-call override on `client(request, flood_sleep_threshold=…)`, but the convenience wrappers (`get_input_entity`, `get_entity`, `iter_messages`) only use the client-wide one. The clean way to get "raise immediately" for a resolution without touching shared state is to bypass the wrapper: read the session cache directly (`client.session.get_input_entity(name)`, which is pure and raises `ValueError` on a miss), and on a miss send `contacts.ResolveUsernameRequest` / `channels.GetChannelsRequest` yourself through the per-call path.
**Affected areas** — `discovery_engine._resolve`; `TgData.on_new_message` handlers and `poll_for_messages` when run concurrently with discovery; the visibility promise for `get_entity`, dialog sync and link mining.

#### Mitigation — Quick
Keep the mutation; document that discovery must not run concurrently with real-time handlers or other fetches on the same `TgData`.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Rewrite `_resolve` with no shared-state mutation: (1) entities pass through; (2) `client.session.get_input_entity(ref)` for the cache (`ValueError` = miss); (3) on a miss with a string, `await client(functions.contacts.ResolveUsernameRequest(username=name), flood_sleep_threshold=0)` — sent directly, *not* through the waiting `_request`, so a `FloodWaitError` propagates unslept for the caller to skip or stop on — and take the matching object from `.chats`; (4) on a miss with an int, the dialog-sync fallback as planned; (5) the full entity from an `InputPeer` via `_request(client, functions.channels.GetChannelsRequest([input_channel]))` (or `messages.GetChatsRequest` for a basic group) so that wait, too, beats. Leave `iter_messages` on the default threshold but note it in the docstring (a paged history read cannot take a per-call threshold; waits there are ≤ 60 s and rare).
**Why this is robust:** no shared state is touched, so concurrent users of the client are unaffected; every resolution wait raises immediately as lesson 2 requires; every other wait discovery causes goes through the beating path.
- [x] selected   - [ ] elegant   - [x] last_resort

**Note**
*Why chosen:* Taken as the lesser fix. The long-term proposal wins on reach per extent — five resolution sites, three of which lack the dialog-sync fallback today — but the size gate routes it out: it edits `message_engine.py`, which this plan was not going to touch. Robust closes the race and the silent sleeps inside the new file only, and survives the later move: the resolver body becomes the shared helper.
*For future:* —

#### Mitigation — Long-term
One `ConnectionEngine.resolve_entity(client, ref, *, sleep_on_flood: bool, heartbeat=None)` — cache-first, dialog-sync fallback, per-call threshold — used by both engines, and the four ad-hoc `client.get_entity(group_id)` sites in `message_engine.py` (`fetch_messages`, `get_message_count`, `search_messages`, `download_media_by_id`) migrated to it. That also gives the three methods that today lack the dialog-sync fallback the same `GroupAccessError` semantics as `fetch_messages`, and removes the plan's private cross-engine call to `MessageEngine._entity_after_dialog_sync`. Grows the plan beyond its files; belongs in its own issue.
**Why this is long term effective:** entity resolution becomes one policy with one home; the next engine (measurement) cannot reinvent it wrongly.
- [ ] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* The better answer — one `resolve_entity` on `ConnectionEngine` used by both engines. Blocked by scope, not by access: file it as the next scoped issue ("entity resolution home"). It also fixes `get_message_count`, `search_messages` and `download_media_by_id` surfacing Telethon's raw "could not find the input entity" on fresh sessions instead of `GroupAccessError`.

---

## Risk 4 — `ParticipantsCount` will probably be empty on discovered rows, and the README will promise parity

**Risk**

*Plain.* The feature returns each found group as a row with the same columns the library already uses when it lists the groups you belong to, including a member count. But Telegram only includes a member count in some replies; the lightweight group objects that a search or a recommendation returns very likely do not carry one, while the "your own groups" listing does. So the column will exist and be empty for nearly every discovered group. Anyone who reads the documentation's "same columns as the group list", then filters candidates by size, will filter everything out and not know why. The tool this is copied from fetches the count separately, one extra request per group, because it had to.

*Precise.* `types.Channel.participants_count` is `Optional[int]` (flag 17, present "in certain contexts"); `contacts.Found.chats` and `messages.Chats` from the recommendations call carry the compact `Channel` constructor, and `find_rooms.measure()` reads `subs = full.full_chat.participants_count` from `GetFullChannelRequest` — never from search results. Plan step 2's `from_entity` uses `getattr(entity, 'participants_count', None)`, step 6 asserts only that the column exists, and step 7 promises "the `list_groups` columns". Trigger: any consumer filtering `search_groups`/`similar_groups` output on `ParticipantsCount`.

**Severity** — Low (downgraded 2026-09-30: the experiment observed `participants_count` on 81 of 81 objects returned by search and recommendations; written before the run as Medium)
**Category** — API contract / Documentation
**Impact** — Misleading empty column; consumers reimplement the per-room count fetch (the duplication the feature exists to remove); a README promise that is false on day one.
**NoobEng** — In MTProto, "chat" objects come in a compact form (id, title, flags) and a "full" form (about text, counts, online count) that costs a separate request per room. Search and recommendation results are compact. A member count therefore either costs one request per row, or is honestly documented as absent. The probe in the verdict prints the field for every result and settles which.
**Affected areas** — `GroupInfo.from_entity`, the README section, any size-based filtering by consumers.

#### Mitigation — Quick
Document in the four docstrings and the README that `ParticipantsCount` is present only when Telegram includes it in the search result, and is usually empty.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Add `with_counts: bool = False` to the four methods. When true, for each `Channel` row one paced `channels.GetFullChannelRequest` (basic groups: `messages.GetFullChatRequest`) through `_request`, filling `ParticipantsCount` from `full_chat.participants_count`, counted against the caps of risk 1; README states the cost plainly ("one extra request per room"). Default stays cheap and the column's meaning matches `list_groups` whenever it is filled.
**Why this is robust:** the contract becomes true on demand rather than by accident, at a cost the caller chose; the empty default is documented instead of surprising.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* — (was selected before the run; unselected 2026-09-30 because the experiment observed the field present on every result, so the promise is true without it)
*For future:* Keep in reserve if a consumer ever reports the column empty for some result type; the twenty-line opt-in is ready to add then.

#### Mitigation — Long-term
Counts belong to the planned measurement feature (`get_group_stats`: subscribers, online now, 7-day average views, writers per day — the finder's `measure()`), where the full-channel request is fetched once and every derived number comes with it. **Better in that future context only**; `with_counts` would then be a thin convenience over it or be retired.
**Why this is long term effective:** one full-channel read per room serves every metric instead of each feature paying for its own.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* When `get_group_stats` lands, counts come from the same full-channel read as views and online-now; keep `with_counts` as a thin wrapper over it, or retire it then.

---

## Risk 5 — Step 4 leaves the mechanisms that carry the README's promises to the implementer's judgement

**Risk**

*Plain.* The plan's central step is described with two carefully written helpers and prose for the four operations that use them. The prose is right as far as it goes, but several details it leaves open are exactly the ones on which the documentation's promises rest: how the four operations share their bookkeeping when chained, how a "there is more" reply from Telegram is handled, whether a starting channel can come back as its own "find", what a row looks like when a linked group's name could not be turned into an id, and what the table looks like when nothing was found. Each of these is a place where a reasonable implementer could make a choice that quietly breaks a promise — a duplicate row, a crash on an empty run, a seed listed as discovered.

*Precise.* Plan step 4 does not specify: (a) the internal signatures `discover_groups` chains — the prose says "each is a coroutine taking `(client, ...)`" and that `seen`/`rows` "travel through every method", without naming the parameter or object; (b) that both `messages.Chats` and `messages.ChatsSlice` expose `.chats` (it says "works for both" without saying how); (c) whether seed keys are pre-added to `seen`, so a seed recommended by another seed is not returned as found via `similar`; (d) the exact unresolved-link row — which columns are `None`/`NA` (`GroupID`, `IsChannel`, `IsMegagroup`, `ParticipantsCount`) and that `Identifier` is the `@name`; (e) `_frame` on empty input — `pd.DataFrame(columns=COLUMNS)` with `GroupID` cast to `Int64` and the two boolean columns to nullable `boolean` so a frame with unresolved rows keeps consistent dtypes; (f) which exceptions each operation swallows per item (`FloodWaitError`, `ValueError`, `TypeError` on a non-channel seed) versus propagates. Hardness is rated 4; the missing pieces are the ones an implementer cannot infer from the message engine, which has no equivalent.

**Severity** — Medium
**Category** — Plan detail / Phase ordering
**Impact** — Divergent implementation choices that break the contract promised in step 7 (duplicates, seeds returned as finds, dtype drift between resolved and unresolved rows, an empty result that lacks columns and crashes the smoke test's assertions).
**NoobEng** — When four operations share mutable bookkeeping and a facade chains them, the shape of that shared state is the design. Writing it down (a tiny `_State` with `seen`, `rows`, `beat`, `pace`, `max_flood_wait`, counters) is a few lines in the plan and saves a round of rework.
**Affected areas** — `discovery_engine` (all operations), the smoke test's assertions, the README's contract.

#### Mitigation — Quick
Implement and let the code become the specification; fix divergences when the smoke test finds them.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust
Extend step 4 before coding with: the `_State` object and the internal signatures `_search(client, st, query, limit)`, `_similar(client, st, seeds, rounds)`, `_links(client, st, sources, posts, resolve)`; `.chats` on both `Chats` and `ChatsSlice`; seeds pre-added to `st.seen`; the unresolved-row contract (`GroupID`, `IsChannel`, `IsMegagroup`, `ParticipantsCount` = `pd.NA`; `Username`/`Identifier` = `@name`; `FoundVia='link'`); `_frame` rules (`columns=COLUMNS` always, `GroupID` → `Int64`, `IsChannel`/`IsMegagroup` → `boolean`); and the per-item exception table (swallow-and-log: `FloodWaitError` on a seed, `ValueError` on an unknown seed, `TypeError` on a basic-group seed; propagate: everything else). Add to step 6 an assertion on the empty case (`search_groups("zzqqxx_no_such_room_123")` returns a frame with all `COLUMNS` and zero rows).
**Why this is robust:** the six ambiguities are named and closed where they live, in the plan, before they can diverge; the empty-case assertion makes the dtype rules testable without the network.
- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* No class — long-term collapses into robust, as the proposal itself says. Closing six named ambiguities in the plan text costs a paragraph and prevents a rework cycle; the empty-case assertion is the one network-free test the plan can have.
*For future:* —

#### Mitigation — Long-term
No genuine class: the message engine is a single long routine and has no equivalent shared-state design to generalise. Long-term collapses into robust.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

---

## Risk 6 — Low items, grouped

None of these changes the verdict or needs mitigation tiers; each is one line to absorb.

- **Dedup key by bare id.** Telegram's user, chat and channel id spaces can overlap numerically; tgdata's session lookup by bare int already tries the marked variants (`sqlite.py` `get_entity_rows_by_id(exact=False)`). Use `telethon.utils.get_peer_id(entity)` (the marked id) as the dedup key while keeping `GroupID` bare for parity with `list_groups`. Category: Data integrity. Affected: `_key`.
- **`t.me/boost/<name>` drops the real target.** The reserved-path filter removes "boost", but the channel is the *second* segment. Special-case `boost/<name>` (and `s/<name>`, already handled) to take the second segment. `tg://resolve?domain=` and `t.me/<name>?start=` are handled or harmless. Category: Coverage. Affected: `TME_LINK`, link mining.
- **Private cross-engine call.** `MessageEngine._entity_after_dialog_sync` is a private static method; calling it from another engine is the coupling risk 3's long-term fix removes. Until then, rename it to a module-level function in `message_engine.py` without the underscore, or accept the coupling with a comment. Category: Layering.
- **Dependency floor.** `Telethon>=1.33` forces an upgrade on any consumer pinned to 1.24–1.32. There is no known such consumer (the finder runs 1.40) — note it in the 0.0.8 changelog line. Category: Compatibility.
- **Seeds as finds.** Without pre-seeding `seen`, a seed recommended by another seed is returned as `FoundVia='similar'`. Covered by risk 5's robust fix. Category: Contract.
- **Export placement.** `__init__.py` ends with a post-`__all__` import of `AuthRequiredError` (`# noqa: E402`). Put the two new exports in the main import block and `__all__`, and fold the trailing import up while there. Category: Package hygiene.
- **Smoke test resolution cost.** Step 6 item 4 resolves three mined usernames — three of the punished request; fine, but say so in the test's banner so a reader does not scale it up.
