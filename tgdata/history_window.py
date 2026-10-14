"""The shared, half-open UTC constraint for historical batch reads."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .message_batch import BatchFormatError


_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_LAST_WIRE_DATE = _EPOCH + timedelta(seconds=(1 << 31) - 1)


def _utc(value, name, *, allow_naive=False):
    try:
        if not isinstance(value, datetime):
            raise ValueError
        if value.tzinfo is None or value.utcoffset() is None:
            if not allow_naive:
                raise ValueError
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        raise BatchFormatError('{} must be a {}datetime'.format(
            name, '' if allow_naive else 'timezone-aware ')) from None


def _encode_date(value):
    return value.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _decode_date(value):
    try:
        if type(value) is not str or not value.endswith('Z'):
            raise ValueError
        parsed = datetime.fromisoformat(value[:-1] + '+00:00')
        if _encode_date(parsed) != value:
            raise ValueError
        return parsed
    except (TypeError, ValueError, OverflowError):
        raise BatchFormatError('saved window dates must be canonical UTC timestamps') from None


@dataclass(frozen=True)
class _HistoryWindow:
    start_date: datetime
    end_date: datetime

    def __post_init__(self):
        start = _utc(self.start_date, 'start_date')
        end = _utc(self.end_date, 'end_date')
        if not _EPOCH <= start < end <= _LAST_WIRE_DATE:
            raise BatchFormatError(
                'window requires 1970-01-01 UTC <= start_date < end_date '
                '<= 2038-01-19 03:14:07 UTC')
        object.__setattr__(self, 'start_date', start)
        object.__setattr__(self, 'end_date', end)

    @classmethod
    def from_dates(cls, start_date, end_date):
        if start_date is None and end_date is None:
            return None
        return cls(start_date, end_date)

    @property
    def seek_date(self):
        # The SDK's date offset is exclusive and its wire date has whole-second
        # precision. Seek early, then use the exact predicate on returned dates.
        if self.start_date < _EPOCH + timedelta(seconds=2):
            return None
        return self.start_date.replace(microsecond=0) - timedelta(seconds=1)

    def contains(self, date):
        return self.start_date <= date < self.end_date

    def to_dict(self):
        return {'start_date': _encode_date(self.start_date),
                'end_date': _encode_date(self.end_date)}
