---
model: gpt-6-astra
effort: max
---
# Triage — #10 reading jobs

**Weight:** feature-heavy. **Path:** feature. **Priority:** P3, selected next by
the maintainer. **Base:** dev `68f6bbda33aeb1963b96b3c719d8f23938fa4449`.
**Branch:** native issue-linked `feat/10-reading-jobs`; isolated worktree
`/private/tmp/tgdata-10-reading-jobs`. There was no previous #10 implementation.

The surfaced territory includes account configuration and exclusive sessions,
verified temporary operations, batch/partial-result delivery, lookup/access/join
outcomes, health notifications, read/join ledgers, process framing and shutdown.
See the 17-item `surfacing.md` trace. A process consumer crosses several existing
contracts and emits results across a new failure boundary; it is not a light CLI
wrapper even if its eventual implementation is small.

## Prerequisites and current work

#4, #6 and #7 are closed and their accepted product is on this base. #1/#5/#9
proxy/session/budget foundations are also present. The issue's old blocked status
and statement that dev does not yet exist are stale and will be corrected while
preserving its original request.

#17 is not a prerequisite named by #10 and is not merged. Its PR26 just failed
fresh critique on two observer/cleanup boundaries and is saved as a draft, with
revision-3 re-planning required. Do not copy its rejected runtime or make this
worker depend on its automatic routing. The worker issue asks for account inventory
and explicit jobs; routing/failover remains a separate capability unless the user
changes that scope. Carry the observed ownership lessons, not its implementation.

## Session warmth and authority

Same warmed session as #7 implementation/merge and #17 integration/review. Current
dev interfaces for TgData construction/owned health/group operations, account
operation/factory, group implementation, batch/budgets/progress and cleanup have
been read or retained unchanged; no redundant archaeology refresh is claimed.
Feature model verified from this session's metadata: GPT-6 Astra/max.

The user explicitly invoked task-impl for #10 after #17's review finished. This
authorizes formal preparation, probes, implementation, tests, checkpoint commits
and required issue publication. It does not authorize Telegram login/join/read,
resetting existing budgets, a deployment, PR publication or a dev merge.
Preserve original checkout/untracked files, duncan and all unrelated worktrees.

## Traverse decision

**Required** by CONTRIBUTING §5: #10 creates a process/job contract that later
consumers stand on and connects request delivery to bounded source ownership,
health and irreversible joins. The question is what a small worker must promise
about admission, account binding, replies, uncertain completion, output backpressure
and termination, and what must stay with the caller. This is a new structure and
a delicate composition; the answer cannot be inferred from a working in-process
library alone.

Run the full same-session traverse at `traverse/` before task-desc/plan. Probe real
SDK/SQLite and real process pipes at the relevant boundaries; synthetic transport
must be labeled and must not supply the ownership/retry behavior under test.

## Inputs still being qualified

A transport preference was asked asynchronously. JSON lines over stdin/stdout is
the stated working default for a small caller-managed process; HTTP is the offered
alternative, not an existing requirement. No downstream protocol was supplied.
Resolve the actual first-delivery contract during traverse, incorporating any
reply, rather than pretending the issue already specifies framing or durable jobs.

Inspect especially the difference between an SDK disconnect attempt and proven
cleanup, between source completion and reply receipt, and between retryable reads
and an uncertain join. No new queue, distributed scheduler or login service is
justified merely by the word worker. No planning blocker is declared before
reading/probing the relevant mechanisms.
