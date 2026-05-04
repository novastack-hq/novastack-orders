"""Rounding money to pence, and splitting amounts across lines fairly."""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from novastack_orders.domain.money import PENNY, Money


def round_pence(amount: Money) -> Money:
    """Round to the nearest penny, halves away from zero."""
    return Money(amount.amount.quantize(PENNY, rounding=ROUND_HALF_UP), amount.currency)


def allocate(amount: Money, weights: list[Money]) -> list[Money]:
    """Split ``amount`` across lines in proportion to ``weights``.

    Each share is whole pence and the shares always add up to exactly
    ``amount`` (largest-remainder method), so a receipt's per-line discounts
    sum to the discount at the bottom.
    """
    if not weights:
        return []
    weight_total = sum((w.amount for w in weights), Decimal(0))
    target = round_pence(amount).amount
    if weight_total == 0:
        shares = [Decimal(0)] * len(weights)
        shares[0] = target
        return [Money(s, amount.currency) for s in shares]

    exact = [target * w.amount / weight_total for w in weights]
    floored = [e.quantize(PENNY, rounding=ROUND_DOWN) for e in exact]
    leftover_pence = int((target - sum(floored, Decimal(0))) / PENNY)

    # Give the leftover pennies to the lines that lost most to rounding down.
    by_remainder = sorted(
        range(len(weights)), key=lambda i: exact[i] - floored[i], reverse=True
    )
    for i in range(leftover_pence):
        floored[by_remainder[i]] += PENNY
    return [Money(share, amount.currency) for share in floored]
