"""PC Agent entrypoint — run manually from terminal on Windows."""

from __future__ import annotations

import asyncio
import signal

from pc_agent.client import AgentClient
from pc_agent.config import AgentConfig
from pc_agent.identity import load_or_create_agent_id
from pc_agent.logging_config import setup_logging


async def _main_async() -> None:
    config = AgentConfig.from_env()
    logger = setup_logging(config.log_level)
    agent_id = load_or_create_agent_id(config.identity_path)

    logger.info("Starting...")
    logger.info("Agent ID: %s", agent_id)
    logger.info("Session: %s", config.session_id)

    client = AgentClient(config, agent_id)
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _request_stop() -> None:
        logger.info("Shutdown requested")
        stop_event.set()
        asyncio.create_task(client.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            pass

    run_task = asyncio.create_task(client.run())
    await stop_event.wait()
    await client.shutdown()
    run_task.cancel()
    try:
        await run_task
    except asyncio.CancelledError:
        pass
    logger.info("Stopped")


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
