# Architecture

NovaStack Orders is a layered application ("ports and adapters", see
[ADR 0003](adr/0003-ports-and-adapters.md)). Dependencies only point
**inwards**: the CLI uses services, services use the domain and *interfaces*
for the outside world, and the domain uses nothing but itself.

```text
            +------------------------------------------------+
            |  cli.py   (argparse; builds everything, prints) |
            +------------------------+-----------------------+
                                     |
            +------------------------v-----------------------+
            |  services/  checkout, orders, receipts, emails |
            +-----+-----------------+------------------+-----+
                  |                 |                  |
     +------------v---+   +---------v--------+  +------v-------------------+
     |  pricing/      |   |  loyalty/        |  |  adapters/ (interfaces)  |
     |  calculator,   |   |  points, tiers   |  |  repositories: memory,   |
     |  discounts,    |   |                  |  |    SQLite                |
     |  rounding, VAT |   |                  |  |  payments: fake gateway  |
     +------------+---+   +---------+--------+  |  notifications: email    |
                  |                 |           +------+-------------------+
            +-----v-----------------v------------------v-----+
            |  domain/  Money, Menu, Basket, Customer, Order |
            +------------------------------------------------+
            utils/ (dates, formatting, ids) can be used by any layer
```

## Rules

- `domain/` has no I/O and imports nothing from `services/` or `adapters/`.
- Services get their adapters through `__init__` (dependency injection), so
  tests pass in fakes from `adapters/` or `tests/conftest.py`.
- Only `cli.py` (and tests) decide which concrete adapters to use.

## What happens on `novastack checkout`

1. `cli.cmd_checkout` loads settings (`config.py`), the menu and customers
   (`data/`), and builds the basket from the JSON file.
2. It wires a `CheckoutService` with the price calculator, repositories, fake
   payment gateway and email stub.
3. `CheckoutService.checkout`:
   1. checks trading hours (`utils/dates.store_is_open`);
   2. prices the basket (`PriceCalculator.calculate`, below);
   3. charges the card (`PaymentGateway.charge`, idempotent per order ID);
   4. works out loyalty points (`loyalty/points.points_earned`);
   5. saves the `Order`, updates the customer's points and tier;
   6. emails a confirmation with the receipt (`services/receipts.py`).

## Pricing pipeline

`pricing/calculator.PriceCalculator.calculate` applies, in this order:

1. **Subtotal**, category by category (`Basket.by_category`).
2. **Promotions**, e.g. the meal deal (`discounts/meal_deal.py`).
3. **Loyalty discount**, *once*, on the promoted total (`discounts/loyalty.py`).
4. **Student discount**, Monday to Friday, on what's left (`discounts/student.py`).
5. **Round** to pence and work out the **VAT** included (`rounding.py`, `tax.py`).

Each discount is rounded to pence as it's applied, so a receipt's lines always
add up to its total.

## Where things live

| Concept | Module |
|---|---|
| Money and rounding | `domain/money.py`, `pricing/rounding.py` |
| Menu items and categories | `domain/menu.py`, `data/menu.json` |
| Order lifecycle (status changes) | `domain/order.py` (`ALLOWED_TRANSITIONS`) |
| Discount rules | `pricing/discounts/` |
| Points and tiers | `loyalty/` |
| Month-end sales report | `services/reporting.py`, `data/orders/` |
| Settings | `config.py`, `config/*.toml` |
| Errors | `errors.py` |
