import pytest

from novastack_orders.pricing.rounding import allocate, round_pence
from tests.factories import gbp


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1.234", "1.23"), ("1.235", "1.24"), ("1.2350001", "1.24"), ("0.005", "0.01")],
)
def test_round_pence(raw, expected):
    assert round_pence(gbp(raw)) == gbp(expected)


def test_allocate_in_proportion():
    assert allocate(gbp("0.30"), [gbp("1.00"), gbp("2.00")]) == [
        gbp("0.10"),
        gbp("0.20"),
    ]


def test_allocate_gives_leftover_pennies_to_largest_remainders():
    assert allocate(gbp("1.00"), [gbp("1"), gbp("1"), gbp("1")]) == [
        gbp("0.34"),
        gbp("0.33"),
        gbp("0.33"),
    ]


def test_allocate_nothing_to_nobody():
    assert allocate(gbp("1.00"), []) == []


def test_allocate_with_zero_weights_puts_it_all_on_the_first_line():
    assert allocate(gbp("0.50"), [gbp("0"), gbp("0")]) == [gbp("0.50"), gbp("0.00")]


@pytest.mark.smoke
def test_allocation_always_sums_to_the_amount():
    weights = [gbp(p) for p in ["5.20", "2.10", "1.60", "1.80", "2.40", "0.95", "6.80"]]
    shares = allocate(gbp("0.81"), weights)
    assert len(shares) == 7
    assert sum(s.pence for s in shares) == 81


@pytest.mark.parametrize("amount", ["0.01", "0.07", "1.00", "3.33", "9.99"])
def test_allocation_sums_for_many_amounts(amount):
    weights = [gbp("1.10"), gbp("2.20"), gbp("3.30")]
    assert sum(s.pence for s in allocate(gbp(amount), weights)) == gbp(amount).pence
