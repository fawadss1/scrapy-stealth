from __future__ import annotations

import logging

from ..config import config


def get_logger() -> logging.Logger:
    return logging.getLogger(config.get("LOGGER_NAME"))
