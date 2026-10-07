# Sensemaking — account routing and failover

## User Input

`_branch.md`, its four alternatives, and `surfacing.md`. First delivery:
existing-access groups; #7 remains paused. Establish what ownership and recovery
must mean before selecting an implementation.

## SV1 — baseline

An account pool might appear to be an ordered list of TgData instances: choose a
healthy one, call its batch reader, catch errors and try the next. That reading
does not yet establish who owns a result or whether another attempt is permitted.

## Phase 1 — anchors / SV2

| ID | Type | Anchor and evidence |
|---|---|---|
| A1 | Constraint | Joining is excluded by the user's explicit scope reply. |
| A2 | Structural point | ConnectionPool is same-account session capacity; account selection is a separate owner. |
| A3 | Insight | Budget admission refreshes authenticated identity; legacy health reads cached identity. |
| A4 | Principle | The existing ledger reserves before each SDK send; switching accounts cannot refund an uncertain attempt. |
| A5 | Structural point | SyncEngine/BackfillEngine own persisted pending observations and acknowledgment. |
| A6 | Constraint | Different accounts can see different history; canonical group identity alone cannot prove equal coverage. |
| A7 | Meaning-node | Eligibility means permission to attempt a specific read now, not a permanent global health certificate. |
| A8 | Insight | SDK and connection-engine handling can obscure the original error or sleep through the entire wait. |
| A9 | Principle | Cancellation requires the attempted task to end before another account can start. |

SV2: this is source-attempt ownership composed with existing delivery ownership.
H4/H5 check: “healthy” is not one cached boolean; #7's examples are evidence of a
broader identity/attribution problem, not the full problem specification.

## Phase 2 — perspectives / SV3

- Technical: the same live credential can disagree with its restored identity
  row. An immutable expected account ID must be checked against actual identity;
  relabeling a legacy summary cannot prove that check happened.
- User: the caller wants a group read and actionable “none available,” not a
  hidden two-hour sleep or a successful empty result for an inaccessible group.
- Strategic: the pool should reuse raw batches and current progress engines.
  A new cursor or receiver would couple reusable routing to application delivery.
- Failure: local disk/store/format errors are not grounds to exhaust other
  accounts. A nonempty completed prefix is owed even if its account is unusable.
- Resources: trying every account on every call wastes metadata traffic and
  allowances. Selection observations have a scope, lifetime and recovery rule.
- Systemic: multiple accounts must not make a failed request free. Existing
  per-account policies remain authoritative; capacity is not created by routing.
- Definitions: “pool” already names same-account connections. A distinct public
  AccountPool must not silently change connection_pool_size.
- Frame-exit (fires for inherited “state” and “recovery”): enumerate session
  state, budget reservations, account restrictions, pending delivery, lifecycle
  attempts and destination receipts. The pool needs the first three but must
  operate within the last three. Ignoring delivery would discard owed output;
  relocating delivery to its existing engine preserves it. Strongest counter is
  that one controller could own all state; that creates two implementations of
  already-tested acknowledgment and independent progress rather than solving the
  source seam. Residual: a dead process may leave source uncertainty; lifecycle
  recovery and caller-established single ownership remain required.
- Phase/calibration: warm-up is currently a reduced allowance, not automatically
  an exclusion. “Past warm-up” needs explicit minimum-age policy or zero extra
  exclusion. Live two-account equivalence has not been established by #19 gates.

SV3: several independent authorities exist. The pool must bind identity and
bound attempts; budget and progress stay in their original authorities. H1/H2/H3/H7:
bounded and integrated readers may share one source seam; durable scheduling is
not implied by the word “pool”; no calibration justifies aggressive retries.

## Actual component probes

Ran `/private/tmp/tgdata17-premise-probes.py` against dev95, Python 3.11.10 and
Telethon 1.45.0; synthetic transport at the existing test18 seam, real factory,
SDK request path, SQLite ledger and progress engines. Socket connect forbidden.
The exact probe source is retained below for reproducibility.

| Probe | Observation |
|---|---|
| Cached111, actual222, real batch denial | Fresh identity222; budget222 reserved1; event and summary both incorrectly111. |
| SDK request_retries=0 | Default exhaustion raises ValueError; raise_last_call_error=True preserves ServerError. Both invoke the SDK's final two-second sleep. |
| Actual ConnectionEngine._authenticate with FloodWait7200 | The method requests a 7200-second sleep, then invokes login again. The sleep was intercepted, not actually waited. |
| Daily pending replay after source identity changes | Same batch, zero new source reads; ack works. |
| Backfill pending replay after source identity changes | Same scoped delivery, zero new source reads. |

Probe-local correction: the first backfill setup omitted its test fixture's TMP
binding and raised TypeError before that probe ran. Bound the fixture directory;
rerun completed all five probes. No runtime code was changed. These probes do not
prove real account visibility, real proxy failure or deployment restart safety.

## Phase 3 — ambiguity collapse / SV4

Each entry names the counter, its structural test, fixed boundary and dependency.

1. **Owner = configured name or cached self?** Counter: session name identifies
   the account sufficiently. Probe shows actual222/cache111 under one name.
   **HIGH:** expected numeric identity plus fresh verification owns reads;
   names are labels. No cached-ID authority. Selection, billing and reporting
   depend on this. Ownership becomes explicit rather than inferred.
2. **Use global health as eligibility?** Counter: existing HealthMonitor already
   classifies all needed states. Its mutable identity and recovery on other
   answered requests cannot prove this group's readability. **HIGH:** use
   operation-owned facts; reuse error taxonomy where justified, not the legacy
   snapshot as authorization. Pool recovery depends on fact scope and evidence.
3. **Retry everything?** Counter: read-only retries cannot corrupt Telegram.
   They still consume allowance, duplicate source observations and hide local
   faults. **HIGH:** only classified account/group/transport unavailability can
   move to another candidate, at most bounded attempts. Unknown/local failures
   stop. Error propagation and candidate enumeration depend on this boundary.
4. **Retry after a partial failure?** Counter: discard prefix and request the
   original range elsewhere; destination dedupe can handle it. The source can
   change visibility and a completed prefix is already a delivery obligation.
   **HIGH:** return/raise that exact prefix to the existing delivery owner before
   another source read. No pool ack/cursor. Progress integration depends on this.
5. **Is empty success complete history?** Counter: same canonical chat and cursor
   imply equivalent reads. Telegram account visibility is a separate input; the
   accepted contracts explicitly carry no equality proof. **HIGH:** results mean
   currently account-visible history. A pool cannot manufacture a union-history
   or absence proof. Documentation and operational expectations depend on it.
6. **Can the ordinary connection path supply bounded failover?** Counter: set
   flood_sleep_threshold=0 and reuse everything. Actual authentication still
   sleeps7200, and default SDK exhaustion loses the cause. **HIGH:** source owner
   needs an opt-in controlled connection/request policy; legacy default behavior
   stays intact. Timing tests must include authentication and SDK exhaustion.
7. **Warm-up finished versus reduced cap?** Counter: any positive remaining cap
   implies fully eligible. A cap controls quantity, not caller-required maturity.
   **HIGH:** minimum age is an explicit additional policy; default extra delay0,
   with all ledger caps enforced. Never invent a finish date from an arbitrary curve.
8. **Durable versus process-local routing facts?** Counter to durability: all
   source behavior is rechecked, so a process-local cache suffices. That does not
   retain an observed wait across restart; counter to a full controller: existing
   source/delivery ownership already solves progress uncertainty. **LOW/open
   mechanism:** known waits must not be silently forgotten; determine minimal
   durability and lifecycle contract in Innovation, without duplicating a scheduler.
9. **One failure pattern or just #7?** Counter: fixing two examples is enough.
   Authentication, message admission, cached entity resolution, concurrent task
   ownership and partial output have separate evidence points. **HIGH:** enforce
   the invariant at those points; do not copy a two-case patch or assume the
   entire #7 redesign is prerequisite. Source-owner design depends on this breadth.

SV4: identity, quota authority, prefix preservation, visibility and retry boundary
are fixed. Selection/durable observation mechanisms remain alternatives, not
irreversible guesses. Load-bearing concepts from prior work (pending observation,
actual account, unknown attempt, visibility-qualified end) have each been tested
against a counter, with the relevant probe or mechanism identified above.

## Phase 4 — degrees of freedom / SV5

Fixed: existing-access scope; separate account owner; same batch format; ledger
reservation; existing progress/receipt state; no joins or automatic merge.
Eliminated: array of arbitrary shared TgData instances plus broad exception catch;
trusting health cache; discarding prefixes; inferring equal history; unbounded
retry/sleep; copying ScrapeOps post-result accounting.
Viable: owned bounded readers with an explicit candidate policy; existing engines
consume that reader; minimal persistent restriction records versus a durable
controller remain to compare. Round-robin, affinity and drain/spread remain policy
choices, not identity mechanisms.

## Phase 5 — SV6 stabilized model

The pool owns permission for and attribution of a bounded source attempt. It
selects among explicitly configured accounts, verifies actual identity before
reading, applies existing budgets and explicit eligibility, records scoped failure
facts, and can try another account only after a quiescent failure with no owed
prefix. The existing daily/backfill engines continue to own durable delivery.

Compared with SV1, selection is a small part of the task; ownership and stopping
conditions are the load-bearing structure. Accommodation check H6: new facts
changed the initial shared-client model, then stabilized this ownership boundary;
no additional exceptions needed. It remains honest about account-visible history.

Telemetry: 9 anchors across all five types; 9 perspectives; 8/9 major ambiguities
resolved, persistence mechanism explicitly open. Final two perspectives refined
existing constraints rather than adding new authority types. Failure-mode checks:
legacy health challenged (no status-quo protection); five composition probes
prevent premature stability; independent identity/quota/delivery anchors prevent
dominance; strongest counters tested; no self-referential framework target.

**Next:** Decomposition of the stabilized boundaries and unresolved durability,
then Innovation to compare concrete mechanisms. No implementation design approved yet.

## Probe source

```python
import asyncio, json, socket, tempfile, logging
from pathlib import Path
from unittest.mock import patch, AsyncMock
from telethon import errors
from tgdata import health, SQLiteSyncStore
from tgdata.sync_engine import SyncEngine
from tgdata.smoke_tests import test_18_read_budget as f
from tgdata.smoke_tests import test_29_backfill_public as u

async def run():
    with tempfile.TemporaryDirectory(prefix='tgdata17-premises-') as directory:
        f.TMP=Path(directory)
        u.d.TMP=Path(directory)
        u.b.TMP=Path(directory)
        budget,_=f.ledger(account=222)
        events=[]
        tg,client,sender=f.instance(budget,account=222,cached=111,events=events)
        fresh=await client._read_budget_account()
        sender.script=[errors.ChannelPrivateError(request=None)]
        await f.expect(errors.ChannelPrivateError,tg.get_message_batch(-1000000000007,limit=1))
        print(json.dumps(dict(probe='identity',fresh=fresh,cached=client._self_id,
            event=events[-1]['account']['user_id'],snapshot=tg._health.snapshot()['account']['user_id'],
            actual_account_reserved=budget.status(222).reserved)))
        plain,c,s=f.instance();c._request_retries=0
        findings=[]
        for last in (False,True):
            c._raise_last_call_error=last;s.script=[errors.ServerError(request=None,message='SYNTHETIC',code=500)]
            with patch('asyncio.sleep',new_callable=AsyncMock) as sleep:
                try: await c(f.history())
                except Exception as e: findings.append(dict(raise_last=last,error=type(e).__name__,sleeps=[x.args[0] for x in sleep.await_args_list]))
        print(json.dumps(dict(probe='sdk_exhaustion',findings=findings)))
        with patch.object(plain.connection_engine,'_log_in',new_callable=AsyncMock,
                          side_effect=[errors.FloodWaitError(request=None,capture=7200),None]),patch('asyncio.sleep',new_callable=AsyncMock) as sleep:
            await plain.connection_engine._authenticate(c)
            print(json.dumps(dict(probe='authentication_wait',sleeps=[x.args[0] for x in sleep.await_args_list])))
        # Actual source -> real raw batch -> actual SQLite pending -> source-free replay.
        daily=SyncEngine(tg.get_message_batch,SQLiteSyncStore(Path(directory)/'sync.sqlite3'))
        await daily.initialize(-1000000000007,after_id=100)
        sender.script=[]
        batch=await daily.prepare(-1000000000007,limit=1)
        calls=len(sender.reads)
        sender.account=333  # no configured allowance: a new read would fail
        replay=await daily.prepare(-1000000000007,limit=1)
        assert replay.batch_id==batch.batch_id and len(sender.reads)==calls
        await daily.acknowledge(-1000000000007,batch.batch_id)
        print(json.dumps(dict(probe='daily_replay',same_batch=True,source_reads_on_replay=0)))
        # Existing public backfill engine/replies also keep owed data independent of reader.
        e=await u.setup()
        e.sender.script=[u.d.finite_response([f.message(101)])]
        turn=await e.tg.prepare_backfill(u.ctx(e.initial))
        calls=len(e.sender.reads);e.sender.account=333
        replay=await e.tg.prepare_backfill(u.ctx(turn.status))
        assert replay.delivery==turn.delivery and len(e.sender.reads)==calls
        print(json.dumps(dict(probe='backfill_replay',same_delivery=True,source_reads_on_replay=0)))
        for c in f.CLIENTS: c.session.close()
logging.disable(logging.CRITICAL)
with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
    asyncio.run(run())
```
