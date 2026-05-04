from decimal import Decimal

import pytest

from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.pricing.discounts.base import PricingContext
from novastack_orders.pricing.discounts.loyalty import LoyaltyDiscount
from tests.factories import WEDNESDAY_LUNCH, gbp, make_basket, make_customer


def ctx(tier: LoyaltyTier) -> PricingContext:
    return PricingContext(
        make_basket(("D01", 1)), make_customer(tier=tier), WEDNESDAY_LUNCH
    )


@pytest.mark.parametrize(
    ("tier", "rate"),
    [
        (LoyaltyTier.NONE, 0),
        (LoyaltyTier.BRONZE, 5),
        (LoyaltyTier.SILVER, 10),
        (LoyaltyTier.GOLD, 15),
    ],
)
def test_rate_for_each_tier(tier, rate):
    assert LoyaltyDiscount().rate_for(tier) == Decimal(rate)


def test_does_not_apply_without_a_card():
    assert not LoyaltyDiscount().applies(ctx(LoyaltyTier.NONE))


def test_applies_with_a_card():
    assert LoyaltyDiscount().applies(ctx(LoyaltyTier.BRONZE))


def test_amount_is_a_percentage_of_the_running_total():
    assert LoyaltyDiscount().amount(ctx(LoyaltyTier.SILVER), gbp("8.10")) == gbp("0.81")


def test_custom_rates():
    rule = LoyaltyDiscount({LoyaltyTier.GOLD: Decimal(50)})
    assert rule.amount(ctx(LoyaltyTier.GOLD), gbp("4.00")) == gbp("2.00")
