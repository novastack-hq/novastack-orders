"""Plain-text receipts."""

from __future__ import annotations

from novastack_orders.domain.basket import calc
from novastack_orders.domain.order import Order
from novastack_orders.utils.formatting import format_price, format_table


def render_receipt(order: Order) -> str:
    """The receipt printed at the till and attached to the confirmation email."""
    rows: list[list[str]] = []
    for line in order.lines:
        rows.append([f"{line.quantity} x {line.item.name}", format_price(calc(line))])
    rows.append(["Subtotal", format_price(order.subtotal)])
    for discount in order.discounts:
        rows.append([discount.description, format_price(-discount.amount)])
    rows.append(["TOTAL", format_price(order.total)])
    rows.append(["  of which VAT", format_price(order.vat)])

    header = [
        "NovaStack Kitchen",
        f"Order {order.order_id}   {order.placed_at:%d/%m/%Y %H:%M}",
        "-" * 36,
    ]
    footer = ["-" * 36, f"Points earned: {order.points_earned}", "Thank you!"]
    return "\n".join([*header, format_table(rows), *footer])
