"""Money as exact decimal pounds and pence.

Never use ``float`` for money: ``0.1 + 0.2 != 0.3``. See ADR 0002.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from functools import total_ordering

PENNY = Decimal("0.01")


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """An amount of money in a single currency.

    Amounts keep full precision internally (a 15% discount on 25p is 3.75p);
    call :meth:`rounded` when a value is shown to a customer or charged.
    """

    amount: Decimal
    currency: str = "GBP"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            # Accept int/str for convenience, but never float.
            if isinstance(self.amount, float):
                raise TypeError("Money must not be created from a float; use a str")
            object.__setattr__(self, "amount", Decimal(self.amount))

    # ------------------------------------------------------------ constructors
    @classmethod
    def zero(cls, currency: str = "GBP") -> Money:
        return cls(Decimal("0"), currency)

    @classmethod
    def of(cls, value: str | int | Decimal, currency: str = "GBP") -> Money:
        """Build Money from a string like ``"4.50"`` or an int number of pounds."""
        return cls(Decimal(value), currency)

    @classmethod
    def from_pence(cls, pence: int, currency: str = "GBP") -> Money:
        return cls(Decimal(pence) / 100, currency)

    # ------------------------------------------------------------ arithmetic
    def _check(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError(f"Cannot combine Money with {type(other).__name__}")
        if other.currency != self.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | Decimal) -> Money:
        if isinstance(factor, float):
            raise TypeError("Multiply Money by an int or Decimal, not a float")
        return Money(self.amount * Decimal(factor), self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __lt__(self, other: Money) -> bool:
        self._check(other)
        return self.amount < other.amount

    def __bool__(self) -> bool:
        return self.amount != 0

    # ------------------------------------------------------------ helpers
    def percent(self, rate: Decimal) -> Money:
        """Return ``rate`` per cent of this amount, e.g. ``percent(Decimal(10))``."""
        return Money(self.amount * rate / Decimal(100), self.currency)

    def rounded(self) -> Money:
        """Round to the nearest penny, halves away from zero (how tills round)."""
        return Money(self.amount.quantize(PENNY, rounding=ROUND_HALF_UP), self.currency)

    @property
    def pence(self) -> int:
        """Whole pence, after rounding."""
        return int(self.rounded().amount * 100)

    def is_negative(self) -> bool:
        return self.amount < 0


def total(amounts: list[Money], currency: str = "GBP") -> Money:
    """Sum a list of Money values (an empty list sums to zero)."""
    result = Money.zero(currency)
    for amount in amounts:
        result = result + amount
    return result
