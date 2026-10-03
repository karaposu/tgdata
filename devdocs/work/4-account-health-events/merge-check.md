---
model: claude-opus-5-5[1m]
effort: max
---

# Merge check — `feat/4-account-health-events` into `dev`

CONTRIBUTING.md §7.1. Read together:
- `triage.md`;
- `desc.md` — amended at this gate (`c875da6`), see question 2;
- `plan.md` — revision 2, with its implementation notes;
- `critic.md`;
- the diff `dev...feat/4-account-health-events`.

The code diff spans three commits:
- `94560f0` — the implementation, plan steps 1–8;
- `a21eea5` — the `health_check()` fix the maintainer asked for after step 5;
- `c5cae8d` — one README line answering critic Risk 10 (Low), written at this gate.

Run in the same warm session that wrote the plan and the code (§7.5).

**Result: passes.** The PR may be opened. It merges only if the PR critic (§7.2) finds no High or Medium. One point is the maintainer's to judge: the model rule, under question 0.

## 0. Was the work done warm, and was it weighed?

**Warm: yes.** `desc.md` opens with `Session warmed at c72eab4 (2026-10-03)`. `c72eab4` is this branch's merge base with `dev`, so it is an ancestor.

**Weighed: yes.** `triage.md` (`18fdfb5`) weighs the work feature-heavy, and #4 carries `enhancement` and `heavy`. They match.

**The model rule (§9) — for the maintainer.** §9 assigns feature work, end to end, to Fable 5.1 at max effort or GPT 6 Astra at xhigh. Every artifact on this branch that records a model names `claude-opus-5-5[1m]`:
- the plan, the critic and the traverse finding, at `max`;
- triage and the traverse passes, with effort `unknown`.

The desc and the code come from the same session. §9 lets the gate send work back on that ground alone. This check does not; that decision is the maintainer's.

## 0b. Did the diff stay inside what triage surfaced?

**Yes.** Every changed code file is in the territory triage surfaced:
- **`tgdata/connection_engine.py`** — items 1–4, 8 and 9: `AuthRequiredError`, `_authenticate`, `_ensure_connected`, `health_check`, `validate_connection`.
- **`tgdata/message_engine.py`** — items 15 and 18: the fetch loop's waits, and `GroupAccessError`.
- **`tgdata/discovery_engine.py`** — items 23–25 and 29: the wait handling and the per-item skips.
- **`tgdata/tgdata.py`** — items 30–35: the constructor, the public calls, polling, the real-time path, and the two facades.
- **`tgdata/smoke_tests/`** — a new offline test in the stand-in pattern of item 41.

**New, as triage expected:** `tgdata/health.py`. Triage confirmed that no health type existed. The docs changed are `README.md` and the smoke-test README.

**Surfaced and left unchanged, on purpose:**
- `models.py` (item 37) — the account identity is read from the engine's loaded config instead;
- `__init__.py` (item 40) — nothing new is exported, as the desc decided;
- the per-message media failures in `_process_message` (item 19) — the desc's "no event" list names them.

The weight held: the diff touches every engine, the facade and the real-time path.

## 1. Does the implementation match the plan?

**Yes, step for step:**
- **Step 1:**
  - `health.py`'s vocabulary, `WAIT_ERRORS`, `telegram_error_name`, `register`, `classify` and `normalise_group`;
  - `AuthRequiredError.first_login`, and `GroupAccessError` registered;
  - discovery and the connection engine import the shared pieces.
- **Step 2:**
  - `poll_for_messages` stops on what retrying cannot fix, and lets callback errors propagate;
  - `validate_connection` logs the classified reason.
- **Step 3:** the monitor, the call context, events, the ledger and recovery, safe delivery, the log mirror, the snapshot and `report()`, with Risks 1–4 folded in.
- **Step 4:** the filter on `telethon.client.users`, with the owner-task rule.
- **Step 5:** the decorator on the twelve methods of the plan's table, `health_check()["health"]`, and the engine report sites.
- **Step 6:** `test_16_health_events.py`, tests 1–17 as the plan numbers them.
- **Step 7:** the README section, the docstrings and the polling text.
- **Step 8:** the compile, the five offline suites and the commits.

**Deviations recorded in `plan.md`'s implementation notes**, items 1–10, each with its reason:
1. `validate_connection()` asks Telegram directly when `get_me()` returns `None`.
2. `classify()` also reads `AuthRequiredError.reason`.
3. A silent sleep's event names Telegram's exact wait.
4. Every attributed wait opens a ledger entry, a swallowed one included.
5. A scope reported in a nested call is noted on every enclosing call.
6. The poll loop's retry branch has no report line; the inner `get_messages` reports.
7. The fetch loop reports at its first statement, as Step 5 says.
8. The decorator, the sleep capture and `normalise_group` are hardened.
9. The smoke-test README gains an entry.
10. The `health_check()` fix, with test 18.

**Found at this gate, not in the notes:**
- **A third discovery report site.** Step 5 lists `_similar`'s seed and round skips and `_links`' lookup-wait and dead-name skips. The code also reports `_links`' source skip — a room whose posts cannot be read — with `group=entity`. It is the same per-item pattern that Risk 4's fold set out.
- **`normalise_group` gives an entity's id.** Step 1 says "anything else gives `None`". Discovery's round and source skips pass the entity, so without its id their no-access events would have no group.
- **`first_login` is set only on the never-logged-in branch of `_auth_required`.** The banned branch runs first and leaves it unset, so a ban is always reported. A brand-new session cannot be banned, so nothing observable changes.
- **The log line carries the wait length** after the error name, e.g. `FLOOD_WAIT_X 5s`. Step 3's format did not show it.

None of these is structural.

## 2. Does the plan still make sense against what the code turned out to be?

**Yes — the plan's reasoning holds.** Each mechanism it relies on is in the code, and a test drives each one:
- the cause chain;
- the counted-once mark;
- the owner task;
- the sentinel level;
- the fail-safe guards.

**Implementation taught one thing the plan did not know.** Telethon's `get_me()` answers a logout or a ban with `None`, not with an error. That is the root of notes 1 and 10. The plan's phrase "`validate_connection()` turns every failure into `False`" understated the problem: a logout after connecting was not a failure at all.

**Where the written record had drifted — now amended in `c875da6`, and noted on #4:**
- **Criterion 2's `group` rule** said "`None` otherwise". The plan and the code lowercase any other string and give an entity's id, and the desc now says so.
- **Criterion 2's `source` list** lacked `recovery`, the source of an `ok`, which the plan added in Step 3.
- **Criterion 6** said a sleep "outside any public call" is an occurrence. That holds for a sleep in a task whose call ended, or in another task during a call. A sleep in code that never ran inside a public call cannot be tied to an account, and is not reported. That limit was unstated; it is now stated.
- **Criterion 10** did not mention the `health_check()` fix or `validate_connection()`'s direct check. It now covers both.

**A reading note.** Step 3's original design sits below its fold notes, and its `_Call` fields and `report()` signature predate the fold. The fold notes override them, as the plan itself says.

## 3. Did the critic's findings actually get answered?

`critic.md`'s verdict was IMPLEMENT AFTER FOLDING THESE IN, with five Medium findings, no High and six Low.

**Medium — all answered:**
- **Risk 1, the reporting path could change what the caller sees.**
  - `HealthMonitor.call()` runs its error and recovery work through `_safely`.
  - `report()`, `_sleep()` and the sleep filter carry their own guards.
  - `_health_failed()` logs once at WARNING, then at DEBUG.
  - Test 14 breaks `_emit`, `_deliver` and `_record`, and checks that the caller still gets its own exception and its own result.
- **Risk 2, long calls absorbed other tasks' sleeps.** `_Call.task` and `owns_current_task()`: `_record` attributes an event to a call only from the call's own task. Test 15.
- **Risk 3, a false "ok".**
  - `c.waited` takes only slept and handled waits.
  - `c.reported`, filled through `note_reported()`, blocks recovery of what the call — or a call inside it — reported.
  - Test 16 runs discovery's real code for all three cases; test 7 covers the per-method and per-group rules.
- **Risk 4, per-item verdicts lost their group.** `report(exc, source, group=)`, and discovery passes the seed, the name or the entity. Test 17.
- **Risk 5, the desc contradicted the plan.** Criterion 10 (`01c176f`) records the decision, and was kept in sync at this gate (`c875da6`). The README's polling section states the stop rule.

**Low:**
- **Risk 6, polling's marker moves before the callback** — consciously left. A restart after a callback error can repeat messages, never lose them.
- **Risk 7, argument binding** — answered: `_reported` guards `bind_partial`.
- **Risk 8, two calls on one request type** — consciously left.
- **Risk 9, polling retries an unknown name** — consciously left: `ValueError` stays transient.
- **Risk 10, capture under `logging.disable`** — answered by the README (`c5cae8d`). A logger that `dictConfig` disabled is handled too, as note 8 records.
- **Risk 11, an async callback from the filter** — answered: `_deliver_now` checks for a running loop, and closes the coroutine if there is none.

**Verification on Telethon 1.45.0:**

| Suite | Result |
|---|---|
| `test_16_health_events` | 18/18 |
| `test_15_login_checks` | 11/11 |
| `test_14_flood_threshold` | 11/11 |
| `test_13_device_identity` | 6/6 |
| `test_12_proxy` | 7/7 |

**Not run, and why:**
- Live tests were not run, because the configured account's session is logged out.
- The critic's premise 1 — that Telegram signals these states with the names the table lists — is still covered only by Telethon's own tables, as the critic recorded.

## 4. Is the issue's status block complete and honest?

Yes, as far as it can be before this file commits:
- T and steps 0–5 are ticked on #4, each naming its commit, and every one of those commits is pushed.
- `desc.md` is posted on #4, and its merge-gate amendments follow as a second comment.
- Step 6 is ticked once this file is committed and the PR is open. Step 7 is ticked once `pr-critic.md` is committed.
