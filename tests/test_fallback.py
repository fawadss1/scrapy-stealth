from __future__ import annotations

from scrapy.http import HtmlResponse, Request

from scrapy_stealth.utils.engine.fallback import (
    FALLBACK_DONE_KEY,
    mark_fallback_done,
    request_method,
    resolve_primary_driver,
    should_driver_fallback,
    should_fallback_response,
)


def _response(body: str = "<html>ok</html>", status: int = 200) -> HtmlResponse:
    return HtmlResponse(
        url="https://example.com/submit",
        status=status,
        body=body.encode(),
        encoding="utf-8",
        request=Request("https://example.com/submit"),
    )


class TestResolvePrimaryDriver:
    def test_auto_expands_to_configured_http_driver(self):
        assert resolve_primary_driver("auto") == "turbo"

    def test_explicit_driver_unchanged(self):
        assert resolve_primary_driver("browser") == "browser"


class TestShouldFallbackResponse:
    def test_js_challenge_html(self):
        body = "<html>Just a moment... cf-browser-verification</html>"
        assert should_fallback_response(_response(body)) is True

    def test_clean_200(self):
        assert should_fallback_response(_response()) is False

    def test_403_counts_as_ban(self):
        assert should_fallback_response(_response(status=403)) is True


class TestShouldDriverFallback:
    def test_post_403_triggers_fallback(self):
        request = Request(
            "https://example.com/login",
            method="POST",
            body=b"user=1",
            meta={"stealth": {"driver": "auto"}},
        )
        response = _response(status=403)
        response.request = request
        assert should_driver_fallback(response, "turbo", request) is True

    def test_post_js_challenge_triggers_fallback(self):
        request = Request(
            "https://example.com/api",
            method="POST",
            body=b"{}",
            meta={"stealth": {"driver": "auto"}},
        )
        body = "<html>Just a moment... cf-browser-verification</html>"
        response = _response(body)
        response.request = request
        assert should_driver_fallback(response, "turbo", request) is True

    def test_no_fallback_without_auto_driver(self):
        request = Request(
            "https://example.com/login",
            method="POST",
            meta={"stealth": {"driver": "turbo"}},
        )
        response = _response(status=403)
        response.request = request
        assert should_driver_fallback(response, "turbo", request) is False

    def test_no_second_fallback(self):
        request = Request(
            "https://example.com/login",
            method="POST",
            meta={"stealth": {"driver": "auto", FALLBACK_DONE_KEY: True}},
        )
        response = _response(status=403)
        response.request = request
        assert should_driver_fallback(response, "turbo", request) is False

    def test_mark_fallback_done_preserves_post_request(self):
        request = Request(
            "https://example.com/login",
            method="POST",
            body=b"a=1",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            meta={"stealth": {"driver": "auto"}},
        )
        mark_fallback_done(request, "turbo")
        assert request.method == "POST"
        assert request.body == b"a=1"
        assert request.meta["stealth"]["headless"] is False
        assert request.meta["stealth"]["fallback_from"] == "turbo"


class TestFallbackHelpers:
    def test_request_method_defaults_to_get(self):
        assert request_method(Request("https://example.com")) == "GET"
