---
model: gpt-6-astra
effort: max
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: the owned raw-batch path cannot resolve supported references without
inheriting broad dialog/contact discovery, or the process output path cannot honor
stop/exit semantics without a final buffered flush keeping it alive.
Affordable now: yes — seconds with the actual SDK, SQLite and owned OS pipes.

Experiment: use a candidate optional BatchEngine resolver that delegates to merged
group-reference resolution inside the verified operation. Prove valid handle/cached
group reading, uncached/invite refusal without dialog/contact scans or joins, original
partial/wait preservation, and unchanged default BatchEngine fallback. Run real
buffered/raw stdout controls for broken reader and SIGTERM under pressure. Re-run
the existing six-case cleanup-receipt candidate to bind all lifetime premises.
Cost: temporary synthetic sessions/SQLite and subprocesses; no account/network access.
Must precede: source Step2 and process Step3; task-impl runs it before Step1.
Disqualifying result: wrong-owner/extra broad source work, lost ordinary prefix/wait,
default-library behavior changed, raw output still waiting for drain after stop,
or cleanup failure knowledge missing when cancellation escapes.
Passing result: only bounded intended source calls, correct ownership/charges and
prefixes, default path retained, raw output exits3/143 as specified without drain,
and every cleanup candidate preserves its original outcome/failure fact.

## High-level summary

The worker's shape is sound. Two Medium details in revision1 are insufficient:
reusing the raw batch engine also reuses its broad fallback resolution, and ordinary
buffered stdout can survive the intended stop boundary during interpreter shutdown.
Both were reproduced with actual components. Zero High, two Medium, zero Low.
Select narrow resolver/output changes, qualify them before implementation, then fold.

## Premise Inventory

### P1 — Verified batch composition is also bounded group resolution

First dependent step2; waste if false: source/process/tests/docs2–6 would promise a
bounded job with an unbounded discovery path. Scheduled test4 covers operations but
does not specify missing-cache resolution histories. Cheapest earlier test: actual
SDK with uncached private ID and ChannelInvalid fallback, seconds offline. Coverage:
the earlier traverse proved account/budget composition for a resolvable handle, not
this fallback. Current reconnaissance invoked GetDialogsRequest before refusing;
source inspection shows `client.get_dialogs()` without a limit. Desired fake resolver
returns would be non-covering. The candidate must use real SDK/group primitives.

### P2 — Synchronous binary writes stop when the worker catches errors/signals

First dependent step3; waste if false: process/exit documentation and tests3–6.
Scheduled test4, after building. Cheapest earlier test: real Python stdout pipe
under closed-reader and blocked-reader conditions, under a second locally.
Coverage: buffered broken pipe exits120 instead of3; buffered SIGTERM waits until
the parent drains output. Raw output exits3/143 without that wait. This actual
interpreter behavior is not established by an in-memory file or a scripted writer.

### P3 — Private cleanup feedback preserves existing results

First dependent step2; scheduled test4, but the earlier six-case actual SDK candidate
already passed. It observes success, source error, setup error, internal cancellation,
repeated caller cancellation and diagnostic failure, plus sticky failure retention.
Re-run that candidate with the selected assembly before implementation. It proves
the primitive, not the unbuilt worker's admission guard; product tests still owe that.

### P4 — Portable process result preserves identifier and retry meaning

First dependent steps1/3. Scheduled tests4/6. Existing Node signed64 probe establishes
decimal-string need and feasibility; existing raw MessageBatch identity is already
portable. No atomic relationship between Telegram join and pipe receipt is claimed.
Parser/frame/projection tests remain required product verification. The specified
output-limit fallback is an explicit delivery failure with omission, not evidence
that an undelivered batch is safely saved or that a source mutation failed.

### P5 — Deployment and live account qualification

Declared external precondition unchanged: approved accounts/group, exclusive sessions
and bounded existing allowance are required before live deployment tests. It does
not gate the seven offline steps. Synthetic wire is non-covering for live proxy/
visibility behavior; no issue or plan box may treat it as live evidence.

## Restart Check

| Observation | Established mechanism | Addressing design |
|---|---|---|
| #17 observer cancellation loses outcome / descendant close deadlocks | Observer and source lifetimes coupled without complete ownership rules | Fixed worker collector and accepted post-cleanup owned monitor; no #17 runtime adoption |
| Method returns while transport remains connected after cleanup fault | Existing helper preserves primary outcome and only logs cleanup error | Tested private failure receipt, sticky worker stop |
| Cancelled stdin await does not terminate process | Default executor still owns blocking read | Serial main-thread input, no executor reader |
| Large numeric query ID rounds in real consumer | JSON number reaches JavaScript Number | Decimal-string worker projection |
| Missing cached group triggers dialog scan | Legacy BatchEngine fallback calls unbounded get_dialogs | Risk1 bounded resolver |
| Stop/error does not finish buffered stdout | Interpreter retries buffered flush | Risk2 raw output path |

## Inherited Lessons

Fresh identity is not a cached label: preserve initial proof and actual admission
guards, already probed before source implementation. Return is not cleanup success:
feedback is captured before cancellation/diagnostics, before next admission. Pipe
publication is not durable receipt: no retry/queue/cursor ownership is introduced.
Existing composition success is not every edge: the missing-cache and final-flush
experiments now precede building. No framework without a real shared need: changes
stay in an optional raw resolver and worker I/O, not a new global client supervisor.

## Risk 1 — A bounded read job can trigger broad account discovery

**Risk**

A caller can ask for a few messages from a group whose access information is not in
the account's saved session. The proposed worker would then use the library's legacy
fallback, which loads the account's full dialog list to try to discover that group.
The job therefore performs a broader operation than its bounded read suggests and
can take many additional Telegram requests before returning a local refusal.

Step2 constructs an ordinary `BatchEngine` over the verified session adapter.
`tgdata/batch_engine.py:167–173` catches get_entity ValueError and calls
`MessageEngine._entity_after_dialog_sync`; `tgdata/message_engine.py:421–438` awaits
`client.get_dialogs()` without a bound. Actual SDK reconnaissance on an uncached
channel, with Telegram's zero-hash attempt returning ChannelInvalid, recorded
GetChannelsRequest → GetDialogsRequest → GetChannelsRequest before GroupAccessError.
Expected-account proof is correct but does not constrain this resolution work.

**Severity:** Medium
**Category:** Source scope / hidden work
**Impact:** unexpectedly broad metadata traffic, latency and account exposure inside
one small job; the existing message ledger does not bound the dialog enumeration.
**NoobEng:** bounding returned message count does not bound the work used to locate
the group. The library's legacy discovery convenience is a separate operation.
**Affected areas:** worker source adapter, BatchEngine resolver seam, protocol target
validation and test37 source histories. Ordinary library fallback need not change.

### Mitigation — Quick

Document that some worker reads scan all dialogs and leave the default path.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Add a private optional `_resolve_entity` constructor hook to BatchEngine, defaulting
to its unchanged current behavior. The worker validates its read target with the
accepted `_parse_target`, calls the merged group `_resolve` under its verified
operation, refuses absent/unsupported read peers, and retrieves the resolved peer's
entity through a bounded SDK call. Check the returned canonical ID against the
lookup before iteration. No dialog/contact sweep, join or arbitrary raw string
resolver fallback. Keep original read/partial/date/media-reference behavior.
**Why this is robust:** it constrains only the new consumer and reuses the accepted
reference/ownership logic while retaining existing raw-reader compatibility.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Long-term

Redesign resolution for all library reads/discovery/pooling around one configurable
resolver policy and explicit cache-discovery operations.
**Why this is long term effective:** could unify resolution scope across all consumers.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Risk 2 — Buffered stdout can outlive the requested stop

**Risk**

When the caller stops reading replies, the worker can block while writing. If a
stop signal interrupts ordinary buffered stdout, Python may try to flush the pending
bytes again while exiting and remain stuck until the caller resumes reading. A
closed pipe can also change the intended exit code during that final flush.

Step3 specifies binary write-all and caught output errors/signals but leaves the
actual stdout layer unspecified. The real process probe uses `sys.stdout.buffer`:
BrokenPipeError caught with exit3 becomes exit120 plus a shutdown warning; SIGTERM
under backpressure reaches the exit handler but process.wait times out until output
is drained. The unbuffered control (`os.write`) exits3/143 without a final-flush wait.
This is interpreter shutdown behavior, not an SDK cleanup that the plan deliberately
allows to remain pending.

**Severity:** Medium
**Category:** Process lifetime / backpressure / exit contract
**Impact:** a stopped worker remains alive for a reason outside the stated cleanup
contract, and caller supervision receives the wrong output-failure exit code.
**NoobEng:** cancelling the current write does not discard bytes owned by a Python
buffer; interpreter exit can try to publish them again.
**Affected areas:** worker writer/bootstrap output normalization, signal/output tests.

### Mitigation — Quick

Require callers always to drain output and accept interpreter-dependent exit codes.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Use an unbuffered CLI output path and write-all without leaving bytes in Python's
stdout buffer. Normalize a trusted bootstrap's standard buffered binary stream to
its raw stream, or require a genuinely unbuffered supplied stream. Keep complete
frame serialization before I/O, short-write handling and one writer. Do not flush
or retry protocol output during teardown after failed/interrupting writes. Prove
closed-reader and SIGTERM/SIGINT-under-pressure cases with real subprocesses and
the read end still open/not drained.
**Why this is robust:** removes the second hidden writer at interpreter teardown
without adding threads, queues or a second process architecture.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Long-term

Build a nonblocking duplex transport abstraction with explicit flush/half-close/
deadline policy for multiple worker transports.
**Why this is long term effective:** could serve future HTTP/socket/pipe adapters
with one fully specified output lifetime.
- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

## Evidence and limits

`probes/plan_falsifiers.py` and its output retain the actual source trace and four
OS output controls. The initial source fixture omitted the SDK's zero-access-hash
GetChannels fallback; its assertion failure is preserved in
`plan_falsifiers-fixture.txt`. Completing that synthetic response with actual
ChannelInvalid exercised the real fallback and passed; no production code or
desired behavior was substituted. The first source probe's early failure prevented
its output cases; those ran separately, then in the complete corrected script.

```text
legacy_raw_resolution: GroupAccessError; GetDialogsRequest attempted; history_requests0
stdout_broken buffered: exit120; warningtrue
stdout_broken raw: exit3; warningfalse
stdout_pressure buffered: stuck_until_drain=true; exit143 after drain
stdout_pressure raw: stuck_until_drain=false; exit143
```

Both findings preserve the selected architecture. No new planning blocker, live
action, runtime edit or #17 dependency is introduced. The formal prebuild experiment
above must receive its Result line before the folded plan is implemented.
