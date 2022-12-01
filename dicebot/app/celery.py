#!/usr/bin/env python3

import asyncio
import logging

from dicebot.app import celery_app, engine
from dicebot.data.db.base import Base


async def main() -> None:
    # Ensure DB setup is complete
    logging.info("Setting up db connection and tables")
    # TODO - Should this *always* run?
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Just run the celery app
    celery_app.start()


if __name__ == "__main__":
    asyncio.run(main())
