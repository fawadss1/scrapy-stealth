from __future__ import annotations

import pytest
from scrapy.http import Request

from scrapy_stealth.config import config
from scrapy_stealth.utils.network.dns import (
    build_chrome_host_resolver_args,
    build_curl_resolve,
    build_wreq_dns_options,
    default_port_for_url,
    dns_fingerprint,
    lookup_dns_ip,
    resolve_dns_overrides,
    validate_dns_overrides,
)


class TestValidateDnsOverrides:
    def test_empty(self):
        assert validate_dns_overrides(None) == {}
        assert validate_dns_overrides({}) == {}

    def test_normalizes_host_and_ip(self):
        assert validate_dns_overrides({"Example.COM.": " 203.0.113.10 "}) == {
            "example.com": "203.0.113.10"
        }

    def test_accepts_ipv6(self):
        assert validate_dns_overrides({"cdn.example": "2001:db8::1"}) == {
            "cdn.example": "2001:db8::1"
        }

    def test_rejects_invalid_ip(self):
        with pytest.raises(ValueError, match="not a valid IPv4/IPv6"):
            validate_dns_overrides({"example.com": "not-an-ip"})

    def test_rejects_empty_host(self):
        with pytest.raises(ValueError, match="empty hostname"):
            validate_dns_overrides({"  ": "1.2.3.4"})

    def test_rejects_url_as_host(self):
        with pytest.raises(ValueError, match="bare hostname"):
            validate_dns_overrides({"https://example.com": "1.2.3.4"})


class TestResolveDnsOverrides:
    def setup_method(self):
        self._original = dict(config.STEALTH_DNS_OVERRIDES)

    def teardown_method(self):
        config.STEALTH_DNS_OVERRIDES = self._original

    def test_merges_config_and_meta_map(self):
        config.STEALTH_DNS_OVERRIDES = {"example.com": "203.0.113.1"}
        request = Request(
            "https://example.com",
            meta={"stealth": {"dns": {"cdn.example.com": "203.0.113.2"}}},
        )
        assert resolve_dns_overrides(request) == {
            "example.com": "203.0.113.1",
            "cdn.example.com": "203.0.113.2",
        }

    def test_meta_bare_ip_pins_request_host(self):
        config.STEALTH_DNS_OVERRIDES = {}
        request = Request(
            "https://www.example.com/path",
            meta={"stealth": {"dns": "203.0.113.10"}},
        )
        assert resolve_dns_overrides(request) == {"www.example.com": "203.0.113.10"}

    def test_meta_overrides_config_for_same_host(self):
        config.STEALTH_DNS_OVERRIDES = {"example.com": "203.0.113.1"}
        request = Request(
            "https://example.com",
            meta={"stealth": {"dns": "203.0.113.99"}},
        )
        assert resolve_dns_overrides(request)["example.com"] == "203.0.113.99"


class TestDnsHelpers:
    def test_lookup_dns_ip(self):
        overrides = {"example.com": "203.0.113.10"}
        assert lookup_dns_ip("Example.COM", overrides) == "203.0.113.10"
        assert lookup_dns_ip("other.com", overrides) is None

    def test_dns_fingerprint(self):
        assert dns_fingerprint({"b.com": "1.1.1.1", "a.com": "2.2.2.2"}) == (
            ("a.com", "2.2.2.2"),
            ("b.com", "1.1.1.1"),
        )
        assert dns_fingerprint({}) == ()

    def test_default_port_for_url(self):
        assert default_port_for_url("https://example.com") == 443
        assert default_port_for_url("http://example.com") == 80
        assert default_port_for_url("https://example.com:8443") == 8443

    def test_build_curl_resolve(self):
        entries = build_curl_resolve(
            {"example.com": "203.0.113.10"}, "https://example.com"
        )
        assert "example.com:443:203.0.113.10" in entries
        assert "example.com:80:203.0.113.10" in entries

    def test_build_chrome_host_resolver_args(self):
        args = build_chrome_host_resolver_args(
            {"example.com": "203.0.113.10", "cdn.example.com": "203.0.113.11"}
        )
        assert len(args) == 1
        assert args[0].startswith("--host-resolver-rules=")
        assert "MAP example.com 203.0.113.10" in args[0]
        assert "MAP cdn.example.com 203.0.113.11" in args[0]
        assert build_chrome_host_resolver_args({}) == []

    def test_build_wreq_dns_options_none_when_empty(self):
        assert build_wreq_dns_options({}) is None

    def test_build_wreq_dns_options_creates_options(self):
        opts = build_wreq_dns_options({"example.com": "203.0.113.10"})
        assert opts is not None
