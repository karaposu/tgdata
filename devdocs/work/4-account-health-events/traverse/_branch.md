# Branch: account-health-events

## Source Input

The user's raw request, preserved verbatim (also in `articulate_simple.md`'s `## User Input`):

```text
Issue #4 in karaposu/tgdata, branch feat/4-account-health-events. Write all output to devdocs/work/4-account-health-events/traverse/ (CONTRIBUTING.md §5: traverse output lives in traverse/ on the branch and becomes the raw material for desc.md). The question: what should "report account health states as events" mean inside tgdata, concretely — (1) the state set (ok, waiting, logged out, banned, restricted, no access): which Telegram signals map to each, including waits Telethon sleeps through silently (≤ flood_sleep_threshold, only logged on telethon.client.users) and what "restricted" can mean for an account that only reads, given Telethon 1.40 has no reading-side restriction error and lacks the frozen-account errors; (2) the event's shape — time, account (tgdata only knows a config path and session name), group, the call that caused it (RPCError.request), wait length — and whether "ok" is emitted per call or only on transitions; (3) where events must be emitted: the persistent connection path (which answers a logout with Telethon's interactive start() and a login-code request), the use-and-close client (whose is_user_authorized() turns any RPC error, flood waits included, into 'not authorized'), the fetch loop, discovery's per-item skips, the poll loop that swallows every error, and the real-time updates loop (which disconnects on a logout and re-raises it from run_until_disconnected); (4) callback semantics — exception-safe like heartbeat, or propagating like found_callback/batch_callback; (5) scope: whether fixing the headless-login bug belongs in #4 or only reporting it. Inputs already on the branch: devdocs/work/4-account-health-events/triage.md (the surfacing record). Consumers to keep in view: issues #3 (pause an account on a failed proxy check), #8 (step-by-step login), #9 (per-account budget), #10 (worker that emits health events). Goal for the onward route-field (_branch.md): a stable, decided meaning from which desc.md for #4 can be written.
```

## Articulation Reference

- **File:** `devdocs/work/4-account-health-events/traverse/articulate_simple.md`
- **Itemize count:** 1
- **Per-item identifiers:** `health-events-meaning`
- **Verdict:** HIGH-PROCEED
- **Flagged conditions:** none

## Question

**Literal statement (MultiDepth):** *What should "report account health states as events" mean inside tgdata, concretely — the state set (ok, waiting, logged out, banned, restricted, no access) and which Telegram signals map to each; the event's shape and whether "ok" is emitted per call or only on transitions; where events must be emitted; whether the callback is exception-safe or propagating; and whether fixing the headless-login bug belongs in #4 or is only reported.*

**What kinds of ask this carries (MQ1, verdict axis) — kept open:**
- **decide-vs-map** — a single decided meaning vs. a mapped design space for `desc.md` to settle.
- **granularity** — conceptual meaning vs. a concrete contract (names, fields, signature) vs. an exhaustive class-level error mapping.
- **facet weighting** — five equal facets vs. the state set as the core the other four derive from.

**What it may be trying to accomplish (MQ3, intent axis) — kept open:**
- **observe-only vs. observe-and-act** — events report signals and change nothing, vs. tgdata also acts on some states (stop retrying, refuse the interactive login, stop a poll loop).
- **stream vs. current state** — events per signal or per transition, vs. a queryable current state per account, vs. both.
- **instrument vs. correct** — add events at today's error sites, vs. first correct the sites that misreport.
- **persistent-path logout scope** (reconciled with MQ4) — report only | fix in #4 | split into its own bug.

## Goal

**Deliverable shape (Deconstruct):** a decided meaning-definition for issue #4, from which `desc.md` is written. Its kinds:
- a state taxonomy with definitions;
- a signal-to-state mapping covering error classes, base classes, silent sleeps, authorization checks and the updates loop;
- an event schema: fields, account identity, and ok-semantics;
- an emission-site inventory;
- a callback contract;
- a scope ruling.

Bounds: the tgdata package plus Telethon 1.40's behaviour. Consumers #3, #8, #9 and #10 shape it but are not built. No code, plan or tests.

**Motivations a good answer might serve (MultiDepth WHY axis) — kept open:**
- **measurement** — learn real account limits from test runs.
- **operational visibility** — see bans and logouts without reading logs.
- **protection** — let a caller pause an account, stop retrying, and stop requesting login codes before damage compounds.
- **trustworthiness** — end today's misreports.
- **process** — a meaning stable enough to survive `desc.md`, the plan and the critique.

**Context the answer needs that the input lacks (MQ2) — kept open:**
- *Verdict — is it available?*
  - Telegram's real answer to reads from a restricted or frozen account: unavailable.
  - Consumers' Telethon versions: 1.40 here, 1.44 cited by a consumer.
  - In-process vs. cross-process event consumption (the #10 worker).
  - Whether "account" is 1:1 with a config file.
- *Kinds:* code context (available) · vendor behaviour (unavailable) · consumer requirements (available) · process context (available).
- *Stance:*
  - documentary vs. behavioural evidence;
  - backward compatibility vs. permitted change;
  - observability-first vs. completeness-first.

**What would fail (MQ4, boundary) — kept open:**
- building any of #3/#8/#9/#10 inside #4;
- producing code, a plan or tests instead of a meaning;
- the state-set boundary — Telegram verdicts only, vs. also connectivity loss, a dead proxy, config errors and throwaway-session "not authorized";
- putting internal operational strategy into anything public.

## Considered Articulations

- **Item `health-events-meaning` — what "report account health states as events" should mean in tgdata:**
  1. **Telegram-verdicts-only, report-only.** Six states for Telegram's own verdicts; every error class and silent sleep mapped; an exception-safe event on each state change; control flow untouched; the headless-login bug reported and filed separately.
  2. **Report and correct the two misreports.** The same states; events on every non-ok signal plus "ok" on recovery; account identity from the config; and tgdata fixes the authorization check and stops prompting on a logged-out persistent session.
  3. **Current state plus a stream.** A queryable current state per account (state, since, cause) that also emits change events; connectivity loss and a dead proxy count as a "waiting"-like state.
  4. **Minimal contract.** Fixed state names, one classification of any exception, one callback wherever tgdata already catches or re-raises; "restricted" defined but marked unobservable for readers; nothing else changes.
  5. **Propagating events.** A callback that propagates like `batch_callback`, so a consumer can end a run on a ban or logout; call and group from the error's request; the persistent path raises instead of prompting.

## Scope Check

**Question covers goal.** Deconstruct's bounds (the tgdata package plus Telethon 1.40; consumers shape it but are not built) cover what the Goal asks for: a meaning `desc.md` can be written from. MQ4's exclusions are respected: no consumer is built and no code is produced.

**Specific-vs-pattern.** The input names six emission sites as examples:
- the persistent path;
- the use-and-close client;
- the fetch loop;
- discovery's skips;
- the poll loop;
- the updates loop.

Default: address the **broader pattern** — every place a Telegram signal surfaces in tgdata. `triage.md` already shows more sites than the six named: `get_message_count`, `search_messages`, `download_media_by_id`, `list_groups`, the real-time handler wrapper, and the per-message media failures. The inquiry treats the six as examples of the pattern, not as its edge.
