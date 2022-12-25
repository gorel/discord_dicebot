#!/usr/bin/env python3

import asyncio
import logging
import sys
from typing import Any, Coroutine

from IPython import embed

from dicebot.core.client import Client


def prep(coro: Coroutine) -> Any:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


def main() -> None:
    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # Start the client
    logging.info("Starting client")
    client = prep(Client.get_and_login())

    # And drop into the IPython session
    logging.info("Embedding IPython session")
    embed()


if __name__ == "__main__":
    main()
