# ADR 0004: Test tiers with pytest markers

- **Status:** Accepted (2026-09-01)
- **Deciders:** Dan Hughes

## Context

The suite passed 200 tests. Running everything on every push wasted CI
minutes and slowed feedback, but running nothing meant bugs reached `main`.

## Decision

Three tiers, selected with pytest markers registered in `pyproject.toml`
(`--strict-markers`, so a typo fails):

| Tier | Marker | Target size | Runs |
|---|---|---|---|
| Smoke | `@pytest.mark.smoke` | ~20 tests, under 5 seconds | Every push |
| Unit | (none) | the rest of `tests/unit/` | Before pushing; on pull requests |
| Integration | `@pytest.mark.integration` | SQLite and end-to-end | Pull requests to `main`; nightly |

## Consequences

- Developers run `uv run pytest -m smoke` constantly and the full suite before pushing.
- Someone must keep the smoke tier small and meaningful; QA reviews it each release.
