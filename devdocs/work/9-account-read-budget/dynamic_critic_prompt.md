# Dynamic critic prompt — issue #9

Use ultrathink. Critique `step_by_step_impl_plan.md` revision 1 at `4a0951a`
against `desc.md`, triage, all affected source and the pre-plan probes. Execute
in this warmed session; no subagent. Read vendor implementations, not merely
method names. The goal is an opt-in shared allowance for explicit message
pulls, with the description's scope assumptions visible.

Question these concepts:
- Identity: is a cached self ID evidence of the current authenticated account?
  What survives stored-session restore, relogin and multiple clients?
- Timing: does every actual send/retry claim capacity after resolution/waits?
  Can cancellation, retries, rollback, late settlement or reconfiguration
  release another job's capacity or reset warm-up?
- Boundaries: which message-returning requests, wrappers and batches are
  admitted? Are metadata/previews/passive updates exclusions explicit? Do the
  configured defaults preserve old behavior?
- Paging: does shrinking and later growing a reverse page preserve offsets?
  Does a denied ID chunk advance its cursor? Are request objects modified?
- Partial results: does a quota stop conceal already processed rows/media or
  links? Do catch-all handlers or polling turn a local stop into retries or a
  false Telegram health state?
- Persistence: are claims serialized across processes, writes short, schema
  failures closed, and counters independent from credential storage?
- Evidence: separate real SDK/SQLite behavior from scripted server replies;
  identify what cannot be proven without live Telegram and test cheap premises
  before implementation. Quote probe results for each behavior-based finding.

Write `critic.md` with model/effort frontmatter (unknown if not exposed), one
of the four critic-d verdicts, falsifier and affordability, summary, ranked
premise inventory, restart/inherited-lessons checks, probes and findings.
Each risk needs plain and precise paragraphs, severity, category, impact,
NoobEng and affected areas. Medium/High risks get quick/robust/long-term
proposals with why robust and long-term work; start with empty selection,
elegant, last-resort boxes and notes. Then execute Phase 3 by reach/extent.
Do not pad the report or classify a stated verification limit as proof.
Declared execution preconditions remain preconditions; no deployment or merge
belongs to this implementation run.
