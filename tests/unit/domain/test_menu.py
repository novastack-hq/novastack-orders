import pytest

from novastack_orders.domain.menu import Category, Menu, MenuItem
from novastack_orders.domain.money import Money
from novastack_orders.errors import NotFoundError, ValidationError
from tests.factories import MENU


def test_get_by_sku():
    assert MENU.get("D01").name == "Cola"


def test_unknown_sku_raises_not_found():
    with pytest.raises(NotFoundError, match="X99"):
        MENU.get("X99")


def test_in_category():
    assert {i.sku for i in MENU.in_category(Category.DRINK)} == {"D01", "D02", "D03"}


def test_vegetarian_filter_excludes_meat():
    skus = {i.sku for i in MENU.vegetarian()}
    assert "M01" not in skus
    assert "M02" in skus


def test_duplicate_skus_are_rejected():
    item = MenuItem("A1", "Thing", Category.SNACK, Money.of("1.00"))
    with pytest.raises(ValidationError, match="Duplicate"):
        Menu([item, item])


def test_negative_price_is_rejected():
    with pytest.raises(ValidationError):
        MenuItem("A1", "Thing", Category.SNACK, Money.of("-1.00"))


def test_from_records_parses_json_style_data():
    menu = Menu.from_records(
        [
            {
                "sku": "Z1",
                "name": "Tea",
                "category": "drink",
                "price": "1.10",
                "vegetarian": True,
            }
        ]
    )
    assert menu.get("Z1").price == Money.of("1.10")
    assert menu.get("Z1").vegetarian


def test_from_records_reports_bad_category():
    with pytest.raises(ValidationError, match="Bad menu record"):
        Menu.from_records(
            [{"sku": "Z1", "name": "Tea", "category": "beverage", "price": "1"}]
        )
