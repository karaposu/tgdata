---
model: gpt-6-astra
effort: xhigh
---
# #50 second rejected PR gate — return to description/traverse

Current product/PR51 head34907d4 remains unchanged and draft. Renewed fidelity
merge-check6314d33 PASS; fresh soundness review REJECTED with one Medium.
Previous rejected PR critique is preserved in pr-critic_r1.md.

The first rejection concerned task/event-loop interruption. Its real native-SRP
falsifier now passes. The second concerns terminal-mode ownership: getpass can be
restoring after ordinary input or EOF while the outer command still labels the
whole call “input.” Its first SIGINT then interrupts that restoration, leaving
echo disabled after main returns. Repeated-signal protection only covers the
history where an earlier signal already changed the outer flag.

The missing question for the description/traverse is: **which component retains
the exact terminal descriptor and original modes until restoration has completed,
regardless of how reading ended or when the first stop arrived?** A high-level
input phase is not evidence that this resource has been retired.

Keep the useful scope: one deliberate CLI, existing LoginFlow, native session
publication, no background auto-login or general worker supervisor. Reassess the
hidden-input ownership contract and its observation boundary before selecting a
mechanism or writing another plan. Use the actual normal-return/EOF/first-SIGINT
failures and the passing read-time signal control; preserve all old evidence.
The selected robust direction is explicit local terminal ownership, not a preselected
implementation or permission to fix the current code in place.

CONTRIBUTING §7.4: “If the second round is rejected too, stop re-planning.” Next is
that upstream description/traverse pass, then only a plan justified by its result.
No automatic revision5, product patch, merge, release or real login occurred here.
The terminal probes used only owned synthetic PTYs and restored their state after
recording the failure. Existing1,010-check verification does not cover this newly
observed first-signal restoration history.
