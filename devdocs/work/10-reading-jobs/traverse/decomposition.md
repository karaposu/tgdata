# Decomposition — #10 worker boundary

## User Input

Decompose W1 using saved `sensemaking.md` SV6 and all V1/V2/V3 alternatives.
This partitions decisions and interfaces; it is not the implementation step list.

## 1 — Coupling Map

Strong cluster A: inventory binding, expected account proof, session/proxy identity,
read/join admission and the actual client's cleanup outcome. Splitting proof from
execution would permit the wrong account to act; splitting cleanup from ownership
would reproduce unsafe next-job permission.

Strong cluster B: input framing/limits, request correlation, process admission,
signals/EOF and stdout backpressure. Buffering or shutdown policy changes affect
when another job may enter, so these cannot be independent utilities with hidden
queues/threads.

Strong cluster C: source result/error/partial batch, correlated health facts and
wire projection. The caller must learn the real source outcome without diagnostics
inventing a new success/failure or leaking configuration.

Moderate boundaries: validated job data crosses B→A; bounded plain outcome plus
cleanup status crosses A→C; a serializable reply crosses C→B. Weak boundary:
application scheduling/receiver persistence supplies future requests and consumes
outcomes without owning SDK tasks. Transport choice changes B, not quota/source APIs.

## 2–3 — Boundaries and bottom-up validation

Atoms: one expected account ID, one bounded job, one actual quota claim, one owned
client, one cleanup attempt/outcome, one raw batch/partial prefix, one health fact,
one complete frame and one process termination. These align with A/B/C without
splitting proof from quota or result from prefix. Top-down/bottom-up agree.

The request schema/caller semantics are a separate contract-level prerequisite to
all three clusters; this breaks their apparent cycle. A runtime closed/unsafe
decision needs an explicit producer in A and a consumer in B, not a derived guess
from normal return or `is_connected()` alone. No proposed piece owns a new ledger,
cursor/ack state, group engine, scheduler or automatic account router.

## 4 — Question Tree

**Q1 — What does one worker request and reply mean?**

- Define all four verbs, fixed version/correlation, explicit account and bounded
  arguments, unsupported/invalid input and duplicate/retry meaning.
- Distinguish parsed/admitted work, actual source result, transport write and
  caller receipt; define lost-reply handling especially for joins.
- State which V1/V2/V3 responsibilities the first delivery selects or defers.

**Q2 — How is each job bound to one owned authenticated account?**

- Resolve trusted startup inventory/config/session/budget configuration before
  source permission; no credentials or arbitrary import/path selection in jobs.
- Observe fresh proof and same-owner quota/join admission; reuse the merged source
  implementations without legacy cache attribution or new routing state.
- Determine actual cleanup failure, including setup failure, and provide a fact
  the process can use to prevent unsafe next-job reuse. Preserve original outcomes.

**Q3 — How does the process admit work and terminate under real I/O?**

- Bound input/output and active work; specify framing, EOF, malformed/oversized
  frames, broken stdout, signals and cooperative/hard termination limits.
- Never introduce an unowned blocked stdin thread or let slow output cause more
  source work than the chosen admission model permits.
- Consume the cleanup fact explicitly; define the process's fail-closed transition
  and behavior after partially written results or unknown completion.

**Q4 — How does the caller receive usable results and health without losing meaning?**

- Project raw MessageBatch v1 unchanged, including partial results, and preserve
  all group outcome distinctions (readable/denied/unprobed; joined/requested/etc.).
- Correlate health to immutable job/account context and settle its delivery rule;
  source output must not wait on arbitrary external observers.
- Provide an executable caller example and actual SDK/process fault qualification,
  showing uncertain joins and replay are caller decisions, not implicit retries.

Each question is independently answerable against the declared interfaces, not
against sibling implementation details. No further recursive split is useful now.

## 5 — Interface Map and assumptions

| Provider → consumer | What flows | Assumptions that must be explicit |
|---|---|---|
| Q1 → Q2/Q3/Q4 | Request/result/version contract, allowed duties | No hidden durable acceptance or transport-selected credentials |
| Q3 → Q2 | Validated immutable job; cancellation/stop request | At most the chosen admitted concurrency; no queued SDK tasks outside owner |
| Q2 → Q3 | Source completed/failed/cancelled and cleanup-safe/unsafe knowledge | Normal body return alone is not successful cleanup; unsafe blocks further admission |
| Q2 → Q4 | Original data/error prefix and owned plain health observations | Actual account, stable job correlation, no client/credential handles |
| Q4 → Q3 | Bounded JSON-ready frames | One writer; output cannot fabricate receiver acceptance |
| Caller → Q3 | Complete requests and continued output draining | Exclusive sessions/account assignment; retry is explicit caller intent |
| Q3/Q4 → caller | Framed outcomes/status or EOF/termination | Missing/truncated reply is not rollback; never automatically retry an uncertain join |

Only cancellation and outcomes make Q2/Q3 bidirectional; the interface is defined
before either implementation. Worker startup/configuration is trusted local input;
job payloads are untrusted structured data within that configured capability set.

## 6 — Dependency order

Q1 first. Then Q2 ownership/failure determination and Q4 result projection can be
reasoned about against Q1; Q3 depends on Q2's real cleanup/source lifetime evidence,
not just its desired type signature. Reassemble all four in actual process tests.
No runtime code begins during this inquiry; Innovation chooses surviving mechanisms,
Critique challenges the combined boundary, and the later plan orders implementation.

## 7 — Self-evaluation

IndependencePASS (contract-level interfaces); completenessPASS (four jobs, inventory,
budgets, proxy/session, health, results, I/O, receipt ambiguity and shutdown covered);
reassemblyPASS (Q2 determines ownership/cleanup rather than assuming it).
TractabilityPASS (four focused questions); interface clarityPASS (data and timing/
resource assumptions named); balancePASS (Q2 and Q3 both carry substantial complexity);
confidencePASS (bottom-up atoms match the clusters). No missing determination piece.

Seven failure modes checked: sensemaking precedes this partition; no strong bond
cut, hidden assumption left unnamed, original duty omitted, one-line fragment
invented, dependency ignored or all complexity hidden in a single piece.

**Result: DV1, four questions, seven explicit interfaces, 7/7 dimensions PASS.**
