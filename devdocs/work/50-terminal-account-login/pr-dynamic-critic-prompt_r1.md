---
model: gpt-6-astra
effort: xhigh
---
# Fresh PR critic prompt — #50 / PR51

Subject: published PR51 diff, head69c240731e9f8dcee794e3f4a88372d8cd9af118
against dev77f2f53eba8bdc6922127a3b9118bf17de4efabf, together with the folded
revision2 step_by_step_impl_plan.md. Archive documents stay on
feat/50-terminal-account-login. Review in this warmed session, never a subagent.

Ultrathink. Judge soundness independently of the preceding fidelity PASS and
existing1,005 checks. Read all seven changed files in full and the actual
LoginFlow/session/native-SQLite/configured-reader interfaces they use. Read
triage, desc, declared blockers, critic, prebuild and verification records.
Do not patch product code or weaken tests during the review.

The core question is whether one deliberate command can preserve the truth of
three distinct outcomes: authenticated, locally prepared, and published. Attack
those ownership boundaries, including paths that the happy-path fixtures skip:

- Native candidate conversion must preserve exact key/DC/own identity, optional
  own cache and update state. Verify failure/retirement of the real SQLite object,
  including constructor and commit failures. A byte-containing file is not proof
  that the ordinary configured reader can use it.
- Creation/replacement authorization remains tied to the original destination.
  Check late sidecars, changed parent/target, no-clobber effects, old backup and
  persistence barriers, sync failures, closed writer, local retry and recovery
  material. Observe actual old/new bytes. Consider failure both before and after
  a syscall effect; syscall fault injection is not physical power-loss evidence.
- Source waits, invalid/expired input, unsupported action and uncertain replies
  must use current status. Known completion plus an error/cleanup failure must
  not accidentally request another code or publish an unsettled credential.
- First/repeated cancellation, failed retirement, pending stop during storage,
  EOF, confirmation and reporting failure must preserve the observed outcome.
  Test actual event-loop/SDK lifecycle and terminal mechanics where relevant;
  mocks that return the desired complete status do not establish behavior.
- Hidden input must refuse echo fallback; safe outputs must not print raw errors,
  credentials or unknown secret arguments. Check diagnostics on exceptional paths,
  not only ordinary success. Scope claims are local POSIX/trusted directory with
  stopped readers, not distributed exclusion, active rotation or universal crash
  recovery. Do not re-derive these declared exclusions as findings.
- Confirm installation/module parity, package/runtime compatibility, independent
  worker/readers and no accidental dependency or version change. Question excess
  abstraction or duplicated policy using concrete other consumers, not imagined
  future frameworks. Identify documentation promises unsupported by code/probes.

Write fresh independent probes under pr-probes/ and run against the exact published
product worktree. Use real LoginFlow/native SDK/SRP/session/filesystem/reader with
controlled source transport; forbid network. Count source effects and assert
native outcome and cleanup. Existing tests are evidence to inspect, not a substitute
for probes. Quote compact actual output; retain scripts/results. Log no credentials.

Create pr-critic.md beside the plan (never overwrite critic.md), with first-line
YAML model/effort from current session metadata, then one skill verdict:
IMPLEMENT AS WRITTEN; IMPLEMENT AFTER FOLDING THESE IN; REORDER — TEST BEFORE BUILD;
or DO NOT IMPLEMENT — MEANING GAP (WRONG LAYER variant if justified).
Directly beneath give Falsifier and Affordable now. Affordable unresolved shape
falsifiers force REORDER and a named real-component experiment, its cost, first
step it must precede, passing/disqualifying results. Completed probes are evidence,
not an unrun experiment. A genuine premise failure invokes skill Phase2.5; do not
paper it over with mitigation tiers.

Place a high-level summary and explicit PR gate PASS/REJECTED before detail.
Then Premise Inventory ranked by waste if false: premise, first dependent step,
waste, scheduled test, cheapest earlier test and covering/non-covering evidence.
Carry declared live/Python3.7 limitations unchanged. Include Restart Check and
Inherited Lessons mappings, distinguishing the two resolved plan findings from
new defects. One Medium/High rejects under CONTRIBUTING §7.3 and requires revision3
re-planning under §7.4; the critic must not fix it in place.

For each real risk use sections, not tables: two Risk paragraphs (self-contained
plain consequence first, exact paths/symbols/triggers second), Severity, Category,
Impact, NoobEng, Affected areas. Medium/High need quick/robust/long-term proposals,
with why this is robust / why this is long term effective. Under each proposal
emit unticked selected/elegant/last_resort and empty Why chosen / For future notes.
Commit Phase2 before Phase3. Phase3 only selects proposals and fills notes; it must
not change risks/severity. Enumerate actual other instances before claiming a class;
compare reach/extent, reject speculative generalization, split oversized framework
work, choose robust when no genuine shared class exists. Low findings are explicit
conscious deferrals. No findings means Phase3 has no mitigation selection to make.

Record exact base/head, read coverage, model proof, in-session execution, fresh
probe counts/results, tested limits and whether the issue checklist is honest.
A PASS requires observed evidence, not confidence from the implementation history.
