from scrapy_stealth.config import StealthConfig


def test_default_engine():
    assert StealthConfig.DEFAULT_ENGINE == "scrapy"


def test_default_timeout():
    assert StealthConfig.DEFAULT_TIMEOUT == 30


def test_default_profile():
    assert StealthConfig.DEFAULT_PROFILE == "chrome_147"
