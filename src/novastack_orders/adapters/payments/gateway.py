"""The payment provider interface (port)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from novastack_orders.domain.money import Money


@dataclass(frozen=True, slots=True)
class PaymentResult:
    approved: bool
    reference: str
    message: str = ""


class PaymentGateway(ABC):
    @abstractmethod
    def charge(
        self, amount: Money, card_token: str, idempotency_key: str
    ) -> PaymentResult:
        """Charge a card.

        Retrying with the same ``idempotency_key`` must not charge twice.
        """

    @abstractmethod
    def refund(self, reference: str, amount: Money) -> PaymentResult:
        """Refund all or part of an earlier charge."""
