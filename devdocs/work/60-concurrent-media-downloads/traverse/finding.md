---
status: active
model: gpt-6-astra
effort: xhigh
---
# Finding: concurrent downloads need bounded ownership and ordered acceptance

## Question
How can tgdata overlap media downloads while preserving both readers, their saved
progress, and the configured Telegram wait policy? The user wants an optional
parameter whose default remains one download at a time.

## Finding Summary
- Keep the default inline reader path. A value above one activates bounded media work.
- Prepare media in finite windows and accept results in source order. Later successful
  files never authorize a cursor beyond an unfinished earlier message.
- The connection engine owns the opt-in operation. Reject another opt-in media read
  on that same engine before source work; do not invent a global account coordinator.
- Observe rate-limit answers at actual request admission, including waits handled
  inside Telethon. Keep the configured SDK wait and retry policy.
- Explicitly own child tasks and their borrowed SDK resources. Cancellation must
  settle them before the reader returns or the pool retires its client.
- Prove the combined behavior with the real SDK, files and public consumers before
  adopting product code. Live speed remains a separate measurement.

## Finding
Daily scraping can spend much of its time waiting for individual photos. Overlapping
several files may reduce this time, but the reader still has to tell its caller which
messages were completely prepared. That is the boundary the design must preserve.

A finite window contains at most the requested number of prepared messages. The
reader prepares metadata in its own task, starts only the window's media work, then
accepts completed results in source order. It settles the window before starting the
next one or invoking a callback that may stop or pause the read. This bounds both
active work and results waiting behind a slow first message.

For example, if messages 101, 102 and 103 are admitted and 102 finishes first, the
saved position stays at 100 until 101 is ready. If 101 fails, 102's file may already
exist as a reusable completed artifact, but it cannot appear as progress past 101.
This uses order in the observed sequence; Telegram message IDs need not be adjacent.

The optional work shares one connection engine's ownership. That includes the
clients the engine manages. A second opted-in operation is rejected while the first
is active, rather than queued behind a lock that an application callback could
re-enter and deadlock. Default sequential calls and independent tgdata instances
retain their existing coordination responsibilities. This is not a guarantee about
all requests made by an authenticated account across applications or machines.

A shared source-wait observation prevents owned tasks from independently pressing
on after one sees a rate limit. The gate must see the response before Telethon can
handle it internally, and check admission again before each retry or next request.
Telethon remains the retry authority. Ordinary readers retain their configured
wait threshold; account-pool clients retain threshold zero and propagate waits.
Existing requests already sent may finish. No worker creates its own retry loop.

Only tasks explicitly started and joined by the media owner may share its health
and heartbeat attribution. Merely inheriting a context variable is insufficient:
SDK background tasks also inherit context and must remain excluded. Media progress
continues to drive heartbeats; bounded windows prevent unlimited later work from
hiding a stalled earlier download.

Resource ownership extends beyond the Task. A probe of Telethon 1.45 observed one
borrowed exported sender and one return on success, but one borrow and zero returns
when the download was cancelled after moving data centres. The actual request was
cancelled. Therefore, task cancellation alone does not prove resource release.
The opt-in download span must account for exported senders and SDK-created CDN
helpers and settle them without replacing the original error or cancellation.
See ../evidence/sdk_lifetimes.py and its recorded JSON.

The two readers retain different default error contracts. The legacy reader often
keeps rows after media failure; the batch reader requires a complete validated blob.
Default one preserves those behaviors. The opt-in legacy path can explicitly fail
on media preparation and return only its prepared prefix, so parallel errors are
not silently turned into apparently complete work. Its final filenames and row shape
remain familiar; newly written files become visible only after successful completion.

The parameter passes through daily continuation, backfill and account-pool read APIs.
It is runtime tuning, not saved receipt state. Replaying a pending batch performs no
new download. Message attachments on disk and in memory are the first scope; profile
photo enrichment remains serial, and selected-ID downloads and worker job schemas
remain unchanged unless separately requested.

## Next Actions
### MUST
- **What:** write the qualified description and plan for the above contract.
  **Who:** task-impl in this session. **Gate:** this finding is committed.
  **Why:** make local scope, opt-in errors and source policy reviewable before code.
- **What:** run a complete real-component candidate before product adoption.
  **Who:** task-impl prebuild. **Gate:** plan critique supplies pass/fail criteria.
  **Why:** native retries, exported resources, files, observations and durable prefixes
  must work together; stand-alone semaphore tests cannot establish this.
### COULD
- **What:** measure cold-cache downloads at one versus three on an existing group.
  **Who:** maintainer/agent with explicit bounded read-only authorization.
  **Gate:** suitable account, group and shared allowance are available.
  **Why:** replace the estimated speedup with observed throughput and waits.
  **Depends-on:** combined real-component candidate PASS. GATED until it passes.
### DEFERRED
- **What:** share admission across independent engines for the same account.
  **Gate:** a concrete concurrent multi-engine deployment requires it.
  **Why:** then verified identity, mixed limits and cross-owner policy merit their
  own contract; they are not needed for this local option.
- **What:** use a continuously refilled ordered queue or individual media timeouts.
  **Gate:** measurement shows finite windows underuse capacity enough to matter.
  **Why:** improve utilization only with evidence that justifies extra state.

## Reasoning
An unrestricted gather limits neither queued tasks nor results waiting behind a slow
message. A semaphore fixes only active I/O. A rolling queue can be bounded, but adds
stall and acceptance rules that finite windows avoid for this first feature.

Treating the maximum completed message ID as progress was rejected because it can
permanently skip a failed earlier message after acknowledgment. A unified new result
schema was rejected because existing batch and row contracts already express the
required results; the private execution helper can be shared without changing them.

Trusting SDK task completion as cleanup was rejected by the native exported-sender
probe. Catching only errors that escape download_media was rejected because the SDK
can sleep and retry internally. Replacing the SDK retry system was rejected because
it changes established wait and pool policies; an admission observer is narrower.

A global account coordinator may eventually be useful, but it introduces identity
and mixed-policy ownership beyond an optional per-read control. The selected engine
scope is explicit about that limitation. Keeping concurrency solely in ScrapeOps
would duplicate library preparation and cursor handling rather than control it.

Persisting the tuning value, changing default behavior, and widening to every media
API were rejected as unnecessary for the requested readers. Runtime forwarding,
finite ownership and ordered acceptance satisfy the current request together.

## Open Questions
### Monitoring
The complete candidate must establish SDK cached waits, exported/CDN behavior,
reference-refresh budgeting, repeated cancellation, file collisions, callback stops
and pending replay. This inquiry supplies the contract, not proof of a future build.
### Refinement Triggers
Revisit window utilization after a bounded live comparison. Revisit account-wide
scope only when independent same-account engines must be coordinated by tgdata.
