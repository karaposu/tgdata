---
model: gpt-6-astra
effort: xhigh
---
# #50 implementation complete under revision4

Archive product: da890a1. Product-only PR51 head:34907d4.
Base: dev77f2f53eba8bdc6922127a3b9118bf17de4efabf.
Earlier revision2 implementation/verification are preserved as *_r2.md; its
rejected PR critique remains unchanged as evidence, not current approval.

## Result

Terminal stop intent now belongs to one _TerminalRun lifetime. SIGINT cancels an
active authentication action once, consumes completed tasks without re-entering
the event loop, and remains recorded through subsequent cleanup. Input interruption
restores terminal settings before repeated signals can interfere. Explicit retirement
can run after stop. Publication uses the same persistent flag and existing effect
receipt; final exit is chosen after cleanup so a late stop cannot erase saved or
uncertain file state.

The actual native-password/real-terminal hang from PR-critic R1 now exits130 with
restored terminal attributes and settled source work. Admission tests prove no new
prompt/action/save follows stop. Already in-flight source effects may be uncertain;
that is preserved rather than described as remote rollback.

## Plan and gate sequence

- Revision3 e7e94c5 was freshly critiqued in-session: prompt46aeed9, Phase2 verdict
  51f47e9, no new rated risks and a mandatory full combined prebuild.
- Revision4 fold d435a54 records zero selected mitigations and the still-pending
  prebuild. This textual fold followed the user's requested order; no product edit
  preceded the experiment.
- e0d764f commits the full prebuild PASS:23 groups,25 real-PTY scenarios,17 retained
  review histories,8 stop transitions and14 publication/stop combinations. First
  run passed, with candidate/product hashes unchanged.
- da890a1 promotes the exact passing CLI bytes, extends permanent smoke48 with the
  executed test functions, and updates the terminal guide/smoke README. Product
  and work records remain separate. 34907d4 is the same product commit on PR51's
  product-only branch; all106 verified source files match and product diff is equal.

Steps1–5 are complete within the implementation scope. Existing LoginFlow,
LoginDestination/native conversion, StoredSession, configured readers, package
exports/version and setup entry points are unchanged from the reviewed product.
No generic supervisor or new dependency was added. Version stays0.1.1.

## Verification and corrections

New23-group suite passed; targeted15/17/32/41/48 passed97 checks. Full supported
34 suites passed1,010 actual offline checks; seven demos passed; three live cases
were deliberately skipped. All106 Python files compile and satisfy3.7 grammar.
The isolated installed tgdata-login entry also passes actual native-SRP interruption
through a real PTY, help/headless checks and installed import/source matching.

No candidate, product or test-expectation correction was needed. One extracted
work-folder helper's extra EOF blank line was trimmed for diff hygiene; the executed
combined suite/candidate bytes were unchanged. No design deviation or unsupported
behavior was patched during verification. See verification.md for evidence paths.

## Handoff

Next: renewed merge-check against the revised diff/plan, then fresh in-session
critic-d PR critique. Historical merge-check98f4a59 and rejected critique93ba179/
d10104b apply to the old head and do not clear this revision. PR51 stays draft.
§9 current-thread2026-10-16T12:07:55.242Z confirms gpt-6-astra/xhigh; no subagent.

No merge, release, live Telegram login, environment deployment or ScrapeOps change.
Original checkout/version edit, duncan, unrelated guides and separate PR49 remain
untouched. Native3.7, live Telegram delivery/real-account2FA, physical power loss
and arbitrary/active-writer filesystem behavior remain unqualified.
