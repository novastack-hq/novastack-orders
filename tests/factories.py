"""Builders for test data, so each test only spells out what it cares about.

basket = make_basket(("M01", 1), ("D01", 2))
customer = make_customer(tier=LoyaltyTier.GOLD)
"""

from __future__ import annotations

from datetime import datetime

from novastack_orders.domain.basket import Basket
from novastack_orders.domain.customer import Customer, LoyaltyTier
from novastack_orders.domain.menu import Category, Menu, MenuItem
from novastack_orders.domain.money import Money

# A fixed week in October 2026, so day-of-week rules are predictable.
MONDAY_LUNCH = datetime(2026, 10, 5, 12, 30)
WEDNESDAY_LUNCH = datetime(2026, 10, 7, 12, 30)
FRIDAY_LUNCH = datetime(2026, 10, 9, 12, 30)
SATURDAY_LUNCH = datetime(2026, 10, 10, 12, 30)
SUNDAY_LUNCH = datetime(2026, 10, 11, 12, 30)

MENU = Menu(
    [
        MenuItem("M01", "Chicken wrap", Category.MAIN, Money.of("5.20")),
        MenuItem(
            "M02", "Falafel wrap", Category.MAIN, Money.of("4.90"), vegetarian=True
        ),
        MenuItem("M03", "Beef burger", Category.MAIN, Money.of("6.80")),
        MenuItem("S01", "Fries", Category.SIDE, Money.of("2.10"), vegetarian=True),
        MenuItem("S02", "Side salad", Category.SIDE, Money.of("1.90"), vegetarian=True),
        MenuItem("D01", "Cola", Category.DRINK, Money.of("1.60"), vegetarian=True),
        MenuItem(
            "D02", "Orange juice", Category.DRINK, Money.of("1.80"), vegetarian=True
        ),
        MenuItem(
            "D03", "Sparkling water", Category.DRINK, Money.of("1.20"), vegetarian=True
        ),
        MenuItem("P01", "Brownie", Category.DESSERT, Money.of("2.40"), vegetarian=True),
        MenuItem("N01", "Crisps", Category.SNACK, Money.of("0.95"), vegetarian=True),
    ]
)


def gbp(value: str) -> Money:
    return Money.of(value)


def make_basket(*lines: tuple[str, int]) -> Basket:
    basket = Basket()
    for sku, quantity in lines:
        basket.add(MENU.get(sku), quantity)
    return basket


def make_customer(
    customer_id: str = "C100",
    tier: LoyaltyTier = LoyaltyTier.NONE,
    is_student: bool = False,
    points: int = 0,
) -> Customer:
    return Customer(
        customer_id=customer_id,
        name="Test Customer",
        email=f"{customer_id.lower()}@example.com",
        tier=tier,
        is_student=is_student,
        points=points,
    )
