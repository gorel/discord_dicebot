#!/usr/bin/env python3

import asyncio
import logging
import sys

from dicebot.app import engine
from dicebot.core.client import Client
from dicebot.data.db.user import User
from dicebot.logging.colored_log_formatter import ColoredLogFormatter


async def main() -> None:
    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root_logger = logging.getLogger()
    handler = root_logger.handlers[0]
    handler.setFormatter(ColoredLogFormatter())

    # Get the client
    logging.info("Logging the bot into discord")
    client = await Client.get_and_login()
    assert client.user is not None

    # Ensure our bot is in the db
    logging.info("Ensuring the bot's user account is in the db")
    async with client.sessionmaker() as session:
        await User.get_or_create(session, client.user.id)

    # And start the client
    logging.info("Running client")
    await client.connect()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
