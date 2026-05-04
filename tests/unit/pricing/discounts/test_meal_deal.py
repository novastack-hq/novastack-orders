import pytest

from novastack_orders.pricing.discounts.base import PricingContext
from novastack_orders.pricing.discounts.meal_deal import MealDeal
from tests.factories import WEDNESDAY_LUNCH, gbp, make_basket, make_customer


def ctx(*lines) -> PricingContext:
    return PricingContext(make_basket(*lines), make_customer(), WEDNESDAY_LUNCH)


def test_needs_a_main_a_side_and_a_drink():
    assert not MealDeal().applies(ctx(("M01", 1), ("D01", 1)))
    assert MealDeal().applies(ctx(("M01", 1), ("S01", 1), ("D01", 1)))


def test_saving_for_one_deal():
    c = ctx(("M01", 1), ("S01", 1), ("D01", 1))  # 5.20 + 2.10 + 1.60 = 8.90
    assert MealDeal().amount(c, gbp("8.90")) == gbp("2.40")


def test_extra_drink_uses_the_most_expensive_one():
    c = ctx(("M01", 1), ("S01", 1), ("D01", 1), ("D02", 1))  # deal uses OJ at 1.80
    assert MealDeal().amount(c, gbp("10.70")) == gbp("2.60")


def test_number_of_deals_is_limited_by_the_scarcest_category():
    assert MealDeal().deals_in(ctx(("M01", 3), ("S01", 2), ("D01", 5))) == 2


def test_two_deals_pair_expensive_items_together():
    c = ctx(("M01", 1), ("M02", 1), ("S01", 1), ("S02", 1), ("D01", 1), ("D03", 1))
    # (5.20 + 2.10 + 1.60) - 6.50 = 2.40 and (4.90 + 1.90 + 1.20) - 6.50 = 1.50
    assert MealDeal().amount(c, gbp("16.90")) == gbp("3.90")


@pytest.mark.parametrize("deal_price", ["8.90", "9.50"])
def test_no_saving_when_the_deal_is_not_cheaper(deal_price):
    c = ctx(("M01", 1), ("S01", 1), ("D01", 1))
    assert MealDeal(gbp(deal_price)).amount(c, gbp("8.90")) == gbp("0")
