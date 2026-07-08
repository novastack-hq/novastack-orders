# Onboarding: your first 15 minutes in this codebase

New to the team? Do this before touching any code. It works for any
professional codebase, not just this one.

## 1. Read the map (3 minutes)

1. `README.md`: what the system does and how to run it.
2. `docs/architecture.md`: the layers and the pricing pipeline.
3. Skim `docs/adr/`: *why* things are the way they are.

## 2. Run it (3 minutes)

```bash
uv run pytest -m smoke
uv run novastack quote data/samples/meal_deal_plus_drink.json --at 2026-10-07T12:30
```

## 3. Follow one request through the code (6 minutes)

Use the IDE, not scrolling:

| Step | VS Code (Windows/Linux · macOS) |
|---|---|
| Open the entry point | Quick Open `Ctrl+P` · `Cmd+P` → `cli.py` |
| Jump to a function by name | Go to Symbol in Workspace `Ctrl+T` · `Cmd+T` → `cmd_quote` |
| Follow a call | Go to Definition `F12`, or Peek `Alt+F12` · `Opt+F12` |
| Who calls this? | Find All References `Shift+F12` |
| Where am I? | Breadcrumbs (top of the editor) and the Outline view |
| Who changed this, and why? | GitLens inline blame, or Timeline view |

Follow `cmd_quote` → `PriceCalculator.calculate` → one discount rule.

## 4. Find the tests (3 minutes)

Tests mirror the source: `pricing/calculator.py` → `tests/unit/pricing/test_calculator.py`.
Open the **Testing** panel (beaker icon), run that file, and read one test.

---

## Setting up by hand

If you'd rather not run `scripts/setup.sh` / `setup.ps1`:

1. Install uv: <https://docs.astral.sh/uv/getting-started/installation/>
   (macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`;
   Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`).
2. In this folder: `uv sync` (installs Python 3.12 and the tools into `.venv`).
3. Create an SSH key and add it to GitHub, following GitHub's guide:
   <https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent>.
   Test with `ssh -T git@github.com`.
4. Point your clone at SSH: `git remote set-url origin git@github.com:<you>/novastack-orders.git`.
5. Check everything: `uv run tools/check_setup.py`.

**pip instead of uv?** `python -m venv .venv`, activate it
(macOS/Linux `source .venv/bin/activate`; Windows `.venv\Scripts\Activate.ps1`),
then `pip install -e . --group dev` (pip 25.1 or later).
