from novastack_orders.services.receipts import render_receipt
from tests.factories import make_basket


def test_receipt_lists_lines_discounts_and_total(checkout):
    order = checkout.checkout(
        "C100", make_basket(("M01", 1), ("S01", 1), ("D01", 1)), "tok_visa"
    )
    receipt = render_receipt(order)
    assert "1 x Chicken wrap" in receipt
    assert "-£2.40" in receipt
    assert "TOTAL" in receipt and "£6.50" in receipt


def test_receipt_shows_vat_and_points(checkout):
    order = checkout.checkout("C200", make_basket(("D03", 5)), "tok_visa")
    receipt = render_receipt(order)
    assert "of which VAT" in receipt
    assert f"Points earned: {order.points_earned}" in receipt
