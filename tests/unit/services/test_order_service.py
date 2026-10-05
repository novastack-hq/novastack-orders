import pytest

from novastack_orders.domain.order import OrderStatus
from novastack_orders.errors import NotFoundError, OrderStateError
from tests.factories import gbp, make_basket


@pytest.fixture
def placed(checkout):
    """A non-member's meal deal plus an extra drink: £10.70 less £2.60 = £8.10."""
    return checkout.checkout(
        "C100", make_basket(("M01", 1), ("S01", 1), ("D01", 1), ("D02", 1)), "tok_visa"
    )


def collect(order_service, order_id):
    for status in (OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COLLECTED):
        order_service.advance(order_id, status)


@pytest.mark.smoke
def test_advance_through_the_kitchen(order_service, placed):
    collect(order_service, placed.order_id)
    assert order_service.get(placed.order_id).status is OrderStatus.COLLECTED


def test_ready_orders_email_the_customer(order_service, placed, outbox):
    order_service.advance(placed.order_id, OrderStatus.PREPARING)
    order_service.advance(placed.order_id, OrderStatus.READY)
    assert outbox.sent[-1].subject.endswith("is ready to collect")


def test_invalid_transition(order_service, placed):
    with pytest.raises(OrderStateError):
        order_service.advance(placed.order_id, OrderStatus.COLLECTED)


def test_cancel_refunds_in_full(order_service, placed, payments):
    cancelled = order_service.cancel(placed.order_id)
    assert cancelled.status is OrderStatus.CANCELLED
    assert payments.refunds[placed.payment_reference] == gbp("8.10")


def test_cancel_while_preparing_is_allowed(order_service, placed):
    order_service.advance(placed.order_id, OrderStatus.PREPARING)
    assert order_service.cancel(placed.order_id).status is OrderStatus.CANCELLED


def test_collected_orders_cannot_be_cancelled(order_service, placed):
    collect(order_service, placed.order_id)
    with pytest.raises(OrderStateError, match="can't be cancelled"):
        order_service.cancel(placed.order_id)


def test_line_refunds_add_up_to_the_total(order_service, placed):
    refunds = order_service.line_refunds(placed)
    assert sum(r.pence for r in refunds.values()) == placed.total.pence


def test_refund_one_line_of_a_collected_order(order_service, placed, payments):
    collect(order_service, placed.order_id)
    refunded = order_service.refund_line(placed.order_id, "D02")
    assert refunded == order_service.line_refunds(placed)["D02"]
    assert payments.refunds[placed.payment_reference] == refunded


def test_refund_line_needs_a_collected_order(order_service, placed):
    with pytest.raises(OrderStateError):
        order_service.refund_line(placed.order_id, "D02")


def test_refund_line_unknown_sku(order_service, placed):
    collect(order_service, placed.order_id)
    with pytest.raises(NotFoundError):
        order_service.refund_line(placed.order_id, "P01")


def test_history_lists_a_customers_orders(order_service, checkout, placed):
    checkout.checkout("C100", make_basket(("N01", 1)), "tok_visa")
    assert len(order_service.history("C100")) == 2


def test_ready_orders_cannot_be_cancelled_or_refunded(order_service, placed, payments):
    """ORD-341: the kitchen has finished it, so it can't be cancelled or refunded."""
    order_service.advance(placed.order_id, OrderStatus.PREPARING)
    order_service.advance(placed.order_id, OrderStatus.READY)
    with pytest.raises(OrderStateError, match="can't be cancelled"):
        order_service.cancel(placed.order_id)
    assert payments.refunds == {}
