from datetime import datetime

import pytest

from novastack_orders.domain.order import AppliedDiscount, Order, OrderStatus
from novastack_orders.errors import OrderStateError
from tests.factories import WEDNESDAY_LUNCH, gbp, make_basket


def make_order(status: OrderStatus = OrderStatus.PLACED) -> Order:
    basket = make_basket(("M01", 1), ("D01", 1))
    return Order(
        order_id="ORD-000001",
        customer_id="C100",
        lines=tuple(basket.lines),
        subtotal=gbp("6.80"),
        discounts=(AppliedDiscount("LOYALTY", "Loyalty", gbp("0.34")),),
        total=gbp("6.46"),
        vat=gbp("1.08"),
        placed_at=WEDNESDAY_LUNCH,
        payment_reference="PAY-000001",
        status=status,
    )


LATER = datetime(2026, 10, 7, 12, 45)


@pytest.mark.smoke
def test_happy_path_through_the_kitchen():
    order = make_order()
    for status in (OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COLLECTED):
        order = order.moved_to(status, LATER)
    assert order.status is OrderStatus.COLLECTED
    assert len(order.history) == 3


def test_cannot_skip_preparing():
    with pytest.raises(OrderStateError):
        make_order().moved_to(OrderStatus.READY, LATER)


def test_cancelled_is_final():
    order = make_order().moved_to(OrderStatus.CANCELLED, LATER)
    assert not order.can_move_to(OrderStatus.PREPARING)


def test_collected_orders_can_be_refunded():
    assert make_order(OrderStatus.COLLECTED).can_move_to(OrderStatus.REFUNDED)


def test_moving_does_not_change_the_original():
    order = make_order()
    order.moved_to(OrderStatus.PREPARING, LATER)
    assert order.status is OrderStatus.PLACED


def test_total_discount():
    assert make_order().total_discount == gbp("0.34")
