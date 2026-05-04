# ADR 0002: Represent money with Decimal, never float

- **Status:** Accepted (2026-05-04)
- **Deciders:** Priya Shah

## Context

`0.1 + 0.2` is `0.30000000000000004` in floating point. Percentage discounts
and VAT produce fractions of a penny, and a till that's out by a penny a day
is out by pounds a year.

## Decision

All amounts are `domain.money.Money`, which wraps `decimal.Decimal`. Creating
`Money` from a `float`, or multiplying it by one, raises `TypeError`. Values
keep full precision until they're shown or charged, then round **half up**
to the penny (`Money.rounded`, `pricing.rounding.round_pence`), matching the
tills.

## Consequences

- Money is created from strings: `Money.of("4.50")`.
- JSON stores amounts as strings, not numbers.
- Discounts are rounded as they're applied so receipts add up (see
  `docs/architecture.md`).
