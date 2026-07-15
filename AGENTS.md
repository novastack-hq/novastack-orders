# AGENTS.md

Instructions for AI coding agents (GitHub Copilot, Claude Code, Codex and
others) working in this repository. Humans: see `CONTRIBUTING.md`.

## Project

NovaStack Orders is a Python 3.12 command-line ordering service. Code lives in
`src/novastack_orders/`, tests in `tests/`. Read `docs/architecture.md` before
changing more than one package.

## Commands

- Install / update the environment: `uv sync`
- Run all tests: `uv run pytest`
- Run the fast tests: `uv run pytest -m smoke`
- Lint and format: `uv run ruff check --fix .` then `uv run ruff format .`
- Type check: `uv run mypy`

Run the tests for the code you changed, and say which ones you ran. Never
claim tests pass without running them.

## Rules

1. **Money is `Money` (Decimal), never `float`.** See `docs/adr/0002-money-as-decimal.md`.
2. **Respect the layers.** `domain/` must not import from `services/` or
   `adapters/`. Services receive adapters through `__init__`.
3. **Type hints on every function signature.** `pricing/` is checked strictly by mypy.
4. **Google-style docstrings** for public functions and classes. Describe only
   behaviour the code actually has.
5. **Tests:** pytest functions (not unittest classes), named
   `test_<behaviour>`, using the builders in `tests/factories.py`. Put unit
   tests in the folder that mirrors the module under `tests/unit/`.
6. **Never edit or delete an existing test to make it pass.** If you think a
   test is wrong, stop and explain why.
7. **Don't add dependencies** to `pyproject.toml` without being asked.
8. Keep changes small and focused on the ticket. Reference the ticket ID
   (e.g. `ORD-317`) in commit messages.
