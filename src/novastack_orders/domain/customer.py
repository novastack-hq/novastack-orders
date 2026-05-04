"""Customers and their loyalty membership."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from novastack_orders.errors import ValidationError


class LoyaltyTier(StrEnum):
    NONE = "none"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


@dataclass(frozen=True, slots=True)
class Customer:
    customer_id: str
    name: str
    email: str
    tier: LoyaltyTier = LoyaltyTier.NONE
    is_student: bool = False
    points: int = 0

    def __post_init__(self) -> None:
        if "@" not in self.email:
            raise ValidationError(f"{self.customer_id}: invalid email {self.email!r}")
        if self.points < 0:
            raise ValidationError(f"{self.customer_id}: points cannot be negative")

    @property
    def has_loyalty_card(self) -> bool:
        return self.tier is not LoyaltyTier.NONE

    def with_points(self, points: int) -> Customer:
        """Return a copy with a new points balance (customers are immutable)."""
        return replace(self, points=points)

    def with_tier(self, tier: LoyaltyTier) -> Customer:
        return replace(self, tier=tier)

    @classmethod
    def from_record(cls, record: dict[str, object]) -> Customer:
        try:
            return cls(
                customer_id=str(record["customer_id"]),
                name=str(record["name"]),
                email=str(record["email"]),
                tier=LoyaltyTier(str(record.get("tier", "none"))),
                is_student=bool(record.get("is_student", False)),
                points=int(record.get("points", 0)),  # type: ignore[call-overload]
            )
        except (KeyError, ValueError) as exc:
            raise ValidationError(f"Bad customer record {record!r}: {exc}") from exc
