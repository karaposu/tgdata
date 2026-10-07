# Critique — refined assembly A2, iteration 2

## User Input

`_branch.md`, current Sensemaking/Innovation, and the accumulator in
`critique_iter1.md`. Evaluate the refined source boundaries without relaxing
the selected existing-access scope or the previous dimensions.

## Phase 0 — fixed dimensions and frame tests

Retain D1–D7 and their weights/success criteria from iteration1: account ownership,
durable restriction/uncertainty, delivery preservation and bounded scope are
critical; compatibility/feasibility and operational clarity high; parsimony
noncritical. Substance checks use actual token/CAS order and actual completed
records, not method names. External anchors are the source and both saved probe
scripts/results. Axis-absence audit includes pre-identity errors, ambiguous
admission, late settlement, restart, store errors with prefixes and external cancel.

What-if-wrong prosecutions: (1) a token could be redundant if timeout proves
quiescence after restart—process-local timeout evidence is lost, so it does not;
(2) two attempt records could be duplicate authority—raw/daily reads have no
backfill token and account restrictions cross group boundaries, so owners differ;
(3) timeout-prefix composition might only work in a stand-in—the probe executed
the actual BatchEngine with one exception-seam change and real SyncEngine/SQLite.
It proves that seam's capability, not the finished pool's implementation.

## Phase 1 — landscape

The same regions persist: owned readers viable; broad-catch/shared-health and
duplicate progress dead; uncertain source boundaries require explicit mechanisms.
A2 occupies the existing viable region after addressing the boundary objections.
Distributed coordination and equal-visibility proof remain outside scope. Live
two-account behavior is an unqualified evidence surface, explicitly not a design
assumption used to claim equal history.

## Phases 2–3 — adversarial accumulator update

| Candidate | Prosecution | Defense | Collision / verdict |
|---|---|---|---|
| Q1G | Aggregate selection can observe several document revisions. | Independent tokens still protect each account. | SURVIVE D1–D7, more bookkeeping; unselected alternative. |
| Q1F | A committed admission can lose its response; clearing it on retry would be unsafe. | Candidate expressly refuses source and preserves that token for explicit recovery. | SURVIVE D1–D7; single document matches serial operation contract. |
| Q1C | A paused worker outlives the lease and later reads concurrently. | Automatic availability is attractive. | KILL D2/D4; seed: elapsed time grants no quiescence proof. |
| Q2G | A timeout never advances to another available account. | It preserves caller control and never overlaps work. | SURVIVE as conservative alternative; weaker automatic recovery. |
| Q2F | Cancellation arriving while timeout is handled could be misclassified. | Only the pool timer becomes PoolTimeoutError; caller cancellation remains BaseException and active token stays. Real prefix probe preserved100 messages. | SURVIVE D1–D7; exact cancellation races remain implementation assertions. |
| Q2C | Another account sees a different history slice and cannot reproduce discarded records. | Re-reading could reduce state complexity. | KILL D3; seed: preserve actual complete records before replacing source. |
| Q3G | A local storage exception could inherit a Telegram error cause and report false health. | Separate read_error and suppressed context avoid that route. | SURVIVE D1–D7 as component of Q3F. |
| Q3F | Recovery could erase a known flood wait or a late old settlement could clear a new attempt. | Explicit bound cannot shorten known prohibitions; exact token/CAS blocks stale settlement. | SURVIVE D1–D7; unknown-outcome retry bound remains a caller assertion. |
| Q3C | Successful batch return hides that the account source permission never settled. | Caller gets useful data. | KILL D2/D6; seed: return useful data through the error prefix while exposing uncertainty. |

Prior kill records remain; no killed candidate revived under a looser criterion.
P1F is now Q2F plus duplicate/unknown-identity requirements; P2F is Q1F+Q3F.
P4C remains an unselected narrower-scope alternative. Six current survivors use
empirical/source anchors; mechanism independence status validated at design level.

## Phase 3.5 — assembly A2 adversarial histories

1. **Restart after server wait, before settlement.** Admission token is already
   durable; reconstructed pool excludes that account. It does not need to know
   the lost wait to avoid immediate source reuse. Explicit recovery preserves
   the distinction between quiescence and unknown Telegram readiness.
2. **Successful data, failed restriction-state settlement.** Returned local
   exception carries the complete records as an interrupted prefix. Actual
   SyncEngine/BackfillEngine prefix mechanisms can publish it; the account token
   remains unresolved if the write did not commit. Neither cursor nor quota is reset.
3. **Admission committed, response lost.** No source begins. Subsequent status
   exposes the token; no implicit “retry means new permission.”
4. **Account B uses account A's credential.** Duplicate known key rejects at
   preflight; distinct-key alias still fails fresh expected-ID check before history
   admission. Expected numeric identity does not become verified identity by naming.
5. **Timeout after a page.** Actual probe:100 records retained, pending send cancelled,
   charged200, replay0 reads. Pool does not try another account before that prefix is
   handled. Timeout is cooperative; the pool waits for cancellation to complete and
   cannot promise to preempt a blocking custom backend or arbitrary SDK code.
6. **Pending replay with broken account inventory/state.** Progress methods consult
   existing pending state before the injected reader; replay/ack must not invoke
   preflight, account state or budget. This is exercised by actual implementation tests.
7. **All accounts unavailable.** Structured refusal replaces neither an empty batch
   nor permanent history completion. User's “read group” request remains actionable.

Strongest defense: all failures have a named owner and conservative stopping point;
the design reuses proven ledger/batch/receipt mechanics rather than multiplying them.
Strongest remaining cost: more explicit recovery than a simple list-of-clients
loop. This cost is necessary to preserve the selected failure semantics, not a
reason to add joining, distributed workers or a global health rewrite.

**Assembly A2: SURVIVE.** No critical design caveat remains. Implementation proof
is still required; this verdict is not a claim that the pool code or live gate exists.

## Phase 4 — coverage / convergence

All9 refined candidates evaluated;6 survivors against all7 dimensions;3 constructive
kills. Combined with the first iteration, ownership, persistence, cancellation,
policy, delivery and evidence alternatives are represented. Two candidate sweeps
(iteration1 and iteration2) stayed in the originally mapped viable/dead/boundary
regions; the second removed critical boundary caveats rather than opening a new
solution region. Information gain narrowed from overall ownership to two exact
seams, then repeated crash/timeout/alias histories added no new authority.
No unexamined in-scope region is likely to replace the survivor; live resources
affect qualification, not the contract's meaning. **Signal: TERMINATE**, ranked
survivor A2, with Q1G/Q2G as less parsimonious or less capable alternatives.

Telemetry: dimensions7/7, adversarial strength STRONG, landscape STABLE in region
topology, clean assembly survivor yes. No wrong dimensions, rubber stamp, nitpick,
blind axis, evaluation drift, false convergence claim about live behavior,
self-reference or external-grounding absence. **Overall: PROCEED**.
