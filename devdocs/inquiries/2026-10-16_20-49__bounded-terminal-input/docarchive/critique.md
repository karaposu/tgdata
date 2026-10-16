---
model: unknown
effort: unknown
---
# Critique — finite streaming input survives; canonical post-read limits do not

## User Input
_branch.md's four articulations, Sensemaking SV6 and Innovation's13 variants.
Evaluate the input contract needed before re-planning, not product merge readiness.

## Phase 0 — dimensions and frame prosecution
| Dimension | Weight | Observable success criterion |
|---|---|---|
| Requested usefulness | Critical | Finite oversized paste refuses without shortened credential; ordinary phone/code/password interaction remains |
| Framing correctness | Critical | Native fragmented bytes, edits, UTF-8, EOF and invalid-line remainder have explicit outcomes |
| Terminal/secret ownership | Critical, project-specific | Selected terminal remains hidden through owned input; exact modes restored or safe failure with no value |
| Stop/source/file separation | Critical, project-specific | No extra byte needed after Ctrl-C; no next auth/save from rejected input; existing file outcomes retained |
| Native feasibility/evidence | Critical for claims | Actual OS input/signal behavior and real consumer handoffs, not simulated success receipts |
| Parsimony | High | One private bounded input interaction; no unneeded general editor, producer protocol or auth rewrite |
| Scope honesty | Critical for claims | Qualified contexts and future-producer limit stated; no isolated-probe=full-product claim |

Frame premises prosecuted independently: (1) terminal input is needed—an external
credential installer would remove the requested conversation; (2) private ownership
can suffice—test exact modes and actual producer/backpressure rather than assume it;
(3) auth/file layers can remain—overflow has a native reproduction without them,
then selected real consumers test the new handoff. Alternatives G1/C1/G3 explicitly
challenge local scope and input timing. Broad secrecy means rejected owned bytes too;
it cannot mean control of all future writes after the command has exited.

## Phase 1 — landscape
Viable: byte-observable input plus bounded framing/discard and complete restoration.
Boundary: canonical timeout under a different timing policy; mature backend or
producer protocol under an actual richer consumer requirement; paste-only interface.
Dead: prefix acceptance, immediate overflow exit while knowingly ignoring a paced
remainder, unlimited accumulation, omitted overflow acceptance, universal frameworks
without a consumer. Unexplored: other OS/runtime/emulator implementations, advanced
editing and producer protocols. These are explicit support frontiers, not silent
claims required to establish this bounded host contract.

## External observations and prototype refinement
The delivery probe showed canonical input withholding incomplete lines, while
noncanonical input exposes bytes and applies partial-write backpressure. The native
writer accepted1022 of5001 requested bytes in one nonblocking call; every subsequent
probe honors partial writes rather than pretending the whole paste was delivered.

An inquiry-only streaming prototype then exercised the proposed value contract:
128 retained bytes,256-byte reads, strict final UTF-8, configured erase/clear/EOF,
invalid-line latch and discard to newline/EOF/stop. It disables canonical processing,
echo, literal-next/extended processing and software-flow control during input;
keeps the interrupt signal active; disables quit/suspend input bindings so those
unsupported controls cause a safe line refusal rather than abruptly abandoning
hidden modes. Original settings are retained and validated, not normalized silently.

The first native trial FAILED exact restoration. macOS had added PENDIN when
canonical processing was re-enabled: local flags1483 became536872395. Apple's
current tty.c also shows that transition and the flush clearing the flag. The
prototype was refined within this inquiry: restore canonical processing with echo
still off, flush pending input, then restore the complete original settings and
verify them. The final restoration is attempted even if the earlier phase fails.
No assertion was relaxed to ignore PENDIN. First source/log and diagnostic retained.

A second trial passed23 cases but its harness couldn't parse an EOF result because
the marker followed an unfinished prompt on the same line. The marker gained an
explicit leading newline; input code and acceptance assertions were unchanged for
the third complete run. It passed45 cases. A further adversarial check added input
queued before prompt invitation: the final prototype flushes after hiding modes,
before showing the prompt. All46 cases were rerun and passed, followed by seven
selected real LoginFlow/native-SRP/SQLite/ordinary-reader handoffs.

Observed final results (evidence/stream-result.json and flow-handoff-result.json):
- 129,5000,500000-byte overflow inputs and a paced5000-byte input refuse. Largest
  producer wrote500001 bytes including newline; reader observed500001, retained
  at most128 and read at most256 per chunk. No test timeout counted as success.
- Unicode/split UTF-8, scalar erase, clear-line and exact128-byte lines work.
  Overflow stays invalid after erase/clear; malformed encoding/unsupported controls
  release no value. Queued pre-prompt data and same-read trailing lines are discarded.
- Empty/partial EOF, Ctrl-C while empty or discarding, first/repeated restoration
  signals, both restoration stages and descriptor-close signals release no value.
- Two actual terminals confirm binding/restoration of the controlling terminal
  rather than stdin. ISTRIP and absent controlling terminal refuse.
- Three deliberately persistent cleanup faults correctly report restore failure
  with no value and observed changed modes. The harness repairs its own terminal
  afterwards; these are not three successful physical restorations.
- Real plain/2FA completion creates a native session that the ordinary reader
  reopens. Oversized phone requests zero codes; oversized password submits no
  CheckPassword; oversized save-retry confirmation preserves the prior file with
  one authentication and one failed local save. Stop during discard and first
  restoration stop return130 with no publication and exact modes restored.

These are finite-stream premise and selected integration observations, not the
future FULL combined prebuild. Old r6 product/candidate bytes stayed unchanged.
The new inquiry prototype includes instrumentation; it is not production code.

## Phases 2–3 — candidate prosecution, defense, collision and verdict

**G1 mature backend — REFINE, conditional reserve.** Prosecution: dependency plus
adapter does not prove exact lifecycle. Defense:broader editing may be safer than
homegrown frontend. Collision:46 native cases show a small declared interaction
is feasible; a named richer consumer could change the tradeoff. Target:qualify an
actual backend against the same ownership contract before claiming simplicity.

**F1 private byte observation — SURVIVE within qualified context.** Prosecution:
mode names do not prove fragmentation, transformation or restoration. Defense:
actual delivery/backpressure plus final native matrix establish observable bytes
and exact settled modes. Collision:the PENDIN failure required explicit settlement,
now tested rather than ignored. All critical dimensions pass for this contract.

**C1 canonical deadline — REFINE, alternate policy.** Prosecution:changes every
human prompt's timing and reports timeout without observing overflow. Defense:
small and stops indefinite waits. Collision:viable if bounded-time entry is requested,
but streaming handles the actual failure without imposing that new deadline.
Target:explicit user timing requirement and proof no accepted truncation/hidden tail.

**G2 complete editor — KILL for #50.** Prosecution:parsimony and support extent.
Defense:rich behavior familiar to users. Collision:basic erase/clear is demonstrated;
no cursor/history need justifies a general editor. Seed:revive a mature backend when
a concrete operator UI requires those controls.

**F2 bounded value/invalid-line discard — SURVIVE.** Prosecution:huge or fragmented
input may still lose a delimiter, editing may revive a prefix. Defense:actual
500001-byte delivered stream, paced input and invalid-after-edit cases observed;
partial writes honored, memory capped. Collision:unfinished/no-newline input remains
visibly invalid and cancellable; no claim that an endless producer completes itself.
This satisfies the requested finite-paste contract without accepting partial secrets.

**C2 no editing — REFINE reserve.** Prosecution:needless restart for ordinary typing
mistakes. Defense:minimal parser. Collision:configured scalar erase/clear works in
the tested boundary without a general editor. Target:revive only if required basic
editing becomes unqualifiable or the user explicitly chooses paste-only interaction.

**G3 producer handshake — REFINE, deferred.** Prosecution:requires producer/emulator
cooperation absent in ordinary terminals. Defense:can define a stronger completion
receipt. Collision:future-write limit is real, but newline/EOF/explicit stop suffices
for current finite input. Target:named cooperating producer protocol; no universal
all-future-input secrecy claim without one.

**F3 settled retirement — SURVIVE with refined native sequence.** Prosecution:
early restore exposes a paced tail; naive canonical restoration differs from the
snapshot. Defense:bounded discard retains no rejected secret, and staged restore
now handles actual kernel state. Collision:keep hidden until framing ends or stop;
flush queued input, verify exact modes before admission. Genuine OS failure blocks
admission and is reported. This is refinement of one owner's cleanup, not a new
supervisor or an assumption that cleanup cannot fail.

**C3 immediate overflow exit — KILL for this interaction.** Prosecution:it releases
the terminal while a known invalid line can still be arriving. Defense:minimal latency.
Collision:the paced native writer is a concrete reachable case; flushing cannot
remove its future writes. Seed:separate invalidation from terminal release.

**G4 universal conformance framework — KILL for this delivery.** Prosecution:
unsupported extent and no second consumer. Defense:broader portability evidence.
Collision:qualify named targets; do not use unbounded framework work as a substitute
for current observed behavior. Seed:per-target qualification on an actual new host.

**F4 native premise then full composition — SURVIVE.** Prosecution:small prototypes
can repeat earlier false confidence. Defense:their bounded claim is explicit;
next plan still requires complete composition before edits. Collision:selected real
handoffs strengthen feasibility without ticking the full-prebuild box. Tests remain
inputs to the next critic, not automatic promotion permission.

**C4 ignore overflow — KILL.** Prosecution:user explicitly says “survives oversized
pastes”; removing the failure does not meet that endpoint. Defense:normal login works.
Collision:wrong scope, not a low-priority polish item. Seed:qualify the stated edge
before product work rather than weaken acceptance to match old tests.

**Unbounded accumulation — KILL.** Prosecution:memory and secret-retention guarantees.
Defense:no length errors. Collision:no authentication input needs arbitrary retained
text; native stream discard supplies refusal without that cost. Seed:bound retained
state independently of total consumed input.

## Phase 3.5 — assemblies
Primary:F1+F2+F3+F4 SURVIVE, first-ranked. Prosecution:small parser can become an editor
or hide complicated cleanup. Defense:46 boundary cases and7 real handoffs, bounded
controls/storage, one existing input owner. Collision:explicit contract and scope
make the responsibility reviewable; exact native settlement is essential complexity,
not a reason to rewrite auth/storage. This supplies a qualified basis for the new plan.

Canonical-deadline assembly REFINE, second reserve under a different explicit timing
contract. Backend-plus-owner assembly REFINE if a richer context needs it. Neither
has stronger current evidence or a user requirement that displaces the primary.

## Phase 4 — accumulator, coverage and convergence
All13 variants and3 assemblies evaluated. Seven dimensions represented at concrete
failure planes:delivery, invalid remainder, edits, supported controls, restoration,
source admission and file effects. Mechanism-independence validated for primary
contract through actual native observations and consumer behavior; reserve backends
remain unqualified. Scope bounded to this native environment; no universal proof.

Adversarial rounds:C0 screened candidate regions; C1 native exact-mode failure
refined retirement; C2 tested no-edit/deadline/producer-protocol alternatives and
pre-prompt admission; C3 reran final46cases plus7handoffs and challenged inherited
auth/file scope. C2/C3 added no new candidate region; both retained the same local
assembly. This is one outer traverse iteration with repeated critique rounds,
not a claim of multiple full traverses. New information fell from concrete mode
semantics to explicit support boundaries. No critical contract caveat is hidden;
future complete-candidate qualification is a subsequent gate, not this inquiry's
claimed result. Nine failure modes checked; no assertion weakening or timeout success.

Signal:TERMINATE with the primary contract/direction, then Routelister/CONCLUDE and
the user-requested description update/re-plan. Manual8/8; PROCEED.
