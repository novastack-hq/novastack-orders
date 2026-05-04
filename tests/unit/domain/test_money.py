from decimal import Decimal

import pytest

from novastack_orders.domain.money import Money, total


@pytest.mark.smoke
def test_adding_money_is_exact():
    assert Money.of("0.10") + Money.of("0.20") == Money.of("0.30")


def test_subtraction():
    assert Money.of("5.00") - Money.of("1.25") == Money.of("3.75")


def test_multiply_by_quantity():
    assert Money.of("1.60") * 3 == Money.of("4.80")


def test_multiply_works_both_ways_round():
    assert 3 * Money.of("1.60") == Money.of("4.80")


def test_float_is_rejected_when_creating():
    with pytest.raises(TypeError):
        Money(0.1)  # type: ignore[arg-type]


def test_float_is_rejected_when_multiplying():
    with pytest.raises(TypeError):
        Money.of("1.00") * 1.5  # type: ignore[operator]


def test_mixing_currencies_is_an_error():
    with pytest.raises(ValueError, match="Currency mismatch"):
        Money.of("1.00", "GBP") + Money.of("1.00", "EUR")


def test_percent():
    assert Money.of("8.10").percent(Decimal(10)) == Money.of("0.81")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0.004", "0.00"),
        ("0.005", "0.01"),  # halves round up, like a till
        ("0.015", "0.02"),
        ("2.675", "2.68"),
        ("-0.005", "-0.01"),
    ],
)
def test_rounded_rounds_halves_away_from_zero(raw, expected):
    assert Money.of(raw).rounded() == Money.of(expected)


def test_pence():
    assert Money.of("9.90").pence == 990


def test_from_pence():
    assert Money.from_pence(1234) == Money.of("12.34")


def test_comparisons():
    assert Money.of("1.00") < Money.of("1.01")
    assert max(Money.of("2"), Money.of("3")) == Money.of("3")


def test_zero_is_falsy():
    assert not Money.zero()
    assert Money.of("0.01")


def test_total_of_empty_list_is_zero():
    assert total([]) == Money.zero()


def test_total_sums_values():
    assert total([Money.of("1.10"), Money.of("2.20"), Money.of("3.30")]) == Money.of(
        "6.60"
    )
