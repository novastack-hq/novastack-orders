"""Self-check for the Lecture 3 labs.

    uv run tools/check_lab3.py beginner
    uv run tools/check_lab3.py intermediate
    uv run tools/check_lab3.py advanced

Each check prints PASS, FAIL (with a hint) or SKIP. Run it as often as you
like: it only reads your work and runs the code; it never changes anything.

This is a learning aid, not an exam. You can read this file, and the expected
answers are in it if you look. Looking won't make you better at debugging.
Using the debugger will.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "src" / "novastack_orders"
SEPTEMBER = "data/orders/2026-09.jsonl"
OCTOBER_MTD = "data/orders/2026-10-mtd.jsonl"
MARCH = "data/orders/2026-03.jsonl"

results: list[str] = []


# ------------------------------------------------------------------ output
def record(passed: bool | None, check: str, hint: str = "") -> None:
    """passed=None means 'couldn't check here' (SKIP: doesn't fail the lab)."""
    status, colour = {
        True: ("PASS", "32"),
        False: ("FAIL", "31"),
        None: ("SKIP", "33"),
    }[passed]
    print(f"[\033[{colour}m{status}\033[0m] {check}")
    if hint and passed is not True:
        for line in textwrap.wrap(hint, 74):
            print(f"       {line}")
    results.append(status)


def heading(text: str) -> None:
    print(f"\n\033[1m{text}\033[0m")


# ------------------------------------------------------------------ running things
def sh(*cmd: str, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout
    )


def run_py(code: str, timeout: int = 60) -> tuple[bool, str]:
    """Run Python in a fresh process (so a crash or a hang can't stop the checker).

    Returns (finished without error, output). Output is the last line of stdout,
    or the last line of the error.
    """
    try:
        result = sh(sys.executable, "-c", textwrap.dedent(code), timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout} s"
    if result.returncode:
        lines = result.stderr.strip().splitlines() or ["(no error message)"]
        return False, re.sub(r"\s*\(/[^)]*\)", "", lines[-1])  # drop long paths
    lines = result.stdout.strip().splitlines()
    return True, lines[-1] if lines else ""


def read(rel: str) -> str:
    path = REPO_ROOT / rel
    return path.read_text(encoding="utf-8") if path.exists() else ""


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ------------------------------------------------------------------ answer sheets
def answers(level: str) -> dict[str, str]:
    """Q1: ... lines from lab3/<LEVEL>.md -> {"Q1": "the answer"}."""
    found: dict[str, str] = {}
    for line in read(f"lab3/{level.upper()}.md").splitlines():
        match = re.match(r"^\s*\**([QRA]\d+)\b[^:]*:\**\s*(.*)$", line)
        if match:
            found[match.group(1)] = match.group(2).strip()
    return found


def check_answer(
    sheet: dict[str, str], key: str, question: str, ok: bool | None, hint: str
) -> None:
    given = sheet.get(key, "")
    if not given:
        record(
            False,
            f"{key} answered: {question}",
            f"write your answer after {key}'s colon in the answer sheet",
        )
        return
    record(ok, f"{key}: {question}", hint)


def has_all(text: str, *words: str) -> bool:
    low = text.lower()
    return all(w.lower() in low for w in words)


def filled(sheet: dict[str, str], keys: list[str], what: str) -> None:
    missing = [k for k in keys if len(sheet.get(k, "")) < 3]
    record(
        not missing,
        f"{what} ({', '.join(keys)}) answered",
        f"still empty: {', '.join(missing)}. These aren't marked right or wrong; writing them down is the point.",
    )


# ------------------------------------------------------------------ shared checks
def check_environment() -> None:
    venv = (REPO_ROOT / ".venv").resolve()
    inside = Path(sys.prefix).resolve() == venv
    record(
        inside,
        "Running in the project's .venv",
        "run the checker with 'uv run tools/check_lab3.py ...' from the project folder",
    )
    record(
        sys.version_info[:2] == (3, 12),
        f"Python 3.12 (you have {sys.version.split()[0]})",
        "run 'uv sync', which installs the version in .python-version",
    )


def check_quality() -> None:
    heading("Quality: the team's checks")
    tests = sh(sys.executable, "-m", "pytest", "-p", "no:cacheprovider")
    last = (tests.stdout.strip().splitlines() or ["?"])[-1]
    record(
        tests.returncode == 0,
        f"All tests pass ({last})",
        "run 'uv run pytest' and read the first failure. Don't edit a test to make it pass (AGENTS.md).",
    )
    ruff = sh(sys.executable, "-m", "ruff", "check", ".")
    fmt = sh(sys.executable, "-m", "ruff", "format", "--check", ".")
    record(
        ruff.returncode == 0 and fmt.returncode == 0,
        "Ruff: no lint errors, and formatted",
        "run 'uv run ruff check --fix .' then 'uv run ruff format .' (saving in VS Code formats for you)",
    )
    mypy = sh(sys.executable, "-m", "mypy")
    record(
        mypy.returncode == 0,
        "mypy: no type errors",
        "run 'uv run mypy' and fix what it reports (the red squiggles in VS Code are the same checks)",
    )
    leftovers = [
        str(p.relative_to(REPO_ROOT))
        for p in PKG.rglob("*.py")
        if re.search(
            r"^\s*(breakpoint\(\)|import pdb|pdb\.set_trace)",
            p.read_text(encoding="utf-8"),
            re.M,
        )
    ]
    record(
        not leftovers,
        "No breakpoint() or pdb left in the code",
        f"remove it from {', '.join(leftovers)}: in production it would freeze the program",
    )


REPORT_NUMBERS = """
import json, sys
from pathlib import Path
from novastack_orders.config import load_settings
from novastack_orders.services import reporting as r
rep = r.build_report("m", r.load_orders(Path(sys.argv[1] if len(sys.argv) > 1 else "{path}")), load_settings(env="").menu_path)
customers = getattr(rep, "customers", None)
customers = rep.new_customers if not isinstance(customers, int) else customers
repeat = getattr(rep, "repeat_orders", None)
repeat = rep.returning_customers if not isinstance(repeat, int) else repeat
print(json.dumps({{
    "orders": rep.order_count,
    "revenue": str(rep.revenue.amount),
    "customers": customers,
    "repeat": repeat,
    "discounts": {{k: str(v.amount) for k, v in sorted(rep.discounts_by_code.items())}},
    "categories": {{k.value: str(v.amount) for k, v in sorted(rep.revenue_by_category.items())}},
}}))
"""

SEPTEMBER_EXPECTED = {
    "orders": 16000,
    "revenue": "97072.80",
    "customers": 2660,
    "repeat": 13340,
    "discounts": {"LOYALTY": "13050.86", "MEALDEAL": "29135.80", "STUDENT": "2251.29"},
    "categories": {
        "dessert": "4730.10",
        "drink": "23161.80",
        "main": "83941.30",
        "side": "27162.70",
        "snack": "2514.85",
    },
}


def report_numbers(
    path: str, timeout: int = 60
) -> tuple[bool, dict[str, object] | str]:
    ok, out = run_py(REPORT_NUMBERS.format(path=path), timeout=timeout)
    if not ok:
        return False, out
    return True, json.loads(out)


def compare_report(
    path: str, expected: dict[str, object], check: str, hint: str
) -> None:
    ok, got = report_numbers(path)
    if not ok:
        record(False, check, f"the report failed: {got}. {hint}")
        return
    assert isinstance(got, dict)
    wrong = [k for k in expected if got.get(k) != expected[k]]
    detail = "; ".join(
        f"{k}: expected {expected[k]}, got {got.get(k)}" for k in wrong[:3]
    )
    record(not wrong, check, f"{detail}. {hint}")


NOT_QUADRATIC = """
from datetime import datetime, timedelta
from novastack_orders.config import load_settings
from novastack_orders.domain.money import Money
from novastack_orders.services import reporting as r
start = datetime(2026, 9, 1, 8)
orders = [
    r.OrderRecord(f"ORD-{{n}}", f"C{{n % {customers}}}", start + timedelta(seconds=n),
                  (r.ReportLine("M01", 1, Money.of("5.20")),), (), Money.of("5.20"))
    for n in range({orders})
]
rep = r.build_report("big", orders, load_settings(env="").menu_path)
print(rep.order_count)
"""


def check_scales(
    check: str, hint: str, orders: int = 40_000, customers: int = 20_000
) -> None:
    """A made-up month with lots of customers: linear code takes a second or two;
    code that loops over every order for every order (or every customer) takes
    many minutes, so it times out."""
    print(f"       (timing a made-up month of {orders:,} orders: up to 15 seconds)")
    ok, out = run_py(
        NOT_QUADRATIC.format(orders=orders, customers=customers), timeout=15
    )
    record(ok and out == str(orders), check, f"{out}. {hint}")


# ------------------------------------------------------------------ beginner
def beginner() -> None:
    sheet = answers("beginner")
    heading("Part 1: Set-up")
    check_environment()

    heading("Part 2: Find your way around")
    q1 = sheet.get("Q1", "")
    check_answer(
        sheet,
        "Q1",
        "STANDARD_RATE",
        "20" in q1 and "tax" in q1.lower(),
        "Go to Definition (F12) on STANDARD_RATE where PriceCalculator uses it. Give the value and the file.",
    )
    q2 = sheet.get("Q2", "")
    check_answer(
        sheet,
        "Q2",
        "who calls points_earned",
        has_all(q2, "cli", "checkout_service"),
        "right-click points_earned -> Find All References (Shift+F12). Name both files in src/.",
    )
    check_answer(
        sheet,
        "Q3",
        "what implements EmailSender",
        "stubemailsender" in sheet.get("Q3", "").lower(),
        "right-click the class name EmailSender -> Go to Implementations (Ctrl+F12 / Cmd+F12)",
    )
    check_answer(
        sheet,
        "Q4",
        "who added the loop, in which ticket",
        has_all(sheet.get("Q4", ""), "priya", "301"),
        "GitLens inline blame on the 'for category, lines in ...' line in PriceCalculator.calculate",
    )
    check_answer(
        sheet,
        "Q5",
        "what the report command calls",
        "build_report" in sheet.get("Q5", ""),
        "open cli.py, find cmd_report and Go to Definition on what it calls",
    )

    heading("Part 3: Refactor")
    uses = [
        str(p.relative_to(REPO_ROOT))
        for p in [*PKG.rglob("*.py"), *(REPO_ROOT / "tests").rglob("*.py")]
        if re.search(r"\bcalc\b", p.read_text(encoding="utf-8"))
    ]
    basket = read("src/novastack_orders/domain/basket.py")
    record(
        not uses and "def calculate_line_total(" in basket,
        "calc renamed to calculate_line_total everywhere",
        f"still 'calc' in: {', '.join(uses)}"
        if uses
        else "rename it with F2 (Rename Symbol), not Find and Replace",
    )
    receipts = read("src/novastack_orders/services/receipts.py")
    record(
        "def receipt_header(" in receipts and "receipt_header(order)" in receipts,
        "receipt_header extracted, and render_receipt calls it",
        "select the 'header = [...]' lines in render_receipt -> Ctrl+. / Cmd+. -> Extract method",
    )
    ok, out = run_py(RECEIPT_HEADER)
    record(ok and out == "ok", "Receipts look exactly the same as before", out)

    heading("Part 4: AI pair programming")
    ok, out = run_py(DISCOUNT_SUMMARY)
    record(
        ok and out == "ok",
        "discount_summary(order) in services/receipts.py does what its docstring says",
        f"{out}. Compare with Demo 2, Goals 5.1 and 5.2: one line per discount, and 'No discounts' when there are none.",
    )

    heading("Part 5: Debug and fix ORD-317")
    q6 = sheet.get("Q6", "").lower()
    check_answer(
        sheet,
        "Q6",
        "category at the second pause",
        "side" in q6,
        "hit count breakpoint (2) on 'if self._loyalty.applies(ctx):' in the unfixed code; look at category in Variables",
    )
    quote = sh(
        sys.executable,
        "-m",
        "novastack_orders",
        "quote",
        "data/samples/meal_deal_plus_drink.json",
        "--at",
        "2026-10-07T12:30",
    )
    total_line = next(
        (row for row in quote.stdout.splitlines() if row.startswith("TOTAL")), ""
    )
    record(
        "£7.29" in total_line,
        "Sam's meal deal quote is right (ORD-317 fixed)",
        f"got '{total_line.strip() or quote.stderr.strip()[-200:]}'. Work it out by hand first: £10.70, meal deal, then 10% Silver once.",
    )
    check_answer(
        sheet,
        "Q7",
        "Sam's total after your fix",
        "7.29" in sheet.get("Q7", ""),
        "run the Demo 1 quote command again after your fix",
    )
    calc_tests = read("tests/unit/pricing/test_calculator.py")
    record(
        "ORD-317: remove when fixed" not in calc_tests,
        "Dan's ORD-317 test is no longer marked xfail",
        "the bug is fixed, so the strict xfail now fails ('XPASS(strict)'). Remove that one decorator line, as its reason says. Don't change the test itself.",
    )

    heading("Part 6: Profile and fix ORD-361")
    compare_report(
        SEPTEMBER,
        SEPTEMBER_EXPECTED,
        "The September report's numbers are unchanged",
        "a speed-up must not change the output. Compare with the before.txt you saved.",
    )
    ok, out = run_py(MENU_READS)
    record(
        ok and out == "1",
        "The menu file is read once per report, not once per line",
        f"read {out} times for a 5-order report. Look at category_of in services/reporting.py.",
    )
    check_scales(
        "The report scales: 40,000 orders in seconds, not minutes",
        "is_returning_customer looks at every order, for every order. Work out each customer's first order once, before the loop.",
    )
    q8 = sheet.get("Q8", "").lower()
    check_answer(
        sheet,
        "Q8",
        "the biggest cumulative time",
        "is_returning_customer" in q8 or "genexpr" in q8,
        "sort cProfile by cumtime (-s cumtime) and look past main, cmd_report and build_report",
    )
    filled(sheet, ["Q9", "R1"], "Timings and reflection")

    check_quality()


RECEIPT_HEADER = """
from datetime import datetime
from novastack_orders.domain.money import Money
from novastack_orders.domain.order import Order
from novastack_orders.services.receipts import render_receipt
order = Order("ORD-9", "C002", (), Money.of("1.00"), (), Money.of("1.00"), Money.of("0.17"),
              datetime(2026, 10, 7, 12, 30), "pay_1", points_earned=3)
lines = render_receipt(order).splitlines()
assert lines[:3] == ["NovaStack Kitchen", "Order ORD-9   07/10/2026 12:30", "-" * 36], lines[:3]
assert lines[-3:] == ["-" * 36, "Points earned: 3", "Thank you!"], lines[-3:]
print("ok")
"""

DISCOUNT_SUMMARY = """
from datetime import datetime
from novastack_orders.domain.money import Money
from novastack_orders.domain.order import AppliedDiscount, Order
from novastack_orders.services.receipts import discount_summary
def order(*discounts):
    return Order("ORD-9", "C002", (), Money.of("10.70"), discounts, Money.of("7.29"),
                 Money.of("1.22"), datetime(2026, 10, 7, 12, 30), "pay_1")
two = order(AppliedDiscount("MEALDEAL", "Meal deal", Money.of("2.60")),
            AppliedDiscount("LOYALTY", "Silver 10%", Money.of("0.81")))
got = discount_summary(two)
assert got == "MEALDEAL -£2.60\\nLOYALTY -£0.81", f"for Sam's order: {got!r}"
got = discount_summary(order())
assert got == "No discounts", f"for an order with no discounts: {got!r}"
print("ok")
"""

MENU_READS = """
from pathlib import Path
from novastack_orders.config import load_settings
from novastack_orders.domain import menu
from novastack_orders.services import reporting as r
calls = 0
original = menu.Menu.from_records.__func__
def counting(cls, records):
    global calls
    calls += 1
    return original(cls, records)
menu.Menu.from_records = classmethod(counting)
r.build_report("m", r.load_orders(Path("tests/fixtures/orders_small.jsonl")), load_settings(env="test").menu_path)
print(calls)
"""


# ------------------------------------------------------------------ intermediate
OCTOBER_MTD_EXPECTED = {
    "orders": 10400,
    "revenue": "67766.77",
    "customers": 1696,
    "repeat": 8704,
}

UNSORTED = """
from datetime import datetime
from novastack_orders.config import load_settings
from novastack_orders.domain.money import Money
from novastack_orders.services import reporting as r
def o(n, customer, day):
    return r.OrderRecord(f"ORD-{n}", customer, datetime(2026, 10, day, 12),
                         (r.ReportLine("M01", 1, Money.of("5.20")),), (), Money.of("5.20"))
# The till's orders, then the app's (appended, so not in time order overall).
orders = [o(1, "C1", 5), o(2, "C2", 6), o(3, "C1", 9), o(4, "C1", 2), o(5, "C3", 3), o(6, "C2", 1)]
rep = r.build_report("m", orders, load_settings(env="test").menu_path)
customers = getattr(rep, "customers", None)
customers = rep.new_customers if not isinstance(customers, int) else customers
repeat = getattr(rep, "repeat_orders", None)
repeat = rep.returning_customers if not isinstance(repeat, int) else repeat
print(f"{customers} customers, {repeat} repeat orders")
"""

TOP_CUSTOMERS = """
from pathlib import Path
from novastack_orders.services import reporting as r
top = r.top_customers(r.load_orders(Path("{path}")))
print([(c, str(m.amount)) for c, m in top])
"""

SEPTEMBER_TOP = "[('C1670', '124.75'), ('C3605', '119.55'), ('C1213', '116.05'), ('C2925', '115.05'), ('C1894', '113.30')]"

TOP_SCALES = """
from datetime import datetime, timedelta
from novastack_orders.domain.money import Money
from novastack_orders.services import reporting as r
start = datetime(2026, 9, 1, 8)
orders = [
    r.OrderRecord(f"ORD-{n}", f"C{n % 30000}", start + timedelta(seconds=n),
                  (r.ReportLine("M01", 1, Money.of("5.20")),), (), Money.of(str(n % 97)))
    for n in range(60000)
]
print(len(r.top_customers(orders)))
"""

RENDER = """
import io, contextlib, hashlib
from pathlib import Path
from novastack_orders.cli import main
from novastack_orders.config import load_settings
from novastack_orders.services import reporting as r
out = io.StringIO()
with contextlib.redirect_stdout(out):
    main(["report", "{path}"])
cli = out.getvalue()
render = getattr(r, "render_report", None)
same = render is not None and cli == render(r.build_report("2026-09", r.load_orders(Path("{path}")), load_settings(env="").menu_path)) + "\\n"
print(hashlib.sha256(cli.encode()).hexdigest()[:16], "same" if same else ("missing" if render is None else "differs"))
"""

SEPTEMBER_REPORT_SHA = "1099782b9b55bf54"


def double_counted() -> set[str]:
    """Customers whose earliest order isn't the first one in the file."""
    first_seen: dict[str, str] = {}
    earliest: dict[str, str] = {}
    for line in read(OCTOBER_MTD).splitlines():
        if line.strip():
            raw = json.loads(line)
            first_seen.setdefault(raw["customer"], raw["at"])
            earliest[raw["customer"]] = min(
                earliest.get(raw["customer"], raw["at"]), raw["at"]
            )
    return {c for c in first_seen if first_seen[c] != earliest[c]}


def intermediate() -> None:
    sheet = answers("intermediate")
    heading("Set-up")
    check_environment()

    heading("ORD-364: customers counted twice")
    ok, out = run_py(UNSORTED)
    record(
        ok and out == "3 customers, 3 repeat orders",
        "Customers are counted once, even when the file isn't in time order",
        f"for six orders from three customers (app orders appended) the report says: {out}. Expected: 3 customers, 3 repeat orders.",
    )
    compare_report(
        OCTOBER_MTD,
        OCTOBER_MTD_EXPECTED,
        "The October month-to-date numbers are right",
        "the CRM says 1,696 different customers ordered",
    )
    compare_report(
        SEPTEMBER, SEPTEMBER_EXPECTED, "The September report hasn't changed", ""
    )
    q1 = sheet.get("Q1", "")
    check_answer(
        sheet,
        "Q1",
        "customers shown vs. actual",
        "1696" in q1.replace(",", ""),
        "give both numbers: the report's (before your fix) and the real count of different customers (Debug Console: len({o.customer_id for o in orders}))",
    )
    q2 = re.findall(r"C\d{4}", sheet.get("Q2", ""))
    check_answer(
        sheet,
        "Q2",
        "a customer counted twice",
        bool(q2) and q2[0] in double_counted(),
        "that customer isn't counted twice. Pause after first_order is built and find an order earlier than its customer's 'first' order.",
    )
    check_answer(
        sheet,
        "Q4",
        "pdb commands",
        bool(re.search(r"\b(b|break)\b", sheet.get("Q4", ""))),
        "include the pdb breakpoint command you used (b file:line, condition)",
    )
    filled(sheet, ["Q3"], "What ORD-363 assumed")

    heading("ORD-365: the report is slow again")
    print("       (timing a made-up month of 60,000 orders: up to 15 seconds)")
    ok, out = run_py(TOP_SCALES, timeout=15)
    record(
        ok and out == "5",
        "Top customers scales: 60,000 orders in seconds, not minutes",
        f"{out}. Profile it (pyinstrument) and look at what top_customers does for every order.",
    )
    ok, out = run_py(TOP_CUSTOMERS.format(path=SEPTEMBER), timeout=90)
    record(
        ok and out == SEPTEMBER_TOP,
        "Top customers for September are unchanged",
        f"got {out}. Faster must still be the same: same customers, same order, ties by customer ID.",
    )
    filled(sheet, ["Q5", "Q6"], "Profiling evidence")

    heading("ORD-367: clearer names, and a report you can test")
    fields = read("src/novastack_orders/services/reporting.py")
    renamed = re.search(r"^\s+customers: int", fields, re.M) and re.search(
        r"^\s+repeat_orders: int", fields, re.M
    )
    leftovers = [
        str(p.relative_to(REPO_ROOT))
        for p in [*PKG.rglob("*.py"), *(REPO_ROOT / "tests").rglob("*.py")]
        if re.search(
            r"\b(new_customers|returning_customers)\b", p.read_text(encoding="utf-8")
        )
    ]
    record(
        bool(renamed) and not leftovers,
        "MonthlyReport.new_customers -> customers, returning_customers -> repeat_orders",
        f"still the old names in: {', '.join(leftovers)}"
        if leftovers
        else "use F2 (Rename Symbol) on each field",
    )
    ok, out = run_py(RENDER.format(path=SEPTEMBER), timeout=90)
    digest, _, verdict = out.partition(" ")
    record(
        ok and verdict == "same",
        "render_report(report) in services/reporting.py returns what the CLI prints",
        f"{verdict or out}. Extract the printing in cmd_report into render_report(report) -> str, move it to services/reporting.py, and make cmd_report print(render_report(report)).",
    )
    record(
        ok and digest == SEPTEMBER_REPORT_SHA,
        "The report's text is exactly as before",
        "every line and every blank line must be the same. Compare 'novastack report' output before and after (VS Code: Compare Selected).",
    )

    heading("AI log")
    filled(sheet, ["A1", "A2", "A3"], "AI log")
    check_quality()


# ------------------------------------------------------------------ advanced
def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments and trailing commas (VS Code allows them)."""
    out, i, in_string = [], 0, False
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\":
                out.append(text[i + 1 : i + 2])
                i += 1
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
            out.append(ch)
        elif text.startswith("//", i):
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end < 0 else end + 2
            continue
        else:
            out.append(ch)
        i += 1
    return re.sub(r",(\s*[\]}])", r"\1", "".join(out))


def launch_configs() -> list[dict[str, object]] | str:
    text = read(".vscode/launch.json")
    if not text:
        return ".vscode/launch.json is missing"
    try:
        data = json.loads(strip_jsonc(text))
    except json.JSONDecodeError as exc:
        return f".vscode/launch.json isn't valid JSON: {exc}"
    configs = data.get("configurations", [])
    return [c for c in configs if isinstance(c, dict)]


TIMESTAMPS = """
from datetime import datetime
from novastack_orders.utils.dates import parse_timestamp
cases = {
    "2026-03-28T12:30": datetime(2026, 3, 28, 12, 30),          # old firmware: local time
    "2026-03-30T11:30:00Z": datetime(2026, 3, 30, 12, 30),      # UTC in summer (BST)
    "2026-01-15T12:30:00Z": datetime(2026, 1, 15, 12, 30),      # UTC in winter (GMT)
    "2026-07-01T09:30:00-02:00": datetime(2026, 7, 1, 12, 30),  # any offset
    "2026-10-25T00:30:00Z": datetime(2026, 10, 25, 1, 30),      # the night the clocks go back
}
for text, expected in cases.items():
    got = parse_timestamp(text)
    assert got == expected and got.tzinfo is None, f"parse_timestamp({text!r}) gave {got!r}, expected {expected!r}"
print("ok")
"""

MARCH_EXPECTED = {
    "orders": 12000,
    "revenue": "78002.66",
    "customers": 1996,
    "repeat": 10004,
}

STREAMING = """
import inspect, tracemalloc, sys
from pathlib import Path
from novastack_orders.config import load_settings
from novastack_orders.services import reporting as r
if not hasattr(r, "iter_orders"):
    sys.exit("services/reporting.py has no iter_orders(path)")
menu = load_settings(env="").menu_path
orders = r.iter_orders(Path("{path}"))
if isinstance(orders, (list, tuple)):
    sys.exit("iter_orders returns a list: make it a generator (yield)")
tracemalloc.start()
rep = r.build_report("2026-09", orders, menu)
peak = tracemalloc.get_traced_memory()[1]
print(rep.order_count, rep.new_customers, rep.returning_customers, round(peak / 1e6, 1))
"""


def advanced() -> None:
    sheet = answers("advanced")
    heading("Set-up")
    check_environment()

    heading("ORD-370: debug configurations for the team (.vscode/launch.json)")
    configs = launch_configs()
    if isinstance(configs, str):
        record(False, "launch.json can be read", configs)
        configs = []
    march = [
        c
        for c in configs
        if c.get("request") == "launch"
        and c.get("module") == "novastack_orders"
        and any("2026-03" in str(a) for a in c.get("args", []) or [])
        and "report" in (c.get("args") or [])
    ]
    record(
        bool(march),
        "A launch configuration runs the March report",
        'add one with "module": "novastack_orders" and "args": ["report", "data/orders/2026-03.jsonl"]',
    )
    env = march[0].get("env", {}) if march else {}
    record(
        isinstance(env, dict) and env.get("NOVASTACK_LOG_LEVEL") == "DEBUG",
        "...and turns the debug logs on for that run only",
        'add "env": {"NOVASTACK_LOG_LEVEL": "DEBUG"} to that configuration',
    )
    record(
        bool(march) and march[0].get("justMyCode") is False,
        "...and lets you step into library code",
        'add "justMyCode": false, so you can step into library code such as json.loads',
    )
    attach = [
        c
        for c in configs
        if c.get("request") == "attach"
        and isinstance(c.get("connect"), dict)
        and c["connect"].get("port") == 5678
    ]
    record(
        bool(attach),
        "An attach configuration connects to port 5678",
        'add one with "request": "attach" and "connect": {"host": "localhost", "port": 5678}',
    )

    heading("ORD-368: the March report crashes")
    ok, out = run_py(TIMESTAMPS)
    record(
        ok and out == "ok",
        "parse_timestamp always returns UK local time, without a time zone",
        out,
    )
    compare_report(
        MARCH,
        MARCH_EXPECTED,
        "The March report runs, with the right numbers",
        "convert in parse_timestamp, where the times come in, not where they're compared",
    )
    check_answer(
        sheet,
        "Q1",
        "the exception and where",
        has_all(sheet.get("Q1", ""), "TypeError"),
        "the exception's type, and the function it was raised in",
    )
    q2 = sheet.get("Q2", "")
    check_answer(
        sheet,
        "Q2",
        "the first order with a UTC time",
        first_utc_order() in q2,
        "a conditional breakpoint in load_orders with a condition on raw['at'] finds it; or run to the exception and look back",
    )
    filled(sheet, ["Q3"], "Raised vs. Uncaught")

    heading("ORD-369: a year of orders in 8 GB")
    ok, out = run_py(STREAMING.format(path=SEPTEMBER), timeout=90)
    parts = out.split()
    if not ok or len(parts) != 4:
        record(False, "iter_orders(path) streams orders into build_report", out)
    else:
        count, customers, repeat, peak = (
            int(parts[0]),
            int(parts[1]),
            int(parts[2]),
            float(parts[3]),
        )
        record(
            (count, customers, repeat) == (16000, 2660, 13340),
            "build_report works on an iterator (one pass)",
            f"got {count} orders, {customers} customers, {repeat} repeat orders: an iterator can only be read once",
        )
        record(
            peak < 8,
            f"Peak memory for September under 8 MB (yours: {peak} MB)",
            "something still keeps every order in memory: a list, or a second pass",
        )
    compare_report(
        SEPTEMBER, SEPTEMBER_EXPECTED, "The September report is unchanged", ""
    )
    q4, q5 = sheet.get("Q4", ""), sheet.get("Q5", "")
    filled(sheet, ["Q4", "Q5", "Q6", "Q7"], "Memory and timing evidence")
    if q4 and q5:
        before = re.findall(r"\d+(?:\.\d+)?", q4)
        after = re.findall(r"\d+(?:\.\d+)?", q5)
        record(
            bool(before and after) and float(before[-1]) > float(after[-1]),
            "Q4/Q5: peak memory went down",
            "write the before and after peaks in MB, from tracemalloc.get_traced_memory()",
        )

    heading("The Dev Container")
    if os.environ.get("NOVASTACK_IN_CONTAINER") == "1":
        smoke = sh(
            sys.executable, "-m", "pytest", "-m", "smoke", "-p", "no:cacheprovider"
        )
        record(
            smoke.returncode == 0,
            "Inside the Dev Container: the smoke tests pass",
            smoke.stdout[-300:],
        )
    else:
        record(
            None,
            "Inside the Dev Container",
            "run this checker again in the Dev Container's terminal (Reopen in Container) to tick this off",
        )
    filled(sheet, ["Q8"], "Container timing")
    check_quality()


def first_utc_order() -> str:
    for line in read(MARCH).splitlines():
        if line.strip():
            raw = json.loads(line)
            if raw["at"].endswith("Z") or "+" in raw["at"]:
                return str(raw["id"])
    return "?"


# ------------------------------------------------------------------ main
def main() -> int:
    parser = argparse.ArgumentParser(description="Self-check for the Lecture 3 labs.")
    parser.add_argument("level", choices=["beginner", "intermediate", "advanced"])
    args = parser.parse_args()
    if not (REPO_ROOT / f"lab3/{args.level.upper()}.md").exists():
        print(
            f"lab3/{args.level.upper()}.md isn't here. Are you on the lab3/{args.level} branch?"
        )
        print(f"    git switch -c lab3/{args.level} upstream/lab3/{args.level}-start")
        return 2
    print(f"Lecture 3 {args.level} lab: self-check")
    {"beginner": beginner, "intermediate": intermediate, "advanced": advanced}[
        args.level
    ]()
    passed, failed, skipped = (results.count(s) for s in ("PASS", "FAIL", "SKIP"))
    print(f"\n{passed} passed, {failed} to do, {skipped} skipped")
    if not failed:
        print("All done. Nice work. 🎉")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
