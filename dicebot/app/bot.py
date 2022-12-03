#!/usr/bin/env python3

import asyncio
import logging
import sys

from dicebot.app import engine
from dicebot.core.client import Client
from dicebot.logging.colored_log_formatter import ColoredLogFormatter


async def main() -> None:
    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root_logger = logging.getLogger()
    handler = root_logger.handlers[0]
    handler.setFormatter(ColoredLogFormatter())

    # And start the client
    logging.info("Running client")
    client = await Client.get_and_login()
    await client.connect()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
