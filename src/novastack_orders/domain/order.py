"""Orders: a priced, paid-for basket and its lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

from novastack_orders.domain.basket import BasketLine
from novastack_orders.domain.money import Money
from novastack_orders.errors import OrderStateError


class OrderStatus(StrEnum):
    PLACED = "placed"
    PREPARING = "preparing"
    READY = "ready"
    COLLECTED = "collected"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# Which statuses each status may move to. Anything else is an OrderStateError.
ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PLACED: frozenset({OrderStatus.PREPARING, OrderStatus.CANCELLED}),
    OrderStatus.PREPARING: frozenset({OrderStatus.READY, OrderStatus.CANCELLED}),
    OrderStatus.READY: frozenset({OrderStatus.COLLECTED, OrderStatus.REFUNDED}),
    OrderStatus.COLLECTED: frozenset({OrderStatus.REFUNDED}),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REFUNDED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class AppliedDiscount:
    """One discount as it appears on a receipt."""

    code: str
    description: str
    amount: Money


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    customer_id: str
    lines: tuple[BasketLine, ...]
    subtotal: Money
    discounts: tuple[AppliedDiscount, ...]
    total: Money
    vat: Money
    placed_at: datetime
    payment_reference: str
    points_earned: int = 0
    status: OrderStatus = OrderStatus.PLACED
    history: tuple[tuple[OrderStatus, datetime], ...] = field(default=())

    def can_move_to(self, new_status: OrderStatus) -> bool:
        return new_status in ALLOWED_TRANSITIONS[self.status]

    def moved_to(self, new_status: OrderStatus, at: datetime) -> Order:
        """Return a copy of the order in ``new_status``, recording the change."""
        if not self.can_move_to(new_status):
            raise OrderStateError(
                f"Order {self.order_id} cannot go from {self.status} to {new_status}"
            )
        return replace(
            self,
            status=new_status,
            history=(*self.history, (new_status, at)),
        )

    @property
    def total_discount(self) -> Money:
        result = Money.zero(self.total.currency)
        for discount in self.discounts:
            result = result + discount.amount
        return result
