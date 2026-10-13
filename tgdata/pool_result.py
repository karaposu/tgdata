"""Caller-owned, single-use data capture for AccountPool reads; no task ownership."""
import asyncio
from contextlib import contextmanager
from dataclasses import dataclass, field
import re
from typing import Optional

from .message_batch import MessageBatch, _interrupted_prefix
from .pool_state import PoolConfigurationError, PoolStateError


@dataclass(frozen=True)
class PoolReadSnapshot:
    """One immutable observation of a public pool call, not a delivery receipt.

    Running and interrupted calls expose only complete interrupted data. A
    successful call preserves its actual batch. Replay has no source account;
    error fields contain bounded type names, never retained exception objects.
    """
    state: str
    batch: Optional[MessageBatch] = field(repr=False)
    account_id: Optional[int]
    error_type: Optional[str]
    read_error_type: Optional[str]


class _CaptureState:
    def __init__(self):
        self.phase = 'unbound'
        self.batch = None
        self.records = None
        self.address = None
        self.account_id = None
        self.expected_account = None
        self.error_type = None
        self.read_error_type = None

    def available(self):
        if self.batch is not None:
            return _interrupted_prefix(self.batch)
        if self.records:
            chat, after, mode = self.address
            return MessageBatch._from_records(chat, after, self.records, mode, 'interrupted')
        return None


class PoolReadCapture:
    """Keep this object before awaiting one pool read/prepare.

    snapshot() never awaits or performs I/O. A running snapshot's batch is only
    available data, with interrupted semantics; it is never an ack receipt.
    Reuse is refused. Drop references to release data. No process-crash promise.
    """
    __slots__ = ('__state', '__weakref__')

    def __init__(self):
        object.__setattr__(self, '_PoolReadCapture__state', _CaptureState())

    def __setattr__(self, name, value):
        raise AttributeError('PoolReadCapture exposes read-only observations')

    def snapshot(self):
        state = object.__getattribute__(self, '_PoolReadCapture__state')
        batch = state.available() if state.phase == 'running' else state.batch
        return PoolReadSnapshot(state.phase, batch, state.account_id if batch is not None else None,
                                state.error_type, state.read_error_type)


def _error_name(error):
    name = type(error).__name__
    return name if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,127}', name) else 'Exception'


class _CaptureWriter:
    def __init__(self, state):
        self.state = state

    def attempt(self, account_id):
        state = self.state
        # A new attempt has no inherited data or source diagnostics.
        if state.records or (state.batch is not None and state.batch.messages):
            raise PoolStateError('Cannot switch source after complete data is available')
        state.records = state.address = state.batch = state.account_id = None
        state.read_error_type = None
        state.expected_account = account_id

    def attach(self, chat_id, after_id, mode, records):
        # Called by the real batch engine only after verified source resolution.
        state = self.state
        state.address, state.records = (chat_id, after_id, mode), records
        state.batch = None
        state.account_id = state.expected_account

    def offer(self, batch):
        if batch is None:
            return
        if not isinstance(batch, MessageBatch):
            raise PoolStateError('Read capture requires validated MessageBatch data')
        state = self.state
        if not batch.messages and (state.records or (state.batch is not None and state.batch.messages)):
            return
        state.batch = batch
        state.records = state.address = None

    def source_error(self, error):
        self.state.read_error_type = _error_name(error)

    def finish(self, error=None):
        state = self.state
        if error is None:
            # A completed source's offer is final only when the public call ends.
            if state.batch is None:
                state.batch = state.available()
            state.phase = 'succeeded'
        else:
            state.batch = state.available()
            state.error_type = _error_name(error)
            state.phase = 'cancelled' if isinstance(error, asyncio.CancelledError) else 'failed'
        state.records = state.address = state.expected_account = None
        self.state = None


@contextmanager
def _capture_call(capture):
    if type(capture) is not PoolReadCapture:
        raise PoolConfigurationError('capture must be a new PoolReadCapture')
    state = object.__getattribute__(capture, '_PoolReadCapture__state')
    if state.phase != 'unbound':
        raise PoolConfigurationError('PoolReadCapture is single-use; allocate one per call')
    state.phase = 'running'
    writer = _CaptureWriter(state)
    try:
        yield writer
    except BaseException as error:
        writer.finish(error)
        raise
    else:
        writer.finish()
