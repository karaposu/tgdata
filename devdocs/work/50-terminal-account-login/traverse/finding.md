---
status: active
model: gpt-6-astra
effort: xhigh
---
# Finding: terminal login should own publication, not authentication

## Question

How should tgdata provide a terminal command that logs an account in and saves a
session its ordinary readers can use? The command must also handle re-login,
interruption and failed saves without damaging an existing credential.

## Finding Summary

- Reuse the existing LoginFlow API for every authentication step.
- Make the first command publish native SQLite session files. Applications using
  custom stores can continue using LoginFlow and their own store directly.
- Create a new destination by default. Replacing an existing destination must be
  explicit and requires the operator to stop readers using that session.
- Prepare and verify the new file privately before changing the destination.
- Keep a private copy of the old file through replacement until publication is
  confirmed. If the outcome is uncertain, retain recovery evidence and say so.
- Retry a failed local save using the completed credential already in memory.
  Do not request another Telegram code to repair a disk failure.
- Prove the actual login, terminal, filesystem and reader composition before
  implementing the product. The isolated compatibility probes are encouraging,
  but do not replace that combined experiment.

## Finding

tgdata already implements the difficult Telegram conversation: phone number,
code, optional password, waits, uncertain replies and cleanup. Its LoginFlow API
deliberately returns a credential without changing the configured reader session.
The new terminal command should preserve that separation.

The returned credential is opaque StoredSession text. A normal reader without a
custom store opens a Telethon SQLite session file instead. The command therefore
needs a small private conversion step using the existing codec and native SDK
session APIs. Writing the opaque text under a `.session` filename cannot work.

A local probe established that this conversion is feasible. A real LoginFlow,
using controlled Telegram replies, produced a credential that was written through
SQLiteSession and reopened by an ordinary verified reader. The reader restored
the same account, authorization key and own-account cache without another code
request. No real account or network connection was used.

The command should use the same configuration and session-name resolution as
the reader. It should show the destination before starting authentication. A
completed candidate should be closed, checked and synchronized before publication.
For a new destination, publication must refuse a collision rather than replace
whatever appeared while the user was entering a code.

Re-login at an existing path needs a stronger contract. The operator must
explicitly request replacement and stop the readers that use that file. The
command must reject symlinks, unsupported file types, SQLite sidecars and a
destination that changes during the conversation. These checks detect conflicts;
they do not prove that every process has stopped. A lock understood only by the
new command would not coordinate existing readers.

Replacement must preserve the prior file in a private per-attempt location
before changing the destination. That recovery copy remains until the new
publication is confirmed. A native-file probe demonstrated a private backup
surviving replacement, and demonstrated that new-file publication refuses a
collision. The supported initial environment is a trusted local POSIX filesystem
with the required publication primitives; broader filesystem guarantees must not
be inferred from that test.

The command needs to distinguish authentication from local publication. A failed
write before publication can leave the old destination untouched. A failure after
a rename may mean the new file is already visible, even if its persistence was
not confirmed. That case must be reported as uncertain, retaining the private
recovery material. It must not be reported simply as “nothing was saved.”

Terminal interaction should remain synchronous between settled asynchronous
LoginFlow actions. A single event loop must serve the entire flow because the
existing API binds an instance to its first loop. On interruption during source
work, the command must cancel and drain the owned action before exiting. A
background input thread is not assumed to disappear when its waiter is cancelled.

Secret input must never fall back to echoing. Python's password helper has such
a fallback, so its warning should become a refusal. The command should report
safe status and error kinds, the account ID and the destination; it should not
print the credential, code, password or checkpoint.

The completed credential remains available for an explicit local save retry
within the same process. Persistent command checkpoints are a separate feature:
they require retention and stale-copy rules and do not make interrupted remote
requests safe to replay. This first command should not create that extra lifecycle.

## Next Actions

### MUST

- **What:** qualify and plan the file-first command and publication outcomes.
  **Who:** task-desc/task-plan for issue #50.
  **Gate:** before product edits.
  **Why:** turn the chosen boundaries into exact, testable behavior.
- **What:** run one combined experiment using real LoginFlow, native SQLite,
  filesystem publication, ordinary reader reopen and terminal interruption.
  **Who:** the implementation agent, using controlled source replies.
  **Gate:** before implementation, with pass/fail conditions fixed by the critic.
  **Why:** catch a false composition assumption before building around it.
- **What:** test failures before and after publication, explicit save retry,
  repeated interruption, secret-output refusal and cleanup precedence.
  **Who:** implementation and permanent offline tests.
  **Gate:** before the feature is declared implemented.
  **Why:** the command must preserve truthful outcomes as well as valid bytes.

### COULD

- **What:** qualify live Telegram delivery and optional 2FA with an isolated account.
  **Who:** maintainer and implementation agent.
  **Gate:** explicit authorization and an agreed exclusive session setup.
  **Why:** add source-level evidence beyond controlled local component tests.
  **Depends-on:** MUST “combined experiment.” GATED until local composition passes.

### DEFERRED

- A terminal adapter for an application store: revive when a named backend and
  consumer require it, with explicit commit/conflict semantics.
- Cross-process CLI resume: revive when requested with checkpoint ownership and
  retention requirements.
- A general session conversion API or operator suite: revive only when a second
  concrete workflow justifies broader public commitments.
- Automatic coordination with active readers: revive when the readers themselves
  participate in a shared rotation protocol.

## Reasoning

The native-file command survives because it serves the existing reader without
new runtime configuration or a new auth implementation. The private bridge,
separate publication outcome and bounded backup protect different parts of that
handoff; removing any one leaves a concrete failure case.

Creating only immutable new destinations is a valid fallback. It avoids
replacement but requires the operator to switch reader configuration. The first
command can retain no-clobber creation as its default while offering deliberate
replacement under the stronger preconditions.

The general store-provider and durable-checkpoint approaches remain useful
possibilities, but neither is necessary for this first consumer. Their missing
backend and recovery contracts would expand the task substantially.

Emitting a credential to stdout was rejected because it moves the requested save
back to the caller and introduces secret transport. Replacing active readers'
files under a SQLite lock was rejected because database locking does not rotate
their cached authorization state. Deferring filesystem and terminal verification
until rollout was rejected because the earliest failures would then affect real
account credentials.

The complete candidate and evidence records are in `docarchive/critique.md` and
the preceding discipline outputs. The onward concept map remains in
`routelister.md`; it enumerates possibilities without changing this decision.

## Open Questions

### Monitoring
The combined prebuild must establish exact interrupt and post-publication failure
handling. The earlier probes demonstrate primitives, not the complete command.

### Blocked
Live code delivery and real-account 2FA acceptance are unqualified until a
maintainer authorizes the isolated setup. This does not block local implementation.

### Refinement Triggers
If explicit replacement cannot meet the preservation/outcome contract with a
small tested protocol, return to create-only destinations rather than introducing
a generic coordinator. If a concrete application-store consumer appears, qualify
that backend separately instead of assuming its save operation matches a file.
