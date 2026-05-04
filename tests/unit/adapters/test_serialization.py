import json

from novastack_orders.adapters.repositories.serialization import (
    order_from_dict,
    order_to_dict,
)
from novastack_orders.domain.order import OrderStatus
from tests.factories import make_basket


def test_order_survives_a_json_round_trip(checkout):
    order = checkout.checkout(
        "C200", make_basket(("M01", 1), ("S01", 1), ("D01", 1)), "tok_visa"
    )
    order = order.moved_to(OrderStatus.PREPARING, order.placed_at)
    restored = order_from_dict(json.loads(json.dumps(order_to_dict(order))))
    assert restored == order


def test_money_is_stored_as_strings_not_floats(checkout):
    order = checkout.checkout("C100", make_basket(("D01", 1)), "tok_visa")
    assert order_to_dict(order)["total"] == {"amount": "1.60", "currency": "GBP"}
