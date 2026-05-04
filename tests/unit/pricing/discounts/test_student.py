import pytest

from novastack_orders.pricing.discounts.base import PricingContext
from novastack_orders.pricing.discounts.student import StudentDiscount
from tests.factories import (
    FRIDAY_LUNCH,
    MONDAY_LUNCH,
    SATURDAY_LUNCH,
    SUNDAY_LUNCH,
    WEDNESDAY_LUNCH,
    gbp,
    make_basket,
    make_customer,
)


def ctx(at, is_student=True) -> PricingContext:
    return PricingContext(
        make_basket(("D01", 1)), make_customer(is_student=is_student), at
    )


@pytest.mark.parametrize("day", [MONDAY_LUNCH, WEDNESDAY_LUNCH])
def test_applies_on_weekdays(day):
    assert StudentDiscount().applies(ctx(day))


@pytest.mark.smoke
def test_student_discount_on_friday():
    """Friday is a student-discount day (Monday to Friday inclusive)."""
    assert StudentDiscount().applies(ctx(FRIDAY_LUNCH))


@pytest.mark.parametrize("day", [SATURDAY_LUNCH, SUNDAY_LUNCH])
def test_not_at_weekends(day):
    assert not StudentDiscount().applies(ctx(day))


def test_not_for_non_students():
    assert not StudentDiscount().applies(ctx(WEDNESDAY_LUNCH, is_student=False))


def test_amount_is_ten_percent():
    assert StudentDiscount().amount(ctx(WEDNESDAY_LUNCH), gbp("6.10")) == gbp("0.61")
