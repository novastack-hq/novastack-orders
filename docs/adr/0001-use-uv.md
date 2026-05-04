# ADR 0001: Use uv to manage Python and dependencies

- **Status:** Accepted (2026-05-02)
- **Deciders:** Tom Okafor, Priya Shah

## Context

New starters lost hours to "works on my machine" problems: different Python
versions, `pip install` into the wrong environment, and `requirements.txt`
files that didn't pin transitive dependencies. Half the team is on Windows.

## Decision

Use [uv](https://docs.astral.sh/uv/) for everything: `.python-version` pins
Python 3.12 (uv installs it), `pyproject.toml` lists dependencies (dev tools in
a `dev` dependency group), and the committed `uv.lock` pins every package for
every OS. Everyone runs tools through `uv run`.

## Consequences

- One install step for new starters; identical environments on every OS and in CI.
- `uv sync --locked` in CI fails if someone edits `pyproject.toml` without
  updating the lockfile.
- pip still works for anyone who needs it (`pip install -e . --group dev`),
  but the lockfile is only honoured by uv.
- uv is maintained by one company (Astral). If that becomes a problem, the
  project metadata is standard `pyproject.toml` and can move to another tool.
