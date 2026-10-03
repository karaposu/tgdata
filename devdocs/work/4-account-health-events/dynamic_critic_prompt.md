# Dynamic critic prompt — issue #4, account health events (CONTRIBUTING step 3)

Critique `devdocs/work/4-account-health-events/plan.md` against `desc.md` in the same folder, and against the code on `feat/4-account-health-events`, with Telethon 1.45.0 in `.venv`. Do it as the owner of tgdata's connection layer and its public API. Ultrathink.

Find what would actually go wrong, not noise. Question the plan's assumptions rather than only patching steps. Read the touched files in full. For anything about behaviour — asyncio, contextvars, logging, Telethon's request path, `contextlib` — run a probe and quote its output.

## What the plan builds, so you know where to look

**A new module, `tgdata/health.py`, holding:**
- a classifier from exceptions, including tgdata's wrappers, to verdict, scope, error name, wait length and request type;
- a per-`TgData` monitor with a ledger, "ok" recovery, safe callback delivery, a log mirror and a snapshot;
- a context variable marking the public call in progress;
- a logging filter that turns Telethon's silent sleeps into events.

**Wiring:**
- a decorator on the public `TgData` methods that talk to Telegram;
- one-line `health.report()` calls at the engines' handled waits and swallow sites;
- `health_check()["health"]`.

**Two fixes the maintainer added:** `poll_for_messages` stops on failures that retrying cannot fix and propagates callback errors, and `validate_connection()` logs its classified reason.

## Questions, by concept

### 1. The reporting path must never change what the caller sees
- The boundary classifies and emits inside the exception path of an async context manager, and recovers on the success path.
- Prove with a probe that the re-raised exception is the same object, with its traceback intact.
- What happens when the health code itself raises there, or inside `health.report()` at an engine swallow site? Can a bug in reporting turn a success into an exception, replace the caller's exception, or end a loop that was designed to keep going?

### 2. Attribution over time — which call does an event belong to?
- The call context lives in a context variable. Every task created during a call inherits it: Telethon's updates loop and keepalive, the tasks that run event handlers, user tasks.
- The plan marks a call inactive when it ends. What about calls that never end, or last for hours — `run_with_event_loop`, `poll_for_messages`?
- Probe whether a task created during a still-active call is attributed to that call, and what that does to the open-wait ledger and to recovery.

### 3. Recovery — can "ok" be false?
Trace each rule against every path that swallows a verdict and then returns normally: discovery's seed and link skips, polling, `validate_connection`. Can a call that itself reported a verdict count as recovering from it?

Check group attribution as well:
- for verdicts about one item inside a multi-item call, such as a seed or a link in discovery;
- for `GroupAccessError` raised from the dialog-sync fallback inside discovery.

### 4. Counted once, across nesting
- `poll_for_messages` calls `get_messages`, which goes through a boundary of its own.
- The fetch loop reports each handled wait and then gives up with `RuntimeError(...) from e`.
- Discovery reports below `max_flood_wait` and raises above it.

Verify that each occurrence yields exactly one event, and that the poll fix still sees verdicts the inner boundary already marked.

### 5. Silent-sleep capture as a process-wide side effect
- Many `TgData` instances share one process, possibly with raw Telethon clients too.
- The sentinel level, the re-check at each boundary, `dictConfig`, `logging.disable`.
- Sync delivery from inside Telethon's request, and async callbacks scheduled from a filter.

What can leak, stall, recurse or be lost?

### 6. The polling and `validate_connection` fixes as public behaviour changes
- Which callers break, and is the break the intended one?
- Is the terminal/transient split right for every error polling can see — `ValueError` from Telethon's lookups, proxy errors, unknown Telegram errors?
- Callback errors now propagate after `after_id` has already advanced: what does a caller lose or duplicate?
- Does `desc.md` still describe the product, given these fixes act where the desc said "reports and never acts"?

### 7. Plan detail against code complexity
- Name any step too high-level for its code. Examples:
  - how handled waits enter a call's waited set;
  - what `group` a swallowed per-item verdict carries;
  - how the decorator binds arguments for every decorated signature.
- Check that the plan's list of decorated methods, report sites and moved definitions matches the code.

### 8. Compatibility
- Python 3.7+ and Telethon 1.33–1.45.
- Import cycles between `health`, the engines and the facade.
- Public API additions.
- JSON-readiness of events and the snapshot.
- Multiple accounts per process (#10).

## Required output

Create a `critic.md` file in the same directory as the implementation plan. The output file has a high-level summary on top.

**Frontmatter first.** Read both fields from session context; write `unknown` rather than guessing:

```yaml
---
model: [model id from session context, e.g., claude-opus-4-7[1m]; "unknown" if not derivable]
effort: [effort setting from session context, e.g., max; "unknown" if not derivable]
---
```

**Then the document-level verdict**, immediately after the frontmatter and above the high-level summary. Exactly one of:
1. **IMPLEMENT AS WRITTEN** — no changes needed.
2. **IMPLEMENT AFTER FOLDING THESE IN** — the plan's shape survives; the findings get absorbed into it.
3. **REORDER — TEST BEFORE BUILD** — the plan builds on an untested premise before testing it. Name the experiment, its cost, the step it must precede, and the result that converts this to verdict 4.
4. **DO NOT IMPLEMENT — MEANING GAP**, or its variant **WRONG LAYER** — the plan rests on a wrong or unestablished premise, or does not address the failures it cites.

The verdict judges shape and sequence, not the count of findings.

**Directly under the verdict**, on verdicts 1–3:

```
Falsifier: [the cheapest observation that would flip this verdict to DO NOT IMPLEMENT]
Affordable now: yes | no — [cost: time, money, access]
```

If it is affordable now and the verdict is 1 or 2, the verdict is wrong: it is REORDER, and the falsifier is the experiment. On verdict 4 the line reads "—".

**Premise Inventory**, after the summary and before any risk. It covers hedged premises and claims about vendor or stochastic behaviour, each with first dependent step, waste if false, test scheduled at, cheapest earlier test with its cost, and coverage — flagging non-covering tests. Rank by waste-if-false. An affordable earlier test scheduled after its first dependent step makes the verdict REORDER. If empty, write "No unproven premises found" and what was checked.

**Restart Check**, one row per failure the desc cites: observed failure | established mechanism | design element that addresses it. An empty cell is a finding; mostly empty means WRONG LAYER.

**Inherited Lessons**, one row per lesson or prior conclusion the desc carries: the lesson, and the step in the plan's ordering that satisfies it. Prose acknowledgement satisfies nothing.

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
