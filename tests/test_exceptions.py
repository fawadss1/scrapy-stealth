import pytest
from scrapy.exceptions import DownloadTimeoutError

from scrapy_stealth.exceptions import (
    EngineNotFound,
    StealthBrowserNotFoundError,
    StealthConnectionError,
    StealthException,
    StealthTimeoutError,
)


def test_stealth_exception_is_exception():
    assert issubclass(StealthException, Exception)


def test_engine_not_found_is_stealth_exception():
    assert issubclass(EngineNotFound, StealthException)


def test_stealth_exception_can_be_raised():
    with pytest.raises(StealthException):
        raise StealthException("test error")


def test_engine_not_found_can_be_raised():
    with pytest.raises(EngineNotFound):
        raise EngineNotFound("engine not found")


def test_engine_not_found_message():
    exc = EngineNotFound("unknown_engine")
    assert "unknown_engine" in str(exc)


class TestStealthTimeoutError:
    def test_is_stealth_exception(self):
        assert issubclass(StealthTimeoutError, StealthException)

    def test_is_download_timeout_error(self):
        assert issubclass(StealthTimeoutError, DownloadTimeoutError)

    def test_can_be_raised(self):
        with pytest.raises(StealthTimeoutError):
            raise StealthTimeoutError("timed out")

    def test_caught_as_download_timeout_error(self):
        with pytest.raises(DownloadTimeoutError):
            raise StealthTimeoutError("timed out")

    def test_message_preserved(self):
        exc = StealthTimeoutError("curl: (28) timed out")
        assert "curl: (28) timed out" in str(exc)

    def test_cause_preserved(self):
        original = RuntimeError("original")
        exc = StealthTimeoutError("timed out")
        exc.__cause__ = original
        assert exc.__cause__ is original


class TestStealthConnectionError:
    def test_is_stealth_exception(self):
        assert issubclass(StealthConnectionError, StealthException)

    def test_is_builtin_connection_error(self):
        assert issubclass(StealthConnectionError, ConnectionError)

    def test_is_oserror(self):
        # ConnectionError → OSError; OSError is in Scrapy's RETRY_EXCEPTIONS
        assert issubclass(StealthConnectionError, OSError)

    def test_can_be_raised(self):
        with pytest.raises(StealthConnectionError):
            raise StealthConnectionError("connection failed")

    def test_caught_as_connection_error(self):
        with pytest.raises(ConnectionError):
            raise StealthConnectionError("connection failed")

    def test_message_preserved(self):
        exc = StealthConnectionError("Basic engine connection failed fetching 'https://example.com'")
        assert "Basic engine connection failed" in str(exc)

    def test_cause_preserved(self):
        original = RuntimeError("dns error")
        exc = StealthConnectionError("connection failed")
        exc.__cause__ = original
        assert exc.__cause__ is original


class TestStealthBrowserNotFoundError:
    def test_is_stealth_exception(self):
        assert issubclass(StealthBrowserNotFoundError, StealthException)

    def test_is_not_oserror(self):
        # Should NOT be retried — browser missing is a config problem, not a transient error
        assert not issubclass(StealthBrowserNotFoundError, OSError)

    def test_can_be_raised(self):
        with pytest.raises(StealthBrowserNotFoundError):
            raise StealthBrowserNotFoundError("Browser binary not found.")

    def test_message_preserved(self):
        exc = StealthBrowserNotFoundError("Browser binary not found. Install Google Chrome.")
        assert "Browser binary not found" in str(exc)

    def test_cause_preserved(self):
        original = FileNotFoundError("google-chrome")
        exc = StealthBrowserNotFoundError("Browser binary not found.")
        exc.__cause__ = original
        assert exc.__cause__ is original
