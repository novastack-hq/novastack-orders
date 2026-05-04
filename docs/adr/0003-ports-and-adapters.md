# ADR 0003: Ports and adapters (layered architecture)

- **Status:** Accepted (2026-05-04)
- **Deciders:** Tom Okafor, Priya Shah, Mei Lin

## Context

The first prototype mixed SQL, pricing and printing in one module. Pricing
couldn't be tested without a database, and switching payment provider would
have meant touching every file.

## Decision

- Business rules live in `domain/`, `pricing/` and `loyalty/`, with no I/O.
- The outside world is reached through abstract interfaces ("ports") in
  `adapters/` (`OrderRepository`, `PaymentGateway`, `EmailSender`), with
  concrete implementations ("adapters") beside them.
- Services receive adapters in their constructor. Only `cli.py` and the
  tests choose which concrete adapters to use.

## Consequences

- Most tests run in memory in milliseconds; only `tests/integration/` touches SQLite.
- Adding a real payment provider means one new class implementing `PaymentGateway`.
- More files and one level of indirection: use *Go to Implementations*
  (`Ctrl+F12` / `Cmd+F12`) to jump from an interface to its adapters.
