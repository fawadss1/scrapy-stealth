from scrapy_stealth.config import config


def test_default_engine():
    assert config.get("DEFAULT_ENGINE") == "scrapy"


def test_default_timeout():
    assert config.get("DEFAULT_TIMEOUT") == 30


def test_http2_default():
    assert config.get("HTTP2") is True


def test_http3_default():
    assert config.get("HTTP3") is False


def test_dns_overrides_default():
    assert config.get("STEALTH_DNS_OVERRIDES") == {}
