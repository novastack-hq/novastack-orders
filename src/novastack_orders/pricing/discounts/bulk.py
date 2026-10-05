"""Bulk discount for office orders (ORD-330).

Spec (from the ticket):

* 10% off any basket line with 10 or more of the same item;
* 15% off a line with 20 or more;
* a promotion: applied alongside the meal deal, before loyalty and student
  discounts; shown on receipts as "Bulk discount" with code ``BULK``.
"""

from __future__ import annotations

from decimal import Decimal

from novastack_orders.domain.basket import Basket
from novastack_orders.domain.money import Money
from novastack_orders.pricing.discounts.base import DiscountRule, PricingContext

# (minimum quantity on one line, percentage off), biggest first.
BULK_TIERS: list[tuple[int, Decimal]] = [(20, Decimal(15)), (10, Decimal(10))]


def bulk_discount(basket: Basket) -> Money:
    """The total bulk discount for ``basket`` (not yet rounded to pence)."""
    raise NotImplementedError("ORD-330: implement the bulk discount")


class BulkDiscount(DiscountRule):
    code = "BULK"
    description = "Bulk discount"

    def applies(self, ctx: PricingContext) -> bool:
        return bulk_discount(ctx.basket) > Money.zero()

    def amount(self, ctx: PricingContext, running_total: Money) -> Money:
        return bulk_discount(ctx.basket)
