---
status: active
model: gpt-6-astra
effort: max
---
# Finding: a small account-owned operation for Stage 1

## Question

How should tgdata implement the selected first stage of #7: declare an expected
account, configure a temporary client before authentication, prove the actual
account, preserve it through admission checks and close reliably?

## Finding Summary

- Build a private operation context for later tgdata features. Do not publish a
  general raw-client extension API in this stage.
- Verify the expected numeric ID against the client's fresh self response. Cached
  IDs and session names never determine the owner.
- Recheck the same identity at later admission, before reserving quota or sending
  a message read. A mismatch refuses; it never changes the declared owner.
- Configure retries and waits when constructing the client, before `connect()`.
- Finish one retained disconnect attempt on every exit. Preserve the work outcome;
  caller cancellation remains cancellation after the close attempt settles.

## Finding

The previous #7 implementation changed event labels while leaving stored health
ownership implicit. Stage 1 addresses the operation's own authority first. Health
storage is deliberately a later consumer of that authority.

The caller supplies a positive numeric Telegram account ID. A new SDK client uses
the existing factory's session, proxy, pinned device and optional read-budget
configuration. Its no-flood-sleep, finite-retry policy exists before connection:
Telethon can fetch the logged-in user inside `connect()` itself.

After noninteractive authorization, a self RPC proves who authenticated. Expected B,
cached A, actual B proceeds as B. Expected A, actual B raises before the context
yields to any group operation. A missing login produces the existing explicit
authentication error; it never calls `start`, requests a code or prompts.

The internal handle exposes the verified ID, the client and a fresh verification
method. The ID is read-only. Verification checks that the handle is active and is
being used by the task that opened it. Later budget admission calls this method
instead of independently selecting an owner. It refuses disagreement before a
reservation or send. Future internal consumers must keep their work inside this
lexical context; the handle is not a sandbox for arbitrary SDK/login calls.

Closing first marks the handle inactive, then retains and awaits one disconnect
attempt. The offline probe of Telethon 1.45 reproduced an otherwise hidden detail:
`disconnect()` shields its own task, so a cancelled direct await can return before
disconnection. Keeping a separate completion reference fixes that ordering, even
with repeated caller cancellation.

Cleanup failure is reported by exception type only and cannot replace successful
work or its primary failure. Cancellation of disconnect itself is a cleanup
failure; cancellation of the caller remains caller cancellation. This guarantees
completion of the close attempt, not successful transport teardown when the SDK
fails, and not a time limit when the SDK hangs.

## Next Actions

### MUST

- **What:** implement the scoped context, fixed constructor policy, explicit proof
  and admission agreement. **Who:** task-impl in this stage folder. **Gate:** plan
  and dynamic critic complete. **Why:** make the five requested guarantees real.
- **What:** test actual SDK composition offline and run the supported regression
  suite. **Who:** implementation verification. **Gate:** code written. **Why:**
  prove the stale-cache, mismatch, auth and cancellation paths without Telegram use.

### DEFERRED

- **What:** health ownership integration. **Gate:** the user starts Stage 2.
  **Why if revived:** attribute health state to the explicit verified owner.
- **What:** public arbitrary-operation API. **Gate:** an actual external consumer
  requires it. **Why if revived:** define detached-work/login/lifetime obligations
  with evidence instead of committing to them speculatively.

## Reasoning

The existing factory and fresh budget-identity provider make the small context
viable. Retained cleanup completion is supported by the real SDK probe, rather
than assuming a fake `disconnect()` behaves like Telethon.

A general policy object has no second consumer here. Reusing the persistent client
would let one operation change another's policy or close its transport. Adopting
whichever account a later proof returns violates the explicit expected-account
requirement. Fire-and-forget or timed-out cleanup leaves SDK cleanup running.

A public extension API would need to govern arbitrary retained clients and login
calls. A per-dispatch identity supervisor introduces recursive proof and extra
traffic. Rebuilding all health ownership first repeats the prior scope growth.
These alternatives were evaluated and excluded from Stage 1, rather than left as
implicit promises. The private handle's task and active checks were retained to
make its smaller lifetime contract enforceable at admission.

## Open Questions

Refinement trigger: if an actual SDK shutdown hang is reproduced, investigate a
bounded transport shutdown contract separately. No Stage 1 caller timeout can
honestly stand in for completed disconnection.

Model/effort evidence is the same-session rollout metadata recorded in triage;
the metadata timestamp is earlier than this finding, not a new model declaration.
