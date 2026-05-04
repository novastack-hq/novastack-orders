"""Date and time rules: trading hours and which days offers apply."""

from __future__ import annotations

from datetime import date, datetime, time

MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)

# Student discount runs Monday to Friday inclusive (term-time trading days).
STUDENT_DISCOUNT_LAST_DAY = FRIDAY


def is_weekend(day: date) -> bool:
    return day.weekday() >= SATURDAY


def is_student_discount_day(day: date) -> bool:
    """True if the student discount applies on ``day`` (Monday to Friday)."""
    return day.weekday() <= STUDENT_DISCOUNT_LAST_DAY


def store_is_open(at: datetime, opening: time, closing: time) -> bool:
    """True if ``at`` falls within trading hours (closing time is exclusive)."""
    return opening <= at.time() < closing


def parse_timestamp(text: str) -> datetime:
    """Parse an ISO 8601 timestamp such as ``2026-10-09T12:30:00``."""
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Not an ISO 8601 timestamp: {text!r}") from exc
