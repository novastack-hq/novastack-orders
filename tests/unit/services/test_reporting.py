from pathlib import Path

import pytest

from novastack_orders.config import load_settings
from novastack_orders.domain.menu import Category
from novastack_orders.services.reporting import build_report, load_orders
from tests.factories import gbp

ORDERS = Path(__file__).parents[2] / "fixtures" / "orders_small.jsonl"


@pytest.fixture
def report():
    return build_report(
        "2026-09", load_orders(ORDERS), load_settings(env="test").menu_path
    )


def test_load_orders_skips_blank_lines():
    orders = load_orders(ORDERS)
    assert [o.order_id for o in orders] == [f"ORD-00000{n}" for n in range(1, 6)]


@pytest.mark.smoke
def test_revenue_and_order_count(report):
    assert report.order_count == 5
    assert report.revenue == gbp("20.46")
    assert report.average_order == gbp("4.09")


def test_discounts_are_totalled_by_code(report):
    assert report.discounts_by_code == {
        "MEALDEAL": gbp("2.40"),
        "LOYALTY": gbp("0.88"),
        "STUDENT": gbp("0.41"),
    }


def test_revenue_by_category_uses_line_totals_before_discounts(report):
    assert report.revenue_by_category[Category.MAIN] == gbp("10.40")
    assert report.revenue_by_category[Category.DRINK] == gbp("6.40")
    assert report.revenue_by_category[Category.SNACK] == gbp("2.85")


def test_best_sellers_count_quantities(report):
    assert report.items_sold.most_common(1) == [("N01", 3)]


def test_empty_month():
    empty = build_report("2026-10", [], load_settings(env="test").menu_path)
    assert empty.order_count == 0
    assert empty.average_order == gbp("0")
