import pytest

from core.vericlose.domain.money import Money


@pytest.mark.parametrize("bad_amount", [-1, 10.5, "100", True, None])
def test_money_rejects_invalid_minor_amounts(bad_amount: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        Money(amount_minor=bad_amount, currency="INR")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_currency", ["", "IN", "RUPEE", "12R", None])
def test_money_rejects_invalid_currency_codes(bad_currency: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        Money(amount_minor=100, currency=bad_currency)  # type: ignore[arg-type]


def test_money_normalizes_currency() -> None:
    assert Money(amount_minor=1250, currency=" inr ").currency == "INR"


def test_money_arithmetic_is_exact_and_currency_safe() -> None:
    assert Money(1000, "INR").add(Money(250, "INR")) == Money(1250, "INR")
    assert Money(1000, "INR").subtract(Money(250, "INR")) == Money(750, "INR")
    with pytest.raises(ValueError, match="currency mismatch"):
        Money(1000, "INR").add(Money(1000, "USD"))
    with pytest.raises(ValueError, match="negative"):
        Money(100, "INR").subtract(Money(101, "INR"))


def test_large_paise_value_remains_exact() -> None:
    amount = 9_999_999_999_999_999
    assert Money(amount).amount_minor == amount
