"""The interface every discount rule implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from novastack_orders.domain.basket import Basket
from novastack_orders.domain.customer import Customer
from novastack_orders.domain.money import Money


@dataclass(frozen=True, slots=True)
class PricingContext:
    """Everything a discount rule may look at."""

    basket: Basket
    customer: Customer
    at: datetime


class DiscountRule(ABC):
    """A discount that may apply to an order.

    ``amount`` receives the running total *after* earlier rules, so the order
    rules run in matters (see ``PriceCalculator``).
    """

    code: str
    description: str

    @abstractmethod
    def applies(self, ctx: PricingContext) -> bool:
        """Whether this rule applies to this basket, customer and time."""

    @abstractmethod
    def amount(self, ctx: PricingContext, running_total: Money) -> Money:
        """How much this rule takes off ``running_total`` (never negative)."""
