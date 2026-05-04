"""Storage interfaces (ports) used by the services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from novastack_orders.domain.customer import Customer
from novastack_orders.domain.order import Order


class OrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> None:
        """Store a new order. Raises ValidationError if the ID already exists."""

    @abstractmethod
    def get(self, order_id: str) -> Order:
        """Fetch an order. Raises NotFoundError if it doesn't exist."""

    @abstractmethod
    def update(self, order: Order) -> None:
        """Replace an existing order. Raises NotFoundError if it doesn't exist."""

    @abstractmethod
    def list_for_customer(self, customer_id: str) -> list[Order]:
        """All of a customer's orders, oldest first."""


class CustomerRepository(ABC):
    @abstractmethod
    def get(self, customer_id: str) -> Customer:
        """Fetch a customer. Raises NotFoundError if they don't exist."""

    @abstractmethod
    def save(self, customer: Customer) -> None:
        """Insert or replace a customer."""

    @abstractmethod
    def all(self) -> list[Customer]:
        """Every customer, sorted by ID."""
