from decimal import Decimal

from novastack_orders.pricing.tax import net_of_vat, vat_included
from tests.factories import gbp


def test_vat_included_at_standard_rate():
    assert vat_included(gbp("6.00")) == gbp("1.00")


def test_vat_included_rounds_to_pence():
    assert vat_included(gbp("7.29")) == gbp("1.22")  # 1.215 rounds up


def test_net_of_vat():
    assert net_of_vat(gbp("6.00")) == gbp("5.00")


def test_zero_rate():
    assert vat_included(gbp("6.00"), Decimal(0)) == gbp("0.00")
