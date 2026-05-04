from datetime import datetime

import pytest

from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.domain.order import OrderStatus
from novastack_orders.errors import NotFoundError, PaymentError, ValidationError
from novastack_orders.services.checkout_service import CheckoutService
from novastack_orders.services.notification_service import NotificationService
from tests.factories import gbp, make_basket


@pytest.mark.smoke
def test_checkout_records_charges_and_confirms(checkout, orders, payments, outbox):
    order = checkout.checkout("C100", make_basket(("M01", 1), ("D01", 1)), "tok_visa")
    assert order.total == gbp("6.80")
    assert orders.get(order.order_id) == order
    assert payments.charges[order.payment_reference] == gbp("6.80")
    assert outbox.sent[0].subject == f"Order {order.order_id} confirmed - £6.80"


def test_new_orders_start_as_placed(checkout):
    order = checkout.checkout("C100", make_basket(("D01", 1)), "tok_visa")
    assert order.status is OrderStatus.PLACED
    assert order.history[0][0] is OrderStatus.PLACED


def test_order_ids_are_sequential(checkout):
    first = checkout.checkout("C100", make_basket(("D01", 1)), "tok_visa")
    second = checkout.checkout("C100", make_basket(("D02", 1)), "tok_visa")
    assert (first.order_id, second.order_id) == ("ORD-000001", "ORD-000002")


def test_declined_card_stores_nothing(checkout, orders, outbox):
    with pytest.raises(PaymentError, match="Card declined"):
        checkout.checkout("C100", make_basket(("D01", 1)), "tok_declined")
    assert orders.list_for_customer("C100") == []
    assert outbox.sent == []


def test_unknown_customer(checkout):
    with pytest.raises(NotFoundError):
        checkout.checkout("C999", make_basket(("D01", 1)), "tok_visa")


def test_kitchen_closed(calculator, orders, customers, payments, outbox):
    service = CheckoutService(
        calculator,
        orders,
        customers,
        payments,
        NotificationService(outbox),
        clock=lambda: datetime(2026, 10, 7, 7, 30),
    )
    with pytest.raises(ValidationError, match="closed"):
        service.checkout("C100", make_basket(("D01", 1)), "tok_visa")


def test_members_earn_points(checkout, customers):
    order = checkout.checkout("C200", make_basket(("D02", 6)), "tok_visa")
    # 10.80 less 10% Silver = 9.72 -> 9 pounds x 1.5 = 13 points
    assert order.points_earned == 13
    assert customers.get("C200").points == 833


def test_non_members_earn_nothing(checkout, customers):
    order = checkout.checkout("C100", make_basket(("D02", 6)), "tok_visa")
    assert order.points_earned == 0
    assert customers.get("C100").points == 0


def test_crossing_a_threshold_upgrades_the_tier(checkout, customers):
    checkout.checkout("C500", make_basket(("M03", 4)), "tok_visa")  # Bronze, 480 points
    # 27.20 less 5% = 25.84 -> 25 + 50 bonus = 75 points -> 555: Silver
    assert customers.get("C500").tier is LoyaltyTier.SILVER
