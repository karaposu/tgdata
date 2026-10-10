---
model: gpt-6-astra
effort: max
---
# Stage 3 merge check — PASS (fidelity)

Reviewed `30ba7062b0d7254b5695c4a0d727a4c8242e3f25...7a357b5eb0402aa82088cd38e7d88de441c714c9`
against triage.md/surfacing.md, desc.md, plan.md revision2, critic.md and verification.md.
The product is commit **a2afc05**; later commits contain work evidence only. Remote dev
still equals30ba706 and remote Stage3 equals7a357b5 at this check. Working tree is clean.

This is §7.1's fidelity check, not the fresh §7.2 soundness verdict. PR publication and
fresh in-session critic follow it. No merge is authorized by this artifact.

## 0 — Warmth, weight and provenance

The session retains Stage1/Stage2 implementation/review/merge and Stage3 implementation.
For this gate, the actual product diff, all354 lines of group_operations, all865 lines
of suite34, changed product docs, plan/fold/critic, and the consumed ownership, evidence,
budget and facade boundaries were refreshed. No new archaeology refresh is claimed.
The warming record in desc.md names30ba706; `git merge-base --is-ancestor 30ba706 HEAD`
exited0. Triage is feature-heavy and matches issue7's `enhancement`/`heavy` labels.

**§9 checked:** the current process's CODEX_THREAD_ID matches the local session record.
Its latest turn_context, **2026-10-10T15:22:02.093Z**, declares **gpt-6-astra**, **max**
effort. This confirms the prescribed model family and an effort at least as high as
§9's feature/merge-gate xhigh requirement. The gate uses current session metadata,
not just copied artifact frontmatter; older provenance notes remain historical.

## 0b — Did the diff stay within triage's territory?

Yes. The10 product files are:

- tgdata/group_operations.py: new read-only reference/observation domain.
- tgdata/tgdata.py and tgdata/__init__.py: two facade methods and public value/error exports.
- tgdata/smoke_tests/test_34_group_access.py and its README: actual SDK public-path coverage.
- README.md, docs/group_operations.md, docs/account_operations.md: public contract and
  links from the merged foundation; stale “public operations are future” wording updated.
- setup.py and requirements.txt: consistent Telethon>=1.45,<2.0 requirement.

The exact new domain/test/doc filenames were settled during planning within the
surfaced group/public-contract/test regions. Product docs were summarized by triage
rather than individually listed in its27-row source inventory. This is expected
completion of the already-heavy surface, not an unweighed subsystem expansion.
No factory, account_operation, owned_health, health, budget, session/cache, persistence,
legacy GroupInfo or discovery runtime file changed. Other changes are the task's
work-folder records. No duncan, stray guide, original untracked files or archaeology.

## 1 — Does implementation match revision2?

Yes. The six steps map to the product as follows:

1. Suite34 Reply/send fixture drives real TL bytes through MTProtoSender/RequestState;
   actual RPC construction comes from suite33. Socket/login/join/import/dialog guards
   and overlap/cleanup barriers are present. No helper supplies the API's verdict.
2. group_operations.py defines frozen portable values, the bounded parser, canonical
   typed identities, exact numeric cache routing, matching reply projection and invite
   forms. Direct GetChats/GetChannels/ResolveUsername/CheckChatInvite avoid broad helpers.
3. _check_group_access reuses one resolution, returns unprobed only without a peer,
   validates one GetHistory(limit1/hash0) reply, and converts only classified group RPC
   refusal. Operational/local errors and cancellation propagate. lookup_group keeps
   original RPC errors, as the result types and product docs specify.
4. The two facade methods use the existing _account_health_operation, with the safe
   reference label and explicit expected account. Only the completed positive access
   result calls confirm_group_access. There is no legacy decorator, new engine or
   persistent selection mutation. Exports and both dependency declarations agree.
5. Suite34's49 groups cover the12 acceptance families, including backend/source-cache
   limitations, typed collisions, large/zero hashes, ownership, invalid replies,
   budget admission, deferred callbacks, real overlaps and cleanup cancellation.
   Product docs retain nullable hints and distinguish membership from readable history.
6. Verification records actual494 offline passes/3 live skips,3 successful demos and
   65 compilation/Python3.7 grammar checks. Product a2afc05 and work7a357b5 are separate.
   The current diff has no whitespace errors; full suite repetition is unnecessary for
   this unchanged product. Fresh critic probes are a separate soundness check.

### Deviations / implementation discoveries

No structural or scope deviation. The empty /joinchat route is explicitly reserved after
trailing-slash normalization; this is the local parser correction recorded in a2afc05
and verification.md, enforcing the planned refusal of empty invite tokens.

The extreme synthetic Chat(10**12) cache row also exposes the SDK's pre-proof self-row0
collision. Its original AttributeError remains an error and has a separate regression.
The valid marked basic-ID boundary is tested without pre-seeding that colliding cache.
This preserves the original source-error policy rather than silently repairing sessions.
Test-construction corrections and their failed/passing runs are recorded in verification;
none weakened a production expectation. Joining/allowance remain later stages.

## 2 — Does the plan still hold against the implemented code?

Yes as a bounded offline delivery. Stateless projection consumes the already-merged
lifetime/ownership architecture. Lookup metadata never supplies group recovery by itself;
readability requires domain interpretation of a successful bounded history response.
The API does not promise live qualification, future access or complete history.

Known hashless CommunityForbidden/SQLite caching failure remains disclosed and preserved,
with store-backed behavior distinguished. Numeric references deliberately depend on exact
cached channel hashes, and aliases are not unified in health. These limitations match the
contract rather than invalidate its architecture. No new service object or state store
was introduced to support later joining before that work is designed.

## 3 — Were the plan critic's findings answered?

**M1, Medium, selected robust/elegant — addressed.** `_canonical` at group_operations.py:154
checks positive ID, signed64 marked representation and exact SDK namespace round trip.
`_identity` uses it for source projection/matching/history peers, and `_numeric_peer` uses
it before any exact-row candidate query. Impossible basic candidates are skipped while
valid large-channel candidates remain. No out-of-range SQLite query is manufactured.

Public regressions at test34:296 and:310 cover cached channel/basic collisions, the
10**12 boundary, large channel candidate and signed64 extremes; both memory and SQLite
sessions are exercised. This implements the selected proposal without a shared legacy
identity migration. Plan critic had no other Medium/High and no Low finding to leave.

## 4 — Is issue7's status complete and honest?

Yes at review start: T/0/1/2/3/4/5 ticks have committed artifacts0a8366a/f174e90/382c911/
8407314/48a662b/d15b5d5/a2afc05+7a357b5. Steps6/7 were unchecked, correctly; this artifact
supports ticking6 only after commit and posting. Step7 must await the fresh PR critique.
The branch is linked, the description was posted, #7 remains open for later stages,
and Stage3 is explicitly not merged. Stages1/2 are historical completed records.

After publication, update the active Stage3 block with the PR/comment and committed gate.
Use **Refs #7** because this stage does not close the parent issue. Preserve the original
request and prior-stage records; no standalone issue is needed.

## Integration boundary

The feature branch archives its work-folder docs. Any later approved merge into dev
must exclude devdocs/work and preserve dev's archaeology per §7.6, run the merged-code
checks and retain the branch. Do not merge now. The next gate is a fresh critic-d on
this exact product diff plus plan, in this session, with executable behavioral probes.
