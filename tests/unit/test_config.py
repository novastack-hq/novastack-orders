from datetime import time
from decimal import Decimal

import pytest

from novastack_orders.config import load_settings
from novastack_orders.errors import ConfigError


def test_defaults():
    settings = load_settings(env="")
    assert settings.vat_rate == Decimal(20)
    assert (settings.opening, settings.closing) == (time(8, 0), time(22, 0))


def test_test_overlay_keeps_the_kitchen_open():
    settings = load_settings(env="test")
    assert settings.closing == time(23, 59, 59)
    assert settings.vat_rate == Decimal(20)  # not overridden, so the default


def test_env_var_selects_the_overlay(monkeypatch):
    monkeypatch.setenv("NOVASTACK_ENV", "test")
    assert load_settings().log_level == "ERROR"


def test_log_level_env_var_wins(monkeypatch):
    monkeypatch.setenv("NOVASTACK_LOG_LEVEL", "debug")
    assert load_settings(env="test").log_level == "DEBUG"


def test_missing_overlay_is_a_config_error():
    with pytest.raises(ConfigError, match="not found"):
        load_settings(env="staging")


def test_invalid_toml(tmp_path):
    (tmp_path / "default.toml").write_text("this is = = not toml", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_settings(env="", config_dir=tmp_path)
