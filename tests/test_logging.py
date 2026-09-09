from scrapy_stealth.config import config
from scrapy_stealth.utils.core.logger import configure_stealth_logging, get_logger


def test_configure_stealth_logging_disables_logger():
    previous = config.STEALTH_LOGS
    try:
        configure_stealth_logging(False)
        assert get_logger().disabled is True
        configure_stealth_logging(True)
        assert get_logger().disabled is False
    finally:
        config.STEALTH_LOGS = previous
        configure_stealth_logging(previous)
