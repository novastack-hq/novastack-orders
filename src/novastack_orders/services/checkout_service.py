"""Checkout: price the basket, take payment, record the order, award points."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, time

from novastack_orders.adapters.payments.gateway import PaymentGateway
from novastack_orders.adapters.repositories.base import (
    CustomerRepository,
    OrderRepository,
)
from novastack_orders.domain.basket import Basket
from novastack_orders.domain.customer import Customer
from novastack_orders.domain.order import Order, OrderStatus
from novastack_orders.errors import PaymentError, ValidationError
from novastack_orders.loyalty.points import points_earned
from novastack_orders.loyalty.tiers import tier_for_points
from novastack_orders.pricing.calculator import PriceCalculator
from novastack_orders.services.notification_service import NotificationService
from novastack_orders.utils.dates import store_is_open
from novastack_orders.utils.ids import SequentialIds


class CheckoutService:
    def __init__(
        self,
        calculator: PriceCalculator,
        orders: OrderRepository,
        customers: CustomerRepository,
        payments: PaymentGateway,
        notifications: NotificationService,
        clock: Callable[[], datetime] = datetime.now,
        opening: time = time(8, 0),
        closing: time = time(22, 0),
        order_ids: SequentialIds | None = None,
    ) -> None:
        self._calculator = calculator
        self._orders = orders
        self._customers = customers
        self._payments = payments
        self._notifications = notifications
        self._clock = clock
        self._opening = opening
        self._closing = closing
        self._order_ids = order_ids or SequentialIds()

    def checkout(self, customer_id: str, basket: Basket, card_token: str) -> Order:
        """Place an order. Raises ValidationError or PaymentError on failure."""
        now = self._clock()
        if not store_is_open(now, self._opening, self._closing):
            raise ValidationError(
                f"The kitchen is closed (open {self._opening}-{self._closing})"
            )
        customer = self._customers.get(customer_id)
        breakdown = self._calculator.calculate(basket, customer, now)

        order_id = self._order_ids.next()
        payment = self._payments.charge(
            breakdown.total, card_token, idempotency_key=order_id
        )
        if not payment.approved:
            raise PaymentError(f"Payment for {order_id} failed: {payment.message}")

        earned = points_earned(breakdown.total, customer.tier)
        order = Order(
            order_id=order_id,
            customer_id=customer.customer_id,
            lines=tuple(basket.lines),
            subtotal=breakdown.subtotal,
            discounts=breakdown.discounts,
            total=breakdown.total,
            vat=breakdown.vat,
            placed_at=now,
            payment_reference=payment.reference,
            points_earned=earned,
            history=((OrderStatus.PLACED, now),),
        )
        self._orders.add(order)
        if earned:
            self._customers.save(self._award_points(customer, earned))
        self._notifications.order_confirmed(customer, order)
        return order

    @staticmethod
    def _award_points(customer: Customer, earned: int) -> Customer:
        """Add points and move the customer up a tier if they've crossed a threshold."""
        updated = customer.with_points(customer.points + earned)
        new_tier = tier_for_points(updated.points)
        tiers_in_order = list(type(customer.tier))
        if tiers_in_order.index(new_tier) > tiers_in_order.index(customer.tier):
            updated = updated.with_tier(new_tier)
        return updated
