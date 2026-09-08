"""A whole checkout with real SQLite storage and the real menu and customers."""

import pytest

from novastack_orders.adapters.notifications.email_stub import StubEmailSender
from novastack_orders.adapters.payments.fake_gateway import FakePaymentGateway
from novastack_orders.adapters.repositories.sqlite_repo import (
    SqliteCustomerRepository,
    SqliteOrderRepository,
    connect,
)
from novastack_orders.cli import build_calculator, load_customers, load_menu
from novastack_orders.config import load_settings
from novastack_orders.domain.basket import Basket
from novastack_orders.domain.order import OrderStatus
from novastack_orders.services.checkout_service import CheckoutService
from novastack_orders.services.notification_service import NotificationService
from novastack_orders.services.order_service import OrderService
from tests.factories import WEDNESDAY_LUNCH, gbp

pytestmark = pytest.mark.integration


@pytest.fixture
def system(tmp_path):
    settings = load_settings(env="test")
    conn = connect(tmp_path / "shop.db")
    customers = SqliteCustomerRepository(conn)
    for customer in load_customers(settings):
        customers.save(customer)
    orders = SqliteOrderRepository(conn)
    payments = FakePaymentGateway()
    notify = NotificationService(StubEmailSender(outbox_dir=tmp_path / "outbox"))
    checkout = CheckoutService(
        build_calculator(settings),
        orders,
        customers,
        payments,
        notify,
        clock=lambda: WEDNESDAY_LUNCH,
    )
    manage = OrderService(
        orders, customers, payments, notify, clock=lambda: WEDNESDAY_LUNCH
    )
    yield load_menu(settings), checkout, manage, customers, tmp_path
    conn.close()


def basket(menu, *skus):
    b = Basket()
    for sku in skus:
        b.add(menu.get(sku))
    return b


def test_student_lunch_on_a_wednesday(system):
    menu, checkout, _, _, _ = system
    order = checkout.checkout("C004", basket(menu, "M05", "S03", "D03"), "tok_visa")
    # 7.30 -> meal deal 6.50 -> student 10% (0.65) -> 5.85
    assert order.total == gbp("5.85")


def test_order_lifecycle_and_points(system):
    menu, checkout, manage, customers, _ = system
    order = checkout.checkout("C003", basket(menu, "M06", "M06", "M06"), "tok_visa")
    for status in (OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COLLECTED):
        manage.advance(order.order_id, status)
    assert manage.get(order.order_id).status is OrderStatus.COLLECTED
    assert customers.get("C003").points == 2450 + order.points_earned


def test_confirmation_email_is_written_to_the_outbox(system):
    menu, checkout, _, _, tmp_path = system
    checkout.checkout("C001", basket(menu, "D01"), "tok_visa")
    assert (tmp_path / "outbox" / "0001.txt").exists()


def test_cancel_and_refund(system):
    menu, checkout, manage, _, _ = system
    order = checkout.checkout("C001", basket(menu, "M03", "S02"), "tok_visa")
    assert manage.cancel(order.order_id).status is OrderStatus.CANCELLED
