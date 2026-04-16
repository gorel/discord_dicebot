#!/usr/bin/env python3

import asyncio

import discord

from dicebot.app import app_sessionmaker, celery_app


@celery_app.task(ignore_result=True)
def notify_event(event_id: int, channel_id: int) -> None:
    # NOTE: unban.py and remind.py still use get_event_loop() — pre-existing debt
    asyncio.run(_notify_event_async(event_id, channel_id))


async def _notify_event_async(event_id: int, channel_id: int) -> None:
    from dicebot.core.client import Client
    from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup

    client = await Client.get_and_login()
    channel = await client.fetch_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return

    async with app_sessionmaker() as session:
        event = await ScheduledEvent.get_by_id(session, event_id)
        if event is None:
            return  # Event was cancelled

        signups = await ScheduledEventSignup.get_all_for_event(session, event_id)

        if not signups:
            await channel.send(f"**{event.name}** is starting now! (No one signed up \U0001f622)")
        else:
            mentions = " ".join(f"<@{s.user_id}>" for s in signups)
            await channel.send(f"{mentions} **{event.name}** is starting now! \U0001f3b2")
