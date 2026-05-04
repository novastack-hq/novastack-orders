"""Convert domain objects to and from plain dicts (for JSON storage)."""

from __future__ import annotations

from typing import Any

from novastack_orders.domain.basket import BasketLine
from novastack_orders.domain.menu import Category, MenuItem
from novastack_orders.domain.money import Money
from novastack_orders.domain.order import AppliedDiscount, Order, OrderStatus
from novastack_orders.utils.dates import parse_timestamp


def money_to_dict(m: Money) -> dict[str, str]:
    return {"amount": str(m.amount), "currency": m.currency}


def money_from_dict(d: dict[str, str]) -> Money:
    return Money.of(d["amount"], d["currency"])


def order_to_dict(order: Order) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "lines": [
            {
                "sku": line.item.sku,
                "name": line.item.name,
                "category": line.item.category.value,
                "price": money_to_dict(line.item.price),
                "vegetarian": line.item.vegetarian,
                "allergens": sorted(line.item.allergens),
                "quantity": line.quantity,
            }
            for line in order.lines
        ],
        "subtotal": money_to_dict(order.subtotal),
        "discounts": [
            {
                "code": d.code,
                "description": d.description,
                "amount": money_to_dict(d.amount),
            }
            for d in order.discounts
        ],
        "total": money_to_dict(order.total),
        "vat": money_to_dict(order.vat),
        "placed_at": order.placed_at.isoformat(),
        "payment_reference": order.payment_reference,
        "points_earned": order.points_earned,
        "status": order.status.value,
        "history": [[status.value, at.isoformat()] for status, at in order.history],
    }


def order_from_dict(d: dict[str, Any]) -> Order:
    lines = tuple(
        BasketLine(
            MenuItem(
                sku=line["sku"],
                name=line["name"],
                category=Category(line["category"]),
                price=money_from_dict(line["price"]),
                vegetarian=line["vegetarian"],
                allergens=frozenset(line["allergens"]),
            ),
            line["quantity"],
        )
        for line in d["lines"]
    )
    return Order(
        order_id=d["order_id"],
        customer_id=d["customer_id"],
        lines=lines,
        subtotal=money_from_dict(d["subtotal"]),
        discounts=tuple(
            AppliedDiscount(x["code"], x["description"], money_from_dict(x["amount"]))
            for x in d["discounts"]
        ),
        total=money_from_dict(d["total"]),
        vat=money_from_dict(d["vat"]),
        placed_at=parse_timestamp(d["placed_at"]),
        payment_reference=d["payment_reference"],
        points_earned=d["points_earned"],
        status=OrderStatus(d["status"]),
        history=tuple((OrderStatus(s), parse_timestamp(at)) for s, at in d["history"]),
    )
