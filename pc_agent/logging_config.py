"""Structured logging for PC Agent."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PREFIX = "[ALPILAB-AGENT]"


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("alpilab.pc_agent")
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(f"{PREFIX} %(message)s")
    stream = sys.stdout
    if stream is not None:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    log_dir = Path.home() / ".alpilab" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "agent.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
