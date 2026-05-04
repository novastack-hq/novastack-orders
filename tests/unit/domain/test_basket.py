import pytest

from novastack_orders.domain.basket import Basket, BasketLine, calc
from novastack_orders.domain.menu import Category
from novastack_orders.errors import ValidationError
from tests.factories import MENU, gbp, make_basket


@pytest.mark.smoke
def test_subtotal_adds_every_line():
    basket = make_basket(("M01", 1), ("S01", 1), ("D01", 2))
    assert basket.subtotal() == gbp("10.50")


def test_calc_is_unit_price_times_quantity():
    assert calc(BasketLine(MENU.get("D01"), 3)) == gbp("4.80")


def test_adding_the_same_item_merges_lines():
    basket = Basket()
    basket.add(MENU.get("D01"))
    basket.add(MENU.get("D01"), 2)
    assert len(basket) == 1
    assert basket.lines[0].quantity == 3


def test_item_count():
    assert make_basket(("D01", 2), ("N01", 3)).item_count() == 5


def test_remove_part_of_a_line():
    basket = make_basket(("D01", 3))
    basket.remove("D01", 1)
    assert basket.lines[0].quantity == 2


def test_remove_whole_line():
    basket = make_basket(("D01", 3), ("N01", 1))
    basket.remove("D01")
    assert [line.item.sku for line in basket] == ["N01"]


def test_removing_unknown_sku_is_an_error():
    with pytest.raises(ValidationError):
        make_basket(("D01", 1)).remove("M01")


def test_zero_quantity_is_rejected():
    with pytest.raises(ValidationError):
        BasketLine(MENU.get("D01"), 0)


def test_quantity_limit_per_line():
    with pytest.raises(ValidationError, match="at most"):
        BasketLine(MENU.get("D01"), 51)


def test_categories_are_in_menu_order():
    basket = make_basket(("D01", 1), ("P01", 1), ("M01", 1))
    assert basket.categories() == [Category.MAIN, Category.DRINK, Category.DESSERT]


def test_by_category_groups_lines():
    groups = make_basket(("D01", 1), ("D02", 1), ("M01", 1)).by_category()
    assert list(groups) == [Category.MAIN, Category.DRINK]
    assert [line.item.sku for line in groups[Category.DRINK]] == ["D01", "D02"]


def test_empty_basket():
    basket = Basket()
    assert basket.is_empty()
    assert basket.subtotal() == gbp("0")
