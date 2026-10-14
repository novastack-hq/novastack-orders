"""Command-line interface: ``uv run novastack --help``.

Examples::

    uv run novastack menu --category drink
    uv run novastack quote data/samples/meal_deal_plus_drink.json --customer C002
    uv run novastack checkout data/samples/meal_deal_plus_drink.json --customer C002
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from novastack_orders.adapters.notifications.email_stub import StubEmailSender
from novastack_orders.adapters.payments.fake_gateway import FakePaymentGateway
from novastack_orders.adapters.repositories.memory_repo import (
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
)
from novastack_orders.config import Settings, load_settings
from novastack_orders.domain.basket import Basket
from novastack_orders.domain.customer import Customer, LoyaltyTier
from novastack_orders.domain.menu import Category, Menu
from novastack_orders.domain.money import Money
from novastack_orders.errors import NovastackError
from novastack_orders.logging_config import setup_logging
from novastack_orders.loyalty.points import points_earned
from novastack_orders.pricing.calculator import PriceCalculator
from novastack_orders.pricing.discounts.loyalty import LoyaltyDiscount
from novastack_orders.pricing.discounts.meal_deal import MealDeal
from novastack_orders.pricing.discounts.student import StudentDiscount
from novastack_orders.services.checkout_service import CheckoutService
from novastack_orders.services.notification_service import NotificationService
from novastack_orders.services.receipts import render_receipt
from novastack_orders.services.reporting import build_report, load_orders
from novastack_orders.utils.dates import parse_timestamp
from novastack_orders.utils.formatting import format_price, format_table

log = logging.getLogger(__name__)


def load_menu(settings: Settings) -> Menu:
    return Menu.from_records(json.loads(settings.menu_path.read_text(encoding="utf-8")))


def load_customers(settings: Settings) -> list[Customer]:
    records = json.loads(settings.customers_path.read_text(encoding="utf-8"))
    return [Customer.from_record(r) for r in records]


def load_basket(path: Path, menu: Menu) -> tuple[Basket, str | None]:
    """Read a basket JSON file (see ``data/samples/``) and its default customer."""
    data = json.loads(path.read_text(encoding="utf-8"))
    basket = Basket()
    for entry in data["items"]:
        basket.add(menu.get(entry["sku"]), int(entry.get("quantity", 1)))
    return basket, data.get("customer_id")


def build_calculator(settings: Settings) -> PriceCalculator:
    return PriceCalculator(
        promotions=[MealDeal(settings.meal_deal_price)],
        loyalty=LoyaltyDiscount(),
        student=StudentDiscount(settings.student_rate),
        vat_rate=settings.vat_rate,
    )


# ------------------------------------------------------------------ commands
def cmd_menu(args: argparse.Namespace, settings: Settings) -> int:
    menu = load_menu(settings)
    items = list(menu)
    if args.category:
        items = menu.in_category(Category(args.category))
    if args.vegetarian:
        items = [i for i in items if i.vegetarian]
    rows = [[i.sku, i.name, i.category.value, format_price(i.price)] for i in items]
    print(format_table(rows))
    return 0


def cmd_quote(args: argparse.Namespace, settings: Settings) -> int:
    menu = load_menu(settings)
    basket, file_customer = load_basket(Path(args.basket), menu)
    customers = {c.customer_id: c for c in load_customers(settings)}
    customer = customers[args.customer or file_customer or "C001"]
    at = parse_timestamp(args.at) if args.at else datetime.now()
    breakdown = build_calculator(settings).calculate(basket, customer, at)
    log.debug(
        "quote for %s at %s: total %s", customer.customer_id, at, breakdown.total.amount
    )

    rows = [["Subtotal", format_price(breakdown.subtotal)]]
    rows += [[d.description, format_price(-d.amount)] for d in breakdown.discounts]
    rows += [["TOTAL", format_price(breakdown.total)]]
    print(f"Quote for {customer.name} ({customer.tier.value}) at {at:%a %d %b %H:%M}")
    print(format_table(rows))
    return 0


def cmd_checkout(args: argparse.Namespace, settings: Settings) -> int:
    menu = load_menu(settings)
    basket, file_customer = load_basket(Path(args.basket), menu)
    at = parse_timestamp(args.at) if args.at else datetime.now()
    service = CheckoutService(
        calculator=build_calculator(settings),
        orders=InMemoryOrderRepository(),
        customers=InMemoryCustomerRepository(load_customers(settings)),
        payments=FakePaymentGateway(),
        notifications=NotificationService(StubEmailSender()),
        clock=lambda: at,
        opening=settings.opening,
        closing=settings.closing,
    )
    order = service.checkout(
        args.customer or file_customer or "C001", basket, args.card
    )
    print(render_receipt(order))
    return 0


def cmd_customers(args: argparse.Namespace, settings: Settings) -> int:
    rows = [
        [
            c.customer_id,
            c.name,
            c.tier.value,
            "student" if c.is_student else "",
            str(c.points),
        ]
        for c in load_customers(settings)
    ]
    print(format_table(rows))
    return 0


def cmd_report(args: argparse.Namespace, settings: Settings) -> int:
    path = Path(args.orders)
    report = build_report(path.stem, load_orders(path), settings.menu_path)
    print(f"Month-end sales report: {report.month}")
    print(
        format_table(
            [
                ["Orders", str(report.order_count)],
                ["Revenue", format_price(report.revenue)],
                ["Average order", format_price(report.average_order)],
                ["Customers", str(report.new_customers)],
                ["Repeat orders", str(report.returning_customers)],
            ]
        )
    )
    print("\nDiscounts given")
    print(
        format_table(
            [[c, format_price(a)] for c, a in sorted(report.discounts_by_code.items())]
        )
    )
    print("\nRevenue by category")
    print(
        format_table(
            [
                [c.value, format_price(a)]
                for c, a in sorted(report.revenue_by_category.items())
            ]
        )
    )
    print("\nBest sellers")
    print(format_table([[sku, str(n)] for sku, n in report.items_sold.most_common(5)]))
    print("\nTop customers")
    print(format_table([[c, format_price(s)] for c, s in report.top_customers]))
    return 0


def cmd_points(args: argparse.Namespace, settings: Settings) -> int:
    print(points_earned(Money.of(args.amount), LoyaltyTier(args.tier)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novastack", description="NovaStack Orders CLI"
    )
    parser.add_argument("--env", help="config overlay to load, e.g. 'test'")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("menu", help="list the menu")
    p.add_argument("--category", choices=[c.value for c in Category])
    p.add_argument("--vegetarian", action="store_true")
    p.set_defaults(func=cmd_menu)

    for name, func, helptext in [
        ("quote", cmd_quote, "price a basket without paying"),
        ("checkout", cmd_checkout, "price, pay for and record a basket"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.add_argument("basket", help="basket JSON file, e.g. data/samples/simple.json")
        p.add_argument("--customer", help="customer ID (default: the one in the file)")
        p.add_argument("--at", help="pretend it's this time, e.g. 2026-10-09T12:30")
        if name == "checkout":
            p.add_argument("--card", default="tok_visa", help="fake card token")
        p.set_defaults(func=func)

    p = sub.add_parser("customers", help="list customers")
    p.set_defaults(func=cmd_customers)

    p = sub.add_parser("report", help="month-end sales report from order records")
    p.add_argument(
        "orders", help="order records (JSON Lines), e.g. data/orders/2026-09.jsonl"
    )
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("points", help="points earned for an amount and tier")
    p.add_argument("amount")
    p.add_argument("--tier", default="bronze", choices=[t.value for t in LoyaltyTier])
    p.set_defaults(func=cmd_points)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.env)
    setup_logging(settings.log_level)
    try:
        return int(args.func(args, settings))
    except NovastackError as exc:
        print(f"error: {exc}")
        return 1
