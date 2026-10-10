---
model: gpt-6-astra
effort: max
---
# Revision 3 planning evidence — 2026-10-10

The user requested the formal revision3 re-plan under CONTRIBUTING §7.4. This
checkpoint contains planning evidence and an exact archive, not implementation.
Product remains3d59455; fetched dev remains53306df; PR22 is OPEN/DRAFT with the
rejecting reviewb9a8a5d. Exactly one Stage2 `pr-critic*.md` has a rejecting Gate.
The older whole-issue PR16 and Stage1 are separate histories, not extra rejections.

The description and fixed-owner/private-boundary scope remain appropriate. The
three Mediums in `pr-critic.md` are mandatory inputs, not optional cleanup. Its
five executed probes remain evidence against the unchanged product; they were
not repeated merely to re-obtain the same output.

## Additional ground truth

Executed `replan_inputs_probe.py` on Python3.11.10 / Telethon1.45.0 with sockets
forbidden. It reuses the review's synthetic decoded-reply adapter but executes
real MTProtoSender.send, RequestState, _handle_rpc_result, factory/Stage1 policy
and error propagation. It does not replace the proposed health predicates or
claim that an unbuilt implementation works.

### Logical request identity

| Caller | Error wrapper chain | Leaf namespace / type | Constructor ID |
|---|---|---|---|
| GetHistory | InvokeWithoutUpdates | messages.GetHistoryRequest | 0x4423e6c5 |
| Takeout(GetHistory) | InvokeWithoutUpdates → InvokeWithTakeout | messages.GetHistoryRequest | 0x4423e6c5 |
| messages.GetMessages | InvokeWithoutUpdates | messages.GetMessagesRequest | 0x63c66506 |
| channels.GetMessages | InvokeWithoutUpdates | channels.GetMessagesRequest | 0xad8c9a23 |

The caller and actual error retain the same leaf type/constructor after known
envelopes are removed. Merely restoring the short class name is insufficient:
the two GetMessages classes have different namespaces and constructor IDs.
Revision3 therefore specifies namespaced keys for the new owned view only.
The existing legacy view keeps its existing strings.

Installed Telethon's diagnostic envelope tuple names seven classes:
InvokeAfterMsgRequest, InvokeAfterMsgsRequest, InitConnectionRequest,
InvokeWithLayerRequest, InvokeWithoutUpdatesRequest, InvokeWithMessagesRangeRequest,
InvokeWithTakeoutRequest. These are the bounded initial unwrapping set; a random
object's `.query` attribute is not authority that it is a transparent envelope.
Production should refer to the generated classes explicitly, not import the SDK's
private diagnostic tuple. The probe uses that tuple only to inspect current facts.

Telethon's `utils.is_list_like` recognizes list, tuple, set, dict, range and generator.
Its `_call` materializes request iterables internally. Evidence extraction must not
invent a request named `generator`/`set` or consume/reorder input before dispatch.
An exhausted/unknown success input supplies no request evidence. This stage does
not repair generic SDK iterable behavior or expand the private source contract.

### Exception provenance

Actual Python raising/handling produced these object chains (the existing bounded
`health._chain` reads them):

```json
{"isolated_chain":["AuthRequiredError","AuthKeyUnregisteredError"],"implicit_wrapper":["RuntimeError","AuthRequiredError","AuthKeyUnregisteredError"],"explicit_wrapper":["RuntimeError","AuthRequiredError","AuthKeyUnregisteredError"],"fresh_rpc":["ChannelPrivateError","AuthRequiredError","AuthKeyUnregisteredError"],"original_cause_can_be_rethrown_by_identity":true,"prior_implicit_context":["ValueError","ChannelPrivateError"],"prior_rpc_is_not_explicit_cause":true}
```

A scan must distinguish the first fresh RPC from an excluded failure farther
down the chain. It must also recognize the original explicitly linked source
when a caller unwraps and rethrows that same object. Conversely, seeding every
implicit ancestor as excluded can adopt a legacy failure that predates isolation.
Revision3 consequently uses exact escaping/cause objects as anchors and an ordered
incoming-chain decision, not any-ancestor membership. Known SDK MultiError leaves
are explicit container members; implicit context alone is not an ownership link.

These observations settle what data the implementation can use. The exact
classification/evidence contracts and their acceptance matrix belong in the new
plan and must be challenged by its next critic. No external decision, account,
credential, live server access or other unmerged feature is required to plan them.

### An awaited child task loses the call-local exclusion

The planning probe was extended with a new unresolved boundary and rerun. An
ordinary client has owner111; an awaited child opens its own temporary operation
and fails authentication before owner222 is verified. Its real SDK refusal crosses
back into a parent legacy health call. The current product reports:

```json
{"unverified_owned_snapshot":null,"legacy_owner":111,"legacy_verdict":"logged out","legacy_events":1,"exception_can_carry_neutral_attribution":true}
```

`isolate_call` currently registers exclusions only in same-task enclosing calls,
so its list does not protect the parent when the exception returns through await.
This extends Medium3's provenance problem and changes the chosen implementation
shape: do not retain a growing list of exception references on each ambient call.
Give the exact escaping failure/explicit causes a small neutral-attribution marker
that travels with that failure. The existing reported-error mechanism already
uses exception metadata; the probe confirms actual SDK/tgdata error instances
retain such a field without changing their text/cause/object identity.

An ordered attribution check can then stop at that marker, or allow a fresh raw
RPC encountered first, regardless of task hops. Marking must not traverse arbitrary
implicit context, which the prior example shows can belong to earlier legacy work.
Diagnostic `classify(..., include_reported=True)` and polling still need to read
the actual verdict; the marker controls emission under a legacy owner, not the
meaning of the exception. This adds no global registry, owner history or persistent
request record. These are available primitives and a planned contract, not an
implemented or reviewed solution.

## Scope and preservation

The main corrective runtime targets are `owned_health.py` and `health.py`.
The existing factory hooks, Stage1 client, budget admission, facade, storage and
notification lifetimes can remain in place. No global registry, legacy migration,
capability engine or callback queue worker is justified by this evidence.

The original revision2 plan, plan critic, dynamic prompt and merge fidelity check
were moved unchanged into `archive/round-1/`; each file was byte-compared with its
Git blob atb9a8a5d. The PR critic/probes stay at root as active re-plan inputs. The
archive README contains computed SHA-256 values. Original product verification
stays tied to3d59455 and is not evidence that revision3 has been built.

Session warmth is retained from the implementation and fresh review, with relevant
source/SDK paths refreshed for this re-plan. Model/effort provenance remains the
same-session Astra/max metadata described in the archived merge check; no fresh
selector reading or archaeology refresh is claimed.
