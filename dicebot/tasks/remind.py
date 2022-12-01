#!/usr/bin/env python3

import asyncio

import discord

from dicebot.app.common import celery_app


@celery_app.task
def send_reminder(channel_id: int, author_id: int, reminder: str) -> None:
    client = discord.Client(intents=discord.Intents.default())
    loop = asyncio.get_event_loop()

    channel = loop.run_until_complete(client.fetch_channel(channel_id))
    assert isinstance(channel, discord.TextChannel)
    # NOTE: Can't use rich .as_mention() since this isn't a db model
    loop.run_until_complete(channel.send(f"Reminder for <@{author_id}>: {reminder}"))
