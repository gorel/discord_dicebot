#!/usr/bin/env python3

# Stub - full implementation in Task 3
# This module will define the notify_event Celery task that fires when a
# scheduled event is about to begin, mentioning all signed-up users.

import asyncio

from dicebot.app import celery_app


@celery_app.task(ignore_result=True)
def notify_event(event_id: int, channel_id: int) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_notify_event_async(event_id, channel_id))


async def _notify_event_async(event_id: int, channel_id: int) -> None:
    # To avoid circular imports, we put this import here
    from dicebot.core.client import Client

    client = await Client.get_and_login()
    # Full implementation: look up event + signups and notify users
    # (Placeholder until Task 3 fills this in)
    pass
