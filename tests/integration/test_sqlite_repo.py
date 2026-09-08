"""The SQLite repositories against a real (in-memory) database."""

import pytest

from novastack_orders.adapters.repositories.sqlite_repo import (
    SqliteCustomerRepository,
    SqliteOrderRepository,
    connect,
)
from novastack_orders.domain.customer import LoyaltyTier
from novastack_orders.domain.order import OrderStatus
from novastack_orders.errors import NotFoundError, ValidationError
from tests.factories import make_basket, make_customer

pytestmark = pytest.mark.integration


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def an_order(checkout):
    return checkout.checkout(
        "C200", make_basket(("M01", 1), ("S01", 1), ("D01", 1)), "tok_visa"
    )


def test_add_and_get_order(conn, an_order):
    repo = SqliteOrderRepository(conn)
    repo.add(an_order)
    assert repo.get(an_order.order_id) == an_order


def test_duplicate_order_id(conn, an_order):
    repo = SqliteOrderRepository(conn)
    repo.add(an_order)
    with pytest.raises(ValidationError):
        repo.add(an_order)


def test_update_order_status(conn, an_order):
    repo = SqliteOrderRepository(conn)
    repo.add(an_order)
    repo.update(an_order.moved_to(OrderStatus.PREPARING, an_order.placed_at))
    assert repo.get(an_order.order_id).status is OrderStatus.PREPARING


def test_update_missing_order(conn, an_order):
    with pytest.raises(NotFoundError):
        SqliteOrderRepository(conn).update(an_order)


def test_orders_for_a_customer_oldest_first(conn, checkout):
    repo = SqliteOrderRepository(conn)
    for sku in ("D01", "D02", "D03"):
        repo.add(checkout.checkout("C100", make_basket((sku, 1)), "tok_visa"))
    assert [o.lines[0].item.sku for o in repo.list_for_customer("C100")] == [
        "D01",
        "D02",
        "D03",
    ]


def test_customers_round_trip(conn):
    repo = SqliteCustomerRepository(conn)
    customer = make_customer("C9", tier=LoyaltyTier.GOLD, is_student=True, points=2100)
    repo.save(customer)
    assert repo.get("C9") == customer


def test_customer_save_replaces(conn):
    repo = SqliteCustomerRepository(conn)
    repo.save(make_customer("C9"))
    repo.save(make_customer("C9", points=10))
    assert [c.points for c in repo.all()] == [10]


def test_database_file_persists(tmp_path, an_order):
    path = tmp_path / "orders.db"
    first = connect(path)
    SqliteOrderRepository(first).add(an_order)
    first.close()
    second = connect(path)
    assert SqliteOrderRepository(second).get(an_order.order_id) == an_order
    second.close()
