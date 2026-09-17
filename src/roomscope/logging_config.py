"""Logging configuration.

Library code only ever calls ``logging.getLogger(__name__)``; front ends call
:func:`configure_logging` once. The library never configures the root logger on
import, so RoomScope can be embedded without side effects.
"""

from __future__ import annotations

import logging
import sys
from typing import IO

LOGGER_NAME = "roomscope"
_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger below the ``roomscope`` namespace."""
    if name is None or name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    if name.startswith(LOGGER_NAME + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def configure_logging(
    level: int | str = logging.INFO,
    stream: IO[str] | None = None,
    *,
    fmt: str = _FORMAT,
) -> logging.Logger:
    """Configure the ``roomscope`` logger with a single stream handler.

    Calling this more than once replaces the previous RoomScope handler instead
    of stacking handlers.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        if getattr(handler, "_roomscope_handler", False):
            logger.removeHandler(handler)
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))
    handler._roomscope_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
