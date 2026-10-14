"""Month-end sales reports for Finance (ORD-344).

Reads the till's order records for a month (JSON Lines, one order per line)
and summarises revenue, discounts, categories, best sellers and customers.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from novastack_orders.domain.menu import Category, Menu
from novastack_orders.domain.money import Money, total
from novastack_orders.utils.dates import parse_timestamp


@dataclass(frozen=True, slots=True)
class ReportLine:
    sku: str
    quantity: int
    line_total: Money


@dataclass(frozen=True, slots=True)
class OrderRecord:
    """One order as the till recorded it."""

    order_id: str
    customer_id: str
    placed_at: datetime
    lines: tuple[ReportLine, ...]
    discounts: tuple[tuple[str, Money], ...]
    total: Money


@dataclass
class MonthlyReport:
    month: str
    order_count: int = 0
    revenue: Money = field(default_factory=Money.zero)
    discounts_by_code: dict[str, Money] = field(default_factory=dict)
    revenue_by_category: dict[Category, Money] = field(default_factory=dict)
    items_sold: Counter[str] = field(default_factory=Counter)
    new_customers: int = 0
    returning_customers: int = 0
    top_customers: list[tuple[str, Money]] = field(default_factory=list)

    @property
    def average_order(self) -> Money:
        if not self.order_count:
            return Money.zero()
        return Money(self.revenue.amount / self.order_count).rounded()


def load_orders(path: Path) -> list[OrderRecord]:
    """Read a month of order records from a JSON Lines file."""
    orders = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line)
            orders.append(
                OrderRecord(
                    order_id=raw["id"],
                    customer_id=raw["customer"],
                    placed_at=parse_timestamp(raw["at"]),
                    lines=tuple(
                        ReportLine(sku, qty, Money.of(total))
                        for sku, qty, total in raw["lines"]
                    ),
                    discounts=tuple(
                        (code, Money.of(amount)) for code, amount in raw["discounts"]
                    ),
                    total=Money.of(raw["total"]),
                )
            )
    return orders


def load_categories(menu_path: Path) -> dict[str, Category]:
    """Every SKU's menu category, read from the menu file once."""
    menu = Menu.from_records(json.loads(menu_path.read_text(encoding="utf-8")))
    return {item.sku: item.category for item in menu}


def first_order_times(orders: list[OrderRecord]) -> dict[str, datetime]:
    """When each customer first ordered this month (ORD-355).

    The till exports orders in time order, so a customer's first order is
    simply the first one we see (ORD-363).
    """
    first: dict[str, datetime] = {}
    for order in orders:
        first.setdefault(order.customer_id, order.placed_at)
    return first


def customer_spend(customer_id: str, orders: list[OrderRecord]) -> Money:
    """Everything one customer spent in these orders."""
    return total([o.total for o in orders if o.customer_id == customer_id])


def top_customers(orders: list[OrderRecord], n: int = 5) -> list[tuple[str, Money]]:
    """The ``n`` customers who spent the most, biggest first (ORD-362)."""
    spend = {o.customer_id: customer_spend(o.customer_id, orders) for o in orders}
    ranked = sorted(spend.items(), key=lambda pair: (-pair[1].amount, pair[0]))
    return ranked[:n]  # ties: by customer ID


def build_report(
    month: str, orders: list[OrderRecord], menu_path: Path
) -> MonthlyReport:
    """Summarise a month of orders."""
    report = MonthlyReport(month=month)
    first_order = first_order_times(orders)
    categories = load_categories(menu_path)
    for order in orders:
        report.order_count += 1
        report.revenue = report.revenue + order.total
        for code, amount in order.discounts:
            report.discounts_by_code[code] = (
                report.discounts_by_code.get(code, Money.zero()) + amount
            )
        for line in order.lines:
            category = categories[line.sku]
            report.revenue_by_category[category] = (
                report.revenue_by_category.get(category, Money.zero()) + line.line_total
            )
            report.items_sold[line.sku] += line.quantity
        if order.placed_at > first_order[order.customer_id]:
            report.returning_customers += 1
        else:
            report.new_customers += 1
    report.top_customers = top_customers(orders)
    return report
