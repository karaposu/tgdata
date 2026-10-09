---
model: gpt-6-astra
effort: max
---
# Stage 2 merge fidelity check — 2026-10-09

**Gate: PASS for fidelity.** This is CONTRIBUTING §7.1, not the fresh soundness
critique under §7.2 and not permission to merge. PR publication and the fresh
critic follow this checkpoint. Product remains `3d59455`.

**Compared:** fetched `origin/dev` = `53306df2c3d87b558be0b7ed4419a42d3229c5f9`,
branch implementation/evidence head `a2b97555c2619b9b3441a72ba450e3edfa41d178`, actual
three-dot diff, triage, description, folded revision2 plan, original critic and
verification. No intervening dev change or existing Stage 2 PR. Same-session review,
with Stage 1/implementation context retained; no delegation.

## 0. Warmth and weight

The description records retained session warmth and base `53306df`; Git confirms
that commit is an ancestor. Triage is feature-heavy, matching #7's `enhancement`
and `heavy` labels. The completed bounded inquiry is committed in `f19ca2a`; its
five baseline probes explain the ownership/recovery/lifetime boundaries. No new
architecture warm-up or archaeology refresh is claimed.

## 0b. Surface and scope

Four runtime files implement the surfaced seams: health ledger/call context,
client request observation, facade composition and the new private owned monitor.
The suite and READMEs cover those interfaces. `docs/account_operations.md` was an
additional touched document, updating Stage 1-only wording and recording the new
private composition contract. This small documentation expansion was named in the
product commit and verification; the heavy weight remains appropriate.

Eight product files differ from dev; the other additions are this stage's work
archive. No legacy group operation, join allowance, routing, new storage, unmerged
#17 code, duncan or stray guide edit is included. The original checkout's untracked
HANDOFF.md/todo.md remain untouched. Keep work docs and any archaeology refresh
out of the eventual merge, and keep this branch as the archive.

## 1. Fidelity to the folded plan

| Step | Implementation evidence | Assessment |
|---|---|---|
| 1 fixed ledger/observation | owned_health.py:17–125; fixed `_owner`, exact client/task/valid handle, condition start ordering, explicit group assertion | Implemented as planned |
| 1 notifications | owned_health.py:127–182; task receives plain event data, guarded callback, failure containment, cooperative retirement | Implemented as planned |
| 2 source hooks/isolation | connection_engine.py:121–130; health.py `_Call`, `isolate_call`, `note_rpc_error`, `report`/sleep guards | Implemented as planned |
| 3 facade/query | tgdata.py:217–249 and close at1043; monitor created only after proof, explicit local query, dispatch outside source context | Implemented as planned |
| 4 coverage/docs | suite33's 41 cases; both READMEs plus internal operation guide | Implemented; extra guide update is the documented deviation |
| 5 verification/checkpoints | product3d59455 separate from evidencea2b9755; verification.md's exact suites/skips/examples | Complete |

No runtime design deviation. Initial account verification intentionally counts as
account proof, not group proof. Later group code must give the explicit access
assertion its semantic meaning. The new query intentionally returns None for
legacy-only activity. The plan does not promise a public group API or a complete
legacy health migration in this stage.

## 2. Does the plan still hold?

The chosen decomposition survived implementation: reuse complete local ledgers,
observe failures at the client wrapper, and separate callbacks from source cleanup.
It did not grow into a global ownership registry, request trace layer or permission
classifier. The prebuild experiment preceded runtime edits (`46866c3` before
`3d59455`). Compatibility and forced-overlap tests exercise the selected design.
Its narrow private semantics and notification limitations are stated in product
docs. Fresh scrutiny of the SDK/evidence and observer edge cases remains the next
gate; this fidelity pass does not treat passing tests as proof of soundness.

## 3. Original critic findings answered

- **Medium1, caught invalidation:** `_OwnedCall.valid()` reads the existing Stage 1
  handle, and `observe()` rechecks it before recovery. Suite33 covers caught
  post-proof mismatch and auth loss. No duplicate invalidation protocol was added.
- **Medium2, SDK MultiError:** the factory catches the real container, the owned
  hook records its raw RPCError leaves with existing deduplication, and only a
  wholly successful outer call supplies request evidence. Suite33 executes the
  actual SDK list-request path with synthetic sender futures.
- No High or Low finding existed in this stage's plan critic. Both selected
  mitigations were folded in `a1accf6`; neither long-term expansion was imported.

## 4. Issue status accuracy

Fetched #7 remains OPEN. T/0/1/2/3/4/5 each reference committed artifacts, all pushed.
The 424 actual offline passes exclude three live skips; 41 are new. The three
offline demo paths and 63-file compile/grammar checks are supported by verification.
Step6 and step7 are correctly unchecked before publication/review. They must update
as their artifacts and publication complete, with any rejecting verdict explicit.

As with merged Stage1 PR21, this partial-stage PR will say **Refs #7**, keeping the
parent open for stages3–5. This is the established staged-work exception to §6.6's
whole-issue `Closes` example; closing the entire feature here would misstate scope.

## Model/effort and small correction

§9's available same-session metadata was reread: `gpt-6-astra`, effort `max`, latest
recorded turn `2026-10-07T05:34:50.039Z`, in the previously identified local session
log. As at Stage1's accepted gate, max is treated as above the feature row's xhigh.
This is retained-session provenance, not a new `/model` selector reading; the older
timestamp is preserved rather than presented as current. No model switch is claimed.

The full branch whitespace check found one extra blank line at the end of the
original dynamic critic prompt. It was removed in this documentation checkpoint.
No product source, test expectation or runtime behavior changed during this pass;
the prior 424-pass verification still describes the product under review.

## Next

Publish PR into dev and post this check. Then run fresh in-session critic-d on the
actual PR diff plus folded plan, with additional behavioral probes. Any High or
Medium rejects under §7.3. Merge requires both gates and the user's go-ahead;
exclude work docs/archaeology updates and retain the archive branch under §7.6–7.7.
