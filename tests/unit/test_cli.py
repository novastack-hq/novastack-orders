import pytest

from novastack_orders.cli import main
from novastack_orders.config import PROJECT_ROOT

SAMPLES = PROJECT_ROOT / "data" / "samples"


@pytest.mark.smoke
def test_menu_lists_drinks(capsys):
    assert main(["menu", "--category", "drink"]) == 0
    out = capsys.readouterr().out
    assert "Cola" in out
    assert "Chicken wrap" not in out


def test_quote(capsys):
    assert (
        main(["quote", str(SAMPLES / "simple.json"), "--at", "2026-10-07T12:30"]) == 0
    )
    assert "TOTAL" in capsys.readouterr().out


def test_checkout_prints_a_receipt(capsys):
    args = ["checkout", str(SAMPLES / "student_lunch.json"), "--at", "2026-10-07T12:30"]
    assert main(args) == 0
    assert "Thank you!" in capsys.readouterr().out


def test_declined_card_is_reported_not_a_crash(capsys):
    args = [
        "checkout",
        str(SAMPLES / "simple.json"),
        "--card",
        "tok_declined",
        "--at",
        "2026-10-07T12:30",
    ]
    assert main(args) == 1
    assert "error: Payment" in capsys.readouterr().out


def test_points(capsys):
    assert main(["points", "23.40", "--tier", "silver"]) == 0
    assert capsys.readouterr().out.strip() == "84"


def test_customers(capsys):
    assert main(["customers"]) == 0
    assert "Riley Chen" in capsys.readouterr().out


def test_report(capsys):
    orders = PROJECT_ROOT / "tests" / "fixtures" / "orders_small.jsonl"
    assert main(["report", str(orders)]) == 0
    out = capsys.readouterr().out
    assert "Month-end sales report: orders_small" in out
