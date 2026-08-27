"""Exact monetary magnitude represented in integer minor units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    """A non-negative magnitude; direction is modeled separately on financial events."""

    amount_minor: int
    currency: str = "INR"

    def __post_init__(self) -> None:
        # bool subclasses int in Python and must be rejected explicitly.
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise TypeError("amount_minor must be an integer, not bool or float")
        if self.amount_minor < 0:
            raise ValueError("amount_minor cannot be negative")
        if not isinstance(self.currency, str):
            raise TypeError("currency must be a string")

        normalized = self.currency.strip().upper()
        if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
            raise ValueError("currency must be a three-letter ASCII code")
        object.__setattr__(self, "currency", normalized)

    def add(self, other: Money) -> Money:
        self._require_same_currency(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def subtract(self, other: Money) -> Money:
        """Subtract magnitudes without silently creating an invalid negative Money."""

        self._require_same_currency(other)
        if other.amount_minor > self.amount_minor:
            raise ValueError("Money subtraction cannot produce a negative magnitude")
        return Money(self.amount_minor - other.amount_minor, self.currency)

    def _require_same_currency(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError("money arithmetic requires another Money value")
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} != {other.currency}")
