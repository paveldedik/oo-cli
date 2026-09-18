"""Time arguments. OpenObserve takes epoch microseconds everywhere."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_OFFSET = re.compile(r"^([+-])(\d+)([smhdw])$")
_UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days", "w": "weeks"}


class TimeError(ValueError):
    pass


def to_micros(value: str, now: datetime | None = None) -> int:
    """Parse "now", an offset like -15m, epoch seconds/millis/micros, or ISO 8601.

    A timestamp without a zone is read as local time.
    """
    now = now or datetime.now(timezone.utc)
    value = value.strip()

    if value == "now":
        return int(now.timestamp() * 1_000_000)

    offset = _OFFSET.match(value)
    if offset:
        sign, amount, unit = offset.groups()
        delta = timedelta(**{_UNITS[unit]: int(amount)})
        moment = now - delta if sign == "-" else now + delta
        return int(moment.timestamp() * 1_000_000)

    if value.isdigit():
        digits = len(value)
        if digits <= 11:
            return int(value) * 1_000_000
        if digits <= 14:
            return int(value) * 1_000
        return int(value)

    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise TimeError(
            f"cannot read {value!r} as a time: use now, an offset (-15m, -2h, -7d), "
            "an epoch timestamp or an ISO 8601 datetime"
        ) from exc
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return int(moment.timestamp() * 1_000_000)
