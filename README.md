# NovaStack Orders

The ordering service behind **NovaStack Kitchen**, the campus food counter:
the menu, baskets, pricing and discounts, loyalty points, checkout, and order
tracking. It runs as a command-line app (`novastack`) backed by SQLite.

> **NovaStack is a fictional company** used to teach professional development
> practice. The codebase, its history and its tickets are realistic on purpose.

## Quick start

You need **VS Code** and **Git**. Everything else (uv, Python 3.12, the
project's tools, your SSH key) is set up by one script.

1. **Fork** this repository on GitHub. Untick *"Copy the `main` branch only"*.
2. Clone your fork and run the set-up script:

   ```bash
   git clone https://github.com/<your-username>/novastack-orders.git
   cd novastack-orders
   ./scripts/setup.sh                                          # macOS / Linux
   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1  # Windows
   ```

3. Open the folder in VS Code (`code .`), accept the recommended extensions,
   and check the status bar shows the `.venv` Python.

The script explains each step before it runs it, and asks before changing
anything outside this folder. To do it all by hand instead, follow
[docs/onboarding.md](docs/onboarding.md#setting-up-by-hand).

## Everyday commands

| Task | uv | pip / venv equivalent |
|---|---|---|
| Set up or update the environment | `uv sync` | `python -m venv .venv`, activate it, `pip install -e . --group dev` (pip 25.1+) |
| Run the app | `uv run novastack --help` | `novastack --help` (venv active) |
| Fast tests (every change) | `uv run pytest -m smoke` | `pytest -m smoke` |
| All tests | `uv run pytest` | `pytest` |
| Lint and format | `uv run ruff check --fix .` and `uv run ruff format .` | `ruff check --fix .` and `ruff format .` |
| Type check | `uv run mypy` | `mypy` |
| Add a dependency | `uv add <package>` | `pip install <package>` and edit `pyproject.toml` |

Try the app:

```bash
uv run novastack menu --category drink
uv run novastack quote data/samples/meal_deal_plus_drink.json --at 2026-10-07T12:30
uv run novastack checkout data/samples/student_lunch.json --at 2026-10-09T12:30
uv run novastack report data/orders/2026-09.jsonl     # Finance's month-end report
```

## Where to look

| You want to… | Read |
|---|---|
| Get your bearings in 15 minutes | [docs/onboarding.md](docs/onboarding.md) |
| Understand how the code is organised | [docs/architecture.md](docs/architecture.md) |
| Know why things are the way they are | [docs/adr/](docs/adr/) (architecture decision records) |
| Look up a term (tier, line, meal deal…) | [docs/glossary.md](docs/glossary.md) |
| Make a change and get it reviewed | [CONTRIBUTING.md](CONTRIBUTING.md) |
| See what changed in each release | [CHANGELOG.md](CHANGELOG.md) |
| Brief an AI coding assistant | [AGENTS.md](AGENTS.md) |

## Layout

```text
src/novastack_orders/
  domain/      pure data and rules: Money, Menu, Basket, Customer, Order
  pricing/     the price calculator, discounts, rounding, VAT
  loyalty/     points and tiers
  services/    use cases: checkout, order management, receipts, emails
  adapters/    storage (memory, SQLite), payments, email - behind interfaces
  utils/       dates, formatting, IDs
  cli.py       the `novastack` command
tests/
  unit/        mirrors src/ package by package
  integration/ SQLite and end-to-end checkout
config/        default.toml + per-environment overlays
data/          the menu, sample customers and sample baskets
docs/          architecture, onboarding, glossary, decision records
tools/         set-up and self-check scripts
```

## Tests

About 210 tests, in three tiers (see [ADR 0004](docs/adr/0004-test-tiers.md)):

| Tier | Run with | When |
|---|---|---|
| Smoke (~17, under a second) | `uv run pytest -m smoke` | Every change; every push in CI |
| Smoke + unit (~198) | `uv run pytest -m "not integration"` | Before you push |
| Integration (~12) | `uv run pytest -m integration` | On pull requests and nightly |

## Team

| Area | Owners (see `.github/CODEOWNERS`) |
|---|---|
| Pricing and discounts | Priya Shah, Dan Hughes |
| Loyalty | Mei Lin |
| Services, adapters, CLI | Tom Okafor |
| QA and test tooling | Dan Hughes |

Work is tracked in **GitHub Issues** on the team's Project board. Ticket IDs
look like `ORD-317`.
