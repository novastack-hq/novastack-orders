"""Self-check for the Lecture 2 labs.

    uv run tools/check_lab.py beginner
    uv run tools/check_lab.py medium
    uv run tools/check_lab.py advanced

Each check prints PASS or FAIL with a hint. Run it as often as you like; it
only reads your work (and GitHub's public API) and never changes anything.
``--offline`` skips the checks that need GitHub.

This is a learning aid, not an exam: you can read this file, and the hidden
tests and seeded bugs below are visible if you look. Looking won't make you
better at debugging. Using the debugger will.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
PKG = SRC / "novastack_orders"

results: list[tuple[str, str]] = []


# ------------------------------------------------------------------ output
def record(passed: bool | None, check: str, hint: str = "") -> None:
    """passed=None means 'couldn't check' (shown as SKIP, doesn't fail the lab)."""
    status, colour = {
        True: ("PASS", "32"),
        False: ("FAIL", "31"),
        None: ("SKIP", "33"),
    }[passed]
    print(f"[\033[{colour}m{status}\033[0m] {check}")
    if hint and passed is not True:
        print(f"       hint: {hint}")
    results.append((status, check))


def sh(
    *cmd: str, env: dict[str, str] | None = None, timeout: int = 300
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, **(env or {})},
    )


def pytest(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return sh(
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-o",
        "addopts=--strict-markers",
        "-q",
        *args,
        env=env,
    )


def read(rel: str) -> str:
    path = REPO_ROOT / rel
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ------------------------------------------------------------------ git and GitHub
def current_branch() -> str:
    return sh("git", "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def fork_owner_repo() -> tuple[str, str] | None:
    origin = sh("git", "remote", "get-url", "origin").stdout.strip()
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", origin)
    return (match.group(1), match.group(2)) if match else None


def github_token() -> str | None:
    """A token lifts GitHub's API limit from 60 to 5,000 requests an hour.

    Anonymous requests are shared by everyone behind the same network address
    (a whole computer lab on eduroam), so they run out quickly.
    """
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    if shutil.which("gh"):
        result = sh("gh", "auth", "token", timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None


def github(path: str) -> object | None:
    """GET from GitHub's API, or None if it can't be reached."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "novastack-check-lab",
    }
    token = github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def check_on_branch(expected: str) -> None:
    branch = current_branch()
    record(
        branch == expected,
        f"You're on your lab branch ({expected})",
        f"you're on '{branch}'. Create {expected} from the issue (start: {expected}-start)",
    )


def check_pushed(branch: str, offline: bool) -> None:
    if offline:
        record(None, "Branch pushed to your fork", "skipped (--offline)")
        return
    remote = sh("git", "ls-remote", "--heads", "origin", branch, timeout=60)
    remote_sha = remote.stdout.split()[0] if remote.stdout.strip() else ""
    local_sha = sh("git", "rev-parse", "HEAD").stdout.strip()
    if remote.returncode != 0:
        record(
            None,
            "Branch pushed to your fork",
            "couldn't reach your fork over SSH: run tools/check_setup.py",
        )
    else:
        record(
            remote_sha == local_sha,
            "Branch pushed to your fork, up to date",
            f"push it: git push -u origin {branch}"
            if not remote_sha
            else "you have commits that aren't pushed: git push",
        )


def check_issue_linked(ticket: str, offline: bool) -> None:
    """An issue for the ticket, assigned to you, mentioned (#n) in one of your commits."""
    if offline:
        record(
            None,
            f"{ticket} issue assigned to you and referenced in a commit",
            "skipped (--offline)",
        )
        return
    fork = fork_owner_repo()
    issues = (
        github(f"/repos/{fork[0]}/{fork[1]}/issues?state=all&per_page=100")
        if fork
        else None
    )
    if not isinstance(issues, list):
        record(
            None,
            f"{ticket} issue assigned to you and referenced in a commit",
            "couldn't reach GitHub's API, or its hourly limit for this network was "
            "used up. Try later, or set GH_TOKEN (see the lab guide). "
            "SKIP doesn't fail the lab.",
        )
        return
    owner = fork[0].lower()  # type: ignore[index]
    mine = [
        i
        for i in issues
        if ticket in i.get("title", "")
        and "pull_request" not in i
        and any(a["login"].lower() == owner for a in i.get("assignees", []))
    ]
    if not mine:
        record(
            False,
            f"{ticket} issue assigned to you and referenced in a commit",
            "enable Issues in your fork (Settings > Features), open the lab ticket from its "
            "template and assign it to yourself",
        )
        return
    numbers = {i["number"] for i in mine}
    log = sh("git", "log", "--format=%B", "-n", "50").stdout
    referenced = {int(n) for n in re.findall(r"#(\d+)", log)} & numbers
    record(
        bool(referenced),
        f"{ticket} issue assigned to you and referenced in a commit",
        f"mention the issue in a commit message, e.g. '(#{min(numbers)})'",
    )


# ------------------------------------------------------------------ shared checks
def check_all_tests() -> None:
    result = pytest()
    summary = (result.stdout.strip().splitlines() or ["no output"])[-1]
    record(
        result.returncode == 0,
        f"All tests pass ({summary})",
        "open the Testing panel, run everything, and debug the red tests",
    )


def check_ruff(path: str = ".") -> None:
    lint = sh(sys.executable, "-m", "ruff", "check", path)
    fmt = sh(sys.executable, "-m", "ruff", "format", "--check", path)
    count = re.search(r"Found (\d+) error", lint.stdout)
    record(
        lint.returncode == 0 and fmt.returncode == 0,
        f"Ruff is clean in {path}",
        (f"{count.group(1)} findings: " if count else "")
        + "open the Problems panel (Ctrl/Cmd+Shift+M); save to format; use the quick fixes",
    )


def check_mypy() -> None:
    result = sh(sys.executable, "-m", "mypy")
    errors = re.search(r"Found (\d+) error", result.stdout)
    record(
        result.returncode == 0,
        "mypy passes",
        (f"{errors.group(1)} errors; " if errors else "")
        + "run `uv run mypy` and read each error",
    )


def section_filled(text: str, heading: str) -> bool:
    """True if the markdown section under ``heading`` has real content (not just a comment)."""
    match = re.search(
        rf"^#+ {re.escape(heading)}[^\n]*\n(.*?)(?=^#+ |\Z)", text, re.M | re.S
    )
    if not match:
        return False
    body = re.sub(r"<!--.*?-->", "", match.group(1), flags=re.S).strip()
    return len(body) >= 15


# ------------------------------------------------------------------ beginner
def beginner(offline: bool) -> None:
    check_on_branch("lab2/beginner")
    check_issue_linked("ORD-341", offline)
    answers = read("ANSWERS.md")
    q1 = re.search(r"## Q1[^\n]*\n(.*?)(?=## Q2|\Z)", answers, re.S)
    q1_text = q1.group(1) if q1 else ""
    record(
        all(name in q1_text for name in ("receipts", "notification_service", "cli")),
        "Q1: every src/ file that calls format_price",
        "select format_price in formatting.py and press Shift+F12 (Find All References)",
    )
    record(
        bool(re.search(r"## Q2[^\n]*\n[^#]*FakePaymentGateway", answers)),
        "Q2: the class that implements PaymentGateway",
        "right-click PaymentGateway > Go to Implementations (Ctrl/Cmd+F12)",
    )
    record(
        bool(re.search(r"## Q3[^\n]*\n[^#]*domain/order\.py", answers)),
        "Q3: the file that defines ALLOWED_TRANSITIONS",
        "Ctrl/Cmd+T, type ALLOWED_TRANSITIONS; give the path, e.g. src/novastack_orders/...",
    )
    record(
        bool(re.search(r"## Q4[^\n]*\n[^#]*\bready\b", answers, re.I)),
        "Q4: what the debugger showed",
        "breakpoint at the top of OrderService.cancel; Debug Test; look at order.status and CANCELLABLE",
    )
    check_ruff("src/novastack_orders/services")
    check_all_tests()
    check_pushed("lab2/beginner", offline)


# ------------------------------------------------------------------ medium
HIDDEN_BULK_TESTS = """
import pytest
from novastack_orders.pricing.calculator import PriceCalculator
from novastack_orders.pricing.discounts.base import PricingContext
from novastack_orders.pricing.discounts.bulk import BulkDiscount, bulk_discount
from tests.factories import WEDNESDAY_LUNCH, gbp, make_basket, make_customer

@pytest.mark.parametrize(("qty", "expected"), [
    (9, "0.00"), (10, "1.20"), (19, "2.28"), (20, "3.60"), (35, "6.30"), (50, "9.00")])
def test_hidden_quantity_tiers(qty, expected):
    assert bulk_discount(make_basket(("D03", qty))).rounded() == gbp(expected)

def test_hidden_lines_judged_separately():
    basket = make_basket(("D03", 12), ("N01", 25), ("M01", 3), ("D01", 9))
    assert bulk_discount(basket).rounded() == gbp("5.00")

def test_hidden_rule_metadata():
    rule = BulkDiscount()
    assert (rule.code, rule.description) == ("BULK", "Bulk discount")
    assert not rule.applies(PricingContext(make_basket(("D03", 2)), make_customer(), WEDNESDAY_LUNCH))

def test_hidden_registered_in_default_calculator():
    result = PriceCalculator.default().calculate(make_basket(("D03", 12)), make_customer(), WEDNESDAY_LUNCH)
    assert "BULK" in result.discount_codes()
    assert result.total == gbp("12.96")

def test_hidden_bulk_before_loyalty():
    from novastack_orders.domain.customer import LoyaltyTier
    result = PriceCalculator.default().calculate(
        make_basket(("D03", 20)), make_customer(tier=LoyaltyTier.SILVER), WEDNESDAY_LUNCH)
    assert result.discount_codes() == ["BULK", "LOYALTY"]
    assert result.total == gbp("18.36")
"""

BULK_FIXTURE = re.compile(
    r"@pytest\.fixture[^\n]*\n(?:@[^\n]*\n)*def \w*bulk\w*\(", re.I
)


def medium(offline: bool) -> None:
    check_on_branch("lab2/medium")
    check_issue_linked("ORD-330", offline)

    with tempfile.TemporaryDirectory() as tmp:
        hidden = Path(tmp) / "test_hidden_bulk.py"
        hidden.write_text(HIDDEN_BULK_TESTS, encoding="utf-8")
        result = pytest(
            str(hidden), "--rootdir", str(REPO_ROOT), env={"PYTHONPATH": str(REPO_ROOT)}
        )
    record(
        result.returncode == 0,
        "bulk_discount meets the ORD-330 spec (hidden tests)",
        "re-read the ticket: 10+ of one item 10% off that line, 20+ 15% off; registered in "
        "PriceCalculator.default() and cli.build_calculator",
    )

    collected = pytest("--collect-only", "-k", "bulk").stdout
    param_ids = [
        line
        for line in collected.splitlines()
        if "bulk" in line.lower() and "[" in line
    ]
    record(
        len(param_ids) >= 6,
        f"At least 6 parametrised bulk test cases ({len(param_ids)} found)",
        "use @pytest.mark.parametrize with boundary values (9, 10, 19, 20 ...)",
    )
    record(
        bool(BULK_FIXTURE.search(read("tests/conftest.py"))),
        "A bulk fixture in tests/conftest.py",
        "add e.g. @pytest.fixture def bulk_office_basket(): ...",
    )

    markers = sh(
        "git",
        "grep",
        "-n",
        "-E",
        "^(<<<<<<<|=======|>>>>>>>)( |$)",
        "--",
        "src",
        "tests",
    )
    record(
        not markers.stdout.strip(),
        "No merge conflict markers left",
        "search for <<<<<<< and use the merge editor to finish resolving",
    )
    ord329 = next(
        (
            r
            for r in ("origin/feature/ORD-329-currency", "feature/ORD-329-currency")
            if sh("git", "rev-parse", "--verify", "--quiet", r).returncode == 0
        ),
        None,
    )
    merged = (
        ord329 is not None
        and sh("git", "merge-base", "--is-ancestor", ord329, "HEAD").returncode == 0
    )
    record(
        merged,
        "feature/ORD-329-currency is merged into your branch",
        "git merge origin/feature/ORD-329-currency, then resolve the conflicts",
    )
    both = sh(
        sys.executable,
        "-c",
        "from novastack_orders.domain.money import Money as M\n"
        "from novastack_orders.utils.formatting import format_price as f\n"
        "assert f(M.of('1234.5')) == '£1,234.50', f(M.of('1234.5'))\n"
        "assert f(M.of('1234.5'), show_code=True) == 'GBP 1,234.50'\n",
    )
    record(
        both.returncode == 0,
        "format_price keeps both behaviours (ORD-327 and ORD-329)",
        "after the merge, £1,234.50 and, with show_code=True, GBP 1,234.50",
    )

    leftover = sh("git", "grep", "-n", "-w", "calc", "--", "src", "tests")
    renamed = "def calculate_line_total" in read(
        "src/novastack_orders/domain/basket.py"
    )
    record(
        renamed and not leftover.stdout.strip(),
        "calc renamed to calculate_line_total everywhere",
        "put the cursor on calc in domain/basket.py and press F2",
    )

    notes = read("DEBUG_NOTES.md")
    record(
        all(
            section_filled(notes, h)
            for h in ("Conditional breakpoint", "Logpoint output", "Cause")
        ),
        "DEBUG_NOTES.md: breakpoint, logpoint output and cause filled in",
        "set a conditional breakpoint and a logpoint in OrderService.line_refunds",
    )
    log = read("AI_LOG.md")
    record(
        all(section_filled(log, h) for h in ("Prompt", "Accepted", "Corrected")),
        "AI_LOG.md: prompt, accepted and corrected filled in",
    )
    check_all_tests()
    check_ruff()
    check_mypy()
    check_pushed("lab2/medium", offline)


# ------------------------------------------------------------------ advanced
POINTS = "src/novastack_orders/loyalty/points.py"
POINTS_TESTS = "tests/unit/loyalty/test_points.py"
MUTANTS = [  # (what the seeded bug does, text in points.py, replacement)
    (
        "no-card customers get the bonus",
        "if tier is LoyaltyTier.NONE or amount_paid.amount <= 0:",
        "if amount_paid.amount <= 0:",
    ),
    (
        "pounds rounded instead of dropping pence",
        "amount_paid.amount.to_integral_value(rounding=ROUND_FLOOR)",
        'amount_paid.amount.to_integral_value(rounding="ROUND_HALF_UP")',
    ),
    (
        "half points rounded up",
        "MULTIPLIERS[tier]).to_integral_value(rounding=ROUND_FLOOR)",
        'MULTIPLIERS[tier]).to_integral_value(rounding="ROUND_HALF_UP")',
    ),
    (
        "bonus needs more than £20",
        "if amount_paid >= BIG_ORDER_THRESHOLD:",
        "if amount_paid > BIG_ORDER_THRESHOLD:",
    ),
    (
        "cap is 501",
        "return min(points, MAX_POINTS_PER_ORDER)",
        "return min(points, MAX_POINTS_PER_ORDER + 1)",
    ),
    (
        "Silver multiplier is x2",
        'LoyaltyTier.SILVER: Decimal("1.5"),',
        'LoyaltyTier.SILVER: Decimal("2"),',
    ),
    (
        "cap applied before the bonus",
        "    if amount_paid >= BIG_ORDER_THRESHOLD:\n        points += BIG_ORDER_BONUS\n"
        "    return min(points, MAX_POINTS_PER_ORDER)",
        "    points = min(points, MAX_POINTS_PER_ORDER)\n    if amount_paid >= BIG_ORDER_THRESHOLD:\n"
        "        points += BIG_ORDER_BONUS\n    return points",
    ),
    (
        "negative amounts not rejected",
        "amount_paid.amount <= 0:",
        "amount_paid.amount == 0:",
    ),
]


def mutation_score() -> tuple[int, list[str]] | None:
    """Run the student's points tests against each seeded bug. Returns (killed, survivors)."""
    original = (REPO_ROOT / POINTS).read_text(encoding="utf-8")
    killed, survivors = 0, []
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "src"
        shutil.copytree(SRC, copy)
        for description, old, new in MUTANTS:
            if old not in original:
                return None  # points.py has been edited; can't seed bugs reliably
            (copy / "novastack_orders/loyalty/points.py").write_text(
                original.replace(old, new, 1), encoding="utf-8"
            )
            result = pytest(POINTS_TESTS, "-x", env={"PYTHONPATH": str(copy)})
            if result.returncode != 0:
                killed += 1
            else:
                survivors.append(description)
    return killed, survivors


def strip_jsonc(text: str) -> str:
    """Turn VS Code's 'JSON with comments' into plain JSON.

    Drops // and /* */ comments (outside strings) and trailing commas.
    """
    out: list[str] = []
    i, in_string = 0, False
    while i < len(text):
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1 : i + 2])
                i += 1
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
            out.append(c)
        elif text.startswith("//", i):
            newline = text.find("\n", i)
            if newline == -1:
                break
            i = newline
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
            continue
        else:
            out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def check_launch_config() -> None:
    text = strip_jsonc(read(".vscode/launch.json"))
    try:
        configs = json.loads(text).get("configurations", [])
    except json.JSONDecodeError:
        record(
            False,
            "launch.json has a CLI debug config with args and env",
            "launch.json isn't valid JSON",
        )
        return
    good = [
        c
        for c in configs
        if c.get("type") == "debugpy"
        and c.get("args")
        and c.get("env")
        and (c.get("module") or c.get("program"))
    ]
    record(
        bool(good),
        "launch.json has a CLI debug config with args and env",
        'add a "debugpy" configuration with "module", "args" and "env" (e.g. NOVASTACK_LOG_LEVEL)',
    )


def check_signed_commits(offline: bool) -> None:
    fork = fork_owner_repo()
    if offline or not fork:
        record(
            None,
            "At least 2 commits on lab2/advanced show Verified on GitHub",
            "skipped",
        )
        return
    commits = github(
        f"/repos/{fork[0]}/{fork[1]}/commits?sha=lab2/advanced&per_page=30"
    )
    if not isinstance(commits, list):
        record(
            None,
            "At least 2 commits on lab2/advanced show Verified on GitHub",
            "couldn't read your branch from GitHub's API; push it, or try again later",
        )
        return
    verified = sum(
        1
        for c in commits
        if c.get("commit", {}).get("verification", {}).get("verified")
    )
    record(
        verified >= 2,
        f"At least 2 commits on lab2/advanced show Verified on GitHub ({verified})",
        "git config gpg.format ssh, user.signingkey, commit.gpgsign true; add the key on GitHub as a Signing Key",
    )


def advanced(offline: bool) -> None:
    check_on_branch("lab2/advanced")
    in_container = bool(
        os.environ.get("NOVASTACK_IN_CONTAINER")
        or os.environ.get("REMOTE_CONTAINERS")
        or os.environ.get("CODESPACES")
    )
    record(
        in_container,
        "Running inside the Dev Container",
        "Command Palette > Dev Containers: Reopen in Container, then run this checker there",
    )
    check_issue_linked("ORD-350", offline)
    check_mypy()
    check_launch_config()

    tests_exist = (REPO_ROOT / POINTS_TESTS).exists()
    passes = tests_exist and pytest(POINTS_TESTS).returncode == 0
    record(
        passes,
        f"{POINTS_TESTS} exists and passes on the real code",
        "ask your AI assistant for tests of loyalty/points.py, save them there, run them",
    )
    if passes:
        score = mutation_score()
        if score is None:
            record(
                False,
                "Mutation score",
                f"don't change {POINTS}; restore it with git checkout",
            )
        else:
            killed, survivors = score
            record(
                killed >= 7,
                f"Your tests catch {killed} of {len(MUTANTS)} seeded bugs (need 7)",
                "still missed: " + "; ".join(survivors),
            )
    log = read("AI_LOG.md")
    record(
        bool(re.search(r"AI suite:\s*\d/8", log))
        and bool(re.search(r"Final suite:\s*\d/8", log)),
        "AI_LOG.md records the AI suite's and your final mutation scores",
        "run the checker after saving the AI's tests (before improving them) and note the score",
    )
    check_signed_commits(offline)
    check_all_tests()
    check_ruff()
    check_pushed("lab2/advanced", offline)


# ------------------------------------------------------------------ main
def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description="Lecture 2 lab self-check")
    parser.add_argument("tier", choices=["beginner", "medium", "advanced"])
    parser.add_argument(
        "--offline", action="store_true", help="skip checks that need GitHub"
    )
    args = parser.parse_args()
    print(f"Lecture 2 {args.tier} lab check\n")
    {"beginner": beginner, "medium": medium, "advanced": advanced}[args.tier](
        args.offline
    )

    failed = [c for s, c in results if s == "FAIL"]
    passed = sum(1 for s, _ in results if s == "PASS")
    print(
        f"\n{passed} passed, {len(failed)} failed, {len(results) - passed - len(failed)} skipped."
    )
    if not failed:
        print("\033[32mLab complete.\033[0m Close the issue and move the card to Done.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
