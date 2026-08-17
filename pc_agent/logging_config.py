"""Structured logging for PC Agent."""

from __future__ import annotations

import logging
import sys

PREFIX = "[ALPILAB-AGENT]"


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("alpilab.pc_agent")
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(f"{PREFIX} %(message)s"))
    logger.addHandler(handler)
    return logger
