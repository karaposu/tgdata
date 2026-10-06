---
status: active
model: gpt-6-astra
effort: max
---

# Finding: group lookup, read access and limited joining

## Question

How should tgdata deliver issue #7's three short-lived operations: look up a
group, check whether an account can read it, and join it with an account limit?
The result must preserve existing account controls, work on Telethon 1.45.0,
and be usable by callers without interpreting raw Telegram objects.

## Finding Summary

- Give each operation an explicit result. Metadata, membership and readable
  history are separate observations.
- Preserve invite previews without inventing a group ID. Describe pending
  approval or required interaction without claiming the account has joined.
- Enforce a caller-configured join-attempt allowance in a durable SQLite ledger.
  Count each actual send, including SDK retries, against a rolling 24-hour limit.
- Use a fresh authenticated account ID before each claim. All clients that
  share an allowance must use the same database file.
- Keep the existing ephemeral client lifecycle. A history probe uses the
  existing read allowance; metadata and joining do not clear history denial.
- Verify SDK behavior and local concurrency offline. No live join is part of
  this implementation run.

## Finding

The application wants to add a group and tell a caller whether an account is
ready to read it. Telegram provides several pieces of evidence, each answering a
different question. Treating every successful request as “ready” loses that
meaning and can cause a caller to schedule work the account cannot perform.

Lookup should return available name, handle and group type, together with observed
membership. An unjoined invite may reveal a title but no ID. A temporary preview
can expose a chat and an expiry without granting lasting membership. These are
useful lookup results, not malformed full groups.

Access checking should perform a bounded history request when an addressable
peer exists. A successful request proves readable history at that moment, even
if it returns no messages. A known Telegram group-access denial becomes a denied
result. No peer means unprobed. Authentication, transport and local quota failures
must propagate with their own meaning rather than masquerading as group denial.

Joining should skip a mutation when preflight establishes existing membership.
Otherwise it sends the appropriate handle or invite request through account
admission. It distinguishes acknowledged joining, already joined, submitted
approval and required interaction. It does not pay or operate a webview.

The installed Telethon 1.45.0 uses layer 229 and wraps join responses in
ChatInviteJoinResultOk or ChatInviteJoinResultWebView. The latter contains bot
and query identifiers, not a URL. The offline probe round-tripped these actual
constructors. For an acknowledgment, available nested updates can supply local
metadata and cache entries. A second network lookup must not be mandatory:
its failure would turn an already acknowledged mutation into an apparent failure.

The allowance counts attempts admitted before the actual sender is called.
A failed response can follow a successful remote mutation, so uncertainty stays
charged. An SDK retry requires another claim. No database transaction remains
open across a network await. A fresh get_me result identifies the account for
that claim; the probe showed cached self ID 111 while fresh self was 222.

A dedicated join ledger avoids mixing message units with membership attempts.
Its rolling 24-hour window and explicit account configuration follow the existing
read-budget operating pattern. It promises coordination among callers sharing
one SQLite file, not a global limit across independent hosts or other Telegram
applications. It supplies no invented “safe” quota for preventing restrictions.

Each public operation uses the existing connect/authenticate/yield/disconnect
context exactly once. That preserves proxy, device identity and stored-session
behavior. The selected design extends the shared client factory with a join
sender guard; it does not fork transport management or disable retries globally.

Health remains observable, but group recovery requires read evidence. A real
probe showed that the current generic successful-call context clears a prior
group denial after metadata alone. A default-preserving group-recovery control
lets the new metadata/join paths retain account and wait recovery without
claiming history access. Private invite strings must not be used as health labels.

## Next Actions

### MUST

- **What:** specify the public contracts and exact runtime decisions, then build
  the parser, result values, ledger, guard and ephemeral operations.
  **Who:** task implementation agent in this task folder and tgdata source.
  **Gate:** description and plan pass their required critic/fold gates.
  **Why:** turn the selected design into a reviewable working feature.
- **What:** verify public operation paths, retries, persistence, concurrent claims,
  cleanup, health and compatibility with the existing offline suites.
  **Who:** task implementation agent and smoke-test harness.
  **Gate:** implementation is available.
  **Why:** demonstrate actual composition rather than a plausible design alone.
- **What:** document configuration, outcome meanings and the shared-file boundary.
  **Who:** task implementation agent, README and smoke-test README.
  **Gate:** public names and result contract are fixed in the plan.
  **Why:** callers need to know what a result and a remaining allowance mean.

### COULD

- **What:** add a live acceptance exercise with designated disposable groups.
  **Who:** account owner and implementation agent.
  **Gate:** explicit account/group authorization and offline verification complete.
  **Why:** add evidence about Telegram acceptance absent from scripted replies.
  **Depends-on:** MUST item “verify public operation paths”. GATED until it resolves.

### DEFERRED

- **What:** provide distributed admission storage.
  **Gate:** a concrete multi-host consumer supplies consistency requirements.
  **Why (if revived):** coordinate an allowance beyond one shared database file.
- **What:** adopt a no-retry join client or exception-only incomplete outcomes.
  **Gate:** the sender seam becomes unsupported, or a concrete consumer requires
  exception-only control flow respectively.
  **Why (if revived):** those viable alternatives solve different integration needs.
- **What:** implement approval, payment or webview completion workflows.
  **Gate:** a separate requested feature defines that interaction and authorization.
  **Why (if revived):** complete entry that this short-lived library call only describes.

## Reasoning

The seven focused candidates survive together: portable results preserve missing
information; durable claims preserve the allowance; sender placement handles
retries; history provides read proof; explicit join outcomes preserve incomplete
states; narrow health control preserves evidence; real offline components provide
reproducible tests. Their combination meets the requested feature without
inventing a new account transport or worker.

The rejected alternatives fail specific parts of the request:

- A universal result envelope lacks known extension rules. Raw SDK objects leave
  callers to infer readiness from changing vendor shapes. Focused values give
  this feature a defined contract.
- A general multi-resource policy engine would migrate working read accounting
  without a shared unit requirement. A process-local success counter loses the
  limit across restarts and lost acknowledgments. A distinct durable attempt
  ledger keeps the necessary boundary.
- A universal mutation interceptor cannot define every Telegram effect within
  this issue. Guarding the two observed join families is concrete and testable.
- A full capability census adds requests without proving every future permission.
  Membership-only access fails because public rooms can be readable by nonmembers.
  One bounded history request answers the requested question directly.
- An eventual-membership workflow introduces external interaction and durable
  jobs. Returning the observed incomplete outcome preserves short-lived ownership.
- A general health-proof rewrite changes all existing methods. Omitting health
  hides waits and account failures. A narrow recovery option fixes the actual
  new-path evidence problem while keeping current defaults.
- Live-only happy-path evidence cannot reliably reproduce races, cancellation
  and identity drift. Live tests can supplement, rather than replace, the
  deterministic SDK/database checks.

The no-retry alternative genuinely works: the real SDK sends once when retry=0.
It was not rejected as technically impossible. It is less suitable here because
it changes common factory retry behavior or needs an isolated construction path.
Expected incomplete states as exceptions are also viable, but ordinary result
values fit the requested caller readiness workflow more directly.

A caller-only atomic provider can support distributed storage, but shifts all
storage implementation to every consumer. A built-in SQLite implementation
makes the delivered feature usable now. The inventory-reservation analogy
explains conservative claims, but only real SDK observations support the chosen
send placement; the analogy is not treated as evidence.

The initial “three wrappers” interpretation was corrected by actual invite and
join types, retry placement and health behavior. Legacy GroupInfo still serves
known discovery groups; the new nullable values do not require changing it.
No architectural question remains that blocks describing and planning the feature.

## Open Questions

### Monitoring

Observe failures of the actual SDK sender/request-wrapper contract on any future
Telethon upgrade. The supported target for this work is exactly 1.45.0.

### Blocked

Live acceptance remains unmeasured until accounts and target groups are supplied
and authorized. This does not block offline implementation or its stated tests.

### Research Frontiers

A shared policy engine, distributed storage and full interaction workflows need
separate consumer requirements before their additional structure can be justified.

### Refinement Triggers

Revisit sender placement if a supported SDK bypasses send on retry. Revisit value
outcomes if an actual consumer requires exception-only completion. Revisit SQLite
coordination when the same allowance must be shared across independent hosts.

## Evidence

`../probe_group_seams.py` runs against the real installed Telethon with sockets
blocked. It observed wrapped serialization/cache behavior, retry sends, fresh
identity drift, the no-retry alternative and metadata-only health recovery.
The source artifacts are in `docarchive/`; `routelister.md` and `_route.md` retain
the broader concept directions. No runtime code was written by this inquiry.
