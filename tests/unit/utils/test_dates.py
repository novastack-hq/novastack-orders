from datetime import date, datetime, time

import pytest

from novastack_orders.utils.dates import (
    is_student_discount_day,
    is_weekend,
    parse_timestamp,
    store_is_open,
)


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 10, 5), True),  # Monday
        (date(2026, 10, 8), True),  # Thursday
        (date(2026, 10, 9), True),  # Friday
        (date(2026, 10, 10), False),  # Saturday
        (date(2026, 10, 11), False),  # Sunday
    ],
)
def test_student_discount_days(day, expected):
    assert is_student_discount_day(day) is expected


def test_weekend():
    assert is_weekend(date(2026, 10, 10))
    assert not is_weekend(date(2026, 10, 9))


@pytest.mark.parametrize(
    ("clock", "expected"),
    [("07:59", False), ("08:00", True), ("21:59", True), ("22:00", False)],
)
def test_trading_hours(clock, expected):
    at = datetime.combine(date(2026, 10, 7), time.fromisoformat(clock))
    assert store_is_open(at, time(8, 0), time(22, 0)) is expected


def test_parse_timestamp():
    assert parse_timestamp("2026-10-09T12:30") == datetime(2026, 10, 9, 12, 30)


def test_parse_timestamp_rejects_nonsense():
    with pytest.raises(ValueError, match="ISO 8601"):
        parse_timestamp("next Tuesday")
