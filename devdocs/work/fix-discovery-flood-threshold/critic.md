---
model: claude-opus-5-5[1m]
effort: max
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: a real Telegram flood wait of 60 s or less, sent through a client built by the patched `_new_client()` with `flood_sleep_threshold=0`, that Telethon still sleeps through instead of raising.
Affordable now: no — a real flood wait cannot be provoked without spending an account's request limits and risking a longer block, and a natural one is unpredictable. Every cheaper observation that bears on the mechanism has already been run (see the Premise Inventory).

# Critique — make Telethon's per-request flood-wait threshold work in tgdata

## High-level summary

**The plan's shape holds.** It is a build-time mixin in tgdata's single client factory, covering the property and `__call__`, keyed to the owning task. It is backed by offline tests that run Telethon's real request code, plus a docs pass. Every load-bearing premise was settled by probe or by reading Telethon's source before any build step, so there is nothing to reorder.

Three Medium findings must be folded in.

1. **Discovery is not ready for every kind of wait the fix will now show it.** Telethon's silent-sleep branch covers four wait errors; discovery catches only one of them, `FloodWaitError`. On Telethon 1.45.0, `FloodPremiumWaitError` is a sibling class, not a subclass. Today Telethon sleeps a short premium wait silently. After the fix it reaches discovery, which then:
   - skips a search query instead of retrying it;
   - in `linked_groups`, lets a raw Telethon error escape a public method instead of `DiscoveryInterrupted`.
2. **Step 4's documentation list is incomplete.** Success criterion 10 needs every statement about discovery's waits to be true. At least four statements are not on the plan's list:
   - the `DiscoveryInterrupted` docstring;
   - the guide's troubleshooting row;
   - the `TgData` facade wording that `linked_groups` inherits;
   - the silent dialog-sync fallback.
3. **Nested requests inherit the per-call value.** A request that triggers other requests in the same task would apply its per-call value to them too. That contradicts the plan's own wording, "exactly for the duration of that request", in a mechanism every future caller will share. No current call site triggers it.

Eight Low findings follow; they are informational.

## Premise Inventory

**What was checked** for unproven premises:
- the plan's hedges and the desc's three `[ASSUMPTION]` marks;
- every claim about Telethon and Telegram behaviour;
- the "settled during planning" list.

Each premise was re-tested here where cheap.

**Confirmed, so not open:**
- *Telethon decides every silent sleep by reading the `flood_sleep_threshold` property.* This is documentary, and was confirmed this pass by a whole-function diff of `__call__` and `_call` between 1.33.1 and 1.45.0.
  - The sleep decisions are identical: the default comes from the property, the pending-wait pre-check uses that local value, and the after-error check reads `self.flood_sleep_threshold`.
  - The property and its setter are identical.
  - The only differences are list handling, `maybe_async`, and one addition from 1.33.1 to 1.45.0: `FloodPremiumWaitError` joined the sleep branch. That addition is the root of finding 1.
  - It was also runtime-confirmed on 1.45.0 by `probe_threshold_workaround.py`, 7 of 7 checks.
- *The owner-task guard keeps the value out of tasks started during the call.* Runtime-confirmed (`probe_owner_task.py`): a plain context variable leaked 0 into a task started mid-call, and the guarded one did not.
- *A build-time mixin keeps test_13's patch point and `isinstance`.* Runtime-confirmed (`probe_mixin.py`).
- *No other Telethon path sleeps on a flood wait without the property.* Confirmed by grep of the installed 1.45.0:
  - the property is read only inside `_call`;
  - the updates loop catches `FloodWaitError` without sleeping;
  - downloads call `_call` directly, but read the same property.
- *Nothing in tgdata checks a client's exact class, or imports `telethon.sync`.* Confirmed by grep.

**Open premises, ranked by waste if false:**

1. **Premise:** Telegram signals a mandated wait as a `FLOOD_WAIT`-family error, which Telethon turns into the classes its sleep branch handles.
   - **First dependent step:** Step 1.
   - **Waste if false:** Steps 1–5. Telethon's own flood handling would be wrong for every user, not only tgdata.
   - **Test scheduled at:** never live. Steps 2–3 run offline.
   - **Cheapest earlier test:** none affordable. A live wait needs an account to be throttled on purpose. The error conversion itself (`rpc_message_to_error`) was verified offline on 1.45.0 in issue #4's critique, and real waits reached this project through Telethon before — a reference finder logged multi-hour lookup waits as `FloodWaitError`.
   - **Coverage:** **non-covering** for this premise — the fake connection supplies the error instead of observing Telegram. The premise rests on that prior real observation.
2. **Premise** (desc `[ASSUMPTION]`): discovery's post reading is out of scope.
   - **First dependent step:** Step 4 (docs).
   - **Waste if false:** one small code change plus a test, added later.
   - **Test scheduled at:** n/a — a scope decision, not a fact.
   - **Cheapest earlier test:** none needed; the user decides.
   - **Coverage:** n/a.
3. **Premise** (desc `[ASSUMPTION]`): no new public API, and the `device_identity()` probe stays as it is.
   - **Waste if false:** none — it would only add an export or a one-line change.
   - **Coverage:** n/a.

**Rule check:** no open premise has an affordable earlier test scheduled after its first dependent step. The verdict is not REORDER.

## Restart Check

The desc exists because of four observed failures.

| Observed failure | Established mechanism | Design element that addresses it |
|---|---|---|
| Discovery is silent for up to 60 s during short waits; no heartbeat ticks | `UserMethods.__call__` drops `flood_sleep_threshold`, and `_call` reads the client-wide property (source in six releases; runtime probe) | Step 1 makes the per-call 0 raise, so `_request` sleeps in beating slices; verified by Step 3 TEST 7 |
| `max_flood_wait` below 60 s is not honoured | same | Step 1; Step 3 TEST 8 |
| Lookup waits are slept through, against the guide's rule | same | Step 1; Step 3 TEST 9. Premium-type lookup waits are only partly covered — finding 1 |
| Docstrings state the opposite of what happens | a consequence of the three above | Step 4 — incomplete, finding 2 |

Every row has a design element, so the plan works at the right layer.

## Inherited Lessons

- **Lesson:** username lookups escalate into multi-hour blocks, so a wait on a lookup is never slept through.
  - **Satisfied by:** Step 1, the mechanism, and tested in Step 3 TEST 9, before the docs and before the commit. The sequence satisfies it.
  - **Caveat — finding 1:** a premium-type lookup wait is not recognised as a wait by `_links`. It is treated as a dead name, so the next name is tried. The next attempt is then refused by Telethon's own pending-wait pre-check, which raises a plain `FloodWaitError` and stops resolution. So the lesson holds today only through that Telethon behaviour, not through tgdata's code.

---

## Risk 1 — Discovery only recognises one of the four wait errors the fix will now show it

### Risk

When Telegram tells a client to slow down, it can say so in four ways: an ordinary flood wait, a "premium" flood wait, a slow-mode wait, and a test-server wait. Telethon, the library tgdata is built on, quietly sleeps through all four when they are short. tgdata's group-discovery code was written to handle the waits itself, but it only recognises the first kind. Today that mismatch is invisible, because Telethon sleeps every short wait before discovery sees it.

Once this fix makes discovery's requests stop being slept, a short premium wait reaches discovery as an unknown error. A search query is then skipped instead of waited for and retried, and the user silently gets fewer rooms. Asking for the rooms linked from a given channel fails with a raw Telegram error, instead of the documented "interrupted — here is what was found, retry after N seconds".

**Precisely.** Telethon 1.45.0's `_call` (`telethon/client/users.py`) sleeps on `(FloodWaitError, FloodPremiumWaitError, SlowModeWaitError, FloodTestPhoneWaitError)`. These are four sibling subclasses of `FloodError`; only the first is a `FloodWaitError`, as verified on 1.45.0. `tgdata/discovery_engine.py` catches only `FloodWaitError`, at lines 253 (`_request`), 344 (`_similar` seeds), 416 (`_mine_room`), 460 (`_links`) and 534 (`linked_groups`).

With Step 1 in place, `client(request, flood_sleep_threshold=0)` raises `FloodPremiumWaitError` for any premium wait. The consequences:
- **In `_request`** it is not caught as a wait. It propagates to `_search`'s `except RPCError`, giving "Search … failed — skipped", and to `_similar`'s `except (RPCError, TypeError)`.
- **In `_resolve`**, `_similar` treats it as a generic seed failure; `_links` treats it as a dead name and tries the next one; `linked_groups` does not catch it at all, so it leaves the public method as `FloodPremiumWaitError`.

On 1.33.1 the premium error is unknown to Telethon, so it arrives as a bare `FloodError` that Telethon never slept. Any wait-family tuple must therefore be built version-robustly. The same `except FloodWaitError`-only assumption exists outside this plan, at `message_engine.py:339` and `connection_engine.py:506` and `:530`. Those sites still use Telethon's 60 s silent sleep, so they are only exposed to waits over 60 s, as before.

### Severity

Medium

### Category

Breaking change — a regression path that appears only after the fix

### Impact

- Silent result loss on non-Premium accounts if Telegram applies premium throttling to search or recommendations.
- A raw `FloodPremiumWaitError` escapes `linked_groups`, where callers are told to expect `DiscoveryInterrupted`.
- Link resolution may try one extra name after a premium lookup wait.

Likelihood is low today: premium waits are mostly seen on file transfers. Telegram can apply them to any method without notice.

### NoobEng

Telethon's "silent sleep" acted as an accidental shock absorber. While it slept, nobody noticed that discovery's error handling only knew one of the four ways Telegram says "wait". The fix removes the absorber on purpose, so discovery's handlers must now really cover what Telethon covered: the exact tuple Telethon's own sleep branch catches. Every one of those exceptions carries `.seconds`, so the handling code needs no change beyond the tuple.

### Affected areas

`DiscoveryEngine._request`, `_similar`, `_mine_room`, `_links`, `linked_groups`; the public `search_groups`, `similar_groups`, `linked_groups`, `discover_groups`; Step 3's tests

### Mitigation

#### Mitigation — Quick

Catch `FloodPremiumWaitError` next to `FloodWaitError` only in `linked_groups`, so the public method raises `DiscoveryInterrupted` as documented. Leave the other sites as they are.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

In `discovery_engine.py`, define one module-level tuple that mirrors Telethon's sleep branch, built version-robustly:

```python
WAIT_ERRORS = tuple(c for c in (FloodWaitError,
                                getattr(errors, 'FloodPremiumWaitError', None),
                                getattr(errors, 'SlowModeWaitError', None),
                                getattr(errors, 'FloodTestPhoneWaitError', None)) if c)
```

Use it at all five discovery catch sites. Add a TEST to Step 3: a `FLOOD_PREMIUM_WAIT` on a raw discovery request is slept with heartbeat ticks and retried, and on a `linked_groups` source it raises `DiscoveryInterrupted`. Step 1's wording — discovery code unchanged — becomes "discovery's catch sites widened to Telethon's wait family".

**Why this is robust:** discovery then handles exactly what Telethon used to sleep for it. The invariant "everything Telethon would have slept, discovery now handles" holds by construction, in one file the plan already touches.

- [x] selected   - [ ] elegant   - [x] last_resort

**Note**
*Why chosen:* It closes this instance in the one file the plan already touches: discovery's five catch sites then mirror Telethon's sleep branch, which is the invariant the fix needs. The class-wide fix is better, but it changes the message engine's fetch loop and authentication, which are core read paths outside this plan. They need their own critique and tests, per the delicacy gate. This robust work survives the class fix — the tuple just moves to a shared home — so the class fix is future improvement, not a prerequisite.
*For future:* —

#### Mitigation — Long-term

Put the wait tuple in one shared place — for example `tgdata/utils.py` or the connection layer — and use it at all eight `except FloodWaitError` sites in tgdata: discovery (5), the message engine's fetch loop (1), and `_authenticate` (2). Add a test asserting each site catches every member.

**Why this is long term effective:** no tgdata module can again handle only one of Telegram's wait kinds. A new Telethon wait class is added in one place.

- [ ] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* The better answer. One shared wait tuple at all eight `except FloodWaitError` sites — discovery (5), `message_engine.py:339`, and `connection_engine.py:506` and `:530` — so no module can again handle only one kind of wait. Not blocked by access, only by scope. Do it as its own small fix once this merges, with a test that drives a `FLOOD_PREMIUM_WAIT` over 60 s through the fetch loop.

---

## Risk 2 — Step 4 does not list every documentation statement that the fix makes untrue or incomplete

### Risk

The fix changes what discovery does during short waits, and the project promises that its docs will match. The plan names two paragraphs to update, one in the README and one in the usage guide, plus the discovery code's own comments. Four further statements describe the same behaviour and would be left wrong or incomplete:
- the description of the "interrupted" error, which says it only happens for long waits or network loss;
- a troubleshooting table that says the same;
- the help text for "rooms linked from a channel", which inherits wording promising visible waits;
- another discovery step that also still sleeps silently.

A user who reads those would be misled about when and why discovery stops.

**Precisely.** Statements not on Step 4's list:
1. **`DiscoveryInterrupted`'s docstring** (`discovery_engine.py:66-74`): "Telegram demanded a wait longer than max_flood_wait, or the network stayed down past max_offline". After the fix, `linked_groups` raises it on any wait for looking up its source, even below `max_flood_wait`, because `_resolve` never sleeps.
2. **The guide's troubleshooting row** (`devdocs/guides/group_discovery.md`, §8): "`DiscoveryInterrupted` with `retry_after > 0` — Telegram demanded a wait above `max_flood_wait`". It has the same gap.
3. **The `TgData` facade docstrings** (`tgdata/tgdata.py`).
   - `search_groups`' `max_flood_wait` says "obeyed exactly, with heartbeat ticks; a longer one raises DiscoveryInterrupted".
   - `similar_groups`, `linked_groups` and `discover_groups` inherit that wording ("as in search_groups").
   - Neither the source-lookup interruption nor post reading's untracked waits are stated.
4. **The silent dialog-sync fallback.** `_resolve`'s fallback for numeric ids (`MessageEngine._entity_after_dialog_sync`) passes no per-call threshold, so its short waits stay silent. The desc names only post reading as staying silent.

Success criterion 10 cannot pass while these stand.

### Severity

Medium

### Category

Phase completeness — a step too high-level for what it must cover

### Impact

- Callers are misled about when `DiscoveryInterrupted` can occur.
- A watchdog author may rely on ticks during every discovery wait.
- The plan reports success criterion 10 as met when it is not.

### NoobEng

A behaviour like "how discovery treats waits" is restated in several places in this project: README, guide, facade docstrings, engine docstrings and the exception's docstring. The plan has to find every restatement, not only the two obvious paragraphs. A grep for the policy's key words finds them: `max_flood_wait`, `DiscoveryInterrupted`, "slept", "heartbeat ticks", "lookup".

### Affected areas

README "Pacing and waits"; guide § waits and § 8 troubleshooting; `DiscoveryInterrupted`; `TgData.search_groups` / `similar_groups` / `linked_groups` / `discover_groups` docstrings; `discovery_engine.py` docstrings

### Mitigation

#### Mitigation — Quick

Add one sentence each to the `DiscoveryInterrupted` docstring and the guide's troubleshooting row: "a lookup wait on a `linked_groups` source also raises it".

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

Expand Step 4 into an explicit list:
- the two paragraphs already named;
- the `DiscoveryInterrupted` docstring;
- the guide's §8 row;
- the facade `max_flood_wait` / `linked_groups` docstrings;
- the engine docstrings;
- one sentence naming both still-silent paths: post reading, and the dialog sync for numeric ids.

Add a check to Step 5: grep README, guide and `tgdata/*.py` for `max_flood_wait|DiscoveryInterrupted|slept|heartbeat tick|lookup`, and read every hit against the new behaviour before committing.

**Why this is robust:** it closes this instance completely, and the grep makes the completeness of the sweep checkable rather than remembered.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* It closes the instance completely, and the grep makes the sweep's completeness checkable. The long-term alternative is not one mechanism: docstrings must stay self-contained for API users, so replacing them with links would need per-place exceptions. Robust wins on reach per extent.
*For future:* —

#### Mitigation — Long-term

Give discovery's wait and lookup policy one canonical home — a "Waits and lookups" section in the guide. README, facade docstrings and the exception's docstring then link to it in one line instead of restating it.

**Why this is long term effective:** the next policy change edits one place, so restatements cannot drift apart again.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

---

## Risk 3 — A per-request setting also applies to the extra requests Telethon makes inside that request

### Risk

The fix lets a caller say "for this one request, do not wait silently". Sometimes Telethon has to make a second, hidden request first — for example, to look up who "@somename" is before it can send the request the caller actually asked for. Under the plan, that hidden lookup also gets "do not wait silently". It would fail on a short wait instead of sleeping through it, as it normally does.

Nothing in tgdata triggers this today. But the mechanism lives in the one place every tgdata client is built, so the next feature that uses a per-request setting inherits this surprise. The plan's own description — the setting holds "exactly for the duration of that request" — would then be wrong.

**Precisely.** Inside Telethon's `_call`, `await r.resolve(self, utils)` can issue nested `self(...)` calls in the same task, for example `get_input_entity` for an unresolved peer. Under Step 1's design:
- the nested `__call__` receives `flood_sleep_threshold=None`, so it takes the `super().__call__` path without touching the context variable;
- the outer `(owner_task, value)` is still set, and the task is the same;
- so the property returns the outer value, and the nested request applies it.

Telethon's documented meaning is "the flood sleep threshold to use for this request". Discovery's two call sites pass requests whose inputs are already resolved — `InputChannel`, `Channel` objects, plain usernames — so nothing nested happens there today. The trigger is any future per-call use with a peer that needs resolution.

### Severity

Medium

### Category

API contract — the semantics of a shared mechanism

### Impact

A future caller passing a per-call threshold could see `FloodWaitError` from a lookup it never asked about. Debugging that would mean knowing this mixin's internals.

### NoobEng

A context variable is like a thread-local for asyncio tasks: anything running in the same task sees what was set. Telethon resolves names by making requests from inside the request you sent, so "inside my request" and "my request" are not the same thing. The fix is to clear the value when a request without its own setting starts while one is active.

### Affected areas

`connection_engine._PerCallFloodThreshold.__call__`; any future tgdata code passing `flood_sleep_threshold`

### Mitigation

#### Mitigation — Quick

State the behaviour in the mixin's docstring and in Step 1's wording: the value applies to the request and to anything Telethon sends from inside it in the same task.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

#### Mitigation — Robust

In `__call__`, when no per-call value is passed but one is active, clear it for the duration of this call:

```python
if flood_sleep_threshold is None:
    if _PER_CALL_FLOOD_THRESHOLD.get() is None:
        return await super().__call__(request, ordered=ordered)
    token = _PER_CALL_FLOOD_THRESHOLD.set(None)
    try:
        return await super().__call__(request, ordered=ordered)
    finally:
        _PER_CALL_FLOOD_THRESHOLD.reset(token)
```

Add a TEST to Step 2: with a per-call value active in the task, a plain `client(request)` sleeps a 1 s wait normally.

**Why this is robust:** it gives exact per-request semantics, matching Telethon's documented meaning, for a few lines in the file the plan already changes. The common path stays one `ContextVar.get()`.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* There is no class: no other per-request setting in tgdata travels through a context variable. So long-term collapses into robust. A few lines in the file Step 1 already changes give exact per-request semantics, and the common path stays a single `ContextVar.get()`.
*For future:* —

#### Mitigation — Long-term

Honour the value only for the request object it was set for. That requires knowing which request `_call` is processing, which means wrapping or replacing Telethon's private `_call`.

**Why this is long term effective:** it is exact by construction, even for nested requests that pass their own values.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

---

## Risk 4 — The fix is proven at runtime only on the newest Telethon

### Risk

tgdata promises to work with any Telethon release from 1.33 up to, but not including, 2.0. The fix is run end-to-end only against the newest release. For older releases it rests on reading Telethon's code.

**Precisely.** The offline runs use Telethon 1.45.0. This pass diffed `__call__` and `_call` between 1.33.1 and 1.45.0: the sleep decisions and the property are identical. So the claim is confirmed by reading, and a runtime run on 1.33.1 would only re-confirm it.

### Severity

Low

### Category

Compatibility

### Impact

None expected. If some untested difference did exist, users on old Telethon releases would silently keep today's behaviour; nothing would crash.

### NoobEng

Reading identical source is strong evidence for deterministic code. A runtime run on the floor release is cheap insurance, not a prerequisite.

### Affected areas

users pinned to Telethon 1.33–1.44

---

## Risk 5 — Replacing the client class with something that is not a class breaks client creation

### Risk

Some test suites replace a library's client with a mock object, to avoid touching the network. tgdata's own tests replace it with a real subclass, which still works under the plan. A downstream test that replaces it with a generic mock would now fail when tgdata builds a client, because a mock cannot be used as a base class.

**Precisely.** `_client_class(TelegramClient)` calls `type(name, (_PerCallFloodThreshold, base), {})`. Patching `tgdata.connection_engine.TelegramClient` with a `MagicMock` raises `TypeError`. A one-line guard — return `base` unchanged when it is not a `TelegramBaseClient` subclass — keeps such mocks working.

### Severity

Low

### Category

Compatibility, for downstream tests

### Impact

Consumers' unit tests that mock the client may break after upgrading tgdata.

### NoobEng

Composing a mixin at run time assumes the base is a real class. A guard keeps the fix out of the way of test doubles.

### Affected areas

`connection_engine._client_class`; downstream test suites

---

## Risk 6 — The upgrade canary only fires if someone runs it

### Risk

The new test fails if a future Telethon stops honouring the mechanism. But the project has no automatic test runs — only a publishing workflow. `requirements.txt` does not pin Telethon, so a new Telethon release can arrive without anyone running the test, and discovery would quietly return to sleeping through short waits.

**Precisely.** `.github/workflows/` holds only `python-publish.yml`; `requirements.txt` lists `Telethon` unpinned; `setup.py` allows `<2.0`. TEST 1 and TEST 5 of `test_14` are the canary.

### Severity

Low

### Category

Process / Stale behaviour

### Impact

A future Telethon change silently undoes the fix until someone runs `test_14`. Nothing crashes; the old behaviour returns.

### NoobEng

A canary needs a schedule. A line in `test_14`'s docstring and in the smoke-tests README — "run after any Telethon upgrade" — is the cheap version; a CI job is the real one.

### Affected areas

`tgdata/smoke_tests/test_14_flood_threshold.py`; release practice

---

## Risk 7 — Discovery's visible behaviour changes without a release note

### Risk

After the fix, discovery behaves differently in a way users can notice:
- it pauses visibly instead of silently;
- it skips a starting name that would require waiting;
- it can stop with "interrupted, retry in a few seconds" where it used to quietly wait and carry on.

This is intended and documented, but nothing in a version number or release note tells existing users.

**Precisely.** The README carries "New in 0.0.8" notes, and `tgdata/__init__.py` holds `__version__ = "0.0.8"`. A note such as "Fixed: discovery now handles every wait itself, as documented" belongs with the merge. The version decision belongs to the maintainer.

### Severity

Low

### Category

Release practice

### Impact

A downstream run sees new `DiscoveryInterrupted` cases or skipped seeds with no explanation.

### NoobEng

A behaviour fix is still a behaviour change for whoever depended on the old behaviour.

### Affected areas

README "New in" notes; versioning at merge

---

## Risk 8 — Tgdata clients lose Telethon's synchronous-call convenience

### Risk

Telethon has an optional mode that lets programs call it without async code. It works by rewriting Telethon's client class when it is imported. tgdata's clients would now use their own version of the call method, which that rewrite does not reach. A program that mixes that mode with tgdata's clients would get a pending coroutine instead of a result.

**Precisely.** `import telethon.sync` runs `syncify(TelegramClient, …)`, which wraps coroutine methods, `__call__` included, on those classes only. `_PerCallFloodThreshold.__call__` shadows the wrapped one on tgdata clients. tgdata never imports `telethon.sync`, and its API is async-only.

### Severity

Low

### Category

Compatibility

### Impact

Only code that both imports `telethon.sync` and calls a tgdata-built client synchronously is affected. No known user does.

### NoobEng

Monkey-patching libraries and subclasses interact. Here the effect is confined to a usage tgdata does not support.

### Affected areas

`TelegramClient` instances obtained from tgdata's connection engine

---

## Risk 9 — Setting aside the stray edit in the guide

### Risk

The working copy holds a small unrelated, uncommitted edit in the discovery guide, made by someone else. The plan sets it aside, edits the guide, commits, and puts it back. Done carelessly, that could commit the edit, lose it, or restore the wrong saved change.

**Precisely.** Line 1 of `devdocs/guides/group_discovery.md` reads `claude # Group discovery — …`. `git stash list` is empty, so the path-limited stash Step 4 pushes will be `stash@{0}`. Push it with a message, pop it only if that message matches, and confirm with `git diff` that only line 1 remains modified.

### Severity

Low

### Category

Working-tree hygiene

### Impact

An unrelated edit could be committed or lost.

### NoobEng

`git stash` is safe when you verify what you pop.

### Affected areas

`devdocs/guides/group_discovery.md`; Step 4 and Step 5

---

## Risk 10 — Issue #4's finding becomes stale when this merges

### Risk

Separate work on account health events, on another branch, records that discovery's short waits are invisible and that discovery only handles waits over a minute. Once this fix merges, that record is wrong, and the health-events design would plan around a problem that no longer exists.

**Precisely.** `devdocs/work/4-account-health-events/traverse/finding.md` (§8 and §13), on the `feat/4-account-health-events` branch. Its probe asserts only on plain `TelegramClient` instances, so it keeps passing.

### Severity

Low

### Category

Cross-feature documentation

### Impact

#4's event-source inventory would list discovery's waits under the wrong source.

### NoobEng

Two branches describe the same code. When one changes it, the other's notes need a line.

### Affected areas

issue #4's work folder

---

## Risk 11 — The lookup budget counts lookups that were never sent

### Risk

Discovery limits how many "who is @name?" lookups one call may spend, and reports how many it spent. After the fix, once Telegram asks for a wait, Telethon refuses the following lookups on the spot without sending them. Discovery still counts each refused attempt as spent, so the reported number is higher than the lookups actually made.

**Precisely.** `_resolve` increments `st.resolved` before sending `ResolveUsernameRequest`. With a pending wait recorded in Telethon's `_flood_waited_requests`, the next call raises in `_call`'s pre-check without sending. Before the fix, short waits were slept and every counted lookup was sent.

### Severity

Low

### Category

Reporting accuracy

### Impact

The log line `N username resolutions spent of M` overstates the spend. No extra lookups are made.

### NoobEng

Count after the request is sent, not before. That is a later tidy-up, not part of this fix.

### Affected areas

`DiscoveryEngine._resolve`; the `discover_groups` summary log line
