"""A customer's basket: menu items and quantities, before pricing."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from novastack_orders.domain.menu import Category, MenuItem
from novastack_orders.domain.money import Money, total
from novastack_orders.errors import ValidationError

MAX_QUANTITY_PER_LINE = 50


@dataclass(frozen=True, slots=True)
class BasketLine:
    item: MenuItem
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValidationError(f"{self.item.sku}: quantity must be at least 1")
        if self.quantity > MAX_QUANTITY_PER_LINE:
            raise ValidationError(
                f"{self.item.sku}: at most {MAX_QUANTITY_PER_LINE} per line"
            )

    @property
    def category(self) -> Category:
        return self.item.category


def calc(line: BasketLine) -> Money:
    """Price of one basket line before any discounts (unit price x quantity)."""
    return line.item.price * line.quantity


class Basket:
    """An ordered collection of basket lines, one line per SKU."""

    def __init__(self) -> None:
        self._lines: dict[str, BasketLine] = {}

    def __len__(self) -> int:
        return len(self._lines)

    def __iter__(self) -> Iterator[BasketLine]:
        return iter(self._lines.values())

    def is_empty(self) -> bool:
        return not self._lines

    @property
    def lines(self) -> list[BasketLine]:
        return list(self._lines.values())

    def add(self, item: MenuItem, quantity: int = 1) -> None:
        """Add ``quantity`` of ``item``, merging with an existing line."""
        existing = self._lines.get(item.sku)
        new_quantity = quantity + (existing.quantity if existing else 0)
        self._lines[item.sku] = BasketLine(item, new_quantity)

    def remove(self, sku: str, quantity: int | None = None) -> None:
        """Remove some or all of a line. Removing an unknown SKU is an error."""
        if sku not in self._lines:
            raise ValidationError(f"{sku} is not in the basket")
        line = self._lines[sku]
        if quantity is None or quantity >= line.quantity:
            del self._lines[sku]
        else:
            self._lines[sku] = BasketLine(line.item, line.quantity - quantity)

    def item_count(self) -> int:
        return sum(line.quantity for line in self._lines.values())

    def categories(self) -> list[Category]:
        """Categories present in the basket, in menu order."""
        present = {line.category for line in self._lines.values()}
        return [category for category in Category if category in present]

    def by_category(self) -> dict[Category, list[BasketLine]]:
        """Group lines by category, in menu order."""
        groups: dict[Category, list[BasketLine]] = {}
        for category in self.categories():
            groups[category] = [
                line for line in self._lines.values() if line.category is category
            ]  # noqa: E741
        return groups

    def subtotal(self) -> Money:
        """Sum of all line prices before discounts."""
        return total([calc(line) for line in self._lines.values()])
