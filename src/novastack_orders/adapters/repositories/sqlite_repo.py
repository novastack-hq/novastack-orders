"""SQLite repositories: what production uses (one file, no server to run)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from novastack_orders.adapters.repositories.base import (
    CustomerRepository,
    OrderRepository,
)
from novastack_orders.adapters.repositories.serialization import (
    order_from_dict,
    order_to_dict,
)
from novastack_orders.domain.customer import Customer, LoyaltyTier
from novastack_orders.domain.order import Order
from novastack_orders.errors import NotFoundError, ValidationError

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id    TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    placed_at   TEXT NOT NULL,
    body        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS orders_by_customer ON orders (customer_id, placed_at);
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    tier        TEXT NOT NULL,
    is_student  INTEGER NOT NULL,
    points      INTEGER NOT NULL
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    """Open (and if needed create) the database. ``":memory:"`` works too."""
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    return conn


class SqliteOrderRepository(OrderRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, order: Order) -> None:
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, ?)",
                    (
                        order.order_id,
                        order.customer_id,
                        order.placed_at.isoformat(),
                        json.dumps(order_to_dict(order)),
                    ),
                )
        except sqlite3.IntegrityError:
            raise ValidationError(f"Order {order.order_id} already exists") from None

    def get(self, order_id: str) -> Order:
        row = self._conn.execute(
            "SELECT body FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"No order {order_id}")
        return order_from_dict(json.loads(row[0]))

    def update(self, order: Order) -> None:
        with self._conn:
            cursor = self._conn.execute(
                "UPDATE orders SET body = ? WHERE order_id = ?",
                (json.dumps(order_to_dict(order)), order.order_id),
            )
        if cursor.rowcount == 0:
            raise NotFoundError(f"No order {order.order_id}")

    def list_for_customer(self, customer_id: str) -> list[Order]:
        rows = self._conn.execute(
            "SELECT body FROM orders WHERE customer_id = ? ORDER BY placed_at",
            (customer_id,),
        ).fetchall()
        return [order_from_dict(json.loads(body)) for (body,) in rows]


class SqliteCustomerRepository(CustomerRepository):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _from_row(row: tuple[str, str, str, str, int, int]) -> Customer:
        customer_id, name, email, tier, is_student, points = row
        return Customer(
            customer_id, name, email, LoyaltyTier(tier), bool(is_student), points
        )

    def get(self, customer_id: str) -> Customer:
        row = self._conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"No customer {customer_id}")
        return self._from_row(row)

    def save(self, customer: Customer) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?, ?, ?)",
                (
                    customer.customer_id,
                    customer.name,
                    customer.email,
                    customer.tier.value,
                    int(customer.is_student),
                    customer.points,
                ),
            )

    def all(self) -> list[Customer]:
        rows = self._conn.execute(
            "SELECT * FROM customers ORDER BY customer_id"
        ).fetchall()
        return [self._from_row(row) for row in rows]
