#!/usr/bin/env python3

import asyncio
import datetime
import random

import discord
import pytz

from dicebot.app import app_sessionmaker, celery_app

# NOTE: Client is imported here (not lazy) so tests can patch it easily.
# The circular-import risk is acceptable since tasks are only imported by workers.
from dicebot.core.client import Client
from dicebot.data.db.active_event import ActiveEvent, EventType
from dicebot.data.db.guild import Guild


@celery_app.task(ignore_result=True)
def check_daily_event() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_daily_event_async())


async def check_daily_event_async() -> None:
    client = await Client.get_and_login()

    async with app_sessionmaker() as session:
        guilds = await Guild.get_all(session)
        for guild in guilds:
            if guild.events_probability is None:
                continue
            if guild.events_channel_id is None:
                continue

            # Check if it's 5am in this guild's timezone
            tz = pytz.timezone(guild.timezone)
            local_now = datetime.datetime.now(tz)
            if local_now.hour != 5:
                continue

            # Idempotent: skip if an event already fired today
            existing = await ActiveEvent.get_current(session, guild.id)
            if existing is not None:
                continue

            # Roll the dice
            if random.random() > guild.events_probability:
                continue

            # Pick a random event and create it
            event_type = random.choice(list(EventType))
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            active_event = ActiveEvent(
                guild_id=guild.id,
                event_type=event_type.value,
                started_at=now,
                expires_at=now + datetime.timedelta(hours=24),
            )
            session.add(active_event)
            await session.commit()

            # Announce it
            channel = await client.fetch_channel(guild.events_channel_id)
            if isinstance(channel, discord.TextChannel):
                title, description = _event_announcement(event_type)
                embed = discord.Embed(
                    title=f"🎲 Today's Event: {title}",
                    description=description,
                    color=discord.Color.gold(),
                )
                embed.set_footer(text="This event lasts 24 hours.")
                await channel.send(embed=embed)


def _event_announcement(event_type: EventType) -> tuple[str, str]:
    from dicebot.commands.roll import CURSE_DAY_CRITICAL_THRESHOLD

    announcements = {
        EventType.DOUBLE_BAN: (
            "Double Ban Day",
            "All ban durations are doubled today. Choose your words carefully.",
        ),
        EventType.LUCKY_HOUR: (
            "Lucky Hour",
            "All roll penalties are halved today. Fortune favors the bold.",
        ),
        EventType.CURSE_DAY: (
            "Curse Day",
            f"Any roll under {CURSE_DAY_CRITICAL_THRESHOLD} counts as a critical fail today. Tread carefully.",
        ),
        EventType.BLESSING_DAY: (
            "Blessing Day",
            "Any roll within 2 of the maximum counts as a win today. The dice gods smile upon you.",
        ),
        EventType.TURBO_DAY: (
            "Turbo Day",
            "The ban reaction threshold is 1 today. One reaction is all it takes.",
        ),
    }
    return announcements[event_type]
