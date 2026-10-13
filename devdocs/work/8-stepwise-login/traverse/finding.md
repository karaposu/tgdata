---
status: active
model: gpt-6-astra
effort: max
---
# Finding: a login conversation owns progress; the application owns storage

## Question
What state, ownership and completion contract lets issue #8 offer separate phone,
code and optional password calls through the current connection and session APIs?

## Finding Summary
- Add one explicit login conversation. Keep its private progress separately from
  its safe, user-facing next-step status.
- Retain an opaque checkpoint between completed calls. An application can store
  it and restore it on another worker, provided only one owner uses the latest state.
- Own a temporary client for each call. Preserve configured proxy/device policy
  and wait for its work and cleanup to finish before releasing the call.
- Record a successful challenge or authentication when Telegram returns it.
  Cancellation or a later local failure cannot erase that observed fact.
- Return the finished credential in the existing session store's format. The
  application saves it and handles any local save failure without logging in again.
- Qualify the complete composition with Telethon1.45 before production changes.
  The five narrow SDK probes already run are supporting evidence, not that gate.

## Finding
The requested feature lets a web handler submit one login input without waiting on
a console or holding a connection while a person decides what to type. A small
conversation object supplies that boundary. Ordinary scraping, worker and pool
clients retain their current refusal to request login codes unattended.

The conversation needs the phone and challenge hash as well as the actual transport
key and data centre. A regular SDK session string does not include that challenge.
Its safe status should report the next supported action, authenticated account when
known, and actionable error categories. Codes and passwords are inputs only; they
must never become part of an exported checkpoint or diagnostic message.

The caller may retain the object entirely in memory. The same contract also allows
an explicit secret export after a settled call and restoration under matching
configuration. The application is responsible for private storage, exclusive use of
the latest checkpoint and saving it after progress. An old copy is not permission to
repeat a request. If a process dies while Telegram may be processing a request, the
last saved checkpoint cannot prove what happened; the API must not promise rollback
or automatically request another code.

The transport lifetime follows each call. Native connection setup, DC migration,
authentication and disconnect all belong to that invocation. The conversation must
retain any actual progress before cleanup and distinguish caller cancellation from
a component that interrupts itself. A cleanup failure cannot silently permit another
local client step. The application must settle the old owner before transferring
its checkpoint; serialized bytes cannot certify that an old process has stopped.

The existing configured client factory remains the authority for proxy and device
settings. Freeze the effective device values for restoration so a worker with a
different platform default cannot silently change them. A newly started flow uses
an isolated in-memory credential, never an existing configured session file or row.

Completion means actual authorization was observed under the retained key. It does
not mean the application's database committed a record. The finished session text
must round-trip through StoredSession, the existing pluggable session implementation.
The caller then deliberately saves it in the intended account's slot. This is needed
because StoredSession.save currently logs backend failures and returns normally.

The supported path is an existing account's code and optional two-factor password.
Other Telegram responses must be reported honestly as unsupported interaction; signup,
payment, password reset and QR login are not implicit fallbacks.

## Next Actions
### MUST
- **What:** Describe and plan this bounded contract, then critique and run a full
  real-component candidate. **Who:** task-impl in this work folder. **Gate:** before
  production implementation. **Why:** native SDK behavior must qualify the complete
  auth/state/cleanup composition, including actual SRP and consumer loading.
- **What:** Implement and verify the qualified API, tests and usage example.
  **Who:** task-impl. **Gate:** full candidate passes and plan has no open blocker.
  **Why:** turns this contract into the requested usable feature.
### COULD
- **What:** Qualify live code delivery and password acceptance on an expressly
  authorized setup. **Who:** user and implementer. **Gate:** account/test-DC setup
  available. **Why:** separates provider acceptance from offline SDK evidence.
  **Depends-on:** MUST implementation/verification; GATED until it is complete.
### DEFERRED
- **What:** A library-managed durable admission service. **Gate:** a named consumer
  needs simultaneous-worker safety or in-flight recovery. **Why (if revived):** that
  owner must coordinate uncertainty rather than pretend Telegram and a DB are atomic.

## Reasoning
The SDK helper-wrapper approach failed the concrete probes: repeated start becomes
ResendCode, and sign_in can raise during update initialization after remote login
already succeeded. Observe the smaller auth operations directly instead.

Immediate publication through normal SDK store hooks failed the actual failing-store
probe. Returning data lets the application observe its own save outcome. A new atomic
provider or durable coordinator was rejected for this delivery because the requested
independent calls do not require a new distributed workflow service.

A duplicate client constructor was rejected because it creates a second policy owner.
Requiring caller-injected raw clients or caller-owned raw cleanup was rejected because
every consumer would have to reconstruct the delicate library guarantees. Importing
sessions without a login API was rejected because it does not satisfy the request.

Persistent in-memory clients remain feasible for a single process, but retaining a
conversation with temporary per-step clients also supports that use without keeping
sockets open during human input. The chosen contract supports both in-memory and
completed-step restoration; it explicitly excludes distributed coordination. Versioned
state and explicit unsupported variants keep this feature bounded as Telegram evolves.

## Open Questions
### Monitoring
The optional persistence preference has no user answer yet. Restorable completed
steps are a stated implementation default, not a user-confirmed durability requirement.
### Refinement Triggers
Reopen the contract if the full candidate loses a known outcome, cannot preserve
actual key/DC during migration, or cannot reload the finished credential. Do not patch
around a failed premise. Live provider qualification remains unperformed; no real code
request or password submission has been made by this inquiry.
