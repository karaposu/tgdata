# Dynamic critic prompt — PR critic for PR #11 (CONTRIBUTING.md §7.2)

**Subject.** Critique the implemented diff `dev...fix/discovery-flood-threshold` — code, tests and product docs; `devdocs/work/` is excluded — together with the plan that produced it, `step_by_step_impl_plan.md` (critic-folded revision). Judge it against the codebase it lands in, with Telethon 1.45.0 in `.venv`.

Read it the way a stranger would: owing nothing to the plan, but able to tell a deviation from a decision because the plan is in view. Ultrathink.

**Rules of evidence (§7.5).**
- Read the touched files in full, not only the diff.
- Never characterise code from a grep.
- Write and run a probe for anything that rests on behaviour, and quote its output.
- A Medium stands only on a line of code or a probe.
- Thresholds (§7.3): any High or Medium rejects the PR; Low only merges, with the Lows recorded and consciously left.

## What the diff does, so you know where to look

**`tgdata/connection_engine.py`:**
- A module-level context variable holds `(owner task, seconds)`.
- A mixin `_PerCallFloodThreshold` overrides Telethon's `flood_sleep_threshold` property and `__call__`, so `client(request, flood_sleep_threshold=N)` works as Telethon documents. Telethon itself ignores the value.
- `_client_class(base)` builds the class at call time from whatever `connection_engine.TelegramClient` is, and `_new_client()` — the single factory for every client — returns it.

**`tgdata/discovery_engine.py`:** `_WAIT_ERRORS`, Telethon's four wait errors built version-robustly, replaces `FloodWaitError` at five catch sites, plus docstrings.

**`tgdata/tgdata.py`, `README.md` and `devdocs/guides/group_discovery.md`:** wording about discovery's waits.

**`tgdata/smoke_tests/test_14_flood_threshold.py`:** eleven offline checks that drive Telethon's real request code with a scripted connection.

## Questions, by concept

### 1. The override's correctness under asyncio
Probe what the tests do not:
- many concurrent requests on one client, mixing the option and no option;
- cancellation in the middle of a request that carries the option — is the variable restored, and is the task's next plain request normal?
- `asyncio.wait_for` and `gather` wrapping the request;
- reads of the property outside a running loop.

Does any path leave a stale value or leak it across tasks or clients? Does the owner-task check hold when Telethon's request code runs in a task other than the one that entered `__call__`?

### 2. Every client path, unchanged where it should be
- The persistent client, `ConnectionPool` connections, `ephemeral_client`, login through Telethon's `start()`, the real-time listener, and the proxy and device-identity arguments.
- `device_identity()`'s probe client.

Is anything that does not pass the option now behaving differently — timing, exceptions, class identity, metaclass, repr?

### 3. Discovery after the change, call site by call site
For each of the five catch sites and each caller of `_request` and `_resolve`, establish by reading the code and by probe what a short wait and a long wait of each of the four kinds now do. Compare with before.

Look for:
- retry loops that can no longer end;
- budget and accounting effects (`max_resolve`, the "resolutions spent" log line);
- log-level changes users will see;
- any path where a wait still escapes as a raw exception, or is silently swallowed.

### 4. The docs against the code
Read every changed sentence against the code paths it describes. Are the named silent paths the only ones (post reading, the dialog sync)? Do the guide's own conventions — for example "verified live … unless marked otherwise" — still hold for the new sentences?

### 5. The tests as evidence
- Do the eleven checks observe behaviour or supply it?
- Which would fail on a real regression, and which could pass while broken?
- Is global state always restored?
- Do they run on the declared Python range, and in which environments could they misbehave — Windows temp files, slow machines and timing?

### 6. Deviation versus decision
Compare the diff with the plan's steps and with `merge-check.md`'s list of deviations. Is any deviation unlisted? Does any listed deviation hide a real change?

## Required output

Create `pr-critic.md` in the same directory as the implementation plan — not `critic.md`, which holds the pre-implementation critique. The output file has a high-level summary on top.

**Frontmatter first.** Read both fields from session context; write `unknown` rather than guessing:

```yaml
---
model: [model id from session context, e.g., claude-opus-4-7[1m]; "unknown" if not derivable]
effort: [effort setting from session context, e.g., max; "unknown" if not derivable]
---
```

**Then the document-level verdict**, immediately after the frontmatter and above the high-level summary. Exactly one of:
1. **IMPLEMENT AS WRITTEN**
2. **IMPLEMENT AFTER FOLDING THESE IN**
3. **REORDER — TEST BEFORE BUILD**
4. **DO NOT IMPLEMENT — MEANING GAP**, or its variant **WRONG LAYER**

For this gate, verdict 1 with Low findings only means "merges". Any Medium or High means rejected under §7.3, whatever the verdict says about shape.

**Directly under the verdict**, on verdicts 1–3:

```
Falsifier: [the cheapest observation that would flip this verdict to DO NOT IMPLEMENT]
Affordable now: yes | no — [cost]
```

If it is affordable now and not yet observed, run it before writing the verdict.

**Premise Inventory** after the summary: hedged premises and vendor or stochastic claims, each with first dependent step, waste if false, test scheduled at, cheapest earlier test, and coverage — flagging non-covering tests. Rank by waste-if-false. If none, write "No unproven premises found" and what was checked.

**Restart Check**, one row per failure the desc cites: failure | established mechanism | design element, now with the evidence that it is addressed.

**Inherited Lessons**, one row per lesson: the lesson, and where the implemented sequence satisfies it.

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
