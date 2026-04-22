import pytest
from unittest.mock import patch

from scrapy_stealth.manager import EngineManager
from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.browser import BrowserEngine


class TestEngineManager:
    @pytest.fixture
    def manager(self):
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient"):
            yield EngineManager()

    def test_get_scrapy_engine(self, manager):
        engine = manager.get("scrapy")
        assert isinstance(engine, ScrapyEngine)

    def test_get_stealth_engine(self, manager):
        engine = manager.get("stealth")
        assert isinstance(engine, BrowserEngine)

    def test_unknown_engine_falls_back_to_scrapy(self, manager):
        engine = manager.get("does_not_exist")
        assert isinstance(engine, ScrapyEngine)

    def test_empty_string_falls_back_to_scrapy(self, manager):
        engine = manager.get("")
        assert isinstance(engine, ScrapyEngine)

    def test_engines_are_singletons_within_manager(self, manager):
        assert manager.get("scrapy") is manager.get("scrapy")
        assert manager.get("stealth") is manager.get("stealth")
