---
model: unknown
effort: unknown
---
# Sensemaking — input completion and terminal retirement are different boundaries

## User Input
`_branch.md`: establish oversized-paste handling and then re-plan #50.

## SV1 — baseline
The failed command needs a way to observe excess input before the kernel withholds
its entire line. Switching input mode initially looks like the remaining change.

## Phase 1 — anchors
- Constraints: no truncated credential admission, bounded retained secret, no echo
  fallback, Ctrl-C without another input byte, exact restoration or truthful failure.
- Insights: a byte-length check only constrains bytes already observed; a flush only
  discards bytes already queued; application memory and terminal queue are different.
- Structural points: producer → terminal processing/queue → reader/framer → settled
  value → LoginFlow; terminal restoration is separate from rejection of a value.
- Principles: observe actual delivery and effects; source/file outcomes do not become
  terminal outcomes; private CLI ownership does not imply general editor support.
- Meaning nodes: bounded input, invalid line, line completion, producer completion,
  stop, retirement, supported editing. These are ordinary input concepts, not a new
  public framework. H4/H5: “bounded” and “complete” need independent definitions.

## SV2 — anchor-informed
An input bound alone does not define how an invalid line finishes or what happens
to its trailing bytes. The command must prevent rejected input from becoming the
next prompt's value and avoid restoring echo while knowingly draining that line.

## Phase 2 — perspectives and new anchors
Technical: new delivery_probe.py observes canonical10bytes/no-newline →0 readable;
noncanonical →10 readable. Canonical5001-byte write →0 readable. Noncanonical
nonblocking write accepts1022 of5001 and exposes all1022: the producer must honor
partial writes. This is actual backpressure, not evidence that5001 were delivered.
Human: Backspace/clear-line/Enter/Ctrl-D/Ctrl-C expectations matter; hidden input does
not need history, cursor navigation or visual redisplay to provide basic correction.
Risk: returning immediately at byte129 could restore echo while the rest of a paced
paste is still arriving. Discarding the rest is an ownership obligation, not storage.
Resource: bounded storage need not mean bounded total consumed bytes or bounded
human wait time. A finite producer can be drained without retaining its content.
Strategic: a new general terminal library would add a public/dependency lifecycle;
no second consumer requires that now. A private parser still needs explicit scope.
Ethical/systemic: never print rejected bytes or submit a shortened password. Secret
handling includes rejected input, not only successful authentication strings.
Internal consistency: no-truncation conflicts with accepting a prefix; prompt timeout
can safely refuse but cannot claim to detect byte count it never observed.
Frame-exit completeness: inherited “ownership” spans terminal, auth action and file
publication. Enumerate producer/emulator/kernel/application ownership too. The
application can flush queued bytes; it cannot erase FUTURE writes after it exits.
Relocate producer behavior to supported interaction/preconditions, not an invisible
promise. Strong counter “never return until absolutely no future byte can arrive”
has no observable completion proof without an extra producer protocol. A newline
is a line boundary, not a proof that all future user input has ceased. No further
residual layer is needed for this scoped command.
Phase/calibration: only native macOS/Python3.11 evidence exists; runtime input
behavior on another host requires qualification. Passing the isolated primitive
still does not qualify complete auth/file/terminal composition.
H1/H2/H3/H7: modes, helper libraries, changed timing contracts and smaller interaction
remain candidates; no choice is fixed merely by the previous plan's terminology.

## SV3 — multi-perspective
The problem is framing one eligible input and retiring its terminal lifetime. It
requires explicit handling of invalid-line remainder, while recognizing that no
terminal reader can control input a producer sends after the reader has exited.

## Phase 3 — ambiguity collapse

### A1 — does “survive” mean accept arbitrary pasted text?
Counter: accepting any length is simpler than refusing. Structural objection:
authentication inputs are finite values; unbounded accumulation adds memory/secret
retention without user value. Resolution HIGH: excess must refuse, never shorten.
Fixed: no value admission from an overflowed line. Excluded: truncate-and-submit.
Dependent: input framing and acceptance. Model change: refusal is a valid outcome.

### A2 — does changing ICANON alone solve the problem?
Counter: native bytes become available, so the old post-read code can stay.
Objection: reads can split lines and UTF-8, include multiple lines, and require
application editing/EOF interpretation. Resolution HIGH: byte observation is only
one premise; explicit framing/retirement is required. Fixed: no read-call=whole-line
assumption. Dependent: parser and native tests. Model change: a protocol boundary.

### A3 — must overflow immediately restore the terminal?
Counter: fastest error is simplest. Objection: producer may be halfway through a
paced paste; deliberate early restoration exposes known remaining input. Resolution
HIGH: distinguish rejecting a value from ending ownership of its arriving line.
Fixed: invalid-line state; no later tail becomes a credential. Excluded: prefix return.
Dependent: discard/stop policy. Model change: rejection need not retain payload.

### A4 — does “bounded” require a timeout for every human prompt?
Counter: otherwise waiting is unbounded and therefore another hang. Objection:
ordinary interactive input intentionally waits for Enter/EOF/stop; meaningful progress
and a responsive stop differ from a lost-delimiter deadlock. Resolution HIGH: bounded
memory and cancellation are required; an overall input timeout is an optional policy,
not an automatic inference. Fixed: specify what is bounded. Excluded: timeout-kill
success. Dependent: acceptance schedules. Timing policy remains for Innovation.

### A5 — can flushing guarantee secrecy of all later input?
Counter: flush before restore solves late-paste leakage. Objection: delivery probe
flushes then writes a new line, which remains readable. No syscall acknowledges a
future producer's completion. Resolution HIGH: protection covers the owned lifetime;
queued input is discarded, future writes require a producer protocol or operator
cooperation. Fixed: no universal future-write guarantee. Dependent: scope/tests/docs.
Model change: temporal boundary is explicit rather than silently impossible.

### A6 — do prior ownership/source/file conclusions survive?
Counter: repeated failures mean rebuild the command/auth layer. Objection: overflow
is reproduced without auth/file components; source/file outcomes remain independent.
Resolution HIGH: keep resource restoration and LoginFlow/native publication; re-test
input framing. Fixed: no causal auth rewrite. Dependent: bounded scope and new plan.

### A7 — is the5000-byte case the whole problem?
Counter: add a case-specific guard and stop. Objection: pre-newline delivery, partial
writes, chunk splits, editing, typeahead and continuous producers share framing but
not that payload size. Resolution HIGH: test the broader finite-stream pattern.
Fixed: vary size/chunking/delimiters and stop timing. Excluded: smaller test payload.
Dependent: native probe and full prebuild matrix. Model change: no case-number patch.

## SV4 — clarified
The replacement must observe and frame a finite input without silent alteration,
keep invalid content inadmissible while settling the input lifetime, and expose
real stop/restoration outcomes. Future producer activity lies outside returned
ownership; exact context limits must be written rather than implied.

## Phase 4 — degrees of freedom
Fixed: private resource owner; secret-free diagnostics; no auth/storage rewrite;
finite input values; no prefix acceptance; actual signals/restoration evidence.
Eliminated: canonical post-read cap alone, immediate prefix return, “flush future
bytes,” equating a process timeout/kill with a successful stop.
Viable for later comparison: explicit streaming framing; guarded mature input
component under the same ownership; canonical input plus a declared refusal deadline;
external/file-based input only if it preserves the requested terminal user value.
Open: exact editing controls, per-line limits, invalid-line completion policy,
support breadth and backend. These are bounded solution choices, not proven outcomes.

## SV5 — constrained
Separate byte observation, value framing and terminal retirement, but keep their
resource lifetime cohesive. Choose a backend only after it demonstrates the finite
paste/partial-write/stop behavior rather than assuming mode names prove it.

## Phase 5 / SV6 — stabilized
The missing contract is how one input line is accepted or rejected while its bytes
are still arriving. The command must cap retained data, prevent invalid remainders
from being submitted, remain cancellable and restore its exact terminal before
handoff. Existing auth/file boundaries remain downstream of that handoff.

Unlike SV1, merely selecting a terminal mode is not enough. Producer behavior and
input framing now have explicit roles. H6 accommodation: the initial “one mode bit”
model was replaced, not patched. No further model change arose from source/file,
resource and scope counterchecks. Seven ambiguity pairs resolved; mechanism choices
remain explicitly open for Innovation. Five anchor types, nine perspective families;
last source/file/scope checks confirmed rather than adding a new anchor class.
Six failure modes checked; native observations prevent self-reference/status-quo
reasoning. Manual8/8. Proceed to Decomposition.
