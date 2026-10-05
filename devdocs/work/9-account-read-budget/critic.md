---
model: unknown
effort: unknown
---

**Verdict: IMPLEMENT AFTER FOLDING THESE IN**

Falsifier: a supported live Telegram read returns more message slots than its
explicit request bound, preventing the pre-dispatch claim from bounding the
actual response.
Affordable now: no — needs a live authenticated account. The approved run is
offline. The adapter must record an oversized response and stop if it occurs;
no claim of a Telegram-safe rate or live response conformance is made.

# Critique — per-account read budget, plan revision 1

Reviewed in this warmed session against `4a0951a`, its description, the core
readers/factory and Telethon 1.45.0 request, iterator and identity code. No
subagent was used. There is one Medium finding; the architecture and six-step
sequence survive. No additional risk was added merely to fill a checklist.

## High-level summary

The plan chooses the necessary boundary: reserve before each sender dispatch,
not after rows are returned and not only around the outer RPC call. This also
covers Telethon retries. SQLite's transaction probe establishes serialization
across processes, and the actual iterator probe establishes both small reverse
pages and resumed full-size pages without changing the offset window.

The unresolved implementation detail is identity authority. Step 2 would use
Telethon's cached self ID whenever present, but this can differ from the
current authenticated self response. The wrong account could be charged, or
a stricter account could spend another account's larger allowance. Verify the
self response before each budgeted send instead of treating the cache as proof.

## Premise inventory

1. **The wire request bounds returned message slots.** First dependency: the
   admission ledger/adapter; failure changes the meaning of a hard ceiling.
   API documentation defines the bounds, while live behavior is unverified.
   Scripted replies are non-covering for the server. A live comparison is the
   cheapest decisive observation but requires an authenticated account. The
   planned oversized-response failure path remains required.
2. **The account used for billing is the authenticated one.** First dependency:
   Step 2. Failure misallocates every charge. A cheap real-SDK probe now shows
   `_self_id=111` while get_me returns 222, and get_me does not overwrite a
   nonempty cached ID. The planned cache-first choice is refuted. The robust
   correction below uses the response, whose decoding is observed; the probe
   supplies the server reply and does not attest to a live account.
3. **Each actual dispatch reaches the admission point, retries included.**
   First dependency: Step 2. The real UserMethods._call was run with an async
   sender proxy. A five-unit failed request on a seven-unit allowance reached
   the sender once; its retry was rejected before a second send. The request
   loop itself was real; the server error was supplied. This runs before build.
4. **Pagination can shrink then grow without cursor loss.** First dependency:
   Step 2. The real iterator sent 37/-37 from 101 and later 100/-100 from 138.
   Its original left and add_offset were restored between calls. Scripted
   messages do not prove Telegram's selection, but the actual outgoing
   parameters and iterator ordering were observed before planning.
5. **Concurrent claims can be serialized durably.** First dependency: Step 1.
   Forty claims in four real processes against one SQLite file admitted 98 of
   100 units and retained precisely 98 after reopening. This observes the real
   storage/transaction component, not a fake ledger.

No affordable earlier experiment is deferred behind implementation. The
remaining server premise is explicitly outside offline coverage.

## Restart check and inherited lessons

This adds a missing capability, rather than restarting after a prior incident.
The relevant inherited lessons are:
- #5's load/save protocol is not an atomic quota store; a separate transaction
  ledger is justified and must not be implemented as blind whole-record saves.
- A label/session suffix is not an account identity; Step 2 must strengthen
  this further by verifying self responses rather than trusting cached IDs.
- Real SDK control flow matters: sender retries and reverse paging both have
  pre-build probes and dedicated implementation tests planned.
- Failures must be observable without misclassifying local policy as a Telegram
  ban/wait: budget exceptions suppress incidental contexts and polling stops.
- Existing successful return types remain; partial-result reporting is added
  only to an explicit interruption path.

## Probe output

`probe_budget_seams.py` uses synthetic credentials and blocks Telegram sockets.

```text
Paging: real iterator sent limit=37, add_offset=-37, offset_id=101; yielded 37 ordered messages
Paging: original 2,000-message limit retained; next page stopped before send
Paging: after renewed allowance, the same iterator sent 100/-100 from 138 without a gap
Identity: cached self ID=111; authenticated get_me response=222; cache alone is not authority
Dispatch: real Telethon retry was denied before its second send; first failed attempt remains charged
SQLite: 40 competing claims across 4 processes charged 98/100, exactly matching accepted claims
SQLite: usage survived closing and reopening all connections
```

## Risk 1 — A cached account ID can charge another account's budget

A client can restore account information that no longer matches the login it
is actually using. If the allowance is selected from that cached information,
reads by one account spend another account's budget. An account with a small
allowance may therefore read against a larger one, while usage reports blame
the wrong account.

Plan Step 2 resolves identity from `_self_id` and calls get_me only when the
cache is empty. Telethon's `get_me(input_peer=False)` asks for InputUserSelf,
but only initializes `_mb_entity_cache.self_id` if it is empty. The probe
retains cached 111 while the authenticated response is 222. Stored-session
identity rows and current authentication are separate inputs; the description
requires the actual Telegram account, not either cache or session name.

**Severity:** Medium
**Category:** accounting integrity / identity authority
**Impact:** per-account ceilings and usage attribution can be wrong.
**NoobEng:** a cache is a performance hint, not evidence of which account the
server currently authenticates. The budget needs the self response's ID.
**Affected areas:** Step 2 identity/dispatch helper, Step 3 status method,
Step 4 account-sharing and identity tests.

### Mitigation — Quick

Clear the cached self ID before each read so the existing fallback runs.
This mutates unrelated SDK state, and other code can refill it; it treats the
cache as the problem instead of choosing an authoritative input.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Read get_me(input_peer=False) before every budgeted send and use the returned
ID without trusting or clearing the cache. The sender proxy returns a coroutine
that verifies identity, reserves synchronously, then forwards to the real
sender without another await between reservation and enqueue. Retries perform
this check again. Page sizing/status also use a self response. Do not add a
long-lived identity cache. When get_me returns None, ask GetState to preserve
Telegram's actual logout/ban exception; if identity is still unavailable,
raise a local budget error without dispatching the message read.

**Why this is robust:** every budgeted send uses fresh authenticated identity,
including stale caches and a relogin during earlier waits; no unrelated SDK
cache or login policy needs to change. The added self lookups are metadata and
must be documented and tested.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Phase 3: the budget adapter is the only new accounting authority;
there is no separate existing budget module to generalize. The same fresh-self
lookup serves dispatch and page/status queries. This closes the identity error
without changing login state, so robust has the best reach for its extent.
*For future:* —

### Mitigation — Long-term

Introduce an explicit verified account context tied to login transitions and
session ownership across the connection engine and future stepwise-login API.

**Why this is long term effective:** all future consumers could share one
well-defined identity lifecycle instead of independently interpreting caches.
It requires changing login/connection contracts beyond this task.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit with #8's stepwise login/account-lifecycle work. It is a
larger, separate contract; the fresh lookup remains useful, so it is not a
prerequisite for this quota feature.

## Scope and execution boundaries

Metadata/previews, passive updates and different ledger files are explicitly
outside the described allowance. The implementation must not market that as
a limit on every Telegram byte/request. Synchronous short SQLite transactions
and their failure behavior must be documented. These are stated contract
boundaries, not proof that chosen quotas prevent Telegram restrictions.

No implementation execution blocker is open. Merge/deployment and live testing
remain outside this run. Model/effort are unknown rather than invented.
