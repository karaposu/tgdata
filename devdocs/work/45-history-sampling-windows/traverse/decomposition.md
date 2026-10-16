# Decomposition — #45 (DV1)

## User Input
_branch.md and committed sensemaking.md: bounded source acquisition across days plus reproducible selection over captured content, with qualified coverage and existing operational contracts.

## 1. Coupling map
High coupling: day visit order, source offsets, request/message limits and per-day coverage; captured content, identity and canonical replay validation; sample allocation, eligibility, rank ordering and unit omissions; expected owner, admission, health and cleanup (existing cluster). Moderate coupling: a portable capture contract separates collection from selection. Weak coupling: caller-specific topic logic and downstream human/LLM use. No required coupling: durable sync/backfill receipts, archives, discovery scheduling or distributed leases.

## 2. Top-down boundaries
P1 portable captured evidence; P2 bounded day-distributed acquisition; P3 deterministic selection and unit disclosure; P4 public operational composition. P1 is an immutable interface, not another storage engine. P2 owns source decisions; P3 cannot promote coverage. P4 reuses current lifetime/admission authorities rather than becoming a supervisor.

## 3. Bottom-up check
Atoms: message ID+content/date; group/account identity; request limit+charge; day boundary+source-end witness; selection policy+eligibility decisions; album ID+observed members. Each remains internally coherent. P1/P2 share a contract but not hidden live SDK objects. P1/P3 share stable data rather than a mutable source iterator. P2/P4 share a verified handle rather than cached account identity. Top-down/bottom-up agree: all four boundaries HIGH confidence. Do not split page validation from accumulator acceptance; their atomicity is one piece.

## 4. Question tree with verification criteria
Root: how does the caller obtain useful period-distributed reading material and reproduce it without conflating omitted, unavailable and never-read data?

| Piece | Question | Verification criteria |
|---|---|---|
| P1 | What captured input and evidence can be retained and replayed? | Exact group/account/window; raw content/IDs/dates; limits and per-day states; canonical portable identity; immutable getters; strict bounded reload; no receipt semantics. |
| P2 | How can a finite reader give requested days an explicit opportunity? | Deterministic visits and hard request/message bounds; empty-day cost; cap-shorter-than-day-count behavior; date/ID pagination; source-end/unknown/incomplete detection; no silent refund-driven infinite loops. |
| P3 | How does a stable selection cover captured days and explain its omissions? | Named algorithm/version; exact size/order/tie rules; sparse redistribution;599/300 counterexample; same-input/decision replay; explicit raw/post unit and observed-album/trail semantics; eligibility never means source coverage. |
| P4 | How do public calls preserve account and failure behavior? | Pre-I/O validation, one verified owner, unchanged budgets/waits/heartbeat, no cursor/ack side effects, original source/cancellation outcome with retained validated prefix, no live callback nondeterminism hidden as replay. |

## 5. Interface map and hidden assumptions
- P1→P2: normalized window/value contract and resource bounds. Assumption: acquisition records facts, not a claim that every planned day was examined.
- P2→P1: validated dated content, per-day requests/slots/end reasons and collection times. Assumption: partial capture is valid evidence; an invalid page contributes nothing to accepted content. Charged work and accepted data may differ on failure.
- P1→P3: portable immutable content and explicit eligibility decisions. Assumption: only local deterministic facts influence selection; fresh source calls are forbidden during reselection.
- P3→caller: selected original observations, policy/version and omission metadata. Assumption: omitted members are intentional within captured input, while unknown source members remain unknown; selection size is not completeness.
- P4→P2: existing verified client and admission/liveness scope. Assumption: neither collector nor selector mutates shared policies, authenticates interactively or invents account ownership.
- P2→P4→caller: normal capture or original failure with available capture best effort. Assumption: cleanup cancellation remains cancellation, not guaranteed durable delivery.
- Caller→P3: optional explicit eligibility set or captured decisions. Assumption: a predicate's identity is not enough to reproduce its answers; placement must make that visible.
No dependency on progress-store publication or acknowledgment crosses these interfaces.

## 6. Dependency order
Set P1 meanings and P3 unit/selection policy before choosing P2's retained shape. Define those contracts together if necessary, then prove P2/P4 real-component feasibility before product work. P3's pure arithmetic can be validated against fixed captures independently once P1 is defined. Integration reconstructs request→owned distributed capture→stable selection→caller. No runtime cycle or hidden storage prerequisite.

## 7. Self-evaluation
Independence PASS with explicit interfaces; completeness PASS across all issue outcomes; reassembly PASS. Runtime determination is explicitly assigned: P2 establishes visited/end/capped/unknown buckets and limits, P3 establishes eligibility/quotas/unit omissions, P4 verifies owner and preserves outcome. Tractability PASS; interface clarity PASS; balance PASS (P2/P3 are the substantive pieces, not one unbounded engine surrounded by trivial tasks); confidence PASS. All seven failure modes checked. Stop at four directly verifiable questions rather than fragmenting algorithms into separate authority layers. Manual structure7/7, full evaluation7/7. PROCEED to Innovation.
