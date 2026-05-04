import pytest

from novastack_orders.domain.customer import Customer, LoyaltyTier
from novastack_orders.errors import ValidationError
from tests.factories import make_customer


def test_no_card_by_default():
    assert not make_customer().has_loyalty_card


def test_any_tier_counts_as_a_card():
    assert make_customer(tier=LoyaltyTier.BRONZE).has_loyalty_card


def test_with_points_returns_a_copy():
    original = make_customer(points=10)
    updated = original.with_points(25)
    assert (original.points, updated.points) == (10, 25)


def test_invalid_email_is_rejected():
    with pytest.raises(ValidationError, match="email"):
        Customer("C1", "Name", "not-an-email")


def test_negative_points_are_rejected():
    with pytest.raises(ValidationError):
        make_customer(points=-1)


def test_from_record_defaults():
    c = Customer.from_record(
        {"customer_id": "C9", "name": "N", "email": "n@example.com"}
    )
    assert (c.tier, c.is_student, c.points) == (LoyaltyTier.NONE, False, 0)
