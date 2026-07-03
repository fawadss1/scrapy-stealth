from unittest.mock import MagicMock

import pytest

from scrapy_stealth.detectors.antibot import AntiBotDetector


@pytest.fixture
def detector():
    return AntiBotDetector()


def make_response(status: int, body: str = ""):
    response = MagicMock()
    response.status = status
    response.text = body
    response.body = body.encode()
    return response


class TestAntiBotDetector:
    def test_403_is_blocked(self, detector):
        assert detector.is_blocked(make_response(403)) is True

    def test_429_is_blocked(self, detector):
        assert detector.is_blocked(make_response(429)) is True

    def test_200_is_not_blocked(self, detector):
        assert detector.is_blocked(make_response(200, "Welcome!")) is False

    def test_301_is_not_blocked(self, detector):
        assert detector.is_blocked(make_response(301)) is False

    def test_captcha_keyword_blocked(self, detector):
        assert (
            detector.is_blocked(make_response(200, "Please solve the captcha")) is True
        )

    def test_access_denied_keyword_blocked(self, detector):
        assert detector.is_blocked(make_response(200, "Access Denied")) is True

    def test_verify_human_keyword_blocked(self, detector):
        assert (
            detector.is_blocked(make_response(200, "Verify you are human to continue"))
            is True
        )

    def test_keyword_case_insensitive(self, detector):
        assert detector.is_blocked(make_response(200, "CAPTCHA REQUIRED")) is True

    def test_normal_body_not_blocked(self, detector):
        assert detector.is_blocked(make_response(200, "<h1>Product List</h1>")) is False

    def test_500_not_blocked(self, detector):
        assert detector.is_blocked(make_response(500, "Internal Server Error")) is False


class TestBrowserSessionBan:
    def test_block_status_is_ban(self, detector):
        assert detector.is_browser_session_ban(make_response(403, "x")) is True

    def test_large_200_with_challenge_sig_is_not_ban(self, detector):
        body = "x" * 3000 + "datadome"
        assert detector.is_browser_session_ban(make_response(200, body)) is False

    def test_large_200_with_block_keyword_is_not_ban(self, detector):
        body = "product " * 500 + "captcha"
        assert detector.is_browser_session_ban(make_response(200, body)) is False

    def test_short_200_challenge_page_is_ban(self, detector):
        assert (
            detector.is_browser_session_ban(
                make_response(200, "<html>just a moment</html>")
            )
            is True
        )

    def test_short_200_keyword_stub_is_ban(self, detector):
        assert (
            detector.is_browser_session_ban(make_response(200, "Access Denied")) is True
        )
