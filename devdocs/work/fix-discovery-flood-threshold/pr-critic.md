---
model: claude-opus-5-5[1m]
effort: max
---

**Verdict: IMPLEMENT AS WRITTEN**

Falsifier: a real Telegram flood wait of 60 s or less, through a client built by `_new_client()` with `flood_sleep_threshold=0`, that Telethon still sleeps through instead of raising.
Affordable now: no — provoking a real wait spends an account's limits; a natural one is unpredictable. Every offline equivalent has been run and passes: `test_14` 11/11, and probes P1–P7 below.

# PR critic — PR #11, `fix/discovery-flood-threshold` into `dev`

CONTRIBUTING.md §7.2. The subject is the implemented diff `dev...fix/discovery-flood-threshold` — code, tests and product docs; `devdocs/work/` is excluded — read together with `step_by_step_impl_plan.md`. It was judged against the codebase on Telethon 1.45.0.

It ran in the same AI session as the implementation, never in a subagent, which is the process §7.5 prescribes. Independence comes from the rules: the touched files were read in full, behaviour was probed, and the output is quoted below.

## High-level summary

**Result under §7.3: merges.** There are no High or Medium findings, and seven Lows are recorded and consciously left.

**What the code does, and that it does it:**
- **Telethon's per-request option now works on every tgdata client.** A request sent with `flood_sleep_threshold=0` raises a short flood wait instead of sleeping through it.
- **Everything else behaves exactly as before.** Probes confirm it under concurrency (40 mixed requests on one client), cancellation, `asyncio.wait_for`, and reads outside a loop.
- **Discovery handles all four of Telethon's wait errors** at its five catch sites. One is an improvement beyond the plan's target: a long premium wait while reading posts used to escape as a raw error, and now ends the run as `DiscoveryInterrupted` (P4).

**The Lows** are:
- an over-count in the lookup budget after a wait (P5);
- three documentation imprecisions;
- two test-hygiene points;
- one unlisted but in-scope docstring addition.

## Premise Inventory

**What was checked:**
- the plan's hedges and the desc's `[ASSUMPTION]`s;
- every behavioural claim the diff relies on;
- the merge-check's list of deviations.

**Confirmed by probe or test this pass, so not open:**
- the option raises on a factory-built client — `test_14` TEST 1;
- requests without it sleep as before — TEST 2;
- requests stay independent — TEST 3, and P1 at 40 concurrent requests;
- the value never sticks and never leaks into a task started mid-request — TEST 4;
- the pending-wait pre-check is honoured — TEST 5;
- per-request scope — TEST 6;
- every connection path builds the class — TEST 7;
- cancellation restores the value — P2;
- `wait_for` wrapping works — P3;
- the built class keeps Telethon's `ABCMeta` and puts the mixin first — P6;
- a read outside a loop returns the stored value — P7.

**Open premise:**
1. **Premise:** a mandated wait from live Telegram arrives as one of the four wait errors.
   - **First dependent step:** the whole diff.
   - **Waste if false:** the diff's purpose — Telethon's own flood handling would be wrong for every user.
   - **Test scheduled at:** never live.
   - **Cheapest earlier test:** none affordable; it needs an account throttled on purpose.
   - **Coverage:** **non-covering.** The scripted connection supplies the error. The premise rests on Telethon's verified error conversion and on real waits this project has observed through Telethon before.

**Rule check:** no affordable earlier test is scheduled after its first dependent step.

## Restart Check

| Observed failure | Established mechanism | Design element, and the evidence it is addressed |
|---|---|---|
| Discovery silent during waits of 60 s or less | `__call__` drops the option; `_call` reads the client-wide property | `_PerCallFloodThreshold`; TEST 8 beats `['search', 'flood-wait 2s', 'search']` |
| `max_flood_wait` below 60 s not honoured | same | TEST 9: `DiscoveryInterrupted(retry_after=2)` in 0.00 s with `max_flood_wait=1` |
| Lookup waits slept through | same | TEST 10: seed skipped in 0.00 s; `linked_groups` interrupted in 0.00 s. TEST 11 for premium waits |
| Docstrings said the opposite | consequence | every changed statement read against its code path — three imprecisions remain, all Low (Risks 2–4) |

## Inherited Lessons

- **Lesson:** username lookups escalate, so a lookup wait is never slept through and never retried early.
  - **Where the implementation satisfies it:** `_resolve` raises at once (TEST 10, TEST 11).
  - P5 shows the second seed's lookup is **refused by Telethon without being sent**, so a lookup wait costs Telegram no further lookups — the point of the lesson.

---

## Risk 1 — After a lookup wait, refused lookups are still counted as spent

### Risk

Discovery limits how many "who is @name?" lookups one call may spend, because Telegram punishes that request hardest, and it reports the number spent at the end. Once Telegram has asked for a wait on lookups, Telethon refuses the following lookups on the spot without contacting Telegram. Discovery still counts each refused one as spent.

So the report overstates what was actually sent. A long call can also run out of its lookup allowance early, on lookups that never left the machine. Before this change that happened only for waits over a minute; now it happens for short waits too.

**Precisely.** `DiscoveryEngine._resolve` increments `st.resolved` before sending `ResolveUsernameRequest`. With a wait already recorded in Telethon's `_flood_waited_requests`, `UserMethods._call`'s pre-check raises `FloodWaitError` without sending. The probe:

```
P5 after one lookup wait, the second seed is refused by Telethon without sending — but still counted as spent
   sent=['ResolveUsernameRequest']; log: 'discover_groups: 0 rooms (2 username resolutions spent of 100)'
```

### Severity

Low

### Category

Reporting accuracy

### Impact

- The summary log overstates lookups.
- `max_resolve` can be reached sooner by link resolution later in the same `discover_groups` call, but only if the lookup wait has expired by then.
- No extra request ever reaches Telegram.

### NoobEng

Count a lookup after it is sent, or skip counting when Telethon refused it locally. This tidy-up is independent of this PR.

### Affected areas

`DiscoveryEngine._resolve`; the `discover_groups` summary log line

---

## Risk 2 — A third discovery step still sleeps short waits silently

### Risk

The updated docs tell users that two discovery steps still let Telethon sleep short waits without a heartbeat tick: reading a room's recent posts, and refreshing the account's chat list to find a numeric id. A third step does the same: when the connection drops, discovery checks it is back by asking "who am I?". A short wait there is slept silently, and a long one is treated as "still offline" rather than as a wait.

So the docs undercount the silent paths by one. The swallowed long wait is older than this PR.

**Precisely.** `DiscoveryEngine._wait_for_network` calls `await client.get_me()` with no per-call threshold, inside `except Exception: # still down`. README ("Pacing and waits"), the guide's waits paragraph, the `TgData.search_groups` `max_flood_wait` docstring, `_resolve` and the module docstring all name only post reading and the dialog sync.

### Severity

Low

### Category

Documentation accuracy

### Impact

A watchdog author is not told that reconnection can be silent for up to a minute. It happens only after a dropped connection.

### NoobEng

The reconnect path is a fallback that rarely runs. Naming it, or passing the option there, is a one-line follow-up.

### Affected areas

discovery docs; `_wait_for_network`

---

## Risk 3 — The guide marks everything as verified live, and the new sentences were not

### Risk

The discovery guide opens by saying everything in it was verified live against a real account, unless marked otherwise. This PR adds sentences that were verified offline, by tests that run Telethon's real code, not live, and they are not marked. A reader trusts them as live-verified.

**Precisely.** `devdocs/guides/group_discovery.md` line 8 reads "Everything here was verified live on 2026-09-30 against a real personal account (Telethon 1.40, Premium) unless marked otherwise." The added "Two steps keep Telethon's own handling…" sentence and the §8 row change carry no mark.

### Severity

Low

### Category

Documentation accuracy

### Impact

It overstates how the new statements were verified. The statements themselves are true per code and tests.

### NoobEng

Add "(verified offline, 2026-10-03, Telethon 1.45.0)" to the two changes.

### Affected areas

`devdocs/guides/group_discovery.md`

---

## Risk 4 — Lookup wording sits in `search_groups`' docstring

### Risk

The help text for the plain search method now explains what happens to username lookups. Plain search never looks up a username; the other discovery methods borrow this text with "as in search_groups". It reads oddly for search alone.

**Precisely.** `tgdata/tgdata.py`, `TgData.search_groups`, `max_flood_wait`: "A wait on a username lookup is never slept: it skips the seed or stops resolving (for a linked_groups source it raises DiscoveryInterrupted)." This sentence is also the one addition the merge-check did not list. It is within Step 5's intent — make every statement exact — but it was not among Step 5's listed edits.

### Severity

Low

### Category

Documentation placement; unlisted deviation

### Impact

Cosmetic.

### NoobEng

Moving the sentence to `similar_groups`, `linked_groups` and `discover_groups` would read more naturally.

### Affected areas

`TgData` discovery docstrings

---

## Risk 5 — Discovery now writes WARNING lines for short waits

### Risk

When discovery waits, it writes a warning to the log. Before this change, short waits were slept inside Telethon and only appeared at the quieter INFO level, which most setups hide. Now every short wait in search, recommendations and lookups produces a visible warning line. That is intended — waits are meant to be visible — but people reading logs will see more warnings than before.

**Precisely.** `DiscoveryEngine._request` logs `FloodWait {e.seconds}s on {name} — waiting, then retrying` at WARNING. Lookup waits log `Seed … skipped …` or `Stopped resolving links …` at WARNING. Previously Telethon logged short sleeps at INFO on `telethon.client.users`.

### Severity

Low

### Category

Observable behaviour change

### Impact

More WARNING lines in discovery-heavy logs. No functional change.

### NoobEng

The heartbeat already carries the same information; the log level could be revisited if it proves noisy.

### Affected areas

consumers' logs

---

## Risk 6 — The new test leaves its temporary session files open

### Risk

The new offline test creates a throwaway session file per client and never closes them before deleting the temporary folder. On Windows, open files cannot be deleted, so the folder would be left behind; the deletion error is ignored. The test also prints an expected "Authentication failed" line from its stand-in client, which looks like a failure to a skimming reader.

**Precisely.** `test_14_flood_threshold.py` builds clients via `ENGINE._new_client(TMP/session_N)` (SQLite sessions) and ends with `shutil.rmtree(TMP, ignore_errors=True)` without `client.session.close()`. TEST 7's `get_client()` logs `Authentication failed: No phone number or bot token provided.`, which test_13 also does.

### Severity

Low

### Category

Test hygiene

### Impact

Leftover temp folders on Windows, and one misleading log line.

### NoobEng

Close each session in a `finally`, or use an in-memory session name for the factory in tests.

### Affected areas

`tgdata/smoke_tests/test_14_flood_threshold.py`

---

## Risk 7 — Carried from the planning critique, consciously left

These Lows from `critic.md` are unchanged by the implementation and remain left:
- no CI runs the canary test — Risk 6 there;
- `telethon.sync` callers lose the synchronous wrapper on tgdata clients — Risk 8;
- a non-class stand-in for `TelegramClient` breaks the factory — Risk 5;
- no release note yet — Risk 7;
- issue #4's notes go stale on merge — Risk 10.

### Severity

Low

### Category

Carried

### Impact

As stated in `critic.md`.

### NoobEng

Each has its follow-up named there.

### Affected areas

as stated in `critic.md`

---

## Phase 3 — mitigation selection

There are no Medium or High findings, so there are no mitigation tiers to select. The Lows above are recorded and consciously left, per §7.3.

## Appendix — probe output

`/private/tmp/…/probe_pr11.py`, run offline against Telethon 1.45.0's real request code:

```
[PASS] P1 40 concurrent requests on one client: option and no-option never cross
       with option: {'raised'}; without: {'State'}; took 1.0s
[PASS] P2 cancelled mid-request: the value is restored; the task's next plain request behaves normally
       {'var after cancel': None, 'next plain request': 'State', 'slept': 1.0}
[PASS] P3 wait_for wrapping (a new task on 3.11) still honours the option
       raised after 0.00s
[PASS] P4 post reading: a 120 s premium wait now ends the run as DiscoveryInterrupted (before: a raw error)
       DiscoveryInterrupted(retry_after=120); FloodPremiumWaitError is a FloodWaitError: False
[PASS] P5 after one lookup wait, the second seed is refused by Telethon without sending — but still counted as spent
       sent=['ResolveUsernameRequest']; log: 'discover_groups: 0 rooms (2 username resolutions spent of 100)'
[PASS] P6 metaclass and MRO of the built class
       TgdataTelegramClient, metaclass=ABCMeta, mro[1:3]=['_PerCallFloodThreshold', 'TelegramClient']
[PASS] P7 property read outside any event loop returns the stored value
       60
```
