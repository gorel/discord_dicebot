#!/usr/bin/env python3

import random

from dicebot.commands import timezone
from dicebot.core.register_command import register_command
from dicebot.data.db.resolution import Resolution
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.tasks.resolution_reminder import remind

SUPPORTED_FREQUENCIES = ["daily", "weekly", "monthly", "quarterly", "yearly", "random"]
SECONDS_IN_DAY = 86400


@register_command
async def resolution(ctx: MessageContext, frequency: str, msg: GreedyStr) -> None:
    """Add a new resolution to track throughout the year.
    The bot will ask you how things are going occasionally.
    `frequency` can be one of 'daily', 'weekly', 'monthly',
    'quarterly', 'yearly', or 'random'."""

    if frequency not in SUPPORTED_FREQUENCIES:
        response = (
            f"Unsupported frequency '{frequency}'\n"
            f"Supported frequencies are {SUPPORTED_FREQUENCIES}"
        )
        await ctx.channel.send(response)
        return

    resolution = Resolution(
        guild_id=ctx.guild_id,
        author_id=ctx.author_id,
        channel_id=ctx.channel.id,
        msg=msg,
        frequency=frequency,
    )
    ctx.session.add(resolution)
    await ctx.session.commit()
    await ctx.session.refresh(resolution)
    response = (
        "Okay, I'll track that resolution for you.\n"
        "If you ever want to stop my reminders, tell me "
        f"`!delete_resolution {resolution.id}`"
    )

    if frequency == "daily":
        for i in range(1, 365 + 1):
            seconds = SECONDS_IN_DAY * i
            remind.apply_async((resolution.id,), countdown=seconds)
    elif frequency == "weekly":
        for i in range(1, 52 + 1):
            seconds = SECONDS_IN_DAY * 7 * i
            remind.apply_async((resolution.id,), countdown=seconds)
    elif frequency == "monthly":
        for i in range(1, 12 + 1):
            # Just... assume there are 31 days in a month. Close enough.
            seconds = SECONDS_IN_DAY * 31 * i
            remind.apply_async((resolution.id,), countdown=seconds)
    elif frequency == "quarterly":
        for i in range(1, 4 + 1):
            # Just... assume there are 31 days in a month. Close enough.
            seconds = SECONDS_IN_DAY * 31 * 4 * i
            remind.apply_async((resolution.id,), countdown=seconds)
    elif frequency == "yearly":
        seconds = SECONDS_IN_DAY * 365
        remind.apply_async((resolution.id,), countdown=seconds)
    elif frequency == "random":
        # Just pick 10 random days to send the reminder
        for i in range(10):
            seconds = SECONDS_IN_DAY * random.randint(1, 365)
            remind.apply_async((resolution.id,), countdown=seconds)

    await ctx.channel.send(response)


@register_command
async def my_resolutions(ctx: MessageContext) -> None:
    resolutions = await Resolution.get_all_for_user(ctx.session, ctx.author_id)
    if len(resolutions) == 0:
        await ctx.channel.send("You have no active resolutions.")
        return

    resolutions_with_times = [
        (r, timezone.localize_dt(r.created_at, ctx.guild.timezone)) for r in resolutions
    ]
    response = "**Your resolutions:**\n"
    response += "\n".join(
        f"  - #{r.id}: {r.msg} (created {t}, {r.frequency} reminders)"
        for r, t in resolutions_with_times
    )
    await ctx.channel.send(response)


@register_command
async def delete_resolution(ctx: MessageContext, resolution_id: int) -> None:
    """Delete an old resolution from reminders"""
    r = await Resolution.get_or_none(ctx.session, resolution_id)
    if r is None or r.author_id != ctx.author_id:
        response = (
            f"Resolution #{resolution_id} doesn't belong to you.\n"
            f"Try `!my_resolutions` to see your resolutions"
        )
        await ctx.channel.send(response)
        return

    resolution.active = False
    await ctx.session.commit()

    localized = timezone.localize_dt(r.created_at, ctx.guild.timezone)
    response = (
        f"You created that resolution {localized}. You're already giving up?\n"
        "Anyway, I'll stop reminding you about it."
    )
    await ctx.channel.send(response)
