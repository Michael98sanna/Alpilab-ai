"""PC Agent handlers for iPhone panic log tools."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any

from .service import IPhonePanicService

logger = logging.getLogger(__name__)

_service = IPhonePanicService()


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


def handle_panic_check(_arguments: dict[str, Any]) -> dict[str, Any]:
    """Tool: iphone.panic_log.check"""
    logger.info("iphone.panic_log.check")
    return _run_async(_service.check())


def handle_panic_analyze(arguments: dict[str, Any]) -> dict[str, Any]:
    """Tool: iphone.panic_log.analyze"""
    force = bool(arguments.get("force_reanalyze", False))
    logger.info("iphone.panic_log.analyze force=%s", force)
    return _run_async(_service.analyze(force_reanalyze=force))
