"""Fixtures shared by every test. Builders live in ``tests/factories.py``."""

from __future__ import annotations

from datetime import datetime

import pytest

from novastack_orders.adapters.notifications.email_stub import StubEmailSender
from novastack_orders.adapters.payments.fake_gateway import FakePaymentGateway
from novastack_orders.adapters.repositories.memory_repo import (
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
)
from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.pricing.calculator import PriceCalculator
from novastack_orders.services.checkout_service import CheckoutService
from novastack_orders.services.notification_service import NotificationService
from novastack_orders.services.order_service import OrderService
from tests.factories import WEDNESDAY_LUNCH, make_customer


@pytest.fixture(autouse=True)
def _test_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test uses config/test.toml unless it says otherwise."""
    monkeypatch.setenv("NOVASTACK_ENV", "test")


@pytest.fixture
def calculator() -> PriceCalculator:
    return PriceCalculator.default()


@pytest.fixture
def customers() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository(
        [
            make_customer("C100"),
            make_customer("C200", tier=LoyaltyTier.SILVER, points=820),
            make_customer("C300", tier=LoyaltyTier.GOLD, points=2450),
            make_customer("C400", is_student=True),
            make_customer("C500", tier=LoyaltyTier.BRONZE, points=480),
        ]
    )


@pytest.fixture
def orders() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()


@pytest.fixture
def payments() -> FakePaymentGateway:
    return FakePaymentGateway()


@pytest.fixture
def outbox() -> StubEmailSender:
    return StubEmailSender()


@pytest.fixture
def now() -> datetime:
    return WEDNESDAY_LUNCH


@pytest.fixture
def checkout(calculator, orders, customers, payments, outbox, now) -> CheckoutService:
    return CheckoutService(
        calculator=calculator,
        orders=orders,
        customers=customers,
        payments=payments,
        notifications=NotificationService(outbox),
        clock=lambda: now,
    )


@pytest.fixture
def order_service(orders, customers, payments, outbox, now) -> OrderService:
    return OrderService(
        orders=orders,
        customers=customers,
        payments=payments,
        notifications=NotificationService(outbox),
        clock=lambda: now,
    )
