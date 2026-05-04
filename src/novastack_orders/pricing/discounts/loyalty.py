"""Loyalty card discount: a percentage off, depending on the customer's tier."""

from __future__ import annotations

from decimal import Decimal

from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.domain.money import Money
from novastack_orders.pricing.discounts.base import DiscountRule, PricingContext

TIER_RATES: dict[LoyaltyTier, Decimal] = {
    LoyaltyTier.NONE: Decimal(0),
    LoyaltyTier.BRONZE: Decimal(5),
    LoyaltyTier.SILVER: Decimal(10),
    LoyaltyTier.GOLD: Decimal(15),
}


class LoyaltyDiscount(DiscountRule):
    code = "LOYALTY"
    description = "Loyalty card discount"

    def __init__(self, rates: dict[LoyaltyTier, Decimal] | None = None) -> None:
        self._rates = rates or TIER_RATES

    def rate_for(self, tier: LoyaltyTier) -> Decimal:
        return self._rates.get(tier, Decimal(0))

    def applies(self, ctx: PricingContext) -> bool:
        return ctx.customer.has_loyalty_card and self.rate_for(ctx.customer.tier) > 0

    def amount(self, ctx: PricingContext, running_total: Money) -> Money:
        return running_total.percent(self.rate_for(ctx.customer.tier))
