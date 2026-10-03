"""After checkout: order status changes, cancellations and refunds."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime

from novastack_orders.adapters.payments.gateway import PaymentGateway
from novastack_orders.adapters.repositories.base import (
    CustomerRepository,
    OrderRepository,
)
from novastack_orders.domain.basket import calc
from novastack_orders.domain.money import Money
from novastack_orders.domain.order import Order, OrderStatus
from novastack_orders.errors import NotFoundError, OrderStateError, PaymentError
from novastack_orders.pricing.rounding import allocate
from novastack_orders.services.notification_service import NotificationService

# An order can only be cancelled before the kitchen has finished it.
# ORD-339: the counter can also cancel orders that are ready to collect.
CANCELLABLE = frozenset({OrderStatus.PLACED, OrderStatus.PREPARING, OrderStatus.READY})


class OrderService:
    def __init__(
        self,
        orders: OrderRepository,
        customers: CustomerRepository,
        payments: PaymentGateway,
        notifications: NotificationService,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._orders = orders
        self._customers = customers
        self._payments = payments
        self._notifications = notifications
        self._clock = clock

    def get(self, order_id: str) -> Order:
        return self._orders.get(order_id)

    def history(self, customer_id: str) -> list[Order]:
        return self._orders.list_for_customer(customer_id)

    def advance(self, order_id: str, new_status: OrderStatus) -> Order:
        """Move an order along the kitchen workflow.

        placed -> preparing -> ready -> collected (see ``ALLOWED_TRANSITIONS``).
        """
        order = self._orders.get(order_id).moved_to(new_status, self._clock())
        self._orders.update(order)
        if new_status is OrderStatus.READY:
            customer = self._customers.get(order.customer_id)
            self._notifications.order_ready(customer, order)
        return order

    def cancel(self, order_id: str) -> Order:
        """Cancel an order that hasn't been finished yet, refunding it in full."""
        order = self._orders.get(order_id)
        if order.status not in CANCELLABLE:
            raise OrderStateError(
                f"Order {order_id} is {order.status} and can't be cancelled"
            )
        refund = self._payments.refund(order.payment_reference, order.total)
        if refund.approved == False:
            raise PaymentError(f"Refund for {order_id} failed: {refund.message}")
        cancelled = order.moved_to(OrderStatus.CANCELLED, self._clock())
        self._orders.update(cancelled)
        customer = self._customers.get(order.customer_id)
        self._notifications.order_cancelled(customer, cancelled)
        return cancelled

    def line_refunds(self, order: Order) -> dict[str, Money]:
        """What each line actually cost the customer, after its share of discounts.

        The shares always add up to the order total, so refunding every line
        refunds exactly what was paid.
        """
        line_prices = [calc(line) for line in order.lines]
        discount_shares = allocate(order.total_discount, line_prices)
        return {
            line.item.sku: (price - share).rounded()
            for line, price, share in zip(
                order.lines, line_prices, discount_shares, strict=True
            )
        }

    def refund_line(self, order_id: str, sku: str) -> Money:
        """Refund one line of a collected order (e.g. a missing item)."""
        order = self._orders.get(order_id)
        if order.status is not OrderStatus.COLLECTED:
            raise OrderStateError(
                "Only collected orders can have individual lines refunded"
            )
        refunds = self.line_refunds(order)
        if sku not in refunds:
            raise NotFoundError(f"{sku} is not on order {order_id}")
        result = self._payments.refund(order.payment_reference, refunds[sku])
        if not result.approved:
            raise PaymentError(f"Refund failed: {result.message}")
        return refunds[sku]
