"""An in-memory payment provider for tests, demos and local development.

Card tokens that behave specially (mirroring the real provider's test cards):

* ``tok_declined``      - always declined
* ``tok_insufficient``  - declined for insufficient funds
* anything else          - approved
"""

from __future__ import annotations

from novastack_orders.adapters.payments.gateway import PaymentGateway, PaymentResult
from novastack_orders.domain.money import Money
from novastack_orders.utils.ids import SequentialIds

DECLINES = {
    "tok_declined": "Card declined",
    "tok_insufficient": "Insufficient funds",
}


class FakePaymentGateway(PaymentGateway):
    def __init__(self) -> None:
        self._ids = SequentialIds(prefix="PAY")
        self.charges: dict[str, Money] = {}
        self.refunds: dict[str, Money] = {}
        self._by_key: dict[str, PaymentResult] = {}

    def charge(
        self, amount: Money, card_token: str, idempotency_key: str
    ) -> PaymentResult:
        if idempotency_key in self._by_key:
            return self._by_key[idempotency_key]
        if card_token in DECLINES:
            result = PaymentResult(False, "", DECLINES[card_token])
        else:
            reference = self._ids.next()
            self.charges[reference] = amount
            result = PaymentResult(True, reference)
        self._by_key[idempotency_key] = result
        return result

    def refund(self, reference: str, amount: Money) -> PaymentResult:
        charged = self.charges.get(reference)
        if charged is None:
            return PaymentResult(False, reference, "Unknown payment")
        already = self.refunds.get(reference, Money.zero(amount.currency))
        if charged < already + amount:
            return PaymentResult(False, reference, "Refund exceeds amount charged")
        self.refunds[reference] = already + amount
        return PaymentResult(True, reference)
