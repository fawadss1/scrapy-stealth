from __future__ import annotations

import logging

from ...config import config


def get_logger() -> logging.Logger:
    return logging.getLogger(config.get("LOGGER_NAME"))


def configure_stealth_logging(enabled: bool | None = None) -> None:
    """Enable or disable all output from the scrapy-stealth logger."""
    if enabled is None:
        enabled = bool(config.get("STEALTH_LOGS", True))
    get_logger().disabled = not enabled
