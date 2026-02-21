"""Date range helpers for dashboard-style filters.

Supports either:
- `days` (integer)
- `start_date` + `end_date` (YYYY-MM-DD)

Returns a (start_datetime, end_datetime_exclusive, days) tuple using naive UTC
`datetime` values (consistent with this codebase's `datetime.utcnow` defaults).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from flask import request


@dataclass(frozen=True)
class DateRange:
    start: datetime
    end_exclusive: datetime
    days: int


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except Exception as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD") from exc


def parse_request_date_range(*, default_days: int = 30, max_days: int = 366) -> DateRange:
    """Parse a date range from query params.

    Query params:
    - days: int
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD

    Behavior:
    - If start_date/end_date are present, uses an inclusive date range and
      returns end_exclusive as the next midnight.
    - Otherwise, uses `days` back from now.
    """

    start_date_str = (request.args.get("start_date") or "").strip()
    end_date_str = (request.args.get("end_date") or "").strip()

    if start_date_str or end_date_str:
        if not start_date_str or not end_date_str:
            raise ValueError("Both start_date and end_date are required for a custom range")

        start_day = _parse_iso_date(start_date_str)
        end_day = _parse_iso_date(end_date_str)

        if end_day < start_day:
            raise ValueError("end_date must be on or after start_date")

        start_dt = datetime.combine(start_day, time.min)
        end_exclusive = datetime.combine(end_day + timedelta(days=1), time.min)
        days = (end_exclusive - start_dt).days
    else:
        days = request.args.get("days", default_days, type=int)
        if not days:
            days = default_days

        if days < 1 or days > max_days:
            raise ValueError(f"days must be between 1 and {max_days}")

        end_exclusive = datetime.utcnow()
        start_dt = end_exclusive - timedelta(days=days)

    if days < 1:
        raise ValueError("Invalid date range")

    return DateRange(start=start_dt, end_exclusive=end_exclusive, days=days)
