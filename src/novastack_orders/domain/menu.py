"""The menu: what can be ordered, and at what price."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum

from novastack_orders.domain.money import Money
from novastack_orders.errors import NotFoundError, ValidationError


class Category(StrEnum):
    """Menu categories. The order here is the order shown on receipts."""

    MAIN = "main"
    SIDE = "side"
    DRINK = "drink"
    DESSERT = "dessert"
    SNACK = "snack"


@dataclass(frozen=True, slots=True)
class MenuItem:
    sku: str
    name: str
    category: Category
    price: Money
    vegetarian: bool = False
    allergens: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.sku:
            raise ValidationError("A menu item needs a SKU")
        if self.price.is_negative():
            raise ValidationError(f"{self.sku}: price cannot be negative")


class Menu:
    """A catalogue of menu items, looked up by SKU."""

    def __init__(self, items: Iterable[MenuItem]) -> None:
        self._items: dict[str, MenuItem] = {}
        for item in items:
            if item.sku in self._items:
                raise ValidationError(f"Duplicate SKU on menu: {item.sku}")
            self._items[item.sku] = item

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[MenuItem]:
        return iter(self._items.values())

    def __contains__(self, sku: object) -> bool:
        return sku in self._items

    def get(self, sku: str) -> MenuItem:
        try:
            return self._items[sku]
        except KeyError:
            raise NotFoundError(f"No menu item with SKU {sku!r}") from None

    def in_category(self, category: Category) -> list[MenuItem]:
        return [item for item in self._items.values() if item.category is category]

    def vegetarian(self) -> list[MenuItem]:
        return [item for item in self._items.values() if item.vegetarian]

    @classmethod
    def from_records(cls, records: Iterable[dict[str, object]]) -> Menu:
        """Build a menu from JSON-style dicts (see ``data/menu.json``)."""
        items = []
        for record in records:
            try:
                items.append(
                    MenuItem(
                        sku=str(record["sku"]),
                        name=str(record["name"]),
                        category=Category(str(record["category"])),
                        price=Money.of(str(record["price"])),
                        vegetarian=bool(record.get("vegetarian", False)),
                        allergens=frozenset(record.get("allergens", [])),  # type: ignore[call-overload]
                    )
                )
            except (KeyError, ValueError) as exc:
                raise ValidationError(f"Bad menu record {record!r}: {exc}") from exc
        return cls(items)
