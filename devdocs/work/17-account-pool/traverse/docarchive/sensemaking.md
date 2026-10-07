# Sensemaking — attempt boundaries, iteration 2

## User Input

`_branch.md`, `critique_iter1.md` refinement targets and current `surfacing.md`.
Keep the established source/ledger/delivery split; resolve durable admission and
timeout prefixes. The prior SV1–SV6 remains context, not a replacement for this pass.

## SV1 — baseline

Durable failure facts leave a gap between source work and fact persistence.
Timeout cancellation may also hide completed records. Both concern the boundary
of an attempted operation, not which account ranks first.

## Phase 1 — anchors / SV2

Constraints: no source before confirmed permission; no new source while old work
is unresolved; caller cancellation must propagate. Insights: a persisted active
attempt records uncertainty without needing to guess its outcome; wait_for waits
for cancellation and retains the CancelledError as its cause in this interpreter.
Structural points: actual SQLite CAS; BatchEngine's outer exception seam; existing
progress prefix publication. Principles: readback is evidence, never permission
to invent a successful read; an account attempt owns source eligibility, whereas
a group receipt owns downstream delivery. Meaning-node: quiescent settlement.
SV2: the two gaps share attempt ownership but have distinct state/output duties.
H4/H5: “active” means admitted and not settled, not “a worker certainly exists.”

## Phase 2 — perspectives / SV3

Technical: CAS an attempt token before starting the child; settle only that token.
User: an unknown attempt should explain recovery, not look like an account ban.
Failure: store error after successful data must carry the completed observation;
store error after an admission may leave an active token even if no request ran.
Resource: no second full lifecycle scheduler is needed; one active token and
restriction row per account has a small state space. Strategic: retain existing
group recovery semantics separately, since source eligibility and owed delivery
can recover in different orders. Systemic: ambiguous failures retain ledger
charges. Definitions/frame-exit: “recovery” has source-quiescence, account repair
and receiver acceptance meanings; only the first two belong here. Treating receipt
ack as account recovery would bypass restrictions, so the clean boundary survives
that counter. Phase/calibration: UTC deadlines require trustworthy time; backward
clock evidence refuses and process restart cannot auto-clear an active token.
SV3: durable permission plus token-specific settlement is enough; no lease that
expires into automatic permission. Last perspectives introduce no new authority.

## Actual probes

Executed `/private/tmp/tgdata17-boundary-probes.py` offline, with actual current
factory, SDK, SQLite and SyncEngine. To test a proposed capability without changing
product files, executed the actual BatchEngine source in a temporary module with
only its outer exception tuple extended to include CancelledError.

- After 100 complete messages, the next sender future stayed pending. A timed read
  cancelled it, retained 100 interrupted records, and the real SyncEngine saved
  and replayed that exact batch with zero additional reads. Charge remained200
  (100 returned plus100 uncertain). No test double supplied the partial batch.
- Actual SQLite admission survived a second backend instance; token-specific CAS
  settlement succeeded once, and a stale settlement using the old raw document
  refused. This proves the primitive, not the future pool state machine.

## Phase 3 — ambiguity collapse / SV4

**Admission token versus expiring lease.** Counter: timeout expiry can authorize
another worker automatically. It cannot prove the earlier task ended; the old
task may be waiting on storage or a paused event loop. HIGH: no automatic expiry
of uncertainty. Fixed: explicit token and quiescence; excluded: elapsed-time-only
recovery. Router/recovery now depend on token ownership rather than a timer guess.

**Source attempt versus delivery attempt.** Counter: reuse the backfill run's
attempt as the only record. Raw reads and daily reads have no such run, and an
account restriction spans groups. HIGH: separate account source permission,
unchanged group delivery authority. No copied pending/ack state in pool storage.
This tests the inherited owner distinction structurally, beyond one #7 example.

**Timeout prefix versus ordinary cancellation.** Counter: attach any prefix and
turn every cancellation into a retryable timeout. Caller cancellation is deliberate
control, whereas the pool's own timer is a source outcome. HIGH: only the internal
timeout becomes an ordinary exception carrying an interrupted prefix; external
cancellation re-raises and leaves the durable attempt unresolved. The probe proves
the narrow BatchEngine seam can expose the prefix without changing MessageBatch.

**Failed settlement versus failed delivery.** Counter: returning the successful
batch while swallowing the pool-store error is harmless. A future call could make
contradictory eligibility decisions, and the caller would miss source uncertainty.
HIGH: local storage error with completed interrupted prefix and separate read_error;
no false Telegram health cause. A nonempty prefix still reaches existing progress
storage. No source retry is allowed inside that failing call.

**Recovery grants health?** Counter: after the process is dead, clear the token and
try immediately. Death proves quiescence, not absence of an unrecorded flood wait.
HIGH: explicit recovery includes the exact attempt ID, caller-confirmed prior reader
stopped, and an explicit retry-not-before bound; it cannot shorten saved waits or
clear bans/identity repair flags. The bound is operator policy under unknown outcome,
not evidence of Telegram permission. Every later read still verifies identity.

SV4: all five remaining semantic ambiguities are resolved; the persistent store
API shape remains an implementation choice within these constraints.

## Phase 4 — reduction / SV5

Fixed: token before source; settlement after quiescence; prefix on local settlement
failure; no timeout-as-caller-cancellation; explicit recovery. Eliminated: expiring
leases, post-result-only state, copying group receipts, and implicit healthy reset.
Viable mechanisms: one opaque pool document with account rows versus separate
account documents; both can implement the same contract with exact CAS.

## Phase 5 — SV6

A source call is permitted by a durably admitted account token. It ends by a
token-specific settlement carrying scoped restrictions, or remains unresolved.
No successful response is fabricated from uncertainty. A pool timeout transfers
completed records to the existing delivery owner after the cancelled task ends.
Caller cancellation retains its existing propagation semantics.

SV6 adds an explicit pre-source boundary to SV1, not another scheduler. H6:
the new evidence fits the source-owner model; no repeated patching of unrelated
health state. Telemetry: all five anchor types, eight perspectives,5/5 ambiguity
resolutions; actual primitive and composed timeout probes. Status-quo bias,
premature stability, anchor dominance, perspective blindness, clean-resolution
and self-reference checks found no unresolved structural conflict. Next: Decomposition.

## Reproducible probe source

```python
import asyncio, json, logging, socket, tempfile, types as pytypes
from pathlib import Path
from unittest.mock import patch
from tgdata import SQLiteSyncStore
from tgdata.sync_engine import SyncEngine
from tgdata.smoke_tests import test_18_read_budget as f

async def run():
    with tempfile.TemporaryDirectory(prefix='tgdata17-boundaries-') as directory:
        f.TMP=Path(directory)
        budget,_=f.ledger(limit=1000)
        tg,client,sender=f.instance(budget)
        # Probe only: execute the actual BatchEngine source with its outer
        # exception tuple extended to include cancellation. No product edit.
        source=Path('tgdata/batch_engine.py').read_text()
        assert source.count('except Exception as error:')==1
        source='import asyncio\n'+source.replace('except Exception as error:', 'except (Exception, asyncio.CancelledError) as error:')
        module=pytypes.ModuleType('tgdata._pool_boundary_probe');module.__package__='tgdata'
        exec(compile(source,'<actual BatchEngine plus cancellation exception seam>','exec'),module.__dict__)
        batch_reader=module.BatchEngine(tg.connection_engine)
        sender.script=[f.response([f.message(n) for n in reversed(range(101,201))]),f.PENDING]
        async def timed_reader(*args,**kwargs):
            try: return await asyncio.wait_for(batch_reader.fetch_batch(*args,**kwargs),0.03)
            except asyncio.TimeoutError as error:
                error.partial_result=getattr(error.__cause__,'partial_result',None)
                raise
        daily=SyncEngine(timed_reader,SQLiteSyncStore(Path(directory)/'daily.sqlite3'))
        await daily.initialize(-1000000000007,after_id=100)
        error=await f.expect(asyncio.TimeoutError,daily.prepare(-1000000000007,limit=200))
        assert len(error.partial_result.messages)==100
        assert error.partial_result.stop_reason=='interrupted'
        assert sender.pending[0].cancelled()
        reads=len(sender.reads);batch=await daily.prepare(-1000000000007,limit=1)
        assert batch.batch_id==error.partial_result.batch_id and len(sender.reads)==reads
        print(json.dumps(dict(probe='timeout_prefix',messages=len(batch.messages),pending_send_cancelled=True,replay_reads=0,charge=budget.status(f.ACCOUNT).used)))
        store=SQLiteSyncStore(Path(directory)/'attempt.sqlite3')
        initial=json.dumps({'version':1,'active':None});active=json.dumps({'version':1,'active':'unique-attempt'})
        assert await store.compare_and_swap(-1,None,initial)
        assert await store.compare_and_swap(-1,initial,active)
        restarted=SQLiteSyncStore(store.path,create=False)
        assert json.loads(await restarted.load(-1))['active']=='unique-attempt'
        outcome=json.dumps({'version':1,'active':None,'not_before':1700007200})
        assert await store.compare_and_swap(-1,active,outcome)
        assert not await store.compare_and_swap(-1,active,initial)
        print(json.dumps(dict(probe='attempt_CAS',reconstruction_retains_active=True,stale_settlement_refuses=True)))
        for client in f.CLIENTS:client.session.close()
logging.disable(logging.CRITICAL)
with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')):
    asyncio.run(run())
```
