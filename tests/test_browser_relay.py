from __future__ import annotations

from scrapy_stealth.utils.browser.relay import (
    chromium_proxy_server_from_url,
    external_cdp_uses_direct_upstream_proxy,
    format_relay_proxy_server,
    is_loopback_host,
    resolve_browser_relay_advertise_host,
    resolve_browser_relay_bind_host,
)


def test_is_loopback_host():
    assert is_loopback_host("127.0.0.1")
    assert not is_loopback_host("172.17.0.1")


def test_relay_bind_external_cdp():
    assert resolve_browser_relay_bind_host(external_cdp=True) == "0.0.0.0"


def test_relay_bind_local():
    assert (
        resolve_browser_relay_bind_host("127.0.0.1", external_cdp=False) == "127.0.0.1"
    )


def test_format_relay_proxy_server():
    assert format_relay_proxy_server(12345, "127.0.0.1") == "http://127.0.0.1:12345"


def test_relay_advertise_local():
    assert resolve_browser_relay_advertise_host(external_cdp=False) == "127.0.0.1"


def test_external_cdp_direct_upstream_without_dns_or_auth():
    assert external_cdp_uses_direct_upstream_proxy(
        external_cdp=True,
        proxy="http://proxy:8080",
        dns_overrides={},
    )


def test_external_cdp_relay_for_authenticated_proxy():
    assert not external_cdp_uses_direct_upstream_proxy(
        external_cdp=True,
        proxy="http://user:pass@proxy:8080",
        dns_overrides={},
    )


def test_external_cdp_relay_when_dns_pin():
    assert not external_cdp_uses_direct_upstream_proxy(
        external_cdp=True,
        proxy="http://user:pass@proxy:8080",
        dns_overrides={"example.com": "1.2.3.4"},
    )


def test_chromium_proxy_server_embeds_auth():
    url = "https://user-rs_test:secret@dc.oxylabs.io:8000"
    assert chromium_proxy_server_from_url(url) == (
        "http://user-rs_test:secret@dc.oxylabs.io:8000"
    )
