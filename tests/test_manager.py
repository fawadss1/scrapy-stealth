from unittest.mock import patch

import pytest

from scrapy_stealth.config import config
from scrapy_stealth.engines.basic import BasicEngine
from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.turbo import TurboEngine
from scrapy_stealth.manager import EngineManager


class TestEngineManager:
    @pytest.fixture
    def manager(self):
        with (
            patch("scrapy_stealth.engines.basic.Client"),
            patch("scrapy_stealth.engines.turbo.Session"),
        ):
            yield EngineManager()

    def test_get_default_engine(self, manager):
        engine = manager.get(config.get("DEFAULT_ENGINE"))
        assert isinstance(engine, ScrapyEngine)

    def test_get_scrapy_engine(self, manager):
        engine = manager.get("scrapy")
        assert isinstance(engine, ScrapyEngine)

    def test_get_stealth_engine_basic_driver(self, manager):
        engine = manager.get("stealth", "basic")
        assert isinstance(engine, BasicEngine)

    def test_get_stealth_engine_turbo_driver(self, manager):
        engine = manager.get("stealth", "turbo")
        assert isinstance(engine, TurboEngine)

    def test_get_stealth_engine_default_driver(self, manager):
        engine = manager.get("stealth")
        assert isinstance(engine, TurboEngine)

    def test_unknown_engine_falls_back_to_scrapy(self, manager):
        engine = manager.get("does_not_exist")
        assert isinstance(engine, ScrapyEngine)

    def test_empty_string_falls_back_to_scrapy(self, manager):
        engine = manager.get("")
        assert isinstance(engine, ScrapyEngine)

    def test_engines_are_singletons_within_manager(self, manager):
        assert manager.get("scrapy") is manager.get("scrapy")
        assert manager.get("stealth", "basic") is manager.get("stealth", "basic")
        assert manager.get("stealth", "turbo") is manager.get("stealth", "turbo")

    # -------------------------------------------------------------------
    # Unknown driver fallback
    # -------------------------------------------------------------------

    def test_unknown_driver_falls_back_to_default(self, manager):
        engine = manager.get("stealth", "browsesr")
        assert isinstance(engine, TurboEngine)

    def test_unknown_driver_logs_error(self, manager, capsys):
        manager.get("stealth", "browsesr")
        out = capsys.readouterr().out
        assert "browsesr" in out
        assert "Falling back to" in out

    def test_unknown_config_driver_falls_back_to_default(self, manager):
        original = config.STEALTH_DRIVER
        try:
            config.STEALTH_DRIVER = "browsesr"
            engine = manager.get("stealth")
        finally:
            config.STEALTH_DRIVER = original
        assert isinstance(engine, TurboEngine)

    def test_auto_driver_resolves_to_turbo_by_default(self, manager):
        engine = manager.get("stealth", "auto")
        assert isinstance(engine, TurboEngine)

    def test_invalid_driver_fallback_is_always_valid(self, manager):
        fallback = config.get("STEALTH_DRIVER") or "turbo"
        default = fallback if fallback in manager._stealth else "turbo"
        engine = manager.get("stealth", "nonexistent")
        assert engine is manager._stealth[default]
