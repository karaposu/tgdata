---
model: gpt-6-astra
effort: max
---
# Dynamic critic prompt — #7 Stage 1

Review this folder's revision1 plan.md against desc.md, traverse/finding.md,
current dev95 code and installed Telethon1.45.0. Same-session review, no delegation.
Create `critic.md` here with model/effort frontmatter, document verdict, falsifier
and affordability, high-level summary, ranked Premise Inventory, Restart Check,
Inherited Lessons, and risk sections. Use critic-d's four verdict families.

Compute premises before risks. For each: premise, first dependent step, wasted
work, scheduled test, cheapest earlier test and present coverage. Distinguish
observing real SDK composition from a fake that supplies the desired behavior.
If an affordable falsifier remains after its first dependent build step, choose
REORDER — TEST BEFORE BUILD; specify real-component experiment, cost, precedence,
passing and disqualifying observations. Do not confuse synthetic Telegram replies
with a live-server test, or replace the local SDK mechanisms being tested.

Challenge the restarted design itself. It must address expected B/cache A/actual B
and expected A/actual B at operation entry, not merely rename events. Health remains
Stage 2; the present feature cannot claim to fix the old public health summary.
Check that each cited former failure is addressed here or explicitly allocated to
a later stage. Read the actual factory, BudgetClientMixin, StoredSession and SDK
connect/get_me/_call/disconnect/_on_login paths before claiming compatibility.

Prosecute these concrete boundaries:

- Does constructor-time policy apply when connect internally calls get_me,
  GetState and GetDifference? Are original RPC failures preserved? Is server
  backoff honestly distinguished from automatic flood sleeps/retries?
- Is proof from the actual temporary client, with strict positive integer ID and
  no cached authority? Is admission checked again after awaiting proof? Can a
  caught identity mismatch leave the operation usable for more work?
- Can a fresh identity disagreement reserve another account's budget or send
  history first? Does metadata proof recurse through the quota guard?
- Can missing auth, a ban, server failure, transport error and absent/malformed
  self response be distinguished without any start/code/prompt path?
- Does active/creator-task enforcement work on real overlapping tasks? Does it
  accidentally govern SDK cleanup or inherited background tasks?
- Does cancelling the caller, then cancelling again while closing, leave a
  disconnect task detached? Can disconnect's own cancellation or logging error
  replace successful work/its primary exception? Does error text leak credentials?
- Are file/store sessions, proxy/device configuration and ordinary persistent,
  pooled and ephemeral defaults preserved? Any schema/import/package impact?
- Is there a smaller sufficient shape? Reject speculative registries, public
  SDK sandboxes and unmerged-pool dependencies without actual consumers.

For each observed risk use two Risk paragraphs: plain self-contained consequence,
then precise paths/symbols/trigger. Include Severity, Category, Impact, NoobEng and
Affected areas. For Medium/High provide Quick, Robust and Long-term proposals with
“why this is robust” and “why this is long term effective”. Each proposal initially
has unticked selected/elegant/last_resort boxes and empty Why chosen/For future notes.
No risk tables. Low findings may be informational. Name execution blockers exactly
as declared (none); never manufacture one from local homework.

Phase 3 separately compares reach/extent. Name a genuine second instance before
calling a generalization class-wide; apply similarity/size/delicacy gates. Tick
only the chosen mitigation and write its selection notes without rewriting Phase 2.
