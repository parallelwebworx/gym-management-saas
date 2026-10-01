"""
IST-anchored date helpers. Timestamps are stored in UTC, but the business "today"
(for membership status, expiry, reports) is Indian Standard Time, matching the
source app's UTC-store / IST-display convention.
"""
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()
