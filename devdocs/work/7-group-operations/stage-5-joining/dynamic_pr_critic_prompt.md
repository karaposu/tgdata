# Fresh Stage 5 PR critic prompt

Subject: PR25's implemented product diff `f15f1a8..4b4ae21` together with Stage5
`plan.md` revision2, against current dev. Read the description, triage, prior plan
critic and real code to establish context, without treating their verdicts as proof.
Run in this warmed session, never a subagent. No product patch, live Telegram action
or merge is authorized by this review.

Ultrathink. Read complete relevant implementations and examine:

1. Authority: expected account versus cached identity; ownership during delayed
   resolution, fresh proof, policy changes and overlapping operations. Can permission
   from an earlier snapshot or another facade authorize this send?
2. Admission: actual SDK enqueue versus helper invocation; synchronous durable claim,
   failed commit/cleanup, process death, cancellation and retries. Can an uncharged
   mutation escape, or an uncertain attempt regain capacity? Distinguish application
   retry from protocol repair of the same request.
3. Evidence: exact source request identity versus matching names; unsupported wrappers,
   malformed result fields, membership versus approval/payment/interaction, and the
   fact that preflight metadata can be incomplete. Can post-reply work replace an
   outcome or falsely prove that no remote mutation occurred?
4. Composition: fixed-owner health, previous read denials, local failures inside source
   awaits, callbacks and teardown; legacy/raw-client behavior, pinned settings,
   read-budget coexistence, exports and supported SDK/runtime claims.
5. Design size: does this stage merely consume the merged prerequisites? Identify an
   actual counterexample before proposing a wider framework. Do not demand routing,
   payment, membership reconciliation or a generic raw-client guard as hidden scope.

Before deciding, run cheap falsifiers on the delivered facade with real SDK/SQLite:
process exits around claim/enqueue, policy changes after preflight, native transaction
failure before/after commit, cross-facade shared-cap competition, altered error
provenance and delayed/cancelled proof. Add probes when reading exposes another concrete
uncertainty. Synthetic transport does not establish Telegram's live decisions; label
malformed/local injections and do not substitute the earlier prototype adapter.

Create `pr-critic.md` here, preserving `critic.md`. First write current-session
`model`/`effort` YAML frontmatter, then one skill verdict (IMPLEMENT AS WRITTEN /
IMPLEMENT AFTER FOLDING THESE IN / REORDER — TEST BEFORE BUILD / DO NOT IMPLEMENT —
MEANING GAP or WRONG LAYER), an explicit §7 Gate ACCEPTED/REJECTED, falsifier and
affordability lines, then the high-level summary. Resolve affordable local experiments
before final acceptance. Record unqualified live premises separately and honestly.

Compute the Premise Inventory before findings: premise, first dependent step, waste
if false, scheduled test, cheapest earlier test/cost and covering versus non-covering
evidence; rank by waste. Include Restart Check (old failures/mechanisms/current design)
and Inherited Lessons with the order that satisfies each. Quote fresh probe output.

For each actual finding use sections, with two Risk paragraphs (plain consequence,
then exact paths/symbols/trigger), Severity, Category, Impact, NoobEng and Affected
areas. Every Medium/High needs quick/robust/long-term proposals, their required why
fields, unchecked selected/elegant/last_resort boxes and empty Why chosen/For future
notes. Phase3 separately chooses by reach/extent, names a real class before generalizing,
and applies the size/blocker gates. No invented risk count or style-only padding.

Every High/Medium must rest on code or reproduced behavior. Any High/Medium rejects
under CONTRIBUTING §7.3: record the result, post it, mark the PR draft and route to
§7.4 re-planning without ad hoc product fixes. Apply the skill's premise-gap handling
if that verdict is warranted. Consciously retain inherited Stage3/4 Lows without
misrepresenting them as new regressions. Commit and post the completed critique.
