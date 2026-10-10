---
model: gpt-6-astra
effort: max
---
**Verdict: REORDER — TEST BEFORE BUILD**

Falsifier: using the real ReadBudget against the proposed join namespace changes
join usage or cannot preserve independent read reservations/settlement.
Affordable now: yes — local actual SQLite/ReadBudget, seconds, no credentials.

Experiment: provision the proposed SQL schema in the actual ReadBudget file;
commit a join charge, exercise real read configure/reserve/settle/reopen, and
confirm both usages/policies persist independently. Inspect actual SQLite schema
descriptors and foreign-key enforcement so planned validation matches real output.
Cost: seconds locally; no network, account or money.
Must precede: step2, the persistent ledger; task-impl runs it before step1.
Disqualifying result: real read operations overwrite join state or the shared
file cannot support independent accounting/required schema primitives.
Passing result: read settlement yields its actual usage while join usage remains
one; reopening preserves both; descriptor/FK behavior matches the proposed schema.

## High-level summary

The standalone admitted-attempt contract fits the staged boundary. No receipt,
refund, raw-client guard or shared quota framework is justified here. Existing
SQLite/process probes are real and useful, but have not yet exercised the stated
same-file composition with ReadBudget. Close that inexpensive premise first.
One Medium compatibility finding requires a small fold: explicitly preserve
asyncio cancellation even on Python3.7, where it inherits Exception. No High/Low
findings; no execution blocker. This is plan critique, not PR acceptance.

## Premise Inventory

### P1 — Actual read/join namespace coexistence

**First dependent step:**2. **Waste if false:** storage/operations/tests/docs2–5.
**Test scheduled at:**4. **Cheapest earlier test:** the experiment above, seconds.
**Coverage:** current ReadBudget and schema source are documentary support;
inquiry probes tested a dedicated ledger, not this actual composition. Not yet
behaviorally covered. This sets REORDER, independently of the risk below.

### P2 — SQLite serialization, durable process exits and uncertain commits

**First dependent step:**2. **Waste if false:**2–5. **Test scheduled at:** inquiry
before the plan, repeated through new methods in4. **Cheapest earlier test:**
already run actual SQLite with six spawned competitors and actual process exits.
**Coverage:** evidence/critique-probe.txt: cap3 admitted3, before-commit exit0,
after-commit exit1, error injected after real commit retains1. The injected error
does not claim a native SQLite postcommit fault, and no physical power-loss proof
is claimed. Covered within the intended same-host operating assumptions.

### P3 — Forward clock/storage custody

**First dependent step:**3. **Waste if false:** a wrong clock or externally reset
database changes accounting. **Test scheduled at:** bounded behavior in4, operating
assumptions documented5. **Cheapest earlier test:** no finite local test can prove
future host-clock accuracy or rule out later valid-looking external file edits.
**Coverage:** explicit limitations, not an unqualified claim of protection.

No premise about live Telegram joining, safe rates or future SDK retry behavior is
being qualified by this stage. Those dependencies are explicitly absent.

## Restart Check

| Observed failure | Established mechanism | Design element addressing it |
|---|---|---|
| Old ledger reopens after dropped attempts table with free allowance | Constructor CREATE IF NOT EXISTS recreates missing history; inquiry reproduction | Step2 explicit provision and complete owned-schema checks on every transaction |
| Negative/future admission time accepted or pruned away | Old status prunes before validating records against prior clock | Step3 validate before clock update/deletion; step4 unchanged-row assertions |
| Old broad #7 stale owner summary | Cache supplied summary owner despite fresh authenticated source | Already merged Stage1/2 foundation; Stage4 has no health/client path; Stage5 must consume verified owner |
| Old broad #7 source error changed meaning | Group wrapper translated operational errors as reference failures | Already merged Stage3 source/error boundary; no group wrappers changed here |

## Inherited Lessons

| Lesson | Ordering that satisfies it |
|---|---|
| Prior review success does not prove a new ledger | Real inquiry probes before plan; new method-level tests4 before delivery6 |
| Local transaction success is not remote outcome | Counting contract fixed before code; step3 consumes before any future send and exposes no refund |
| More machinery does not establish ownership | Stage1/2 merged first; step5 documents the later verified consumer, no ambient owner added |
| Missing state must not become allowance | Step2 refusal precedes step3 observation; step4 destructive temp-file tests |
| A status query is not a reservation | Step3 claim decides/inserts atomically, concurrency tested4 |

## Risk 1 — Cancellation depends on the interpreter's exception hierarchy

**Risk**

On an older supported Python version, stopping an operation can look like an
ordinary callback or storage failure. The caller then receives the wrong error
instead of cancellation, and retry or shutdown logic can proceed incorrectly.
The tests on the current interpreter would not expose the older hierarchy.

Step1 catches callback Exception and step2 maps a sole close Exception to a local
error in `tgdata/join_budget.py`. `setup.py:58` advertises Python>=3.7. Python3.7's
`asyncio.CancelledError` inherits Exception; Python3.8 changed it to BaseException.
The plan says cancellation propagates but does not prescribe an explicit preceding
CancelledError branch, leaving these concrete proposed catches contradictory on3.7.

**Severity:** Medium
**Category:** Compatibility / cancellation
**Impact:** lost cancellation identity and inappropriate local-error handling at
clock/argument callback or sole cleanup boundaries on a supported interpreter.
**NoobEng:** broad Exception catches exclude task cancellation today, but that is
not true for the oldest advertised version. Name cancellation before converting
ordinary errors. Cleanup secondary to an existing failure is still suppressed.
**Affected areas:** new module's conversions, clock call and cleanup-only error path;
tests must distinguish native current-runtime cancellation from a compatibility fixture.

Evidence: package metadata and [Python's exception documentation](https://docs.python.org/3/library/asyncio-exceptions.html).
This is a documented hierarchy difference, not a live vendor-behavior hypothesis.

### Mitigation — Quick

Document cancellation support only on3.8+, leaving metadata and oldest behavior inconsistent.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* —

### Mitigation — Robust

Explicitly re-raise asyncio.CancelledError before each generic conversion catch,
including sole close. Preserve the original when cancellation is merely a secondary
cleanup failure. Add native cancellation tests plus a clearly labeled Exception-derived
compatibility fixture at those catches; do not claim a native Python3.7 run.

**Why this is robust:** makes the promised behavior independent of the inheritance
change at the precise new error boundaries, without altering existing modules.

- [x] selected   - [x] elegant   - [ ] last_resort

**Note**
*Why chosen:* Best reach/extent: explicit cancellation handling closes all new conversion boundaries in one module. SQLiteSyncStore has a similar close catch, but shared synchronous/async cleanup abstractions need different policies; a repository audit/CI is wider work and not a prerequisite. The bounded fix survives that future work.
*For future:* —

### Mitigation — Long-term

Audit generic conversion/cleanup catches across the library and add native multi-version CI.

**Why this is long term effective:** gives other storage/callback paths and future
changes direct execution coverage on all advertised interpreters.

- [ ] selected   - [ ] elegant   - [ ] last_resort

**Note**
*Why chosen:* —
*For future:* Revisit a native oldest-version CI/audit separately when the supported-runtime matrix is qualified. SQLiteSyncStore and account-operation cleanup are concrete audit subjects, not grounds to expand this allowance stage.

## Review scope and negative findings

Schema/data checks are sufficiently explicit for implementation. Offset used-limit
correctly waits for enough expirations after a cap reduction. Denial is raised only
after maintenance commit. No health/client mutations, input sessions or credentials
are stored. Short synchronous transactions can block for5s under contention and scan
owned rows for corruption; these are bounded local storage operations, not nonblocking
network work. Large usage incurs proportional validation; no unrealistic latency
guarantee is made. Existing status/import compatibility is qualified in steps4–6.

No plan rewrite, parked task or meaning-gap deprecation is warranted. Run the
composition experiment, select the bounded mitigation and then fold without re-critique.
