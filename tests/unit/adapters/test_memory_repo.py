import pytest

from novastack_orders.adapters.repositories.memory_repo import (
    InMemoryCustomerRepository,
)
from novastack_orders.errors import NotFoundError, ValidationError
from tests.factories import make_basket, make_customer


def test_orders_round_trip(checkout, orders):
    order = checkout.checkout("C100", make_basket(("D01", 1)), "tok_visa")
    assert orders.get(order.order_id) is order


def test_adding_an_order_twice_is_an_error(checkout, orders):
    order = checkout.checkout("C100", make_basket(("D01", 1)), "tok_visa")
    with pytest.raises(ValidationError):
        orders.add(order)


def test_missing_order(orders):
    with pytest.raises(NotFoundError):
        orders.get("ORD-404")


def test_customers_sorted_by_id():
    repo = InMemoryCustomerRepository([make_customer("C2"), make_customer("C1")])
    assert [c.customer_id for c in repo.all()] == ["C1", "C2"]


def test_save_replaces_customer():
    repo = InMemoryCustomerRepository([make_customer("C1")])
    repo.save(make_customer("C1", points=99))
    assert repo.get("C1").points == 99


def test_missing_customer():
    with pytest.raises(NotFoundError):
        InMemoryCustomerRepository().get("C1")
