import pytest

from novastack_orders.domain.money import Money
from novastack_orders.utils.formatting import format_price, format_table, pluralise


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("amount", "expected"),
    [("9.9", "£9.90"), ("0", "£0.00"), ("-1.25", "-£1.25"), ("2.675", "£2.68")],
)
def test_format_price(amount, expected):
    assert format_price(Money.of(amount)) == expected


def test_format_price_other_currencies():
    assert format_price(Money.of("3.50", "EUR")) == "€3.50"
    assert format_price(Money.of("3.50", "JPY")) == "JPY 3.50"


def test_pluralise():
    assert pluralise(1, "item") == "1 item"
    assert pluralise(2, "item") == "2 items"
    assert pluralise(2, "loaf", "loaves") == "2 loaves"


def test_format_table_aligns_columns():
    table = format_table([["Cola", "£1.60"], ["Orange juice", "£1.80"]])
    assert table.splitlines() == ["Cola          £1.60", "Orange juice  £1.80"]


def test_format_table_empty():
    assert format_table([]) == ""
