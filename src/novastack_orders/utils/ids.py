"""Identifier generation for orders and payments."""

from __future__ import annotations

import itertools
import secrets


class SequentialIds:
    """Predictable IDs such as ``ORD-000042``: easy to read in logs and tests."""

    def __init__(self, prefix: str = "ORD", start: int = 1) -> None:
        self._prefix = prefix
        self._counter = itertools.count(start)

    def next(self) -> str:
        return f"{self._prefix}-{next(self._counter):06d}"


def random_reference(prefix: str = "PAY") -> str:
    """An unguessable reference for payment records."""
    return f"{prefix}-{secrets.token_hex(6).upper()}"
