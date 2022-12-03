#!/usr/bin/env python3

import asyncio

from dicebot.app import celery_app


async def main() -> None:
    # Just run the celery app
    celery_app.start()


if __name__ == "__main__":
    asyncio.run(main())
