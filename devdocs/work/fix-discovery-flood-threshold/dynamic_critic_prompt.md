# Dynamic critic prompt — make Telethon's per-request flood-wait threshold work in tgdata

Critique `devdocs/work/fix-discovery-flood-threshold/step_by_step_impl_plan.md` against its `desc.md` and the codebase, the way a senior engineer who owns tgdata's connection layer would. Ultrathink. Find the errors, compatibility issues, risks and conflicts that would actually matter. Do not pad with noise, and do not just patch the plan: question whether its assumptions are correct.

## What this change is, so you know where to look

tgdata wraps Telethon, a Telegram client library. Every Telegram client tgdata creates — the persistent one, each pool connection, every use-and-close lookup — is built by one factory, `ConnectionEngine._new_client()` in `tgdata/connection_engine.py`, called "the one door".

Telethon documents `client(request, flood_sleep_threshold=N)` as a per-request override of how long a flood wait it will sleep through silently. In every release from 1.33.1 to 1.45.0 it ignores the value:
- `UserMethods.__call__` drops it;
- `_call` decides whether to sleep by reading the client-wide `flood_sleep_threshold` property.

tgdata's discovery relies on the override in two places, `DiscoveryEngine._request` and `DiscoveryEngine._resolve`, so waits of 60 s or less are slept silently today. Discovery's documented guarantees are false for those waits: heartbeat ticks during waits, `max_flood_wait`, and "a wait on a lookup is never slept through".

The plan applies a mixin to the client class at build time. The mixin:
- overrides the property, returning a per-call value held in a context variable together with the task that set it;
- overrides `__call__`, setting that value for the duration of one request.

Discovery's code is unchanged. Offline tests drive Telethon's real request code with a fake connection, and the docs are made exact.

## Questions to answer, by concept

### 1. Telethon's request path — is the premise complete?
- Read `telethon/client/users.py` (`__call__`, `_call`) and `telethon/client/telegrambaseclient.py` (the property and setter, `__init__`, `connect`, `_switch_dc`, exported senders) in the installed Telethon (1.45.0).
- Does anything else in Telethon sleep on a flood wait without consulting the property?
- Does anything call `_call` without going through `__call__`, and does that matter?
- Is anything relied on that is private, and how would a future 1.x release break it — loudly or silently?
- Does the plan's canary actually catch the silent case?
- The declared range is `Telethon>=1.33,<2.0`. Is the mechanism proven across that range, or only on 1.45.0? What happens to users on older 1.x releases if it does not hold there?

### 2. The per-call override's scope — exactly one request, nothing else
- Concurrency: tgdata shares one persistent client across concurrent operations (fetch, discovery, real-time handlers). Can a per-call value leak into another task's request?
- Background tasks: Telethon starts tasks inside `connect()` — the updates loop and keepalive — and can reconnect mid-request on a data-center switch. Can they inherit the value?
- Nested requests: a request can trigger other requests in the same task, for example resolving an input entity. Which threshold should those get, and which do they get under the plan? Compare with what Telethon documents ("for this request").
- Cancellation, `asyncio.wait_for`, `gather`, and reads of the property outside a running loop: is the value always restored, and is `asyncio.current_task()` always meaningful where it is called?

### 3. The one door and its users
- Every path that builds a client must get the behaviour, and nothing else may change: proxy and device-identity kwargs, `ephemeral_client`, `get_client` / `_authenticate`, `ConnectionPool`, the `device_identity()` probe client.
- tgdata's tests replace `connection_engine.TelegramClient` with stand-ins (test_13). Does build-time subclassing keep them meaningful?
- What if downstream code patches that name with something that is not a class, such as a mock?
- `isinstance` checks, `repr`, class identity, `functools.lru_cache` growth, and any code that compares classes.
- User code that obtains a tgdata client and passes `flood_sleep_threshold` itself: is this an API-contract change, and is it documented?

### 4. Discovery's behaviour after the fix — what users will see
- Trace every caller of `_request` and `_resolve` — search, similar, linked, discover, seeds, link resolution, the source of `linked_groups`. For each, what does a 1–60 s wait now do?
  - Sleep with heartbeat ticks and retry?
  - Skip a seed?
  - Stop link resolution?
  - Raise `DiscoveryInterrupted`?
  - Is anything left uncaught?
- Which of these changes a result or an exception a caller sees today? Are they all intended by the design the docs describe? Is any of them too harsh, for example `linked_groups` raising on a 2-second lookup wait?
- Telethon records waits per request type (`_flood_waited_requests`). After discovery sleeps a wait itself, does the retry pass Telethon's pre-check cleanly? Can discovery and a concurrent fetch of the same request type interfere?
- Is any wait still silent inside discovery (post reading through `iter_messages`, the dialog-sync fallback), and do the docs say so?

### 5. Docs that must end up true
- `desc.md` success criterion 10 requires every docstring, comment, README sentence and guide sentence about discovery's waits to match the behaviour.
- Search README.md, `devdocs/guides/group_discovery.md` (including its troubleshooting table), the `DiscoveryInterrupted` docstring, the `TgData` facade docstrings in `tgdata/tgdata.py`, and `discovery_engine.py`.
- Does Step 4 list every statement that changes meaning, or only some? Name any it misses.

### 6. Tests — do they observe the behaviour or supply it?
- The fake connection replaces Telegram's reply, not Telethon's logic. Say which premises the offline tests cover, and which they cannot: a live FLOOD_WAIT through `MTProtoSender`.
- Are the timing assertions robust?
- Do the discovery-level tests run the real `DiscoveryEngine` code paths?
- Does TEST 6 restore global state on failure?
- Would the canary fail on the right future change and pass on harmless ones, for example Telethon fixing `__call__` itself?

### 7. Process and working tree
- No GitHub issue exists, and the branch has no issue number. Which CONTRIBUTING steps (issue, merge-check, PR) does that defer, and does the plan say so?
- The working tree holds an unrelated uncommitted edit in the guide, which Step 4 sets aside with `git stash`. Can that lose it, commit it, or pop the wrong stash?
- Cross-feature: issue #4's traverse finding, on another branch, states that discovery's short waits are invisible. What becomes stale when this merges?

### 8. Architecture — is this the right shape?
- Compare with the alternatives:
  - temporarily setting the client-wide threshold, which is shared and racy;
  - a dedicated discovery client, which is heavier;
  - a global monkeypatch of Telethon, which the desc forbids;
  - raising the Telethon floor.
- Say whether the mixin should become tgdata's general home for Telethon-facing behaviour. Issue #4 will need connect-time context handling on the same clients. State plainly that this is better only in the future context.

Also check whether each step is detailed enough for the complexity of the code it touches. A step that is too high-level for its code is a Medium risk.

## Required output

Create a `critic.md` file in the same directory as the implementation plan. The output file has a high-level summary on top.

**Frontmatter first.** It records what produced the critique; read both fields from session context at write time and write `unknown` rather than omitting or guessing:

```yaml
---
model: [model id from session context, e.g., claude-opus-4-7[1m]; "unknown" if not derivable]
effort: [effort setting from session context, e.g., max; "unknown" if not derivable]
---
```

**Then the document-level verdict**, immediately after the frontmatter and above the high-level summary. Exactly one of:
1. **IMPLEMENT AS WRITTEN** — no changes needed.
2. **IMPLEMENT AFTER FOLDING THESE IN** — the plan's shape survives; the findings below get absorbed into it.
3. **REORDER — TEST BEFORE BUILD** — the plan builds on an untested premise before testing it. Name the experiment, its cost, the step it must precede, and which result converts this to verdict 4.
4. **DO NOT IMPLEMENT — MEANING GAP** — the plan rests on a wrong or unestablished premise, so its steps would be rewritten, not adjusted. Variant: **DO NOT IMPLEMENT — WRONG LAYER**, when the plan cites failures it does not address.

The verdict is about the plan's shape and sequence, not the count or severity of findings.

**Directly under the verdict**, on verdicts 1, 2 and 3:

```
Falsifier: [the cheapest observation that would flip this verdict to DO NOT IMPLEMENT]
Affordable now: yes | no — [cost: time, money, access]
```

If the falsifier is affordable now and the verdict is 1 or 2, the verdict is wrong: it is REORDER, and the falsifier is the experiment. On verdict 4 the line reads "—".

**Premise Inventory**, immediately after the high-level summary and before any risk item. Compute it first: it can set the verdict on its own.
- **What goes in:** any premise the plan or desc hedges or marks unproven, and any claim about how a vendor service (Telegram) or other stochastic component behaves.
- **Per premise:**
  - **Premise**
  - **First dependent step**
  - **Waste if false**
  - **Test scheduled at**
  - **Cheapest earlier test**, with its cost; "none" must be argued
  - **Coverage** — flag as **non-covering** any test that supplies the behaviour rather than observing it, such as a fake connection returning the wanted error
- **Rank** by waste-if-false.
- **Rule:** a premise with an affordable cheapest-earlier-test, scheduled after its first dependent step, makes the verdict REORDER.
- **If empty**, write "No unproven premises found" and say what was checked.

**Restart Check.** The desc cites observed failures as its reason for existing. Give one row per failure: observed failure | established mechanism | design element that addresses it. An empty cell is a finding. Most cells empty means DO NOT IMPLEMENT — WRONG LAYER.

**Inherited Lessons.** The desc carries prior conclusions — for example, lookup waits escalate, so a lookup wait is never slept through. Give one row per lesson: the lesson, and the step in the plan's ordering that satisfies it. Prose acknowledgement satisfies nothing; the sequence does or does not.

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
