"""One pending observation per group, acknowledged independently of fetching."""

import asyncio
from dataclasses import replace
import os

from .batch_files import prepare_directory, _verify_existing
from .message_batch import MessageBatch, MAX_BATCH_MESSAGES, MAX_MESSAGE_ID
from .sync_store import (
    SyncError, SyncConfigurationError, SyncNotInitializedError,
    SyncConflictError, SyncStorageError, _State, _chat_id, _integer,
    _mode, _batch_id, _decode, _validate_batch,
)


class SyncEngine:
    def __init__(self, read_batch, store):
        self._read_batch = read_batch
        self._store = store
        self._preparing = set()

    def _require_store(self):
        if (self._store is None or not callable(getattr(self._store, 'load', None))
                or not callable(getattr(self._store, 'compare_and_swap', None))):
            raise SyncConfigurationError('Configure a sync_store with async load and compare_and_swap')

    async def _backend(self, method, *args):
        self._require_store()
        try:
            return await getattr(self._store, method)(*args)
        except asyncio.CancelledError:
            raise
        except SyncError as error:
            raise error from None
        except Exception as error:
            raise SyncStorageError('Sync store {} failed ({})'.format(method, type(error).__name__)) from None

    async def _load(self, chat_id, required=True):
        raw = await self._backend('load', chat_id)
        if raw is None:
            if required:
                raise SyncNotInitializedError('Initialize this group with an explicit after_id first')
            return None, None
        return raw, _decode(raw, chat_id)

    async def _replace(self, chat_id, expected, state):
        written = await self._backend('compare_and_swap', chat_id, expected, state.encode())
        if type(written) is not bool:
            raise SyncStorageError('Sync store compare_and_swap must return a boolean')
        if not written:
            raise SyncConflictError('Sync state changed; reload before retrying')

    async def initialize(self, chat_id, *, after_id, media_mode='references'):
        chat_id = _chat_id(chat_id)
        after_id = _integer(after_id, 'after_id', 0, MAX_MESSAGE_ID)
        media_mode = _mode(media_mode)
        raw, existing = await self._load(chat_id, required=False)
        if existing is not None:
            if existing.initial_after_id != after_id or existing.media_mode != media_mode:
                raise SyncConflictError('Group already enrolled with a different initial position or media mode')
            return existing.status()
        state = _State(chat_id, after_id, after_id, media_mode)
        await self._replace(chat_id, raw, state)
        return state.status()

    @staticmethod
    def _directory(media_mode, directory):
        if media_mode == 'references':
            if directory is not None:
                raise SyncConfigurationError('Reference-only enrollment does not accept a media directory')
            return None
        if (not isinstance(directory, (str, os.PathLike)) or isinstance(directory, bool)
                or directory == ''):
            raise SyncConfigurationError('Download enrollment requires an explicit media directory')
        return prepare_directory(directory)

    @staticmethod
    def _verify_media(batch, directory):
        verified = set()
        for record in batch.messages:
            media = record['media']
            blob = media['blob'] if media is not None else None
            if blob is None:
                continue
            key = (blob['sha256'], blob['size'])
            if key not in verified:
                _verify_existing(directory / blob['path'], blob['sha256'], blob['size'])
                verified.add(key)

    async def _publish(self, raw, state, batch):
        value = _validate_batch(batch, state.chat_id, state.after_id, state.media_mode)
        if not value['messages']:
            return None
        await self._replace(state.chat_id, raw, replace(state, pending=batch))
        return batch

    async def prepare(self, chat_id, *, limit=200, download_media_to=None):
        chat_id = _chat_id(chat_id)
        limit = _integer(limit, 'limit', 1, MAX_BATCH_MESSAGES)
        self._require_store()
        if chat_id in self._preparing:
            raise SyncConflictError('Sync preparation is already in progress for this group')
        self._preparing.add(chat_id)
        try:
            raw, state = await self._load(chat_id)
            directory = self._directory(state.media_mode, download_media_to)
            if state.pending is not None:
                if state.media_mode == 'download':
                    self._verify_media(state.pending, directory)
                return state.pending
            try:
                batch = await self._read_batch(
                    chat_id, after_id=state.after_id, limit=limit,
                    download_media_to=directory,
                )
            except asyncio.CancelledError:
                raise
            except Exception as read_error:
                partial = getattr(read_error, 'partial_result', None)
                if isinstance(partial, MessageBatch) and partial.messages:
                    try:
                        await self._publish(raw, state, partial)
                    except asyncio.CancelledError:
                        raise
                    except SyncError as storage_error:
                        # Persistence is part of preparation, not cleanup. The
                        # prefix cannot be advertised as durable if this failed.
                        storage_error.read_error = read_error
                        raise storage_error from None
                raise
            return await self._publish(raw, state, batch)
        finally:
            self._preparing.discard(chat_id)

    async def acknowledge(self, chat_id, batch_id):
        chat_id = _chat_id(chat_id)
        batch_id = _batch_id(batch_id)
        raw, state = await self._load(chat_id)
        if batch_id == state.last_acked_batch_id:
            return state.status()
        if state.pending is None or state.pending.batch_id != batch_id:
            raise SyncConflictError('Acknowledgment does not match this group\'s pending batch')
        accepted = replace(state, after_id=state.pending.next_after_id,
                           pending=None, last_acked_batch_id=batch_id)
        await self._replace(chat_id, raw, accepted)
        return accepted.status()

    async def status(self, chat_id):
        chat_id = _chat_id(chat_id)
        _, state = await self._load(chat_id, required=False)
        return state.status() if state is not None else None
