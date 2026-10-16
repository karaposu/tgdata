---
status: active
model: unknown
effort: unknown
refines: devdocs/inquiries/2026-10-16_19-25__terminal-login-ownership/finding.md
---
# Finding: reject oversized input while still owning the arriving line

## Question

How should #50's terminal login command survive an oversized paste, and what can
we establish before writing another implementation plan?

## Finding Summary

- Read input as arriving bytes, without waiting for the terminal to assemble a
  whole line. A small private framer handles the supported input controls.
- Retain at most128 UTF-8 bytes for a value. Once a line overflows, it stays invalid;
  never submit its prefix or a later shortened tail.
- Keep echo disabled while discarding the invalid line through Enter, EOF or Ctrl-C.
  Discarding bytes does not require storing them.
- Clear queued input before inviting a prompt and during retirement. Restore and
  verify the exact terminal state before releasing any value.
- Retain LoginFlow authentication and native session publication. Their existing
  behavior works with this input boundary in the selected real-component probes.
- The premise is established on the tested native host:46 input cases and7 real
  handoff cases passed their expected outcomes, including a500,000-byte paste.
- Write a replacement plan from this contract. A fresh plan critique and the full
  combined candidate prebuild remain mandatory before product implementation.

## Changes from Prior

**Prior path:** `devdocs/inquiries/2026-10-16_19-25__terminal-login-ownership/finding.md`.
**Trigger:** revision6's full prebuild disproved its canonical-input assumption,
then the user requested input handling that survives oversized pastes and a re-plan.
**Preserved:** one private terminal owner, nonthrowing stop intent, settled value
admission, existing authentication/native publication and full prebuild requirement.
**Changed:** mode selection alone is insufficient; input framing and invalid-line
completion are explicit. Native restoration also needs a measured transition back
to canonical processing before echo is restored.
**New:** bounded streaming, deliberately basic editing, invalid-line discard,
pre-prompt queue disposal and native producer/backpressure evidence.
**Migration:** keep revision6 deprecated and all failed evidence. Update desc.md and
write revision7; do not promote the inquiry prototype or patch the old candidate.

Action drift from the prior finding is explicit:

- MUST drift: prior “revise #50's description around explicit terminal ownership
  and independent stop, authentication and publication outcomes.” New “revise #50's
  description and write a replacement plan from the qualified streaming-input
  contract.” Rationale: the user now requests re-planning after the new premise is
  established; input framing was the missing behavior revealed by the full prebuild.
- MUST “qualify the complete candidate with real LoginFlow, native SQLite,
  filesystem publication, ordinary reader reopen and owned terminal interaction”
  remains unchanged. The new native observations do not clear that gate.
- MUST drift: prior “retain publication, retry and secrecy tests, and cross input
  exit reasons with first/repeated stops and resource acquisition/restoration
  failures.” New “retain source/publication/secrecy tests and add native framing,
  backpressure, queue disposal and staged restoration to the full prebuild.”
  Rationale: the false premise lived in byte delivery and line completion, not
  only in signal cleanup; those observations must join the acceptance surface.
- COULD live Telegram delivery/2FA remains gated by full local composition and an
  explicitly authorized exclusive account setup. No scope expansion.

## Finding

### 1. A bound applied after reading cannot constrain input that is withheld

The command asks for a phone number, a Telegram code and sometimes a password.
Revision6 tried to preserve the terminal's normal line editing and reject a line
longer than128 bytes after reading it. In canonical mode, the terminal assembles
that line before the application can read it.

The failed prebuild wrote5,000 bytes followed by newline, but the terminal delivered
no readable line before the test deadline. The application never reached its length
check. That result remains recorded in the
[failed prebuild](https://github.com/karaposu/tgdata/blob/2317623/devdocs/work/50-terminal-account-login/critic.md).

This inquiry compared delivery directly. In noncanonical mode, the application
could read before newline. A nonblocking writer accepted only1,022 bytes from a
5,001-byte request while the queue was full. That is backpressure: the producer
must continue from the number actually written. The later experiments honored all
partial writes and verified both the total sent and the total consumed.
See [delivery observations](evidence/delivery-result.json).

### 2. Rejection and input completion need different states

The private reader should accumulate a bounded candidate value. An oversized line
switches to an invalid state and clears the candidate. Remaining bytes are consumed
without being retained. Enter completes refusal; EOF or Ctrl-C stops the interaction.
No overflowed line becomes valid again through erase, clear-line or a plausible tail.

This keeps the terminal hidden while a finite paste is still arriving. Returning
immediately at byte129 would knowingly restore echo before a paced paste finished.
A previous flush cannot erase bytes the producer has not sent yet.

An unfinished line may still wait for its delimiter, just as ordinary input waits
for Enter. The difference is observable: it is already rejected, retains no growing
secret and remains cancellable without another input byte. The command does not
promise that an endless producer will finish itself, or impose an unrequested
whole-prompt deadline on normal human entry.

The supported interaction stays small: strict UTF-8, the terminal's configured
erase and clear-line controls before overflow, Enter, EOF and Ctrl-C. Erase removes
one Unicode scalar, not a grapheme cluster. Cursor/history navigation and other
control sequences are refused; they are not silently added to passwords. The
native experiment disables extended literal-next and flow-control processing during
input, and prevents quit/suspend input keys from abandoning hidden terminal state.
All original settings remain owned for restoration.

### 3. Exact restoration includes native transition behavior

The first streaming trial failed its exact-mode assertion even on ordinary input.
macOS sets a pending-input flag when canonical processing is restored. Ignoring
that bit would weaken the existing contract; the experiment retained the failure.

The qualified sequence restores canonical processing while echo is still disabled,
flushes the pending input, then restores the complete original settings and checks
them. The final restore is attempted even if an earlier cleanup phase fails. This
matches the observed native state transition and the relevant
[Apple terminal implementation](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/tty.c).

Queued input is also flushed after hidden mode is established and before a prompt
is invited. This prevents previously queued bytes from answering a new prompt.
Data already read after the first delimiter is discarded, as is remaining queued
input at retirement. A value leaves only after exact restoration and descriptor
release have been established.

A real cleanup failure remains a failure. The probe's three deliberately persistent
cleanup failures returned no value and reported changed terminal state; the test
harness repaired its own synthetic terminals afterwards. These outcomes are not
counted as successful physical restoration.

The temporal boundary is explicit: the command protects its owned interaction and
discards queued input. It cannot control arbitrary future writes after it returns.
A stronger producer-completion guarantee would require a cooperating input protocol.
Ordinary operators should supply one prompted input at a time.

### 4. Native and consumer evidence supports re-planning

The final native matrix passed46 cases. It includes exact limits, Unicode and
fragmented UTF-8, basic editing, invalid encodings/controls, queued input, two distinct
terminals, EOF, first/repeated signals, disposal cancellation and cleanup failures.

The largest paste contained500,000 data bytes plus newline. The reader consumed all
500,001 delivered bytes, retained at most128 value bytes and read at most256 bytes
per chunk. A paced5,000-byte paste also refused with exact restoration. Neither
returned a prefix or required a timeout kill.

Seven selected handoff cases use the real LoginFlow API, native Telethon SRP password
calculation, session conversion, filesystem publisher and ordinary configured reader.
Only Telegram transport responses are controlled; network connections are forbidden.
Plain and2FA logins save sessions that reopen. Excess input at phone/password/local
retry confirmation never submits that value or damages the old session. Cancellation
while discarding and first interruption during restoration preserve the stop contract.

Results: [46 native cases](evidence/stream-result.json),
[7 real handoffs](evidence/flow-handoff-result.json), [source manifest](evidence/manifest.json).
The native-mode failure and an EOF result-marker harness correction are preserved
with their source snapshots and logs. The exact-mode assertion was never relaxed.

These experiments establish a viable input contract. They are not the next full
combined prebuild, a new PR critique or permission to publish the prototype.

## Inherited Commitments Re-test

- **Commitment:** retain terminal ownership until restoration is established.
  **Source:** prior ownership finding, Finding.
  **Re-test status:** RE-TESTED — commitment confirmed but frame revised.
  **Evidence:** first native PENDIN mismatch, followed by staged exact restoration
  in46 cases. Mode transition is part of settlement, not merely a final setter call.
- **Commitment:** use nonthrowing stop intent with a controllable wait.
  **Source:** prior ownership finding, Finding.
  **Re-test status:** RE-TESTED — commitment confirmed.
  **Evidence:** native first/repeated signals and real CLI stop during discard;
  no extra byte and no timeout kill supplied the successful stop.
- **Commitment:** canonical editing plus a small post-read limit is sufficient.
  **Source:** failed revision6 plan and current failed-prebuild critique at2317623.
  **Re-test status:** RE-TESTED — commitment found INVALID.
  **Evidence:** new delivery probe again observes canonical withholding; streaming
  experiments observe and reject the full finite paste instead.
- **Commitment:** terminal transformations must not silently change input.
  **Source:** critic_r5.md, R1's native ISTRIP witness and selected refusal.
  **Re-test status:** RE-TESTED — commitment confirmed.
  **Evidence:** actual ISTRIP refusal, exact UTF-8 values, split encoding/control
  cases and supported-mode checks in the native matrix.
- **Commitment:** keep existing authentication/native publication boundaries.
  **Source:** prior ownership finding, retained component responsibilities.
  **Re-test status:** RE-TESTED — commitment confirmed.
  **Evidence:** seven actual consumer handoffs, including native2FA, reader reopen,
  prior-file preservation and zero next source action from rejected inputs.
- **Commitment:** retain the complete prior source/storage failure and durability rules.
  **Source:** prior ownership finding and historical full prebuild.
  **Re-test status:** INHERITED-WITHOUT-RE-TEST.
  **Reason:** selected handoffs do not rerun the entire failure matrix. Product bytes
  are unchanged; the complete matrix remains required in the next combined prebuild.
- **Commitment:** full candidate qualification precedes product implementation.
  **Source:** prior finding's MUST actions and failed-prebuild critique.
  **Re-test status:** RE-TESTED — commitment confirmed but frame revised.
  **Evidence:** native-mode refinement and framing cases show why both local premise
  evidence and complete composition are necessary; include both in the next plan.
- **Commitment:** live source/native3.7 claims require separate evidence.
  **Source:** prior finding's limits and COULD action.
  **Re-test status:** INHERITED-WITHOUT-RE-TEST.
  **Reason:** no real Telegram login or alternate native runtime was used here.

## Next Actions

### MUST

- **What:** revise #50's description and write a replacement plan from the qualified
  streaming-input contract.
  **Who:** task-desc and task-plan in the existing #50 work folder.
  **Gate:** now, after this inquiry; before any replacement product implementation.
  **Why:** replace the disproved premise with concrete behavior and support bounds.
- **What:** qualify the complete candidate with real LoginFlow, native SQLite,
  filesystem publication, ordinary reader reopen and owned terminal interaction.
  **Who:** fresh plan critic and a later full combined prebuild.
  **Gate:** after critique/fold and before product edits.
  **Why:** prevent these selected probes from being mistaken for whole-command proof.
- **What:** retain source/publication/secrecy tests and add native framing,
  backpressure, queue disposal and staged restoration to the full prebuild.
  **Who:** the next plan/prebuild and permanent offline tests.
  **Gate:** complete candidate qualification, then product verification before reviews.
  **Why:** preserve earlier findings while covering the actual new failure plane.

### COULD

- **What:** qualify live Telegram delivery and optional2FA with an isolated account.
  **Who:** maintainer and implementation agent.
  **Gate:** explicit authorization and an exclusive session setup.
  **Why:** supplement controlled transport evidence.
  **Depends-on:** MUST “qualify the complete candidate.” GATED until local composition passes.

### DEFERRED

- **What:** canonical prompt deadlines, paste-only interaction or a richer terminal backend.
  **Gate:** an explicit operator timing/editing requirement or a required context that
  the bounded reader cannot qualify.
  **Why (if revived):** meet a concrete interaction need with a different tradeoff.
- **What:** producer handshake/bracketed-paste protocol and broader platform support.
  **Gate:** a named cooperating producer or additional host/runtime becomes required.
  **Why (if revived):** support stronger completion semantics or new execution contexts.
- **What:** generic editor/supervisor, custom-store CLI, durable resume or reader rotation.
  **Gate:** a separate named consumer and established ownership/backend contract.
  **Why (if revived):** serve additional workflows without silently expanding #50.

## Reasoning

The bounded streaming assembly survives because it handles the observed overflow
without arbitrary prompt deadlines, unbounded retained data or a general editor.
Discarding invalid input while retaining its terminal owner joins two responsibilities
that must finish together, while leaving authentication and file publication separate.

A canonical timeout is a legitimate alternative policy. It bounds waiting but does
not observe overflow and changes the time available for every ordinary prompt.
There is no requested timing requirement that outweighs the now-demonstrated reader.
A mature backend remains a reserve when richer controls become necessary; its
cleanup still needs proof and its maturity alone would not close this contract.

Removing all editing is smaller but needlessly reduces usability when basic erase/
clear works within the bounded parser. A complete Unicode editor or universal terminal
conformance framework adds unrequested scope. Neither is needed for a hidden value.

Immediate overflow exit was rejected because it restores the terminal before a known
paced remainder finishes. Unlimited accumulation was rejected because finite auth
values do not justify unbounded memory and secret retention. Ignoring the overflow
test was rejected because it directly contradicts the user's requested behavior.
A producer handshake could offer a stronger boundary, but no such producer contract
exists here and ordinary finite input does not require inventing one.

## Open Questions

### Monitoring
The next complete candidate must retain the bounded parser and exact cleanup behavior
without inquiry instrumentation, and preserve all source/publication/entry-point cases.
The private reader must not grow into a general frontend through speculative controls.

### Blocked
Current-turn §9 model/effort verification remains pending. Live Telegram setup and
native Python3.7 execution remain separately unqualified; no prior stamp substitutes
for current evidence.

### Research Frontiers
The current POSIX full page was unavailable; primary excerpts, Python API text,
Apple source and actual native observations are distinguished. Other hosts/emulators
and stronger producer protocols require their own observations.

### Refinement Triggers
If the full candidate cannot preserve the measured framing/retirement contract,
return to that concrete failed premise. If a required interaction needs cursor/history,
nonstandard control binding or a longer supported value, reconsider the input policy
or backend explicitly instead of silently weakening a test.

## Source Input

<details>
<summary>Raw user input</summary>

```text
Next: establish input handling that survives oversized pastes, then re-plan
```

</details>
