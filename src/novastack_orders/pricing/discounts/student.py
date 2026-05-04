"""Student discount: 10% off for verified students on student-discount days."""

from __future__ import annotations

from decimal import Decimal

from novastack_orders.domain.money import Money
from novastack_orders.pricing.discounts.base import DiscountRule, PricingContext
from novastack_orders.utils.dates import is_student_discount_day

STUDENT_RATE = Decimal(10)


class StudentDiscount(DiscountRule):
    code = "STUDENT"
    description = "Student discount (Mon-Fri)"

    def __init__(self, rate: Decimal = STUDENT_RATE) -> None:
        self._rate = rate

    def applies(self, ctx: PricingContext) -> bool:
        return ctx.customer.is_student and is_student_discount_day(ctx.at.date())

    def amount(self, ctx: PricingContext, running_total: Money) -> Money:
        return running_total.percent(self._rate)
