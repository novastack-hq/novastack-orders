---
name: "Lab 2 Beginner: ORD-341 refund but no cancellation"
about: Lecture 2 Beginner lab ticket (start branch lab2/beginner-start)
title: "ORD-341: Refund issued when cancelling a ready order, but the order isn't cancelled"
labels: bug
---

**Reported by:** Front-of-house, via Dan Hughes (QA)  **Priority:** P2  **Area:** services

## What happened

A customer asked to cancel an order the kitchen had already marked **ready**.
The till showed an error, but the customer's card was **refunded anyway** and
the order still shows as *ready*. Ready orders are not meant to be cancellable.

Dan also notes that the last commit on this branch left a pile of Ruff
warnings in `services/`.

## Your tasks

Create your branch **`lab2/beginner`** from **`lab2/beginner-start`** (not from
`main`). Full instructions are in the Lecture 2 Beginner lab guide.

- [ ] Assign this issue to yourself and create your branch from it
- [ ] Answer the navigation questions in `ANSWERS.md`
- [ ] Clear every Ruff finding in `src/novastack_orders/services/`
- [ ] Find the bug with a breakpoint; record the value that gave it away in `ANSWERS.md`
- [ ] Fix it; `uv run pytest` is green
- [ ] Commit with a message that mentions this issue (`#<number>`) and push over SSH
- [ ] `uv run tools/check_lab.py beginner` prints all PASS
