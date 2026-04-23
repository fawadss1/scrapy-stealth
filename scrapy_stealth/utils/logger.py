from __future__ import annotations

import logging

from ..constants import LOGGER_NAME


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
