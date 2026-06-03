import pytest

from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.loyalty.tiers import points_to_next_tier, tier_for_points


@pytest.mark.parametrize(
    ("points", "tier"),
    [
        (0, LoyaltyTier.BRONZE),
        (499, LoyaltyTier.BRONZE),
        (500, LoyaltyTier.SILVER),
        (1999, LoyaltyTier.SILVER),
        (2000, LoyaltyTier.GOLD),
        (10_000, LoyaltyTier.GOLD),
    ],
)
def test_tier_thresholds(points, tier):
    assert tier_for_points(points) is tier


def test_negative_points_are_invalid():
    with pytest.raises(ValueError):
        tier_for_points(-1)


def test_points_to_next_tier_from_bronze():
    assert points_to_next_tier(120) == (LoyaltyTier.SILVER, 380)


def test_points_to_next_tier_from_silver():
    assert points_to_next_tier(1500) == (LoyaltyTier.GOLD, 500)


def test_gold_is_the_top():
    assert points_to_next_tier(2500) is None
