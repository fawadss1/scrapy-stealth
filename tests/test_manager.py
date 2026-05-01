import pytest
from unittest.mock import patch

from scrapy_stealth.config import config
from scrapy_stealth.manager import EngineManager
from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.basic import BasicEngine
from scrapy_stealth.engines.turbo import TurboEngine


class TestEngineManager:
    @pytest.fixture
    def manager(self):
        with patch("scrapy_stealth.engines.basic.Client"), \
             patch("scrapy_stealth.engines.turbo.Session"):
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
        assert isinstance(engine, BasicEngine)

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
