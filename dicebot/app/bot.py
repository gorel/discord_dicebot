#!/usr/bin/env python3

import asyncio
import logging
import sys

from dicebot.app import engine
from dicebot.core.client import Client
from dicebot.data.db.base import Base
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # And start the client
    logging.info("Running client")
    client = await Client.get_and_login()
    await client.connect()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
