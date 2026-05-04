"""Settings, loaded from ``config/default.toml`` plus an optional overlay.

Set ``NOVASTACK_ENV=test`` (or any name) to merge ``config/<name>.toml`` over
the defaults. ``NOVASTACK_LOG_LEVEL`` overrides the logging level.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from pathlib import Path
from typing import Any

from novastack_orders.domain.money import Money
from novastack_orders.errors import ConfigError

# src/novastack_orders/config.py -> repository root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass(frozen=True, slots=True)
class Settings:
    vat_rate: Decimal
    meal_deal_price: Money
    student_rate: Decimal
    opening: time
    closing: time
    menu_path: Path
    customers_path: Path
    log_level: str


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` into a copy of ``base``."""
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}") from None
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


def load_settings(env: str | None = None, config_dir: Path = CONFIG_DIR) -> Settings:
    data = _read(config_dir / "default.toml")
    env = env if env is not None else os.environ.get("NOVASTACK_ENV", "")
    if env:
        data = _merge(data, _read(config_dir / f"{env}.toml"))
    try:
        pricing, store, files = data["pricing"], data["store"], data["data"]
        level = os.environ.get("NOVASTACK_LOG_LEVEL") or data["logging"]["level"]
        return Settings(
            vat_rate=Decimal(str(pricing["vat_rate"])),
            meal_deal_price=Money.of(str(pricing["meal_deal_price"])),
            student_rate=Decimal(str(pricing["student_rate"])),
            opening=time.fromisoformat(store["opening"]),
            closing=time.fromisoformat(store["closing"]),
            menu_path=PROJECT_ROOT / files["menu"],
            customers_path=PROJECT_ROOT / files["customers"],
            log_level=str(level).upper(),
        )
    except (KeyError, ValueError) as exc:
        raise ConfigError(f"Missing or invalid setting: {exc}") from exc
