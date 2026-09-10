"""Date helpers for SLA tracking."""

from datetime import datetime, timedelta, timezone


def parse_iso(value: str) -> datetime:
    """Parses an ISO-8601 timestamp from the API or the database."""
    return datetime.fromisoformat(value)


def hours_elapsed(raised_at: str) -> float:
    """Hours since a ticket was raised, for SLA breach checks."""
    return (datetime.now(timezone.utc) - parse_iso(raised_at)).total_seconds() / 3600


def add_business_days(start: str, days: int) -> datetime:
    """Adds working days to a date, skipping weekends."""
    current = parse_iso(start)
    while days > 0:
        current = current + timedelta(days=1)
        if current.weekday() < 5:
            days -= 1
    return current
