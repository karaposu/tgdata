---
model: unknown
effort: unknown
---

# #7 — group lookup, access checks and joining

> Session warm at `45bab7172621f576fa5e4b3265f87ec20da04fd5` (2026-10-05)
> by retained full-source work on #5/#9/#6 and refreshed group, connection,
> session, budget, health and installed-SDK paths for #7. The contemporaneous
> record is `triage.md` in `15edbe0`; this required top-of-description line was
> restored during the merge check. No new warming-skill run is claimed, and
> `devdocs/archaeology/` was left unchanged under CONTRIBUTING §4.1's retained
> session / warming-by-reading provision.

## Problem Statement

Callers can discover groups and read messages, but have to assemble their own
short-lived lookup and account-readiness checks. tgdata provides no group-joining
operation. Group metadata, membership and readable history are different facts;
private invite previews and pending join requests make a single Boolean misleading.

Source: [issue #7](https://github.com/karaposu/tgdata/issues/7), qualified by the
committed [design finding](traverse/finding.md). The request is adopted as a
feature-heavy task. No duplicate issue or incompatible existing group API was found.

## User Value Proposition

A caller can fill a group's real details, ask whether its assigned account can
read it, and explicitly request a join through the same authenticated account
controls. Portable outcomes distinguish ready-to-read, unknown/unprobed access,
approval requested and interaction required. A durable join-attempt allowance
limits requests across short-lived clients and process restarts.

## Success Criteria

1. Three public asynchronous operations use one existing ephemeral client each,
   without interactive login or changing the caller's persistent current group.
2. Lookup accepts supported handles and Telegram invite links, returns available
   name/handle/type, and preserves unknown IDs/membership and temporary expiry.
   Known numeric group peers are also useful for lookup/access. No lookup joins.
3. Access checking issues one logical history request with limit1 for an available
   peer. Telethon may retry it; each actual send obeys the existing read budget.
   It returns readable, denied (actual group-access error), or unprobed
   (no peer); auth, network and local policy failures retain their own meaning.
   The history read obeys the existing read budget.
4. Join by handle/invite observes existing membership before a mutation, then
   distinguishes acknowledged joining, already joined, approval submitted,
   required interaction and payment required. It never automatically completes
   webviews/payments. Acknowledgment does not require a fallible second lookup.
5. Joining requires an explicit per-account allowance. Every admitted actual join
   send, including SDK retries and uncertain/cancelled outcomes, costs one.
   No successful-completion-only accounting or automatic uncertainty refund.
6. The allowance is durable and atomic across processes sharing its SQLite file.
   [ASSUMPTION] Use a rolling 24-hour window, consistent with ReadBudget, with
   caller-selected integer limits and no invented safe numeric default. Each
   send uses a freshly authenticated account ID, not session name or cached self.
7. Result dictionaries contain portable values. The existing GroupInfo discovery
   API remains intact. Available nested join-update group entities are retained
   locally without requiring post-ack network enrichment.
8. The client factory preserves proxy, device, stored-session, read-budget and
   health behavior. Metadata/join outcomes do not clear history-access denial;
   successful access reads can. Health labels/results do not expose invite tokens.
   Local validation/storage errors cannot inherit unrelated Telegram health.
9. Offline tests exercise real Telethon 1.45.0 dispatch/serialization and real
   SQLite transactions/concurrency, plus public lifecycle/failure paths. Existing
   supported offline regressions pass; any live skips are stated explicitly.
10. Public documentation explains accepted references, observation outcomes,
    allowance configuration/units, conservative attempts, shared-file coordination,
    failure behavior and the absence of a Telegram restriction-prevention guarantee.

## Scope Boundaries

No live Telegram joins in this coding run. No paid-entry or webview execution,
posting-rights census, account-login workflow, worker implementation, distributed
quota provider, general policy-engine refactor or #3 proxy testing. No changes to
legacy discovery's non-joining behavior or GroupInfo shape. Other Telegram clients,
independent database files and delayed approval decisions are outside this local
admission guarantee. Telethon target is 1.45.0 only. `duncan/` is excluded from
commits; merge requires the user's separate go-ahead.

## Priority Level

**Medium (P2).** It completes the group-operation prerequisite for worker #10
and removes repeated consumer glue, without being a production outage.

## Known Blockers

None for planning or offline implementation. The installed SDK seam probe has
confirmed its wrapped outcomes and retry behavior. Live acceptance needs
explicit test accounts/groups and authorization and is outside this run. Exact
model/effort metadata are unavailable; use unknown and flag CONTRIBUTING §9 at
the later merge check rather than claim compliance with an unobserved model.
