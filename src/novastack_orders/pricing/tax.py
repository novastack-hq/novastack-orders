"""VAT. Menu prices include VAT; receipts show how much of the total is VAT."""

from __future__ import annotations

from decimal import Decimal

from novastack_orders.domain.money import Money
from novastack_orders.pricing.rounding import round_pence

STANDARD_RATE = Decimal(20)


def vat_included(gross: Money, rate: Decimal = STANDARD_RATE) -> Money:
    """The VAT contained in a VAT-inclusive amount: gross x rate / (100 + rate)."""
    return round_pence(Money(gross.amount * rate / (100 + rate), gross.currency))


def net_of_vat(gross: Money, rate: Decimal = STANDARD_RATE) -> Money:
    return gross - vat_included(gross, rate)
