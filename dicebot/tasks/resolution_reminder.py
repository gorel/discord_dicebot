#!/usr/bin/env python3

import asyncio

import discord

from dicebot.app import app_sessionmaker, celery_app
from dicebot.data.db.resolution import Resolution


@celery_app.task(ignore_result=True)
def remind(resolution_id: int) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(remind_async(resolution_id))


async def remind_async(resolution_id: int) -> None:
    # To avoid circular imports, we put this import here
    # Unfortunately how the tasks are setup, we can't import Client at the top level
    from dicebot.core.client import Client

    client = await Client.get_and_login()

    async with app_sessionmaker() as session:
        resolution = await Resolution.get_or_none(session, resolution_id)

    if resolution is None or not resolution.active:
        return

    channel = await client.fetch_channel(resolution.channel_id)
    if not (
        isinstance(channel, discord.TextChannel)
        or isinstance(channel, discord.DMChannel)
    ):
        return

    await channel.send(
        f"<@{resolution.author_id}>: Hey, how's your resolution going? This one:\n"
        f"> {resolution.msg}",
    )
