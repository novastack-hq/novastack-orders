"""Turn a basket into a price breakdown: subtotal, discounts, total and VAT.

Order of operations (see docs/architecture.md, "Pricing pipeline"):

1. Add up the basket, category by category.
2. Basket promotions, e.g. the meal deal.
3. The loyalty discount, once, on the promoted total.
4. The student discount, on what's left.
5. Round to pence and work out the VAT included.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from novastack_orders.domain.basket import Basket, calc
from novastack_orders.domain.customer import Customer
from novastack_orders.domain.menu import Category
from novastack_orders.domain.money import Money, total
from novastack_orders.domain.order import AppliedDiscount
from novastack_orders.errors import ValidationError
from novastack_orders.pricing.discounts.base import DiscountRule, PricingContext
from novastack_orders.pricing.discounts.loyalty import LoyaltyDiscount
from novastack_orders.pricing.discounts.meal_deal import MealDeal
from novastack_orders.pricing.discounts.student import StudentDiscount
from novastack_orders.pricing.rounding import round_pence
from novastack_orders.pricing.tax import STANDARD_RATE, vat_included

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PriceBreakdown:
    subtotal: Money
    discounts: tuple[AppliedDiscount, ...]
    total: Money
    vat: Money
    category_subtotals: dict[Category, Money]

    @property
    def discount_total(self) -> Money:
        return total([d.amount for d in self.discounts], self.subtotal.currency)

    def discount_codes(self) -> list[str]:
        return [d.code for d in self.discounts]


class PriceCalculator:
    """Prices baskets. Build one with :meth:`default` unless a test needs fakes."""

    def __init__(
        self,
        promotions: list[DiscountRule],
        loyalty: LoyaltyDiscount,
        student: StudentDiscount,
        vat_rate: Decimal = STANDARD_RATE,
    ) -> None:
        self._promotions = promotions
        self._loyalty = loyalty
        self._student = student
        self._vat_rate = vat_rate

    @classmethod
    def default(cls) -> PriceCalculator:
        return cls(
            promotions=[MealDeal()],
            loyalty=LoyaltyDiscount(),
            student=StudentDiscount(),
        )

    def calculate(
        self, basket: Basket, customer: Customer, at: datetime
    ) -> PriceBreakdown:
        if basket.is_empty():
            raise ValidationError("Cannot price an empty basket")

        ctx = PricingContext(basket=basket, customer=customer, at=at)
        applied: list[AppliedDiscount] = []
        running = Money.zero()
        category_subtotals: dict[Category, Money] = {}

        # Category subtotals and the loyalty discount in a single pass (ORD-301).
        for category, lines in basket.by_category().items():
            category_total = total([calc(line) for line in lines])
            category_subtotals[category] = category_total
            running = running + category_total
            if self._loyalty.applies(ctx):
                running = self._apply(self._loyalty, ctx, running, applied)

        for rule in self._promotions:
            if rule.applies(ctx):
                running = self._apply(rule, ctx, running, applied)

        if self._student.applies(ctx):
            running = self._apply(self._student, ctx, running, applied)

        final = round_pence(running)
        return PriceBreakdown(
            subtotal=basket.subtotal(),
            discounts=tuple(applied),
            total=final,
            vat=vat_included(final, self._vat_rate),
            category_subtotals=category_subtotals,
        )

    def _apply(
        self,
        rule: DiscountRule,
        ctx: PricingContext,
        running: Money,
        applied: list[AppliedDiscount],
    ) -> Money:
        """Take one rule's discount off ``running`` and record it for the receipt."""
        amount = rule.amount(ctx, running)
        if amount.is_negative():
            raise ValidationError(f"{rule.code} produced a negative discount")
        # Round each discount as it's applied, so the receipt always adds up.
        amount = round_pence(min(amount, running))  # never below zero
        applied.append(AppliedDiscount(rule.code, rule.description, amount))
        log.debug(
            "applied %s: -%s (running total %s -> %s)",
            rule.code,
            amount.amount,
            running.amount,
            (running - amount).amount,
        )
        return running - amount
