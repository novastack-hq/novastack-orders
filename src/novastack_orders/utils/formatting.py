"""Turning values into text for receipts, emails and the CLI."""

from __future__ import annotations

from collections.abc import Sequence

from novastack_orders.domain.money import Money

CURRENCY_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}


def format_price(amount: Money) -> str:
    """Format money for customers, e.g. ``£9.90`` or ``-£1.25``."""
    rounded = amount.rounded()
    symbol = CURRENCY_SYMBOLS.get(rounded.currency, rounded.currency + " ")
    sign = "-" if rounded.is_negative() else ""
    return f"{sign}{symbol}{abs(rounded.amount):.2f}"


def pluralise(count: int, singular: str, plural: str | None = None) -> str:
    """Count plus noun: ``pluralise(3, "item")`` is ``"3 items"``."""
    word = singular if count == 1 else (plural or singular + "s")
    return f"{count} {word}"


def format_table(rows: Sequence[Sequence[str]], right_align_last: bool = True) -> str:
    """Lay out rows of strings as fixed-width columns."""
    if not rows:
        return ""
    widths = [max(len(row[col]) for row in rows) for col in range(len(rows[0]))]
    lines = []
    for row in rows:
        cells = []
        for col, cell in enumerate(row):
            last = col == len(row) - 1
            cells.append(
                cell.rjust(widths[col])
                if last and right_align_last
                else cell.ljust(widths[col])
            )
        lines.append("  ".join(cells).rstrip())
    return "\n".join(lines)
