"""Meal deal: a main, a side and a drink for a fixed price."""

from __future__ import annotations

from novastack_orders.domain.menu import Category
from novastack_orders.domain.money import Money
from novastack_orders.pricing.discounts.base import DiscountRule, PricingContext

DEFAULT_DEAL_PRICE = Money.of("6.50")


def _unit_prices(ctx: PricingContext, category: Category) -> list[Money]:
    """One entry per unit in ``category``, most expensive first."""
    prices: list[Money] = []
    for line in ctx.basket:
        if line.category is category:
            prices.extend([line.item.price] * line.quantity)
    return sorted(prices, reverse=True)


class MealDeal(DiscountRule):
    code = "MEALDEAL"
    description = "Meal deal (main + side + drink)"

    def __init__(self, deal_price: Money = DEFAULT_DEAL_PRICE) -> None:
        self._deal_price = deal_price

    def deals_in(self, ctx: PricingContext) -> int:
        return min(
            len(_unit_prices(ctx, Category.MAIN)),
            len(_unit_prices(ctx, Category.SIDE)),
            len(_unit_prices(ctx, Category.DRINK)),
        )

    def applies(self, ctx: PricingContext) -> bool:
        return self.deals_in(ctx) > 0

    def amount(self, ctx: PricingContext, running_total: Money) -> Money:
        """Saving = full price of the items in each deal minus the deal price.

        The most expensive main, side and drink are grouped first, which gives
        the customer the biggest saving.
        """
        mains = _unit_prices(ctx, Category.MAIN)
        sides = _unit_prices(ctx, Category.SIDE)
        drinks = _unit_prices(ctx, Category.DRINK)
        saving = Money.zero(running_total.currency)
        for i in range(self.deals_in(ctx)):
            full_price = mains[i] + sides[i] + drinks[i]
            if self._deal_price < full_price:
                saving = saving + (full_price - self._deal_price)
        return saving
