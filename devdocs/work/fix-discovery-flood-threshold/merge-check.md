---
model: claude-opus-5-5[1m]
effort: max
---

# Merge check — `fix/discovery-flood-threshold` into `dev`

CONTRIBUTING.md §7.1. Read together:
- `desc.md`;
- `step_by_step_impl_plan.md` — the critic-folded plan, this branch's revision 2;
- `critic.md`;
- the diff `dev...fix/discovery-flood-threshold`.

The diff spans two commits:
- `7ad74fa` — the fix;
- `cd11892` — two corrections found while preparing this gate.

Run in the same warm session that wrote the plan and the code (§7.5).

**Result: passes.** The PR may be opened. It merges only if the PR critic (§7.2) finds no High or Medium.

## 0. Was the work done warm, and was it weighed?

**Warm: yes.** `desc.md` opens with `Session warmed at f411c9c (2026-10-03)`, and `f411c9c` is the commit this branch was cut from, so it is an ancestor. The record was reformatted at this gate to the §4.2 form. It previously said "already warm" without naming the commit; its content is unchanged.

**Weighed: no — a deviation the maintainer accepted.**
- There is no `triage.md` and no GitHub issue. The maintainer waived the issue for this fix on 2026-10-03, and with it the label that records a weight.
- The work instead came from a probe-backed investigation, recorded in `desc.md`'s Problem Statement, and a full `/critic-d` before implementation.
- By its shape it is *light*: one factory function, five catch sites, docstrings and docs, and one new offline test.

## 0b. Did the diff stay inside what triage surfaced?

There is no triage, so it cannot be checked against one. Every file the plan names, and nothing else:
- `tgdata/connection_engine.py`;
- `tgdata/discovery_engine.py`;
- `tgdata/tgdata.py`;
- `tgdata/smoke_tests/test_14_flood_threshold.py`;
- `README.md`;
- `devdocs/guides/group_discovery.md`;
- this work folder.

## 1. Does the implementation match the plan?

**Yes, step for step:**
- **Step 1** — the mixin, the per-base class builder, and `_new_client()` building through it.
- **Step 2** — `_WAIT_ERRORS` at the five discovery catch sites.
- **Steps 3–4** — TESTs 1–11, as numbered in the plan.
- **Step 5** — the listed documentation statements.
- **Step 6** — the grep sweep, the compile, three offline suites, the commit, and the stray guide edit restored uncommitted.

**Deviations, all named:**
1. **The module alias.** `_WAIT_ERRORS` imports Telethon's errors as `tl_errors`, matching the module's existing `tl_utils` / `tl_types`, not the plan's `telethon_errors`. Naming only.
2. **A dropped space.** Step 2's edit turned `COLUMNS = [` into `COLUMNS =[`. It was found reading the diff for this gate and restored in `cd11892`; there was no behaviour change.
3. **One stale docstring.** The module docstring of `discovery_engine.py` still said every wait is "obeyed … visibly". Step 6's sweep pattern did not match its wording ("obeys flood waits exactly and visibly"). It was corrected in `cd11892` to name the two steps that keep Telethon's own silent sleeps.
4. **One extra README sentence**, as Step 6 allows. The sweep found "a wait on a lookup is skipped or stopped" missing the `linked_groups` source case; it was fixed in `7ad74fa`.

## 2. Does the plan still make sense against what the code turned out to be?

**Yes.** Implementation taught nothing that contradicts the plan's reasoning:
- the owner-task guard;
- exact per-request scope;
- the build-time mixin that keeps test_13's patch point;
- discovery handling Telethon's whole wait family.

All four hold in the code, and the tests demonstrate each. One observation worth keeping, about TEST 7: the persistent path with a stand-in client fails inside Telethon's `start()` on "No phone number or bot token provided" before it connects. That is the same path test_13 exercises, and it is expected.

## 3. Did the critic's findings actually get answered?

The `critic.md` verdict was IMPLEMENT AFTER FOLDING THESE IN. It found three Medium risks and no High.

**Medium findings — all answered:**
- **Risk 1, discovery recognised only one of four wait errors.** Answered by `_WAIT_ERRORS` in `discovery_engine.py`, used at `_request`, `_similar`, `_mine_room`, `_links` and `linked_groups`. TEST 11 drives premium waits through `search_groups` and `linked_groups`.
- **Risk 2, Step 4's documentation list was incomplete.** Every listed statement was updated: the docstrings of `_request`, `_resolve`, `DiscoveryInterrupted` and the module; the `TgData` `search_groups` `max_flood_wait` text and the `linked_groups` `Raises:`; the README's "Pacing and waits" and its lookup sentence; the guide's waits paragraph and its §8 row. The grep sweep ran, and deviation 3 above is the one it missed.
- **Risk 3, nested requests inherited the per-call value.** Answered in `_PerCallFloodThreshold.__call__`, which clears an inherited value for a request without its own. TEST 6 covers it.

**Low findings — consciously left:**
- *Floor runtime* (critic Risk 4) — confirmed by reading the whole function in 1.33.1.
- *A mock as the client class* (Risk 5).
- *The canary runs only by hand* (Risk 6). The test's and the mixin's docstrings say to run it after any Telethon upgrade; CI is out of scope.
- *A release note* (Risk 7) — for the maintainer at release time.
- *`telethon.sync`* (Risk 8).
- *Issue #4's notes go stale on merge* (Risk 10) — a follow-up on that branch.
- *The lookup budget counts refused lookups* (Risk 11).

Risk 9, the stash, was handled: the stray guide edit is back in the working tree and was never committed.

**Verification on Telethon 1.45.0:**

| Suite | Result |
|---|---|
| `test_14_flood_threshold` | 11/11 |
| `test_13_device_identity` | 6/6 |
| `test_12_proxy` | 7/7 |

Live tests were not run: their configured account's session is logged out, and the persistent path would request a login code.

## 4. Is the issue's status block complete and honest?

There is no issue and so no status block, because the maintainer waived it. This merge check, the PR description and the branch's work folder are the record.
