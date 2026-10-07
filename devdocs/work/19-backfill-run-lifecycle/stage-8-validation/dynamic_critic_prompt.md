---
model: gpt-6-astra
effort: max
---
# Dynamic critique — Stage 8 / Gate D

Review plan `f502ea2` with description `863fbbc`, triage, the full lifecycle contract,
44-case matrix, actual public/fault/store/source interfaces and prior gate evidence.
Use this same warmed session, not a subagent. Confirm declared blockers before analysis.
This is validation of an implemented feature; do not invent runtime redesign work.

Question whether each claimed proof observes the real owner of the fact. Does the
public facade actually run? Does a SQLite commit really occur? Is receiver byte custody
complete before its receipt? Are complete snapshots retained, not only dedup counters?
Does a child really exit before recovery? Can an old response, receipt or command acquire
new authority? Distinguish acknowledged progress, source end, permission and timing.

Audit fault placement against real code: before/after admission, publication, ack,
empty completion, controls, recovery, abandonment and succession; ordinary exception,
cancellation, close/rollback failures and unavailable/corrupt data. No helper-created
state, successful boolean or fake provider result may substitute for a durable/server
observation. Existing tests may be reused as components, not relabeled public/live.

Challenge the LIVE plan. Independently freeze the oracle before tested reads; account
for shared SDK decoder dependence, date ties, actual page bounds, changed source view
and daily records arriving later. Check complete accepted sets, media hash/custody and
qualified origin. Stage-wide reservations must survive crashed workers/reruns and keep
the real account ledger authoritative, including locally blocked but reserved attempts.
No policy reset, source writes, joining or deliberate flood/ban is allowed.

Trace operation attribution and health. Local public state/control/replay/ack/recovery
must create no SDK RPC or false recovery. Clearly mark seeded health problems and local
send failures as INJECTED, never server facts. Account identity verification must not
silently repair a stale-cache issue or expose credentials. Keep prior gate originals.

Verify the selected backend/receiver and same-process lifetime boundaries are actually
those used by the gate. Namespace and receiver variants are explicit test composition,
not a production framework. Real waits/process restarts are separate from virtual clocks;
do not infer portable monotonic time or death from elapsed time. Check that resource
conditions stop execution rather than masquerade as a design failure or assumed PASS.

Compute a ranked Premise Inventory before choosing the verdict: first dependent step,
waste if false, scheduled test, cheapest earlier real test/cost, current coverage and
any non-covering stand-in. An affordable earlier falsifier requires REORDER even if
the content is sound. The existing public source/selected receiver can be exercised
before building the large matrix. A prior internal gate does not close that composition.

Create critic.md here with verified model/effort frontmatter (unknown if not derivable),
one verdict (IMPLEMENT AS WRITTEN / IMPLEMENT AFTER FOLDING THESE IN / REORDER — TEST
BEFORE BUILD / DO NOT IMPLEMENT — MEANING GAP or WRONG LAYER), then falsifier and
affordability. For REORDER specify the real experiment, cost, first dependent step,
disqualifying and passing observations. Follow with high-level summary, ranked premises,
Restart Check (observed failure, established mechanism, design response), Inherited
Lessons (lesson, satisfying step and order) and only real risk findings.

For every risk write two Risk paragraphs: plain/self-contained consequence first,
precise files/symbols/trigger second. Include Severity, Category, Impact, NoobEng and
Affected areas. Medium/High findings need actionable Quick/Robust/Long-term proposals,
why robust/long-term effective, initially unticked selected/elegant/last_resort boxes
and empty Why chosen/For future notes. A separate third pass only selects and annotates;
compare reach/extent, enumerate real other instances before claiming a class, and reject
unrelated framework expansion. Do not manufacture noise to force a mitigation count.

Check final evidence accounting: all 44 cases need scoped dispositions, aggregate issue
status must reflect actual stage artifacts, and a readiness audit cannot replace the
formal merge-check/PR critic. No unexplained substantive finding may be hidden under
"deployment assumption". If a meaning gap exists, follow critic-d's deprecation/blocker
procedure; otherwise hand the selected proposals/experiment to task-impl without
re-critiquing the fold. No PR or protected merge is implied.
