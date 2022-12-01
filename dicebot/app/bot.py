#!/usr/bin/env python3

import asyncio
import logging
import os
import sys

from dicebot.app.common import client, create_all, engine
from dicebot.logging.colored_log_formatter import ColoredLogFormatter


async def main() -> None:
    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root_logger = logging.getLogger()
    handler = root_logger.handlers[0]
    handler.setFormatter(ColoredLogFormatter())

    # Ensure DB setup is complete
    logging.info("Setting up db connection and tables")
    # TODO - Should this *always* run?
    await create_all()

    # And start the client
    logging.info("Running client")
    discord_token = os.getenv("DISCORD_TOKEN", "")
    await client.start(discord_token)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
