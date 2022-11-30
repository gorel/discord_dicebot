#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
import sys
from typing import List, Optional

import dotenv
from sqlalchemy.ext.asyncio import create_async_engine

from dicebot.core.client import Client
from dicebot.data.db_models import Base
from dicebot.logging.colored_log_formatter import ColoredLogFormatter

DEFAULT_DB_URI = "sqlite+aiosqlite:///:memory:"


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Discord dicebot")
    parser.add_argument(
        "-t", "--test", action="store_true", help="Start the bot in test mode"
    )
    parser.add_argument(
        "-e",
        "--env-file",
        help="Use a specific file for dotenv (defaults to .env)",
        default=".env",
    )
    return parser


async def main(argv: Optional[List[str]] = None) -> None:
    # Parse args
    argv = argv or sys.argv
    parser = get_parser()
    args = parser.parse_args()

    # Load environment
    dotenv.load_dotenv(args.env_file)
    db_uri = os.getenv("DB_URI", DEFAULT_DB_URI)
    discord_token = os.getenv("DISCORD_TOKEN", "")

    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root_logger = logging.getLogger()
    handler = root_logger.handlers[0]
    handler.setFormatter(ColoredLogFormatter())

    # Ensure DB setup is complete
    logging.info("Setting up db connection and tables")
    engine = create_async_engine(db_uri)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # And start the client
    logging.info("Running client")
    client = Client(engine, is_test=args.test)
    await client.start(discord_token)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
