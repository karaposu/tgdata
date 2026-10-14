"""Bounded passive account-pool health observations; no application execution."""

import asyncio
import json
from .health import HealthMonitor

MAX_EVENTS = 128
MAX_EVENT_BYTES = 4096
MAX_TOTAL_BYTES = 65536
MAX_DROPPED = (1 << 63) - 1
_EVENT_KEYS = frozenset('kind time account verdict scope group call request wait_seconds error source'.split())
_ACCOUNT_KEYS = frozenset('label session user_id'.split())


class ObservationBuffer:
    def __init__(self):
        self.events, self.byte_count, self.dropped = [], 0, 0

    def lose(self):
        self.dropped = min(self.dropped + 1, MAX_DROPPED)

    @staticmethod
    def scalar(value):
        if value is None:
            return value
        if type(value) is str and len(value) <= MAX_EVENT_BYTES:
            return value
        if type(value) is int and -(1 << 63) <= value < (1 << 63):
            return value
        raise ValueError('not a bounded plain health scalar')

    @staticmethod
    def keys(value, expected):
        return (type(value) is dict and len(value) == len(expected)
                and all(type(key) is str for key in value) and value.keys() == expected)

    def own(self, event):
        if not self.keys(event, _EVENT_KEYS) or not self.keys(event['account'], _ACCOUNT_KEYS):
            raise ValueError('not a health event shape')
        result = {key: self.scalar(event[key]) for key in _EVENT_KEYS if key != 'account'}
        result['account'] = {key: self.scalar(event['account'][key]) for key in _ACCOUNT_KEYS}
        if result['kind'] != 'health':
            raise ValueError('not health')
        payload = json.dumps(result, ensure_ascii=True, allow_nan=False,
                             sort_keys=True, separators=(',', ':')).encode('ascii')
        return result, len(payload)

    def capture(self, event):
        try:
            if len(self.events) >= MAX_EVENTS:
                self.lose()
                return
            owned, size = self.own(event)
            if size > MAX_EVENT_BYTES or self.byte_count + size > MAX_TOTAL_BYTES:
                self.lose()
                return
            self.events.append(owned)
            self.byte_count += size
        except (Exception, asyncio.CancelledError):
            self.lose()

    def drain(self):
        events, dropped = self.events, self.dropped
        self.events, self.byte_count, self.dropped = [], 0, 0
        return {'events': events, 'dropped': dropped}


class PoolMonitor(HealthMonitor):
    def __init__(self, buffer, label, identity):
        super().__init__(None, label, identity)
        self.buffer = buffer

    async def _deliver(self, event):
        self.buffer.capture(event)

    def _deliver_now(self, event):
        self.buffer.capture(event)

    def _health_failed(self):
        self.buffer.lose()


