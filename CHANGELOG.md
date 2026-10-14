# Changelog

All notable changes are listed here. Format:
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- The month-end report is fast again: each customer's first order is
  found in one pass, and the menu is read once (ORD-361).
- The loyalty discount is applied once per basket, not once per category (ORD-317).

### Added
- The month-end report lists the five top customers by spend (ORD-362).
- The month-end report shows new customers and repeat orders (ORD-355).

## [1.3.0] - 2026-09-14

### Changed
- Category subtotals and the loyalty discount are calculated in a single pass
  over the basket, and the breakdown now reports subtotals per category (ORD-301).

### Added
- Month-end sales report for Finance: `novastack report` (ORD-344).
- Integration tests for a full checkout against SQLite (ORD-296).

## [1.2.0] - 2026-08-03

### Added
- Line-level refunds for collected orders, with discounts shared fairly across
  lines so refunds always add up to what was paid (ORD-284).
- Confirmation, ready and cancellation emails (ORD-271).

## [1.1.0] - 2026-06-22

### Added
- Student discount, 10% Monday to Friday (ORD-245).
- Loyalty points and automatic tier upgrades (ORD-238).

### Fixed
- Halfpennies are now rounded up, matching the tills (ORD-251).

## [1.0.0] - 2026-05-11

### Added
- Menu, baskets, meal deal pricing, loyalty discount, VAT on receipts.
- Checkout with the payment gateway; in-memory and SQLite storage.
- `novastack` command-line interface.
