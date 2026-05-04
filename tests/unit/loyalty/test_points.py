import pytest

from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.loyalty.points import points_earned
from tests.factories import gbp


@pytest.mark.smoke
def test_one_point_per_whole_pound_for_bronze():
    assert points_earned(gbp("7.99"), LoyaltyTier.BRONZE) == 7


def test_no_card_no_points():
    assert points_earned(gbp("50.00"), LoyaltyTier.NONE) == 0


@pytest.mark.parametrize(
    ("paid", "tier", "expected"),
    [
        ("10.00", LoyaltyTier.SILVER, 15),
        ("11.00", LoyaltyTier.SILVER, 16),  # 16.5 -> 16
        ("10.00", LoyaltyTier.GOLD, 20),
        ("0.99", LoyaltyTier.GOLD, 0),
    ],
)
def test_tier_multipliers(paid, tier, expected):
    assert points_earned(gbp(paid), tier) == expected


def test_big_order_bonus_at_exactly_twenty_pounds():
    assert points_earned(gbp("20.00"), LoyaltyTier.BRONZE) == 70


def test_no_bonus_just_under_twenty_pounds():
    assert points_earned(gbp("19.99"), LoyaltyTier.BRONZE) == 19


def test_bonus_is_added_after_the_multiplier():
    assert points_earned(gbp("30.00"), LoyaltyTier.GOLD) == 110


def test_points_are_capped_per_order():
    assert points_earned(gbp("400.00"), LoyaltyTier.GOLD) == 500


def test_zero_or_negative_amounts_earn_nothing():
    assert points_earned(gbp("0"), LoyaltyTier.GOLD) == 0
    assert points_earned(gbp("-5.00"), LoyaltyTier.GOLD) == 0
