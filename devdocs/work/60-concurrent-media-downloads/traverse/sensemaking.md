# Sensemaking — ownership before parallelism
## User Input
_branch.md: bounded ownership/completion/wait contract for issue60; all four variants.
## SV1 — baseline
Overlapping several media downloads may hide per-file latency while preserving the
reader's externally sequential output. A semaphore initially appears sufficient.
## Anchors / SV2
Constraints: default1 unchanged; optional overlap; bounded work; ordered completed
prefix; no new receipt authority; no client-wide policy mutation; caller cancellation.
Insights: a semaphore does not bound waiting tasks/results; media uses SDK _call
rather than normal __call__; sender borrow is not returned on actual cancelled SDK
download (sdk_lifetimes.json). Structural points: reader owns records, file owner owns
bytes, SDK owns retries, ConnectionEngine owns persistent client, delivery owns receipt.
Principles: receiving a later file cannot establish successful earlier preparation;
completed file is not durable acknowledgment. Meaning nodes: admission, completion,
publication and release are distinct observations. H4/H5: existing vocabulary, not
new invented product roles; document/media/DC variation matters beyond small photos.
SV2: the feature is bounded speculative media work with ordered acceptance, not
parallel message processing or a global throughput controller.
## Perspectives / SV3
Technical: raw-sender seam sees retries/exported media; catching only final errors
misses internal waits. New anchor: gate before actual sends without swapping policy.
User: default1 is a compatibility promise; N is permission for overlap, not speed or
account immunity. New anchor: explain scope plainly and preserve opt-in ergonomics.
Strategic: common bounded ownership may serve both readers, but their error policies
differ. New anchor: share scheduling; do not force a single result model.
Failure: repeated caller cancellation can interrupt cleanup; cancelled Task is not
proof of released SDK borrow. New anchor: retained joining and resource accounting.
Resource: later completed files/results accumulate behind a stalled first item.
New anchor: admission must be bounded by unaccepted work, not active I/O alone.
Systemic: per-account allowance is not a bandwidth/rate-limit allowance; file-reference
refresh may consume message budget. Existing charging must remain at actual send.
Internal consistency: legacy suppresses ordinary media failures, batch download mode
requires complete blobs. Preserve1; decide opted-in errors explicitly before coding.
Frame-exit: 'owner' refers to invocation/client/account/receipt authority. Enumerate
all four; caller's unrelated account users stay outside this library invocation, but
that exclusion means no global per-account rate guarantee may be claimed. Strongest
counter: genuine account safety needs shared coordinator. Structurally true globally,
which is why local concurrency cannot promise it; no distributed mechanism requested.
Residual: same engine multiple clients must not be mistaken for distinct accounts.
Calibration: no measured safeN or speedup; default1 remains, example3 is a trial.
H1/H2/H3/H7: candidates are extent choices, not different goals; SDK leakage expands
ownership accounting only, not account routing. No repeated model accommodation needed.
SV3: scheduling, reader acceptance, SDK retry and resource release must cooperate;
none can infer another's completion from its own success.
## Ambiguity collapse / SV4
A1 'sequential compatibility': counter says switch everyone to one new pool atN1.
That can change source lookahead, errors and callbacks without any requested benefit.
HIGH resolution:1 retains inline path; optional path may explicitly strengthen failure
handling. Fixed: no default source/queue/task behavior change; excludes universal
refactor. Reader integration/compatibility tests depend on it.
A2 'completed': counter says later successful downloads can advance next_after_id.
Batch validates strictly ordered IDs and its cursor equals last prepared record;
acknowledgment of a gap loses work. HIGH: only ordered complete prefix is deliverable.
Fixed: completed bytes beyond gap may remain reusable but cannot grant progress.
A3 'backoff': counter says catch FloodWait at download_media and sleep each worker.
Actual UserMethods._call may consume the error internally; pool policy forbids sleep.
HIGH: coordinate admission around source waits, retain existing wait/raise policy and
bounded SDK retries, do not invent independent worker retry loops. Gate design depends.
A4 'settled': counter says gather cancelled downloads then client may close safely.
Actual borrowed1/returned0 cancellation falsifies resource equality. HIGH: own SDK
borrowed resources within opted-in download span and settle before outcome escapes;
no hard timeout guarantee while physical cleanup remains incomplete.
A5 'account-wide': strongest counter to engine scope is multiple configured clients
on one authenticated account. Current API makes no global invocation limit andN1
must remain unchanged; a global registry would add identity/policy ownership not
requested. LOW choice retained OPEN for innovation: define local extent, cover multiple
owned clients and explicitly state caller responsibilities across independent engines.
A6 'photo only': counter says photos prove documents/CDNs/refresh behavior. SDK paths
differ, so observations do not generalize. HIGH: shared scheduling correctness covers
supported message attachments, test document/exported/refresh boundaries explicitly;
other media surfaces receive explicit inclusion/exclusion, not accidental concurrency.
SV4: default behavior, ordered prefix, wait authority and physical settlement fixed;
coordination extent and chosen scheduling shape remain design alternatives.
## Degrees of freedom / SV5
Eliminate unrestricted gather, detached cleanup, shared policy swapping, account
switching to evade waits and cache-as-ack inference. Keep per-call or engine-scoped
bounded scheduling, bounded windows or ordered refill, with explicit owned-task
observation. Global coordination is an alternative whose cost must be justified;
not a default assumption. No schema/dependency/per-file chunk changes needed.
## SV6 — stabilized model
One read may own a bounded set of unfinished media preparations. Only its ordered
accepted results reach existing readers/receipts. Each owned source request respects
existing wait/admission policy; cancellation retires the whole span before return.
The local coordinator's scope is part of the contract, not inferred from cached
account identity. This changes SV1's 'semaphore' into accountable admission/completion/
release, without deciding implementation prematurely.
Telemetry:6 ambiguities,5 fixed/1 extent decision retained; five anchor types and
nine perspectives. Last consistency/calibration checks confirm prior types. All six
failure modes checked; no self-referential framework target. Structural SV1–SV6,
anchors,perspectives,counters,remaining freedom and provenance7/7 manual PASS.
