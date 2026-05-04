"""How many loyalty points an order earns.

Rules (from the loyalty scheme terms, v2):

* Only loyalty card holders earn points.
* 1 point per whole pound actually paid (after discounts). Pence don't count.
* Tier multiplier: Bronze x1, Silver x1.5, Gold x2. Fractions of a point are dropped.
* Orders of £20.00 or more (after discounts) earn a 50-point bonus,
  added after the multiplier.
* No single order earns more than 500 points.
* Nothing paid (zero, or a negative correction) earns nothing.
"""

from __future__ import annotations

from decimal import ROUND_FLOOR, Decimal

from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.domain.money import Money

MULTIPLIERS: dict[LoyaltyTier, Decimal] = {
    LoyaltyTier.NONE: Decimal(0),
    LoyaltyTier.BRONZE: Decimal(1),
    LoyaltyTier.SILVER: Decimal("1.5"),
    LoyaltyTier.GOLD: Decimal(2),
}
BIG_ORDER_THRESHOLD = Money.of("20.00")
BIG_ORDER_BONUS = 50
MAX_POINTS_PER_ORDER = 500


def points_earned(amount_paid: Money, tier: LoyaltyTier) -> int:
    """Points earned for paying ``amount_paid`` as a member of ``tier``."""
    if tier is LoyaltyTier.NONE or amount_paid.amount <= 0:
        return 0
    whole_pounds = int(amount_paid.amount.to_integral_value(rounding=ROUND_FLOOR))
    points = int(
        (whole_pounds * MULTIPLIERS[tier]).to_integral_value(rounding=ROUND_FLOOR)
    )
    if amount_paid >= BIG_ORDER_THRESHOLD:
        points += BIG_ORDER_BONUS
    return min(points, MAX_POINTS_PER_ORDER)
