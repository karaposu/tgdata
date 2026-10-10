---
model: gpt-6-astra
effort: max
---
# IMPLEMENT AS WRITTEN

Falsifier: a well-formed successful uncached live GetHistory reply fails to establish
even momentary read access to the supplied concrete group for the authenticated account.
Affordable now: no — requires a designated live permission experiment outside this
scoped offline review. SDK/task/cache/budget falsifiers available offline were exercised
before this verdict; synthetic source replies are not evidence of live permissions.

**PR23 decision under CONTRIBUTING §7.3: ACCEPT — 0 High, 0 Medium, 1 Low.**
No required product change or revision3 re-plan. The Low remains consciously recorded;
acceptance is not merge authorization or live qualification.

## High-level summary

Fresh in-session review of the implemented `30ba706...a2afc05` product diff plus plan.md
revision2 d15b5d5. PR23 was published at1348028; later f75ee09 adds this review's prompt,
not runtime changes. `git diff a2afc05 HEAD -- tgdata docs README.md setup.py requirements.txt`
is empty. The prior plan critic and passing merge-check were evidence, not verdicts
adopted by this review. No subagent or runtime patch was used.

The layer is appropriately small: ordinary stateless functions interpret references and
observations, while the merged account/lifetime/budget/health code keeps its authority.
The API separates metadata and membership from one validated history reply. Six new
probe groups exercise cached-versus-current evidence, malformed nested replies, reversed
completion order, budget refusal after denial, invalid numeric-source reasons and a
mismatched service message. One malformed invite path leaks a native error type; it
fails closed and does not invent access or health. No merge-blocking defect reproduced.

## Premise Inventory

### 1. Live source success means momentary history readability

**Premise:** an ordinary successful uncached concrete GetHistory reply is a read observation,
not membership, complete visibility or a future guarantee.
**First dependent step:** plan3, then facade confirmation in4.
**Waste if false:** access-result semantics and group recovery require redesign.
**Test scheduled at:** live permission qualification is excluded from this delivery;
actual local composition was tested before/through implementation and this review.
**Cheapest earlier test:** an authorized live group/permission experiment. Outside this
review scope; no claim that source stubs close it.
**Coverage:** official [GetHistory method](https://core.telegram.org/method/messages.getHistory)
and [peek invitation](https://core.telegram.org/constructor/chatInvitePeek) semantics are
consistent with the bounded contract. Reading them is documentary evidence only.
Suite34 and these probes execute the actual SDK, but their network replies are synthetic.
The plan does not schedule expensive future stages before a promised live gate here.

### 2. Reusing an owner boundary does not smuggle stale cache facts into results

**Premise:** fresh verified account and source metadata determine the observation; an old
full cache row cannot upgrade current minimal metadata into a proven readable peer.
**First dependent step:**2/4.
**Waste if false:** reference projection and owner composition would need replacement.
**Test scheduled at:** pre-plan contract probes, public suite34 and this review before verdict.
**Cheapest earlier test:** actual SDK/session paths with stale rows and a changed response;
run now on both file and store backends in pr_probes.py.
**Coverage:** fresh hash22, rather than cached11, reached the history request. A subsequent
minimal hash33 reply returned unprobed with zero new history sends and retained the prior
denial on both backends. No helper supplied a GroupAccess value or confirmation. Stale
identity111 versus owner222 is separately covered by suite34 and the overlap probe.

### 3. Failure ordering and quota remain conservative through the public API

**Premise:** newer successful work cannot erase a failure actually observed later, and
budget refusal is not group recovery or a new Telegram refusal.
**First dependent step:**3/4.
**Waste if false:** the new public orchestration would violate merged health/budget rules.
**Test scheduled at:** suite34 plus reversed completion and combined-failure probes now.
**Cheapest earlier test:** actual SDK sender errors, real SQLite budget and forced asyncio
barriers; executed before this verdict.
**Coverage:** newer call returned readable; older call later returned denied, retained
owner222's condition and total charge2. Cached111 never gained a ledger. A later exhausted
budget sent no extra history, retained the existing denial and left event count1.
These are actual local component outcomes; no assertion was supplied to the monitor.

### 4. Structured error promises cover unexpected nested TL objects

**Premise:** recognized outer invite wrappers contain group entities that projection can
interpret or explicitly reject.
**First dependent step:**2.
**Waste if false:** local error typing needs hardening; the domain architecture survives.
**Test scheduled at:** metadata/shape cases in5, additional malformed nested wire data now.
**Cheapest earlier test:** encode/decode ChatInviteAlready with wrong nested TL classes;
executed now through real RequestState and SDK result handling.
**Coverage:** PeerChat/PeerChannel yielded AttributeError, whereas User yielded
GroupResponseError. All failed without history or health events and closed the client.
This narrows the robustness promise (L1); it does not falsify ownership/access evidence.

No unrun affordable local architecture experiment remains. The accepted boundary excludes
live permission proof, arbitrary backend correctness and third-party SDK cache repair.

## Restart Check

| Established earlier failure | Mechanism | Actual answer in this diff / prerequisite |
|---|---|---|
| Verified B event but cached A health state | Legacy owner was read from mutable cached identity | Stage2 fixed-owner boundary; facade uses it directly; stale-identity public regressions |
| Operational source error became input failure | Broad catch around generic SDK resolver translated native/terminal errors | Direct explicit requests and narrow RPC conversion; original server/local error tests |
| Metadata success could be mistaken for access recovery | Request success lacked a semantic history assertion | _validate_history followed by a complete GroupAccess, then facade confirmation |
| Primary outcome lost during teardown/notification | Client lifetime and callbacks were not separated | Unmodified Stage1/2 cleanup/notification composition; delayed/cancelled/failed public tests |

These mechanisms were previously established and are not new rejection rounds. Stage3's
new typed-ID plan finding is covered by _canonical and the existing public boundary tests.

## Inherited Lessons

- Owner prerequisites were merged before this domain feature; no second owner registry
  or group engine was introduced. Every result takes operation.account_id.
- Metadata and availability of an input peer do not prove history access. Current minimal
  metadata remains unprobed even when the session has stronger older cached data.
- Domain assertions follow actual reply validation. Invalid service-message peer8 was
  rejected for target7 with zero health events; probe data did not provide confirmation.
- Native cache/transport errors remain errors. The known file-cache failure is tested and
  disclosed, not silently converted to an unavailable group or hidden by a cache rewrite.
- Larger abstractions need demonstrated reach. Three frozen values and stateless helpers
  cover this stage without a scheduler, permission matrix, alias registry or join policy.

## L1 — Malformed invite nesting can leak a native projection error

**Risk**

If an invite response contains a bare peer identifier where full group details belong,
the lookup fails with an attribute error instead of the dedicated malformed-response
error. A caller that handles only the documented response error would miss this unusual
failure. The operation still refuses to return access, closes its client and leaves
health unchanged; an ordinary well-formed Telegram reply is unaffected.

In tgdata/group_operations.py:164, _identity deliberately accepts PeerChat/PeerChannel
for request/message identity work. _resolve at:301 accepts a ChatInviteAlready/Peek
wrapper, then _project at:250 passes its chat through that same permissive helper.
_text_count at:233 accesses source.title without first restricting projection to the
Chat/Channel/Community entity families. A wire-decoded ChatInviteAlready(PeerChat(7))
or ChatInviteAlready(PeerChannel(7)) consequently escapes as AttributeError. The same
wrapper with User(7) is rejected correctly as GroupResponseError by _identity.

**Severity:** Low
**Category:** API error consistency / malformed-response hardening
**Impact:** consumers' narrow error handling can miss a malformed nested response. No
false readable result, history request, health event, quota spend or cleanup bypass.
**NoobEng:** a helper reused to compare identifiers also accepts lightweight peer IDs;
the richer metadata projection needs a narrower input family before reading title.
**Affected areas:** invite Already/Peek projection and its error surface.
**Evidence:** pr_probes.py malformed_nested_invite; real TL bytes/SDK dispatch, synthetic
schema-violating nested data; see quoted output below. No live server occurrence claimed.
**Optional correction:** require the supported entity families at _project entry, then
raise GroupResponseError for other TL objects; add the public nested-wrapper cases.
A broad validation framework or foundation rewrite is unnecessary.
**Disposition:** consciously left as nonblocking under §7.3: the server must violate
its nested Chat schema, and the existing path fails closed. No runtime patch in review.

## Executed evidence

Command (worktree root, project Python3.11.10 / Telethon1.45.0):

```
python devdocs/work/7-group-operations/stage-3-group-access/pr_probes.py
```

Exit0. The six probe groups use the real facade, generated SDK objects, actual SDK
sender/error construction, owned lifetime/health and real session/SQLite budgets.
Only transport/auth replies and deliberate malformed/fault conditions are supplied;
source sockets, login code and join/import/dialog work are forbidden. Probe output is
saved in verification/pr-probes.txt. Relevant exact output:

```json
{"cache_vs_current_reply": [{"backend": "file", "fresh_hash": 22, "minimal": "unprobed", "extra_history": 0, "denial_retained": true}, {"backend": "stored", "fresh_hash": 22, "minimal": "unprobed", "extra_history": 0, "denial_retained": true}]}
{"malformed_nested_invite": [{"nested": "PeerChat", "outcome": "AttributeError", "expected": "GroupResponseError", "health_events": 0, "closed": true}, {"nested": "PeerChannel", "outcome": "AttributeError", "expected": "GroupResponseError", "health_events": 0, "closed": true}, {"nested": "User", "outcome": "GroupResponseError", "expected": "GroupResponseError", "health_events": 0, "closed": true}]}
{"late_old_failure": {"newer": "readable", "older_completed_later": "denied", "denial_retained": true, "owner": 222, "budget_used": 2, "cached_owner_has_health": false}}
{"budget_denial_never_changes_group_state": {"events": 1, "denial_retained": true, "history_sends": 1, "second_call": "ReadBudgetExceeded"}}
{"numeric_rejection_is_qualified_source_reason": {"status": "denied", "reason": "CHANNEL_INVALID", "lookup": null, "events": 1}}
{"service_message_peer_validation": {"outcome": "GroupResponseError", "wrong_peer": 8, "health_events": 0}}
```

The numeric-source probe establishes current classification behavior, not that Telegram
emits that error for a particular stale hash in live use. [GetChannels documentation](https://core.telegram.org/method/channels.getChannels)
describes CHANNEL_INVALID as an invalid input channel. This implementation deliberately
retains the existing classifier and exact reason: denied here means a classified refusal
to the supplied reference, not proof of a membership ban. It neither joins nor creates
metadata for the unresolved target. No new vendor-cause claim is inferred from the stub.

The original **494 offline groups/3 live skips,3 demos,65 compilation/grammar checks**
remain valid for unchanged product a2afc05 (verification.md). They were not all rerun
solely to relabel prior passes as fresh. New probes supplement them at uncovered
intersections. Source/trace review also checked callbacks, cancellation, nullable hints,
IDs/hash bounds, imports/dependency floor, safe labels and unchanged legacy behavior.

## Phase 3 selection record

**Note**
*Why chosen:* There are no High/Medium mitigation tiers to select. L1 is consciously left under the PR threshold because the demonstrated malformed nested reply fails closed with no false source/health observation; optional hardening stays a small domain guard, not new infrastructure.
*For future:* If the optional L1 hardening is taken up, narrow _project to the supported entity families and retain the real-TL malformed-wrapper regression. No shared validation framework or ownership rework is justified.

## Provenance and next gate

Current session metadata matched CODEX_THREAD_ID and declared gpt-6-astra/max at
2026-10-10T15:22:02.093Z; §9's feature-review model/effort requirement is met. Full
code/document reading and behavioral probes ran sequentially in this warmed session.
No subagent, re-plan, runtime fix or merge was performed.

Commit/post this critique to PR23, record the accepted Low and update the active #7
stage status. PR can become ready. A later user go-ahead is still required to merge,
with work docs excluded, merged-code checks and the archive branch retained. Parent
#7 remains open for Stages4/5.
