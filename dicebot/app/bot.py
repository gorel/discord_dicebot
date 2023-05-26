#!/usr/bin/env python3

import asyncio
import logging
import os
import sys

from dicebot.app import engine
from dicebot.core.client import Client
from dicebot.logging.colored_log_formatter import ColoredLogFormatter

from tldrwl.register import Register


async def main() -> None:
    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root_logger = logging.getLogger()
    handler = root_logger.handlers[0]
    handler.setFormatter(ColoredLogFormatter())

    # If TLDRWL_API_KEY is set, use it. Otherwise, use default (OPENAI_API_KEY)
    if os.getenv("TLDRWL_API_KEY"):
        Register.register(openai_api_key_env_var="TLDRWL_API_KEY")

    # And start the client
    logging.info("Running client")
    client = await Client.get_and_login()
    await client.connect()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
