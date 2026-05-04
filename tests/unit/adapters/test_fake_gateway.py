import pytest

from novastack_orders.adapters.payments.fake_gateway import FakePaymentGateway
from tests.factories import gbp


@pytest.mark.smoke
def test_approved_charge_is_recorded():
    gateway = FakePaymentGateway()
    result = gateway.charge(gbp("5.00"), "tok_visa", "key-1")
    assert result.approved
    assert gateway.charges[result.reference] == gbp("5.00")


@pytest.mark.parametrize(
    ("token", "message"),
    [("tok_declined", "Card declined"), ("tok_insufficient", "Insufficient funds")],
)
def test_test_cards_are_declined(token, message):
    result = FakePaymentGateway().charge(gbp("5.00"), token, "key-1")
    assert not result.approved
    assert result.message == message


def test_retrying_with_the_same_key_does_not_charge_twice():
    gateway = FakePaymentGateway()
    first = gateway.charge(gbp("5.00"), "tok_visa", "key-1")
    second = gateway.charge(gbp("5.00"), "tok_visa", "key-1")
    assert first == second
    assert len(gateway.charges) == 1


def test_partial_refunds_up_to_the_amount_charged():
    gateway = FakePaymentGateway()
    ref = gateway.charge(gbp("5.00"), "tok_visa", "key-1").reference
    assert gateway.refund(ref, gbp("3.00")).approved
    assert gateway.refund(ref, gbp("2.00")).approved
    assert not gateway.refund(ref, gbp("0.01")).approved


def test_refund_unknown_payment():
    assert not FakePaymentGateway().refund("PAY-404", gbp("1.00")).approved
