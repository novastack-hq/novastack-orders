"""Tier thresholds: how many lifetime points each tier needs."""

from __future__ import annotations

from novastack_orders.domain.customer import LoyaltyTier

# Lifetime points needed for each tier. Joining the scheme gives Bronze.
TIER_THRESHOLDS: list[tuple[LoyaltyTier, int]] = [
    (LoyaltyTier.GOLD, 2000),
    (LoyaltyTier.SILVER, 500),
    (LoyaltyTier.BRONZE, 0),
]


def tier_for_points(points: int) -> LoyaltyTier:
    """The tier a card holder with ``points`` lifetime points belongs in."""
    if points < 0:
        raise ValueError("points cannot be negative")
    for tier, threshold in TIER_THRESHOLDS:
        if points >= threshold:
            return tier
    return LoyaltyTier.BRONZE  # unreachable while BRONZE's threshold is 0


def points_to_next_tier(points: int) -> tuple[LoyaltyTier, int] | None:
    """The next tier up and how many more points it needs, or None at the top."""
    current = tier_for_points(points)
    higher = [(t, th) for t, th in reversed(TIER_THRESHOLDS) if th > points]
    if not higher or current is LoyaltyTier.GOLD:
        return None
    tier, threshold = higher[0]
    return tier, threshold - points
