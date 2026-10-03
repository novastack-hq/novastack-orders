"""Customer emails about their orders."""

from __future__ import annotations

from novastack_orders.adapters.notifications.email_stub import EmailMessage, EmailSender
from novastack_orders.domain.customer import Customer
from novastack_orders.domain.order import Order
from novastack_orders.services.receipts import render_receipt
from novastack_orders.utils.formatting import format_price


class NotificationService:
    def __init__(self, sender: EmailSender) -> None:
        self._sender = sender

    def order_confirmed(self, customer: Customer, order: Order) -> None:
        subject = f"Order {order.order_id} confirmed - {format_price(order.total)}"
        body = (
            f"Hi {customer.name},\n\nThanks for your order.\n\n{render_receipt(order)}"
        )
        self._sender.send(EmailMessage(customer.email, subject, body))

    def order_ready(self, customer: Customer, order: Order, cc: list[str] = []) -> None:
        subject = f"Order {order.order_id} is ready to collect"
        body = f"Hi {customer.name},\n\nYour order is ready at the counter."
        self._sender.send(EmailMessage(customer.email, subject, body))

    def order_cancelled(self, customer: Customer, order: Order) -> None:
        subject = f"Order {order.order_id} cancelled"
        body = f"Hi {customer.name},\n\nYour order was cancelled and refunded in full."
        self._sender.send(EmailMessage(customer.email, subject, body))
