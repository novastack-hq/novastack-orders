---
name: "Lab 2 Medium: ORD-330 bulk discount"
about: Lecture 2 Medium lab ticket (start branch lab2/medium-start)
title: "ORD-330: Bulk discount for office orders"
labels: enhancement
---

**Requested by:** Sales, via Priya Shah  **Priority:** P3  **Area:** pricing

## The feature

Offices order lunch for whole teams. Give them a bulk discount:

- **10% off** any basket line with **10 or more** of the same item;
- **15% off** a line with **20 or more**;
- bulk discount is a *promotion*: it's applied with the meal deal, before
  loyalty and student discounts;
- it appears on receipts as "Bulk discount" with code `BULK`.

Implement `bulk_discount(basket)` and the `BulkDiscount` rule in
`src/novastack_orders/pricing/discounts/bulk.py`, and add the rule to
`PriceCalculator.default()` and `cli.build_calculator`.

## Also on this branch

- `test_line_refunds_add_up_for_a_team_order` is failing after a teammate's
  change. Find out why with a **conditional breakpoint** and a **logpoint**.
- Merge `feature/ORD-329-currency` into your branch; it conflicts with a
  formatting change already here. Keep both behaviours.
- Rename the badly named `calc` function to `calculate_line_total` everywhere.

## Your tasks

Start from **`lab2/medium-start`**; name your branch `lab2/medium`. Full
instructions are in the Lecture 2 Medium lab guide.

- [ ] Assign this issue to yourself and create your branch from it
- [ ] `bulk_discount` implemented, with at least 6 parametrised test cases and a fixture in `conftest.py`
- [ ] Rounding bug found (logpoint output in `DEBUG_NOTES.md`) and fixed
- [ ] `feature/ORD-329-currency` merged, conflict resolved
- [ ] `calc` renamed to `calculate_line_total` (F2)
- [ ] `AI_LOG.md` filled in
- [ ] `uv run tools/check_lab.py medium` prints all PASS
