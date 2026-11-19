from scrapy.http import Request

from scrapy_stealth.utils.core.response import StealthResponse


def test_stealth_response_uses_effective_url():
    request = Request("https://example.com/start")
    response = StealthResponse(
        request=request,
        status=200,
        headers={},
        body=b"ok",
        url="https://www.example.com/final",
    )

    assert response.url == "https://www.example.com/final"
    assert response.request.url == "https://www.example.com/final"


def test_stealth_response_ignores_invalid_effective_url():
    request = Request("https://example.com/start")
    response = StealthResponse(
        request=request,
        status=200,
        headers={},
        body=b"ok",
        url="<html>not-a-url</html>",
    )

    assert response.url == "https://example.com/start"