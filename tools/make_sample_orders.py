"""Generate a month of realistic order records for the sales report.

    uv run tools/make_sample_orders.py 2026-09 16000 > data/orders/2026-09.jsonl

Deterministic: the same arguments always give the same file.
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta

from novastack_orders.cli import load_menu
from novastack_orders.config import load_settings
from novastack_orders.domain.basket import Basket
from novastack_orders.domain.customer import Customer, LoyaltyTier
from novastack_orders.pricing.calculator import PriceCalculator

TIERS = (
    [LoyaltyTier.NONE] * 5
    + [LoyaltyTier.BRONZE] * 3
    + [LoyaltyTier.SILVER] * 2
    + [LoyaltyTier.GOLD]
)


def main() -> None:
    month, count = sys.argv[1], int(sys.argv[2])
    rng = random.Random(f"{month}-{count}")
    menu = list(load_menu(load_settings(env="")))
    by_category: dict[str, list] = {}
    for item in menu:
        by_category.setdefault(item.category.value, []).append(item)
    customers = [
        Customer(
            f"C{n:04d}",
            "Customer",
            f"c{n}@example.com",
            rng.choice(TIERS),
            rng.random() < 0.3,
        )
        for n in range(1000, 1000 + count // 6)
    ]
    calculator = PriceCalculator.default()
    start = datetime.fromisoformat(f"{month}-01T08:00")
    records = []
    for _ in range(count):
        at = start + timedelta(days=rng.randrange(30), minutes=rng.randrange(14 * 60))
        basket = Basket()
        if rng.random() < 0.5:  # a meal deal
            for category in ("main", "side", "drink"):
                basket.add(rng.choice(by_category[category]))
        for _ in range(rng.choice([0, 0, 1, 1, 2])):
            basket.add(rng.choice(menu), rng.choice([1, 1, 1, 2]))
        if basket.is_empty():
            basket.add(rng.choice(menu))
        customer = rng.choice(customers)
        breakdown = calculator.calculate(basket, customer, at)
        record = {
            "customer": customer.customer_id,
            "at": at.isoformat(timespec="minutes"),
            "lines": [
                [
                    line.item.sku,
                    line.quantity,
                    str((line.item.price * line.quantity).amount),
                ]
                for line in basket
            ],
            "discounts": [[d.code, str(d.amount.amount)] for d in breakdown.discounts],
            "total": str(breakdown.total.amount),
        }
        records.append(record)
    records.sort(key=lambda r: r["at"])  # the till exports orders in time order
    for n, record in enumerate(records, start=1):
        print(json.dumps({"id": f"ORD-{n:06d}", **record}, separators=(",", ":")))


if __name__ == "__main__":
    main()
