# Dynamic critic prompt — Issue 10, group discovery in tgdata

Target: `devdocs/scoped/10/step_by_step_impl_plan.md` (its `desc.md` sits beside it).
Reference implementation the plan lifts from: `~/Desktop/projects/flatmir-growth/work/tg/tg_groups_audit/find_rooms.py` (`collect`, `link_mine`, `resolve_username`, `wait_for_network`, the checkpoint logic).

You are critiquing a plan that adds a **fourth engine** to a small Telethon wrapper whose whole value is *discipline around one long-lived personal Telegram session*: one persistent authenticated client, bounded and resumable flood-wait handling, a liveness heartbeat, a safety bound on unbounded walks, and one row contract for groups. The new engine will issue **hundreds to thousands of paced requests in one session block** — far more than any existing operation — using two raw MTProto calls tgdata has never sent (`contacts.SearchRequest`, `channels.GetChannelRecommendationsRequest`) plus the request Telegram punishes hardest (`contacts.ResolveUsername`). Judge the plan against *that* reality, not against a generic library checklist.

Ultrathink. Read the plan, the desc, `tgdata/connection_engine.py`, `tgdata/message_engine.py`, `tgdata/tgdata.py`, `tgdata/models.py`, `tgdata/utils.py`, `setup.py`, and the finder's `collect`/`link_mine`/`resolve_username`/`wait_for_network` before writing a word. Where a claim about Telethon's behaviour matters, open the installed source under `.venv/lib/python3.11/site-packages/telethon/` and confirm it; do not reason from memory.

## Read the declared blockers first

The plan's `### Huge Hard Blockers` and the desc's `## Known Blockers` already declare: four **closed** planning premises (dependency floor, result caching, per-call flood threshold, cache-first lookup) and two **open execution** blockers (a live smoke test needs the user's account and consent; a PyPI release is the user's GitHub action). Do not re-derive these as findings. Carry the execution blockers into `critic.md` unchanged as preconditions — no severity, no tiers. The closed premises still go into the Premise Inventory: *known* is not *handled*, and a premise whose only real test is scheduled after the code that depends on it has been disclosed, not closed.

## The questions this plan must answer

Work through every one. A question you cannot answer from the code is a finding, not a shrug.

### 1. Premises about the vendor, and when they are tested
- Which claims about what Telegram will *return* — recommendations on a non-Premium account, search hits for name queries, `participants_count` on search results, cacheable (non-`min`) `Channel` objects with access hashes — are behavioural rather than documentary? The finder proves some of them on *another* account, possibly a Premium one; which ones does that evidence not transfer to this account and this composition (through `ConnectionEngine.session()` with a per-call `flood_sleep_threshold=0`)?
- The plan tests everything live at step 6, after the engine is written at step 4. What is the cheapest observation that would settle each premise *before* step 4, what does it cost, and what does it need? If it is a handful of read-only requests from the configured account, say so and apply the REORDER rule.
- Which premise, if false, would **rewrite** steps rather than adjust them? Name the steps.

### 2. The session, the cache and bare ids
- Every row the plan returns carries a bare `GroupID` and no access hash; usability by `get_messages` rests entirely on Telethon writing search/recommendation results into the SQLite session (`process_entities`). Under what conditions does that write *not* happen (`min` entities, zero access hash, a session other than SQLite, a result type `process_entities` does not walk)? Would the caller notice, or get `GroupAccessError` later?
- tgdata resolves bare ints by trying marked variants in the session (`get_entity_rows_by_id(exact=False)`). Can a basic-group id and a channel id collide numerically, and does the plan's dedup key or `GroupID` contract expose that?
- Is the `list_groups` parity claim (same columns, same meaning) true for every column on a search result? `Dialog.is_channel`, `megagroup`, `participants_count` — check what a `contacts.Found` `Channel` actually carries versus a dialog's.

### 3. Flood discipline, shared-client state and concurrency
- The plan sends raw requests with a per-call `flood_sleep_threshold=0` precisely to avoid mutating the shared persistent client — then mutates `client.flood_sleep_threshold` inside `_resolve` because `get_input_entity` has no per-call route. Who else can be using that client at that instant (`on_new_message` handlers via `run_with_event_loop`, `poll_for_messages`, a concurrent `get_messages` task)? What happens to *their* request during the window? Is there a mutation-free way to get the same guarantee (`client.session.get_input_entity` for the cache, `ResolveUsernameRequest` / `GetChannelsRequest` sent through the same per-call path)?
- Which paths in the plan still sleep *silently* under Telethon's default 60-second threshold — `get_entity(peer)`, `get_dialogs()` in the dialog-sync fallback, `iter_messages` in link mining — and does that contradict the desc's "make the wait visible" rule?
- Telethon remembers a pending FloodWait per request type (`_flood_waited_requests`) and re-raises without sending; does `_request`'s retry loop and `DiscoveryInterrupted.retry_after` behave sensibly in that state?
- `MessageEngine.fetch_messages` bounds flood interruptions by count (`MAX_FLOOD_RETRIES`); the plan bounds by wait length (`max_flood_wait`). Is the inconsistency justified, and does either bound the *total* time a discovery can spend sleeping?

### 4. What is unbounded
- `fetch_messages` has `DEFAULT_FETCH_LIMIT` for walks with no limit. Where does the plan issue an open-ended number of requests with no equivalent bound — link-mining sources in `discover_groups(mine_links=True)`, username resolutions with `resolve_links=True`, rounds × seeds × recommendations? Compare each against the finder's caps (`LINKMINE_ROOMS_CAP`, `LIST_MINED_CAP`, `DAILY_ROOM_CAP`) and against the account-block history in the desc. Which default would a naive caller hit?

### 5. What ends a run, and what survives it
- The plan preserves partial results on a long flood wait (`DiscoveryInterrupted.found`). What happens on a dropped socket, a laptop sleeping, an `asyncio.IncompleteReadError` mid-way through 1,287 queries? `ConnectionEngine._ensure_connected` runs only when `session()` is entered; the finder needed `wait_for_network` and a 100-room checkpoint after losing 487 rooms this way. Does the same exposure exist in `fetch_messages`, and is that a class?
- Is there any way for a caller to receive rows as they are found (the `batch_callback` idea) so a two-hour run is not all-or-nothing?

### 6. Layering and coupling
- The engine calls `MessageEngine._entity_after_dialog_sync`, a private static method of a sibling engine. Where else in `message_engine.py` is entity resolution done ad hoc without that fallback (`get_message_count`, `search_messages`, `download_media_by_id`)? Is entity resolution a class that wants one home?
- Does anything the plan adds change an existing signature, an existing column, an existing export, or the meaning of `GroupInfo`? Circular imports between `discovery_engine`, `message_engine`, `models`, `tgdata`?

### 7. Contracts the documentation will promise
- For every promise the README section (step 7) will make — "already usable by `get_messages`", "same columns as `list_groups`", "waits obeyed exactly with heartbeat ticks", "nothing found is lost" — point to the code path that makes it true, or flag the promise.
- The link regex: which real link forms does it accept, which does it drop (`t.me/boost/<name>`, `t.me/<name>?start=`, `tg://resolve?domain=`), and does the reserved-path list drop a target that lives in the *second* path segment?

### 8. Detail versus complexity
- Step 4 is hardness 4 and ~300 lines, described with two helper snippets and prose for the four operations. Which mechanisms are left to the implementer's judgement — the internal signatures `discover_groups` chains, `messages.ChatsSlice` handling, whether seeds pre-seed the dedup set, the exact contract of an unresolved link row, `_frame`'s dtype rules on empty input? If the prose is too high-level for the concepts involved, that is a Medium finding.

### 9. Tests and the release
- The repo's only tests are live smoke scripts. Does step 6 exercise the behaviours that carry the risk (a flood wait, a network drop, a resolution stop, an empty result) or only the happy path? What can be asserted without the network?
- Does the version bump, the export list and the dependency floor form a coherent 0.0.8, and does raising the floor above 1.24 affect any consumer pinned below 1.33?

## Required document structure for `critic.md`

Create `critic.md` in the same directory as the implementation plan (`devdocs/scoped/10/`). Its **high-level summary sits at the top**, immediately after the verdict block.

1. **Frontmatter**, the very first thing in the file:
   ```yaml
   ---
   model: [model id from session context; "unknown" if not derivable]
   effort: [effort setting from session context; "unknown" if not derivable]
   ---
   ```
   Read both from session context at write time. Write `unknown` rather than omitting or guessing.

2. **Document-level verdict**, exactly one of: **IMPLEMENT AS WRITTEN** · **IMPLEMENT AFTER FOLDING THESE IN** · **REORDER — TEST BEFORE BUILD** · **DO NOT IMPLEMENT — MEANING GAP** (variant **DO NOT IMPLEMENT — WRONG LAYER**). The verdict judges the plan's shape and sequence, not the count of findings. If the plan's first untested premise is tested after the work that depends on it and an earlier test is affordable now, the verdict is REORDER regardless of what the risk analysis finds; name the experiment, its cost, the step it must precede, the disqualifying result and the passing result.

3. **Falsifier line** directly under the verdict (verdicts 1–3):
   ```
   Falsifier: [the cheapest observation that would flip this verdict to DO NOT IMPLEMENT]
   Affordable now: yes | no — [cost: time, money, access]
   ```
   If it is affordable now and the verdict is 1 or 2, the verdict is wrong: it is REORDER and the falsifier is the experiment. On verdict 4 the line reads "—".

4. **Preconditions** — the declared execution blockers, carried unchanged.

5. **High-level summary.**

6. **Premise Inventory**, before any risk item. Two signals admit a premise: the plan's own hedging (*hypothesis, assume, expect, ~10 per seed, likely, verified on another account*), and any claim about how a vendor service or device will behave. Per premise: **Premise** · **First dependent step** · **Waste if false** · **Test scheduled at** · **Cheapest earlier test** (with cost; "none" must be argued) · **Coverage** (flag as **non-covering** any test that supplies the behaviour instead of observing it). **Rank by waste-if-false**, never by how clearly the plan discloses the premise. If empty, write "No unproven premises found" and say what was checked — an empty inventory on a plan that talks to a vendor is itself a finding.

7. **Restart Check** — only if the plan or desc cites a prior failure as its reason for existing; otherwise state that it does not apply and why. **Inherited Lessons** — the desc carries four numbered lessons from the finder's account blocks; one row per lesson: the lesson, and the step in the plan's ordering that satisfies it. Prose acknowledgement satisfies nothing; the sequence does or does not.

8. **Risk items**, each with the fields below. No tables for risk items — sections and subsections.

## Output Format

For each risk found, document these fields:

**Risk** — written as TWO paragraphs, in this order. This is the field readers hit
first, so it carries both registers itself rather than deferring the plain one to
a box further down.

  *Paragraph 1 — plain.* What goes wrong, for someone who has not read this plan
  and does not know this codebase's vocabulary. Self-contained. Every
  project-specific name — a module, class, config key, feature, table — is
  introduced with what it IS before it is used. Not "the resolver drops the
  trailing scope" but "the part that turns a login into a list of permissions
  drops the last permission on the list." State the consequence in terms someone
  would actually notice: what breaks, for whom, when. No file paths, no symbol
  names, no line numbers.

  *Paragraph 2 — precise.* The same risk stated technically: file paths, function
  and class names, config keys, the call path or data flow involved, and the exact
  conditions under which it fires. This is the paragraph the implementer and the
  AI work from.

  Both paragraphs describe the SAME risk at two resolutions. Paragraph 1 is not a
  summary of paragraph 2 — it is a genuine explanation of it. Test: could someone
  who has never opened this repository read paragraph 1 alone and understand what
  would go wrong and why it matters? If not, it has failed, and the usual cause is
  internally-referential shorthand — phrasing that works for whoever has been
  living with this codebase's vocabulary and fails for everyone else.

**Severity** — Low / Medium / High
**Category** — Breaking change / Import error / Circular import / Package discovery / Stale cache / Missing file / Phase ordering / (others as the codebase warrants)
**Impact** — possible effects if this risk materialises
**NoobEng** — for an engineer who reads code fine but does not know THIS system's dynamics. The middle register between the two Risk paragraphs: assumes engineering literacy, assumes no familiarity with this project.
**Affected areas** — which existing features, modules, or endpoints are affected
**Mitigation** (Medium/High only) — three proposals: quick fix, robust fix, long-term fix. Keep the existing "why this is robust:" and "why this is long term effective:" subfields.

  Under EACH of the three proposals — quick, robust and long-term alike — emit this scaffold, boxes unticked and both note sections empty. Do not fill them; a later pass does that.

      - [ ] selected   - [ ] elegant   - [ ] last_resort

      **Note**
      *Why chosen:* —
      *For future:* —


Dont use tabular format,  it should be sections with subsections and detailed enough.

## Guidelines

- Be specific: name the file, the symbol, the request type, the trigger. "This might be slow" is useless; "1,287 queries at a 2 s pace is 45 minutes inside one `session()` block with no reconnect path" is useful.
- Only real risks. Do not pad with Low items that obscure the ones that matter; group trivia into one short Low section.
- Every Medium/High risk gets three actionable mitigations. Where the codebase already has a convention for the problem (`DEFAULT_FETCH_LIMIT`, the sliced beating sleep, `handle_rate_limit`, `batch_callback`), the robust fix should reuse it.
- Question the plan's assumptions; where the plan is right, say so briefly rather than manufacturing doubt.
- Where a near-future requirement is known — the planned measurement feature (`get_group_stats`, the finder's `measure()`), the finder switching over to tgdata, `scoped/9`'s heartbeat coverage work — use it to shape long-term proposals, and say explicitly that they are better *in that future context only*.
