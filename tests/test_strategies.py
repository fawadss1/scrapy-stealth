import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import Request

from scrapy_stealth.config import config
from scrapy_stealth.strategies.proxy import ProxyRotator
from scrapy_stealth.strategies.fingerprint import ProfileRotator, FINGERPRINTS
from scrapy_stealth.strategies.retry import RetryHandler


# ---------------------------------------------------------------------------
# ProxyRotator
# ---------------------------------------------------------------------------

class TestProxyRotator:
    def test_returns_none_when_no_proxies(self):
        strategy = ProxyRotator()
        assert strategy.get() is None

    def test_returns_none_with_empty_list(self):
        strategy = ProxyRotator(proxies=[])
        assert strategy.get() is None

    def test_returns_proxy_from_list(self):
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        strategy = ProxyRotator(proxies=proxies)
        assert strategy.get() in proxies

    def test_single_proxy_always_returned(self):
        strategy = ProxyRotator(proxies=["http://proxy1:8080"])
        assert strategy.get() == "http://proxy1:8080"

    def test_proxy_is_random(self):
        proxies = [f"http://proxy{i}:8080" for i in range(10)]
        strategy = ProxyRotator(proxies=proxies)
        results = {strategy.get() for _ in range(50)}
        assert len(results) > 1

    def test_valid_https_proxy_accepted(self):
        strategy = ProxyRotator(proxies=["https://proxy1:8080"])
        assert strategy.get() == "https://proxy1:8080"

    def test_valid_socks5_proxy_accepted(self):
        strategy = ProxyRotator(proxies=["socks5://proxy1:1080"])
        assert strategy.get() == "socks5://proxy1:1080"

    def test_valid_proxy_with_auth_accepted(self):
        strategy = ProxyRotator(proxies=["http://user:pass@proxy1:8080"])
        assert strategy.get() == "http://user:pass@proxy1:8080"

    def test_invalid_proxy_no_scheme_raises(self):
        with pytest.raises(ValueError, match="Invalid proxy"):
            ProxyRotator(proxies=["proxy1:8080"])

    def test_invalid_proxy_unsupported_scheme_raises(self):
        with pytest.raises(ValueError, match="unsupported scheme"):
            ProxyRotator(proxies=["ftp://proxy1:8080"])

    def test_invalid_proxy_no_port_raises(self):
        with pytest.raises(ValueError, match="missing port"):
            ProxyRotator(proxies=["http://proxy1"])

    def test_invalid_proxy_in_mixed_list_raises(self):
        with pytest.raises(ValueError):
            ProxyRotator(proxies=["http://proxy1:8080", "bad-proxy"])


# ---------------------------------------------------------------------------
# ProfileRotator
# ---------------------------------------------------------------------------

class TestProfileRotator:
    def test_returns_valid_fingerprint(self):
        strategy = ProfileRotator()
        assert strategy.get() in FINGERPRINTS

    def test_returns_string(self):
        strategy = ProfileRotator()
        assert isinstance(strategy.get(), str)

    def test_rotates_across_calls(self):
        strategy = ProfileRotator()
        results = {strategy.get() for _ in range(100)}
        assert len(results) > 1

    def test_fingerprints_are_latest(self):
        assert any(fp in FINGERPRINTS for fp in ("chrome_145", "chrome_146", "chrome_147"))
        assert any(fp in FINGERPRINTS for fp in ("firefox_147", "firefox_148", "firefox_149"))
        assert any("safari_26" in fp for fp in FINGERPRINTS)
        assert any(fp in FINGERPRINTS for fp in ("edge_145", "edge_146", "edge_147"))
        assert any(fp in FINGERPRINTS for fp in ("opera_128", "opera_129", "opera_130"))

    def test_fingerprints_include_mobile(self):
        assert any("ios" in fp or "android" in fp or "ipad" in fp for fp in FINGERPRINTS)

    def test_fingerprints_include_multiple_browsers(self):
        browsers = {"chrome", "firefox", "safari", "edge", "opera"}
        covered = {b for b in browsers if any(b in fp for fp in FINGERPRINTS)}
        assert len(covered) >= 4

    def test_fingerprints_not_empty(self):
        assert len(FINGERPRINTS) > 10


# ---------------------------------------------------------------------------
# RetryHandler
# ---------------------------------------------------------------------------

def make_response(status: int):
    response = MagicMock()
    response.status = status
    return response


class TestRetryHandler:
    @pytest.fixture
    def strategy(self):
        return RetryHandler()

    @pytest.fixture
    def base_request(self):
        return Request("https://example.com", meta={})

    def test_should_retry_on_403(self, strategy):
        assert strategy.should_retry(make_response(403)) is True

    def test_should_retry_on_429(self, strategy):
        assert strategy.should_retry(make_response(429)) is True

    def test_should_retry_on_503(self, strategy):
        assert strategy.should_retry(make_response(503)) is True

    def test_all_block_codes_trigger_retry(self, strategy):
        for code in config.get("BLOCK_CODES"):
            assert strategy.should_retry(make_response(code)) is True, f"Expected {code} to trigger retry"

    def test_should_not_retry_on_200(self, strategy):
        assert strategy.should_retry(make_response(200)) is False

    def test_should_not_retry_on_404(self, strategy):
        assert strategy.should_retry(make_response(404)) is False

    def test_should_not_retry_on_500(self, strategy):
        assert strategy.should_retry(make_response(500)) is False

    def test_build_increments_retry_times(self, strategy, base_request):
        retry = strategy.build(base_request)
        assert retry.meta["retry_times"] == 1

    def test_build_increments_from_existing(self, strategy):
        request = Request("https://example.com", meta={"retry_times": 2})
        retry = strategy.build(request)
        assert retry.meta["retry_times"] == 3

    def test_build_switches_to_stealth(self, strategy, base_request):
        retry = strategy.build(base_request)
        assert retry.meta["engine"] == "stealth"

    def test_build_sets_dont_filter(self, strategy, base_request):
        retry = strategy.build(base_request)
        assert retry.dont_filter is True

    def test_build_preserves_url(self, strategy, base_request):
        retry = strategy.build(base_request)
        assert retry.url == base_request.url

    def test_build_does_not_mutate_original(self, strategy, base_request):
        original_meta = dict(base_request.meta)
        strategy.build(base_request)
        assert base_request.meta.get("retry_times", 0) == original_meta.get("retry_times", 0)
