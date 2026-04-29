import pytest
from scrapy_stealth.exceptions import StealthException, EngineNotFound


def test_stealth_exception_is_exception():
    assert issubclass(StealthException, Exception)


def test_engine_not_found_is_stealth_exception():
    assert issubclass(EngineNotFound, StealthException)


def test_stealth_exception_can_be_raised():
    with pytest.raises(StealthException):
        raise StealthException("test error")


def test_engine_not_found_can_be_raised():
    with pytest.raises(EngineNotFound):
        raise EngineNotFound("rnet not found")


def test_engine_not_found_message():
    exc = EngineNotFound("unknown_engine")
    assert "unknown_engine" in str(exc)
