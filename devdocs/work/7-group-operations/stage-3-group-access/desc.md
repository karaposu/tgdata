---
model: gpt-6-astra
effort: max
---
# #7 Stage3 — Group lookup and access checks

> Session warm at `30ba7062b0d7254b5695c4a0d727a4c8242e3f25`, retained from this
> session's Stage1/Stage2 implementation, reviews and merges. Factory, verified
> lifetime, health, budget, sessions and facade are retained/refreshed; current
> group models, SDK1.45/layer229 shapes and original PR16 failure evidence were
> read for this stage. No new archaeology refresh is claimed. See triage.md.

Source: issue7, the user's explicit Stage3/task-impl request in source-input.md,
and the completed bounded contract inquiry at traverse/finding.md (`f174e90`).
The earlier broad implementation is reference evidence, not the code to resume.

## Problem Statement

Callers still assemble their own “what group is this?” and “can this account read
it?” operations. Stages1 and2 now provide the verified temporary client and account-
owned health needed to expose those operations correctly.

Group metadata, membership and readable history are different facts. Invite previews
can omit a usable peer or provide temporary access. A failed request, exhausted budget
or cache error must not be mistaken for a negative group observation. The old broad
attempt also showed that generic exception translation can lose real server errors.

## User Value Proposition

A caller can obtain a group's current details or make a small read-only access check
under an explicitly expected Telegram account, with a portable result it can retain
after the temporary client closes. The access result includes available lookup details,
so the caller need not repeat the lookup or reconstruct preview qualifications.

## Success Criteria

1. Two public async operations, lookup_group and check_group_access, require the
   expected numeric account ID. Each uses one existing owned operation, preserving
   proxy/device/session policy, authentication refusal, task lifetime and cleanup.
   No persistent current_group/client selection or interactive login is introduced.
2. Supported handles, Telegram username/invite links and deterministic numeric group
   references have an explicit bounded grammar. Marked basic-group IDs can resolve
   directly; channels need an exact cached hash; a bare ID requires one cached group
   namespace. No phone/self alias, arbitrary collision selection, join or dialog sweep.
3. Fresh resolution checks typed target identity and projects current SDK group forms
   into separate immutable GroupMetadata/GroupLookup values. Unknown IDs/membership
   and available preview/request/payment hints remain explicit. Existing GroupInfo
   and discovery output contracts stay unchanged.
4. Every result includes the verified owner and a safe target correlation label.
   A plain dictionary conversion contains portable values and UTC expiry text. Raw
   clients, SDK entities and transport access hashes are not returned as result fields;
   an invite's raw token is not used as its result/health label.
5. If resolution completes with a usable peer, access checking makes one logical
   GetHistory(limit=1, hash=0) request through normal read-budget admission. A valid
   history response, including an empty one, yields readable. Validate response shape
   and any supplied message peer before claiming success; malformed/cache-only replies
   cannot produce readable or recover group health.
6. A classified group-access RPC refusal yields denied with Telegram's reason and
   whatever lookup was completed. A recognized completed lookup without a usable
   peer yields unprobed. Authentication/identity, waits, network/server, budget and
   local cache/storage failures remain errors with their original operational meaning.
   No broad native-exception translation or catch-all false/unknown fallback.
7. GroupAccess retains the full optional GroupLookup, including preview expiry and
   uncertain hints; derived group/member/readable views cannot disagree with it.
   Readability is an observation, not membership, a join authorization, a promise of
   complete history or a guarantee that later reads will work.
8. The existing owned-health path records actual failures under the verified owner.
   Only a validated history result gives its explicit group-access confirmation;
   lookup/unprobed/failed/cancelled work cannot manufacture group recovery. Existing
   owner/order/handle-validity guards and post-cleanup notifications remain intact.
9. Offline tests use actual Telethon1.45.0 dispatch/serialization/error construction,
   the real facade and merged foundations, real session backends and SQLite budgets.
   They force concurrent/cancelled/failing paths, malformed/no-peer replies and old
   error/owner counterexamples. Synthetic replies are not called live-server proof.
10. Document the known SDK file-cache limitation for a hashless CommunityForbidden,
    and characterize it through the public path: default SQLite may fail before the
    source returns; that local error propagates without a fake access result. No silent
    vendor/session workaround or universal backend-success claim.
11. Align dependency metadata with the selected1.45 API, document accepted inputs,
    result/error behavior and costs, and pass the existing supported offline suites,
    examples and compatibility grammar checks before checkpointing the implementation.

## Scope Boundaries

This is read-only Stage3. Joining, join allowance, account routing, login UX,
scheduling, new persistence, dialog enumeration, a permission matrix, canonical
health-alias migration and a global legacy-health rewrite are excluded. A separate
stateful group engine is unnecessary; the selected domain module consumes existing
ownership/lifetime rather than adding its own.

Use Telethon1.45.0; no1.33 testing or compatibility layer. Source failures may prevent
an observation, including the measured current SDK cache edge. No live Telegram
requests, new account login, membership change, PR/merge gate or deployment is part
of this implementation run. Keep duncan, the stray guide and original untracked files
out of commits. Work-folder documents stay on the archive branch at any later merge.

## Priority Level

**Medium / P2 within #7.** This delivers the read-only public group operations and
removes consumer glue now that the ownership prerequisites are merged. It does not
justify expanding into the later mutation or account-pool stages.

## Known Blockers

None open for planning or offline implementation. Four executed component probe
groups establish available local mechanisms and the explicit SDK cache limitation;
that limitation is preserved as an error, not assumed solved. The later plan critic
must challenge the composed public-path assumptions before code depends on them.
Live server qualification needs a separately designated setup and is not claimed
by this delivery. No missing account or unmerged #17 dependency blocks local work.
