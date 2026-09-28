from decimal import Decimal

import pytest

from novastack_orders.domain.basket import Basket
from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.domain.money import Money
from novastack_orders.errors import ValidationError
from novastack_orders.pricing.calculator import PriceCalculator
from novastack_orders.pricing.discounts.base import DiscountRule, PricingContext
from novastack_orders.pricing.discounts.loyalty import LoyaltyDiscount
from novastack_orders.pricing.discounts.student import StudentDiscount
from tests.factories import (
    SATURDAY_LUNCH,
    WEDNESDAY_LUNCH,
    gbp,
    make_basket,
    make_customer,
)


@pytest.mark.smoke
def test_no_discounts_total_is_subtotal(calculator):
    result = calculator.calculate(
        make_basket(("M01", 1), ("D01", 1)), make_customer(), WEDNESDAY_LUNCH
    )
    assert result.subtotal == gbp("6.80")
    assert result.total == gbp("6.80")
    assert result.discounts == ()


@pytest.mark.smoke
def test_meal_deal_price(calculator):
    basket = make_basket(("M01", 1), ("S01", 1), ("D01", 1))
    result = calculator.calculate(basket, make_customer(), WEDNESDAY_LUNCH)
    assert result.total == gbp("6.50")
    assert result.discount_codes() == ["MEALDEAL"]


def test_loyalty_discount_on_a_single_category(calculator):
    customer = make_customer(tier=LoyaltyTier.GOLD)
    result = calculator.calculate(make_basket(("D01", 2)), customer, WEDNESDAY_LUNCH)
    assert result.total == gbp("2.72")  # 3.20 less 15%


@pytest.mark.smoke
@pytest.mark.xfail(reason="ORD-317: remove when fixed", strict=True)
def test_loyalty_discount_applied_once(calculator):
    """ORD-317: a Silver customer orders a meal deal plus an extra drink.

    Subtotal £10.70; meal deal saves £2.60 -> £8.10; Silver loyalty is 10% of
    that, once -> £7.29.
    """
    customer = make_customer(tier=LoyaltyTier.SILVER)
    basket = make_basket(("M01", 1), ("S01", 1), ("D01", 1), ("D02", 1))
    result = calculator.calculate(basket, customer, WEDNESDAY_LUNCH)
    assert result.discount_codes().count("LOYALTY") == 1
    assert result.total == gbp("7.29")


def test_student_discount_midweek(calculator):
    customer = make_customer(is_student=True)
    result = calculator.calculate(
        make_basket(("M02", 1), ("D03", 1)), customer, WEDNESDAY_LUNCH
    )
    assert result.total == gbp("5.49")  # 6.10 less 10%


def test_no_student_discount_at_weekends(calculator):
    customer = make_customer(is_student=True)
    result = calculator.calculate(
        make_basket(("M02", 1), ("D03", 1)), customer, SATURDAY_LUNCH
    )
    assert result.total == gbp("6.10")


def test_loyalty_then_student_discount(calculator):
    customer = make_customer(tier=LoyaltyTier.BRONZE, is_student=True)
    result = calculator.calculate(make_basket(("M02", 1)), customer, WEDNESDAY_LUNCH)
    # 4.90 - 5% (0.245 -> 0.25) = 4.65; then - 10% (0.465 -> 0.47) = 4.18
    assert result.discount_codes() == ["LOYALTY", "STUDENT"]
    assert result.total == gbp("4.18")


def test_vat_is_a_sixth_of_a_vat_inclusive_total(calculator):
    result = calculator.calculate(
        make_basket(("D03", 5)), make_customer(), WEDNESDAY_LUNCH
    )
    assert result.total == gbp("6.00")
    assert result.vat == gbp("1.00")


def test_receipt_adds_up(calculator):
    customer = make_customer(tier=LoyaltyTier.GOLD, is_student=True)
    basket = make_basket(("M03", 2), ("S02", 1), ("D02", 3), ("P01", 1))
    result = calculator.calculate(basket, customer, WEDNESDAY_LUNCH)
    assert result.subtotal - result.discount_total == result.total


def test_empty_basket_cannot_be_priced(calculator):
    with pytest.raises(ValidationError, match="empty"):
        calculator.calculate(Basket(), make_customer(), WEDNESDAY_LUNCH)


class _HugeDiscount(DiscountRule):
    code = "HUGE"
    description = "More than the basket is worth"

    def applies(self, ctx: PricingContext) -> bool:
        return True

    def amount(self, ctx: PricingContext, running_total: Money) -> Money:
        return running_total * 10


def test_discounts_never_make_the_total_negative():
    calculator = PriceCalculator(
        [_HugeDiscount()], LoyaltyDiscount(), StudentDiscount()
    )
    result = calculator.calculate(
        make_basket(("D01", 1)), make_customer(), WEDNESDAY_LUNCH
    )
    assert result.total == gbp("0.00")


def test_custom_vat_rate():
    calculator = PriceCalculator(
        [], LoyaltyDiscount(), StudentDiscount(), vat_rate=Decimal(5)
    )
    result = calculator.calculate(
        make_basket(("D03", 7)), make_customer(), WEDNESDAY_LUNCH
    )
    assert result.vat == gbp("0.40")  # 8.40 x 5/105
