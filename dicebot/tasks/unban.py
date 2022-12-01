#!/usr/bin/env python3

import asyncio
import datetime
import os

import discord

# TODO: Put this initialization in a common folder
from dicebot.app.common import async_sessionmaker, celery_app, client
from dicebot.data.db.ban import Ban
from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User


@celery_app.task
def unban(channel_id: int, guild_id: int, target_id: int) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unban_async(channel_id, guild_id, target_id))


async def unban_async(channel_id: int, guild_id: int, target_id: int) -> None:
    discord_token = os.getenv("DISCORD_TOKEN", "")
    await client.login(discord_token)
    channel = await client.fetch_channel(channel_id)
    assert isinstance(channel, discord.TextChannel)

    async with async_sessionmaker() as session:
        guild = await Guild.get_or_none(session, guild_id)
        target = await User.get_or_none(session, target_id)

        if guild is None or target is None:
            return

        current_ban = await Ban.get_latest_unvoided_ban(session, guild, target)

    if current_ban is not None and current_ban.banned_until < datetime.datetime.now():
        await channel.send(f"<@{target_id}>: You have been unbanned.")
