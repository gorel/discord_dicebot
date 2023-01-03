#!/usr/bin/env python3

import asyncio

import discord

from dicebot.app import celery_app


@celery_app.task(ignore_result=True)
def send_reminder(channel_id: int, author_id: int, reminder: str) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_reminder_async(channel_id, author_id, reminder))


async def send_reminder_async(channel_id: int, author_id: int, reminder: str) -> None:
    # To avoid circular imports, we put this import here
    # Unfortunately how the tasks are setup, we can't import Client at the top level
    from dicebot.core.client import Client

    client = await Client.get_and_login()

    channel = await client.fetch_channel(channel_id)
    assert isinstance(channel, discord.TextChannel)
    # NOTE: Can't use rich .as_mention() since this isn't a db model
    await channel.send(f"Reminder for <@{author_id}>: {reminder}")
