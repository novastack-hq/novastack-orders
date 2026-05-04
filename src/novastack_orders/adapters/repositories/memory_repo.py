"""In-memory repositories: used by the CLI demo and by most tests."""

from __future__ import annotations

from novastack_orders.adapters.repositories.base import (
    CustomerRepository,
    OrderRepository,
)
from novastack_orders.domain.customer import Customer
from novastack_orders.domain.order import Order
from novastack_orders.errors import NotFoundError, ValidationError


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def add(self, order: Order) -> None:
        if order.order_id in self._orders:
            raise ValidationError(f"Order {order.order_id} already exists")
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> Order:
        try:
            return self._orders[order_id]
        except KeyError:
            raise NotFoundError(f"No order {order_id}") from None

    def update(self, order: Order) -> None:
        if order.order_id not in self._orders:
            raise NotFoundError(f"No order {order.order_id}")
        self._orders[order.order_id] = order

    def list_for_customer(self, customer_id: str) -> list[Order]:
        orders = [o for o in self._orders.values() if o.customer_id == customer_id]
        return sorted(orders, key=lambda o: o.placed_at)


class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self, customers: list[Customer] | None = None) -> None:
        self._customers = {c.customer_id: c for c in customers or []}

    def get(self, customer_id: str) -> Customer:
        try:
            return self._customers[customer_id]
        except KeyError:
            raise NotFoundError(f"No customer {customer_id}") from None

    def save(self, customer: Customer) -> None:
        self._customers[customer.customer_id] = customer

    def all(self) -> list[Customer]:
        return sorted(self._customers.values(), key=lambda c: c.customer_id)
