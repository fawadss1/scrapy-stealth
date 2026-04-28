from scrapy_stealth.config import config


def test_default_engine():
    assert config.get("DEFAULT_ENGINE") == "scrapy"


def test_default_timeout():
    assert config.get("DEFAULT_TIMEOUT") == 30


def test_default_profile():
    assert config.get("DEFAULT_PROFILE") == "chrome_147"


def test_http2_default():
    assert config.get("HTTP2") is True
