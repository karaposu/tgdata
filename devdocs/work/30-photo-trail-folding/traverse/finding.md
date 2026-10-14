---
status: active
model: gpt-6-astra
effort: xhigh
---
# Finding: infer photo trails from saved original posts

## Question

How should tgdata offer optional photo-trail folding—a person's text or album followed by additional photos—without losing original messages or producing inconsistent results across batches and restarts?

The user authorized implementing #30 after album assembly merged. This inquiry qualifies the behavior and its ownership boundaries before the implementation plan.

## Finding Summary

- Keep the original Telegram posts intact. Represent a photo trail as an explicit, provisional association between those posts.
- Compute a complete current view from a caller-selected, bounded set of saved observations. A later caption or other evidence can remove a previous association.
- Use every original message's position to decide whether activity interrupts a trail. An album's first message alone cannot represent all its interruptions.
- Only infer links for the same positively identified user and actual photo-only follow-ups. Keep uncertain cases separate.
- Reuse the existing receiver's saved original records for restart support. Source acknowledgment remains independent of inference.
- In the SQLite example, refuse a requested range that cuts a known album. The caller can choose a wider range; the helper must not silently widen, clip or discard context.
- Eleven contract histories passed using actual SDK values, SQLite and both source engines. A complete public implementation still needs its own plan, critique and full combined prebuild.

## Finding

People often post text and then send photos separately. ScrapeOps currently combines some of these messages before classification. Moving this behavior into tgdata is useful, but Telegram does not mark the intended relationship. Unlike an album, the relationship is a guess that can be wrong.

### Preserve the originals and make the guess visible

The existing TelegramPost value represents Telegram's explicit album grouping or a single message. Its identity and original member records should remain unchanged. A photo-trail view should retain those original values once and describe which ones it associates with a preceding post.

The view needs the exact heuristic policy, its version, a content revision and explicit association links. Counts should distinguish absorbed original posts from attached original photo messages: a photo-only album can contribute one post and several photo messages.

This is a full current view for a scope chosen by the application. The application replaces its older view for that scope; it must not append each result as though it were a permanent new post. Removing an association in the new view restores the original separate posts without reconstructing lost data.

### Keep the rule conservative and opt-in

Existing tgdata calls keep their behavior. The new helper's policy is disabled by default; callers explicitly enable inference.

An anchor is a text-bearing ordinary post or a Telegram album. It must have one positively identified user across its members and usable, nondecreasing dates. A lone uncaptioned singleton photo does not become an anchor for reverse text merging.

A follower contains only ordinary, textless photo messages. It may be a singleton or a photo-only Telegram album, but the whole original post attaches or remains separate. Every member must have the same positive user identity as the anchor. Unknown, mixed or channel-style identities never establish a shared person.

Each reply must refer to an already known earlier member of the anchor or attached chain. A reply to another or unknown message breaks the attempted trail; no Telegram lookup is performed to infer that message's author.

The gap is measured from the previous member. Bound both the total elapsed time from the original anchor's last member and the number of attached photo messages. Proposed starting settings are30 seconds per gap,120 seconds total and20 attached photos; these are configurable policy choices, not claims about Telegram or human intent.

### Evaluate activity at original message positions

The output is grouped into original posts, but interruptions happen at individual messages. For example, an unknown-author album may contain messages1 and5, while a known user posts text2 and photos3 and6. The unknown message at5 must interrupt the earlier trail before photo6. Looking at the unknown album only at its first position would miss that interruption.

Precompute each post's eligibility using its complete supplied observation. Treat overlapping post intervals from the same known user and regressed or missing chronology conservatively. Then examine original member events in message-ID order. Unknown-author activity clears active trails in that chat at each of its actual member positions; unsafe known-user activity clears that user's trail. Other positively identified users remain independent.

Make a whole post's attachment or anchor decision at its last currently observed member. A new text-bearing post ends the previous trail. A follower that fails a reply, gap, span or count check stays separate and ends the previous chain. Eligible independent text posts or albums may become new anchors.

This does not declare an album complete. It describes only the supplied current observations. If a later member changes eligibility, recomputing the full view can withdraw the earlier attachment.

### Retain facts across calls and restarts

#29's SQLite receiver already stores immutable original member records and recognition of accepted raw inputs. That storage can retain the evidence needed for a later photo-trail view. A separate tail database or inference-delivery acknowledgment is unnecessary.

After the receiver accepts a normal source delivery, the caller can acknowledge its original raw batch ID or full backfill delivery reference. Constructing a photo-trail view is separate application work. If a view exceeds a bound or refuses its scope, original stored data and exact-input confirmation remain valid.

The helper does not copy downloaded media. Original media references remain intact, and the caller still owns the bytes and their durability before source acknowledgment.

### Make a bounded range honest

The first proposed adapter selected posts touched by a message-ID range and loaded every member of those posts. An actual SQLite probe disproved that approach: selecting messages1–2 returned1,2,4 after album expansion, while omitting the saved same-user text at3. That text could change the folding decision.

The qualified example uses an explicit interval `(after_id, through_id]` in one chat. It includes all stored records inside that interval and requires each selected post's complete currently stored observation to fit inside it. If a known album crosses either boundary, the view refuses. Choosing a wider interval is an explicit caller action.

Selection, extent checks and loading must use one consistent read transaction. Check counts and encoded-size lower bounds before materializing keys or payloads, then enforce the exact whole-operation input/output policy. No limit permits silent truncation, eviction or resetting a known collection.

This is completeness relative to the declared set of currently stored observations. It does not prove that no unseen or deleted Telegram message exists. Later acquired records can change the view, which is why inference stays provisional.

## Next Actions

### MUST

- **What:** write the feature description and concrete API/format/adapter plan. **Who:** this task-impl run. **Gate:** this qualified finding. **Why:** make the new surface and its limits reviewable before product code.
- **What:** run fresh critic-d on that plan, then execute its complete real-component candidate experiment before production adoption. **Who:** this same session. **Gate:** reviewed plan and named pass/fail criteria. **Why:** the contract sketches do not qualify every public serialization, malformed-state, cleanup or resource path.
- **What:** implement only the qualified folded plan and run focused plus full offline verification. **Who:** this task-impl run. **Gate:** full candidate PASS. **Why:** demonstrate preserved source behavior and usable restartable inference.

### COULD

- **What:** measure false-fold behavior on a separately approved labeled corpus. **Who:** a later consumer-validation task. **Gate:** a representative consented corpus exists. **Why:** tune convenience against conservative nonattachment without inventing an accuracy claim. **Depends-on:** MUST implementation/verification; GATED for testing the actual implementation rather than the sketch.

### DEFERRED

- Automatic context widening: reconsider when a consumer repeatedly needs manual range widening and accepts bounded closure semantics.
- Finalized stream segments or an inference event ledger: reconsider only when a concrete consumer supplies closure authority or cannot replace current views.
- Interval-index optimization: reconsider only after a measured projection bottleneck and an equivalence test against member-event behavior.
- ScrapeOps migration: a separate adoption task after this library capability is reviewed and merged.

## Reasoning

An unchanged copy of the consumer helper was rejected because actual probes showed video-only, backward-time and channel-identity folds, as well as mutation of its inputs. Its representative overflow fixture also counts11 members with only10 distinct IDs. These are implementation/fixture details to correct in new tests, not compatibility promises to inherit.

A library-owned permanent history or inferred-event ledger would add another state authority without a current consumer need. Coupling inference to receiver acceptance would recreate #29's previously reproduced failure: a successful raw input could become impossible to confirm when its derived view grows.

A strictly forward finalized stream would require an additional closure contract and would restrict supported late/reversed observations. An explicit-reply-only rule would miss the ordinary nonreply photo follow-up motivating this task. Both remain possible future policies under different consumer requirements.

Lossy display summaries were rejected because they cannot reliably expose or undo an association. Pure-helper-only delivery was refined to include a runnable optional receiver example: storage remains caller-owned, but the requested restart behavior has concrete evidence.

Automatic transitive context closure can be correct, but needs wider selection and extra bounded work. Explicit refusal is simpler and preserves the caller's chosen range. Reconstructing partial albums inside the range would silently change the meaning of a current original-post judgment by omitting already known caption/identity evidence.

The surviving approach keeps one original-data authority and one deterministic inference operation. Nine contract histories passed, followed by two fresh backfill and concurrent-WAL histories. The latter prove original receipt replay and consistent views during concurrent growth. Evidence is in foundation_probe.json, scope_probe.json (the retained counterexample), contract_probe.json and contract_critic_probe.json.

## Open Questions

### Monitoring
Actual inference accuracy remains unmeasured outside the consumer motivation. The helper is explicitly optional and provisional; no percentage-confidence or semantic-correctness guarantee will be published.

### Refinement Triggers
A complete candidate failure that changes these ownership, scope or ordering rules requires returning to the contract. A local implementation typo does not. New public fields/options and the complete corruption/cleanup/concurrency matrix are for the imminent plan/prebuild, not unresolved human-only blockers.

## Source Input
The user invoked task-impl for “#30 — Optional photo-trail folding” after #29 merged. The original issue request is preserved verbatim in ../source-input.md. No request to deploy, migrate ScrapeOps, merge or release was included.
