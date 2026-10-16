---
model: unknown
effort: unknown
---
# Decomposition — bounded input within one terminal lifetime

## User Input
_branch.md and saved Sensemaking SV6: establish framing under oversized input,
then use the established contract for a replacement #50 plan.

## 1. Coupling map
Strong cluster: terminal selection/settings, byte availability, nonblocking wait,
mode restoration and signal timing share one descriptor and lifetime. Do not split
these into separate owners. Strong cluster: byte count, UTF-8 boundaries, editing,
invalid-line state, delimiters and discard policy share one input-state machine.
Moderate boundary: framed value/error/stop crosses to the command only after the
terminal owner settles. Weak boundary: actual auth and publication preserve existing
contracts and need no knowledge of keyboard editing. Cross-cutting evidence depends
on the chosen interaction and native delivery rather than scalar helper returns.

## 2–3. Top-down boundaries and bottom-up validation
Identify questions about supported observation, value framing, retirement/handoff,
and qualification. These are reasoning boundaries, not four mandated modules.
Atoms: original fd/modes cannot be separated from restoration; an incomplete UTF-8
scalar cannot be independently accepted; an invalid-line tail cannot be a new prompt;
source action admission cannot precede retirement. Top-down cuts preserve these atoms.
Confidence HIGH at the contract boundaries. Q1/Q2 share an explicitly specified
byte/control contract; implementation may keep them in one private module.

## 4. Question tree
Root: How can one finite input be accepted or refused without kernel-line deadlock,
secret leakage during ownership or premature source admission?

### Q1 — Which terminal context supplies observable input and stop?
Verification: selected fd and foreground/mode support discoverable before source
work; delivery before newline measured; partial writes/backpressure honored; byte
transformations and controls explicit; signal wait remains responsive.

### Q2 — What exactly makes one input valid, invalid or complete?
Verification: retained-byte cap; exact UTF-8 policy; editing/EOF/control semantics;
no silent truncation; invalid content cannot recover through a trailing fragment;
finite oversized paste reaches a refusal; incomplete input remains stoppable.

### Q3 — When may the command release input ownership or admit another action?
Verification: hidden-mode lifetime includes invalid remainder; flush/readback/restore/
close failure outcomes; SIGINT at first/repeated cleanup boundaries; no value released
before settlement; source/file effects remain independent; future producer boundary
stated without an impossible all-future-input guarantee.

### Q4 — What evidence is sufficient to write and later implement the plan?
Verification: native premise probe covers sizes/chunks/controls/faults; known failed
histories retained; complete candidate prebuild remains before product changes;
real-component versus mocked-input evidence separated; support/runtime limits and
model provenance honest; replacement description/plan supersedes only false premise.

## 5. Interface map and assumptions
| From → to | Flow / direction | Required assumption made explicit |
|---|---|---|
| User/producer → Q1 | bytes, one-way | finite paste writes may be partial; newline/EOF/stop is meaningful; future writes after exit are external |
| Q1 → Q2 | byte fragments/control observations, one-way | no read-call=whole-line assumption; no undocumented stripping or literal-next transformation |
| Q2 → Q1 | continue reading/discard/finish, feedback | invalid input needs no unbounded retained payload; stopping can interrupt discard |
| Q1/Q2 → Q3 | value candidate, failure, framing completion, one-way | candidate is not yet an admitted credential; exact terminal resource still owned |
| Q3 → command | settled value/error/stop, one-way | terminal failures release no value; stop precludes subsequent auth/save |
| command → Q3 | sticky stop and settled-step admission, one-way | source cleanup remains owned; no arbitrary exception injected into terminal restoration |
| Q1/Q2/Q3 → Q4 | concrete observations and support contract | probing a parser alone does not prove OS delivery; probing input alone does not prove complete CLI |
| Q4 → later plan | established premises, residual qualification gates | native host proof is not cross-platform/live qualification; no failed experiment silently promoted |

## 6. Dependency order
Define Q1/Q2's byte/control contract together; compare mechanisms without treating
mode choice as proof. Q3 retains the old ownership principle but qualifies its new
framing boundary. Q4 consumes all three before writing the plan. No implementation
parallelism is proposed; reasoning dependencies do not authorize subagents.
The feedback between Q1 and Q2 is internal to one input interaction, not a cycle
between independent services. Source/file layers consume Q3's settled handoff.

## 7. Self-evaluation
Independence PASS at declared contracts; completeness PASS across input/end/stop/
release; reassembly PASS including runtime support and invalid-line determinations.
Tractability PASS (four bounded questions); interface clarity PASS (producer/timing
assumptions explicit); balance PASS (Q1/Q2 are difficult, Q3/Q4 substantial); confidence
PASS (atoms agree with top-down cuts). All seven failure modes checked. No extra
module/service/public API inferred. Manual7/7; proceed to Innovation.
