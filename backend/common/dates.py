"""
IST-anchored date helpers. Timestamps are stored in UTC, but the business "today"
(for membership status, expiry, reports) is Indian Standard Time, matching the
source app's UTC-store / IST-display convention.
"""
from datetime import UTC, date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()


def ist_day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    """UTC [start, end) datetimes spanning the IST calendar day ``day``.

    Use to filter UTC-stored ``created_at`` by an IST business day.
    """
    start_ist = datetime(day.year, day.month, day.day, tzinfo=IST)
    end_ist = start_ist + timedelta(days=1)
    return start_ist.astimezone(UTC), end_ist.astimezone(UTC)
