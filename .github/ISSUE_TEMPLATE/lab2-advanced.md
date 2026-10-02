---
name: "Lab 2 Advanced: ORD-350 reproducible environment and trustworthy tests"
about: Lecture 2 Advanced lab ticket (start branch lab2/advanced-start)
title: "ORD-350: Dev Container, signed commits, typed pricing, and real tests for points"
labels: enhancement
---

**Raised by:** Tom Okafor (platform) and Dan Hughes (QA)  **Priority:** P2

## Background

- New starters keep hitting "works on my machine" problems: prove our Dev
  Container gives an identical environment.
- Security wants **signed commits** on all branches.
- `pricing/` must pass mypy, but a recent change broke it.
- Someone deleted the tests for `loyalty/points.py`. We need a replacement
  suite that actually catches bugs, not one that just runs the code.

## Your tasks

Start from **`lab2/advanced-start`**; name your branch `lab2/advanced`. Full
instructions are in the Lecture 2 Advanced lab guide.

- [ ] Reopen the project in the Dev Container; run the checker inside it
- [ ] Set up SSH commit signing; at least 2 commits show **Verified** on GitHub
- [ ] `uv run mypy` passes
- [ ] Add a `launch.json` configuration that debugs the CLI with arguments and an environment variable
- [ ] Have an AI assistant write tests for `loyalty/points.py`, then improve them until they catch at least 7 of the checker's 8 seeded bugs
- [ ] Record the AI suite's score and your final score in `AI_LOG.md`
- [ ] `uv run tools/check_lab.py advanced` prints all PASS
