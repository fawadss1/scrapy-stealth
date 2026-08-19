import base64

import pytest
from scrapy.http import Request

from scrapy_stealth.exceptions import StealthRequestError
from scrapy_stealth.utils.network.headers import _FINGERPRINT_KEYS
from scrapy_stealth.utils.network.request import (
    StealthRequestPayload,
    build_stealth_request,
    extract_cookie_header,
    parse_cookie_pairs,
)


class TestBuildStealthRequest:
    def test_single_entry_point_strips_fingerprint_headers(self):
        payload = build_stealth_request(
            Request(
                "https://example.com",
                method="GET",
                headers={
                    "User-Agent": "scrapy",
                    "Accept": "text/html",
                    "Authorization": "Bearer x",
                    "Cookie": "a=1",
                },
            )
        )
        assert payload.method == "GET"
        assert payload.body is None
        assert payload.cookie_header == "a=1"
        assert payload.extra_headers == {"Authorization": "Bearer x"}
        assert payload.headers["Cookie"] == "a=1"
        assert payload.headers["Authorization"] == "Bearer x"
        for key in _FINGERPRINT_KEYS:
            assert key not in {k.lower() for k in payload.extra_headers}

    def test_basic_profile_defaults_merged(self):
        payload = build_stealth_request(
            Request(
                "https://example.com",
                headers={"Authorization": "Bearer z"},
            ),
            profile="chrome_137",
        )
        assert payload.headers["Authorization"] == "Bearer z"
        assert "accept" in {k.lower() for k in payload.headers}
        assert "user-agent" not in {k.lower() for k in payload.headers}

    def test_post_body_and_content_type(self):
        payload = build_stealth_request(
            Request(
                "https://example.com/submit",
                method="POST",
                body=b"a=1",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        )
        assert payload.method == "POST"
        assert payload.body == b"a=1"
        assert payload.http_kwargs() == {
            "headers": payload.headers,
            "data": b"a=1",
        }
        assert payload.basic_http_kwargs() == {
            "headers": payload.headers,
            "body": b"a=1",
        }
        assert payload.needs_browser_setup is True

    def test_plain_get_no_browser_setup(self):
        payload = build_stealth_request(Request("https://example.com"))
        assert payload.needs_browser_setup is False

    def test_normalizes_method_case(self):
        payload = build_stealth_request(
            Request("https://example.com/api", method="post", body=b"{}")
        )
        assert payload.method == "POST"
        assert payload.method_name == "post"

    def test_rejects_unsupported_method(self):
        with pytest.raises(StealthRequestError, match="Unsupported HTTP method"):
            build_stealth_request(Request("https://example.com", method="CONNECT"))

    def test_rejects_blank_url(self):
        request = Request("http://example.com")
        request._url = "   "
        with pytest.raises(StealthRequestError, match="URL is required"):
            build_stealth_request(request)

    def test_extract_cookie_header_from_bytes(self):
        request = Request("https://example.com", headers={b"Cookie": b"s=1"})
        assert extract_cookie_header(request) == "s=1"

    def test_parse_cookie_pairs(self):
        assert parse_cookie_pairs("a=1; b=2") == [("a", "1"), ("b", "2")]

    def test_build_fetch_expression_includes_method_and_body(self):
        from scrapy_stealth.utils.browser.request import _build_fetch_expression

        payload = StealthRequestPayload(
            url="https://postman-echo.com/post",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=b'{"ok":true}',
            cookie_header=None,
            extra_headers={"Content-Type": "application/json"},
        )
        expr = _build_fetch_expression(payload, payload.url)
        assert '"POST"' in expr
        assert "application/json" in expr
        assert base64.b64encode(b'{"ok":true}').decode() in expr

    def test_build_fetch_expression_merges_form_hidden_fields(self):
        from scrapy_stealth.utils.browser.request import _build_fetch_expression

        payload = StealthRequestPayload(
            url="https://quotes.toscrape.com/login",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=b"username=admin&password=admin",
            cookie_header=None,
            extra_headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        expr = _build_fetch_expression(payload, payload.url)
        assert "FormData(form)" in expr
        assert "username=admin&password=admin" in expr
        assert "init.body = Uint8Array" not in expr

    def test_coerce_fetch_result_from_deep_serialized_remote_object(self):
        from scrapy_stealth.utils.browser.request import _coerce_fetch_result

        class _Deep:
            value = [
                ["status", {"type": "number", "value": 200}],
                ["bodyB64", {"type": "string", "value": "aGk="}],
                [
                    "headers",
                    {
                        "type": "object",
                        "value": [
                            [
                                "content-type",
                                {
                                    "type": "string",
                                    "value": "application/json; charset=utf-8",
                                },
                            ]
                        ],
                    },
                ],
            ]

        class _Remote:
            value = None
            deep_serialized_value = _Deep()

        parsed = _coerce_fetch_result(_Remote())
        assert parsed["status"] == 200
        assert parsed["bodyB64"] == "aGk="
        assert parsed["headers"]["content-type"] == "application/json; charset=utf-8"

    def test_request_origin(self):
        from scrapy_stealth.utils.browser.request import request_origin

        assert request_origin("https://quotes.toscrape.com/login") == (
            "https://quotes.toscrape.com/"
        )

    def test_same_origin(self):
        from scrapy_stealth.utils.browser.request import _same_origin

        assert _same_origin(
            "https://postman-echo.com/post",
            "https://postman-echo.com/post",
        )
        assert not _same_origin(
            "https://www.postman.com/foo",
            "https://postman-echo.com/post",
        )

    def test_browser_cdp_headers_skip_content_type(self):
        from scrapy_stealth.utils.browser.request import browser_cdp_headers

        raw = {
            "Authorization": "Bearer x",
            "Content-Type": "application/json",
            "Content-Length": "12",
        }
        assert browser_cdp_headers(raw) == {"Authorization": "Bearer x"}

    def test_evaluate_error_message_from_exception_details(self):
        from scrapy_stealth.utils.browser.request import _evaluate_error_message

        class _Exc:
            text = "Uncaught (in promise) TypeError: Failed to fetch"

        assert "Failed to fetch" in (_evaluate_error_message(_Exc()) or "")

    def test_fetch_response_headers_strip_content_encoding(self):
        from scrapy_stealth.utils.browser.request import _fetch_response_headers

        raw = {
            "content-type": "text/html; charset=utf-8",
            "content-encoding": "br",
            "Content-Length": "1234",
        }
        assert _fetch_response_headers(raw) == {
            "content-type": "text/html; charset=utf-8",
        }
