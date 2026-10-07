"""Shared state-only progress facade over an injected bounded batch reader."""

from .backfill import (
    BackfillStartRequest, BackfillRunRef, BackfillPrepareContext, BackfillDeliveryRef,
    BackfillConfigurationError,
)
from .backfill_engine import BackfillEngine


class ProgressFacade:
    def _new_backfill_engine(self, collection):
        return BackfillEngine(self._backfill_store, collection, read_batch=self.get_message_batch)

    async def initialize_sync(self, chat_id, *, after_id, media_mode='references',
                              start_date=None, end_date=None, last_days=None):
        """Enroll a canonical negative chat ID at an explicit initial cursor.

        Zero starts at the oldest visible history. Matching repeated enrollment
        preserves current progress; a different initial cursor or mode raises.
        This only accesses the configured sync_store, never Telegram.
        For a historical collection, supply timezone-aware start_date/end_date
        or last_days (N*24 hours ending at first enrollment). Matching repeated
        relative enrollment reuses the saved dates. Dates include start and
        exclude end, intersecting after_id. A conflicting window raises; use
        separate progress stores for daily and historical collections.
        """
        return await self.sync_engine.initialize(
            chat_id, after_id=after_id, media_mode=media_mode,
            start_date=start_date, end_date=end_date, last_days=last_days)

    async def sync_group(self, chat_id, *, limit=200, download_media_to=None):
        """Prepare/replay one durable pending MessageBatch, or None if empty.

        Enroll the canonical chat ID first. Pending replay does not contact
        Telegram or spend budget. Deliver the batch durably, then explicitly
        acknowledge_sync(chat_id, batch.batch_id). One reader per group/store
        is supported; source behavior comes from the configured batch reader.

        An ordinary read error's nonempty partial_result is saved as pending
        before that same error is re-raised. A failed partial save raises a
        local SyncError with the original exception in read_error instead.
        Download-mode replay verifies every referenced blob at the given root.
        """
        # Only the actual configured batch reader carries a source health context.
        # Local replay must not count as fresh Telegram recovery evidence.
        return await self.sync_engine.prepare(chat_id, limit=limit,
                                              download_media_to=download_media_to)

    async def acknowledge_sync(self, chat_id, batch_id):
        """Assert durable destination acceptance and atomically advance progress.

        The next cursor comes from the saved batch, never from the caller.
        Repeating the latest acknowledgment is harmless; wrong/older IDs raise
        without clearing newer work. No Telegram connection is needed.
        """
        return await self.sync_engine.acknowledge(chat_id, batch_id)

    async def get_sync_status(self, chat_id):
        """Return immutable SyncStatus, or None if not enrolled; storage only."""
        return await self.sync_engine.status(chat_id)

    def _backfill_for(self, address, expected_type):
        if not isinstance(address, expected_type):
            raise BackfillConfigurationError('{} is required'.format(expected_type.__name__))
        owned = expected_type.from_dict(address.to_dict())
        if self._backfill_store is None:
            raise BackfillConfigurationError('configure a backfill_store in its own collection namespace')
        collection = (owned.run.collection_id if isinstance(owned, (BackfillPrepareContext, BackfillDeliveryRef))
                      else owned.collection_id)
        engine = self._backfill_engines.get(collection)
        if engine is None:
            engine = self._new_backfill_engine(collection)
            self._backfill_engines[collection] = engine
        return engine, owned

    async def start_backfill(self, start_request: BackfillStartRequest, *, submission):
        """Create explicit new intent or recognize its retained original request.

        submission is required: 'new' or 'retry'. Retain the request before
        submission; an unknown retry never creates. This is storage-only.
        """
        engine, request = self._backfill_for(start_request, BackfillStartRequest)
        return await engine.start(request, submission=submission)

    async def get_backfill_status(self, run: BackfillRunRef):
        """Return immutable stored facts for this complete run reference.

        Missing/pruned/corrupt/unavailable state raises; it never implies new
        intent or readiness. No source, credential or account refresh occurs.
        """
        engine, run = self._backfill_for(run, BackfillRunRef)
        return await engine.status(run)

    async def prepare_backfill(self, context: BackfillPrepareContext, *, download_media_to=None):
        """Prepare/replay one exact delivery, or return stored status/local wait.

        A stale cursor/control context refuses without auto-rebase. Until ack,
        pending replay uses saved bytes and does not contact Telegram. Only an
        eligible new attempt calls the existing get_message_batch health boundary.
        Ordinary source errors retain a valid prefix before re-raising; obtain
        its full delivery reference by replaying the stored pending observation.
        """
        engine, context = self._backfill_for(context, BackfillPrepareContext)
        return await engine.prepare(context, download_media_to=download_media_to)

    async def acknowledge_backfill(self, delivery: BackfillDeliveryRef):
        """Assert durable receiver acceptance of the exact full delivery reference.

        Advances only to the saved next cursor. It neither contacts the source
        nor checks/deletes media. Retained duplicate receipts are harmless;
        another run's equal hash cannot settle this run's obligation.
        """
        engine, delivery = self._backfill_for(delivery, BackfillDeliveryRef)
        return await engine.acknowledge(delivery)

    async def control_backfill(self, run: BackfillRunRef, *, command_id,
                               expected_control_revision, action):
        """Record pause/resume/cancel/abandon with its original exact context.

        Pause/cancel preserve admitted work and owed output; resume grants only
        operator permission. Only explicit quiescent abandonment withdraws an
        obligation. A recognized retry does not apply again or reset any wait.
        """
        engine, run = self._backfill_for(run, BackfillRunRef)
        return await engine.control(run, command_id=command_id,
                                    expected_control_revision=expected_control_revision, action=action)

    async def recover_backfill(self, run: BackfillRunRef, *, attempt_id, command_id,
                               expected_control_revision, previous_reader_stopped):
        """Reconcile one exact interrupted attempt after its worker actually stopped.

        The required true assertion does not terminate a worker or provide a
        distributed lease. Active local preparation refuses. Recovery preserves
        facts, uses known end evidence or one conservative wait, and never reads,
        acknowledges, resumes or refunds quota. Retain unchanged retry arguments.
        """
        engine, run = self._backfill_for(run, BackfillRunRef)
        return await engine.recover(run, attempt_id=attempt_id, command_id=command_id,
                                    expected_control_revision=expected_control_revision,
                                    previous_reader_stopped=previous_reader_stopped)
