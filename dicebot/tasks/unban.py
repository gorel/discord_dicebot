#!/usr/bin/env python3

import asyncio
import datetime
from typing import Optional

import discord

# TODO: Put this initialization in a common folder
from dicebot.app import app_sessionmaker, celery_app
from dicebot.data.db.ban import Ban
from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User


@celery_app.task(ignore_result=True)
def unban(
    channel_id: int, guild_id: int, target_id: int, ban_id: Optional[int] = None
) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unban_async(channel_id, guild_id, target_id, ban_id))


async def unban_async(
    channel_id: int, guild_id: int, target_id: int, ban_id: Optional[int] = None
) -> None:
    # To avoid circular imports, we put this import here
    # Unfortunately how the tasks are setup, we can't import Client at the top level
    from dicebot.core.client import Client

    client = await Client.get_and_login()

    channel = await client.fetch_channel(channel_id)
    assert isinstance(channel, discord.TextChannel)

    async with app_sessionmaker() as session:
        guild = await Guild.get_or_none(session, guild_id)
        target = await User.get_or_none(session, target_id)

        if guild is None or target is None:
            return

        current_ban = await Ban.get_latest_unvoided_ban(session, guild, target)

        if (
            current_ban is not None
            and current_ban.banned_until < datetime.datetime.now()
        ):
            # If ban_id is provided, check that the latest ban *is* this ban
            if ban_id is not None and current_ban.id != ban_id:
                return

            await channel.send(f"<@{target_id}>: You have been unbanned.")
            # Remember to set this ban as now being acknowledged!
            current_ban.acknowledged = True
            await session.commit()
