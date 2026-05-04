# Contributing to NovaStack Orders

## The workflow

1. **Every change starts with an issue.** Find it on the team's Project board,
   assign it to yourself and move it to *In progress*.
2. **Branch from the issue** (issue sidebar → *Development* → *Create a
   branch*), or from the command line:

   | Kind of work | Branch name |
   |---|---|
   | Bug fix | `fix/ORD-317-double-discount` |
   | New feature | `feature/ORD-330-bulk-discount` |
   | Tidy-up, docs, tooling | `chore/ORD-335-update-ruff` |

3. **Reproduce first.** For a bug, write (or un-skip) a failing test before you
   fix anything.
4. **Make small commits** that each do one thing (see *Commit messages*).
5. **Run the checks** before pushing:

   ```bash
   uv run pytest -m smoke        # seconds
   uv run pytest                 # everything
   uv run ruff check . && uv run ruff format --check .
   uv run mypy
   ```

6. **Push and open a pull request** using the template. CODEOWNERS adds the
   right reviewers. Link the issue with `Fixes #<number>` so it closes on merge.
7. Move the card to *In review*. After approval and green CI, squash-merge.

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/) with the
ticket ID at the end:

```text
fix(pricing): apply loyalty discount once per basket (ORD-317)

The ORD-301 refactor moved the loyalty discount inside the category loop,
so baskets with several categories were discounted once per category.
Apply it once, after promotions, as the pricing pipeline describes.
```

- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`.
- The summary line is imperative ("apply", not "applied"), under 72 characters.
- The body explains **why**, not what (the diff shows what).

## Code style

- Ruff formats and lints on save in VS Code (settings are committed in `.vscode/`).
- Type hints on every function. `pricing/` must pass `mypy` strictly.
- Money is always `Money`, never `float`.
- Keep `domain/` free of I/O; see `docs/architecture.md`.

## Tests

- Mirror the source tree: `src/novastack_orders/pricing/tax.py` →
  `tests/unit/pricing/test_tax.py`.
- Build data with `tests/factories.py`; shared fixtures live in `tests/conftest.py`.
- Mark critical-path tests `@pytest.mark.smoke` (keep the smoke tier under ~20
  tests) and tests that touch SQLite or a whole checkout `@pytest.mark.integration`.
- A known bug may be captured with `@pytest.mark.xfail(strict=True, reason="ORD-…")`
  until it's fixed. `strict=True` makes the test fail loudly once the bug is
  fixed, reminding you to remove the marker.

## Definition of done

- [ ] Tests cover the change, including the edge cases in the ticket
- [ ] All checks above pass locally
- [ ] Docs, `CHANGELOG.md` (under *Unreleased*) and docstrings updated
- [ ] PR links the issue and has been approved by a code owner
