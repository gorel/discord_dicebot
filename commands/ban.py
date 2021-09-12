#!/usr/bin/env python3

import asyncio
import logging
import time

import command
from commands import timezone
from message_context import MessageContext
from models import BotParam, DiscordUser, Time


async def ban(
    ctx: MessageContext,
    target: DiscordUser,
    timer: Time,
    ban_as_bot: BotParam[bool] = False,
) -> None:
    """Ban a user for a given amount of time (bot will shame them)"""
    new_ban = int(time.time()) + timer.seconds
    new_ban_end_str = timezone.localize(new_ban, ctx.server_ctx.tz)
    if ban_as_bot:
        await ctx.channel.send(
            f"I have chosen to ban <@{target}>. "
            f"The ban will end {new_ban_end_str}\n"
            f"May God have mercy on your soul."
        )
    else:
        await ctx.channel.send(
            f"<@{ctx.discord_id}> has banned <@{target}>. "
            f"The ban will end {new_ban_end_str}\n"
            "May God have mercy on your soul."
        )

    current_ban = ctx.server_ctx.bans.get(target.id, -1)
    if current_ban > new_ban:
        localized = timezone.localize(current_ban, ctx.server_ctx.tz)
        await ctx.channel.send(f"Oh... you're already banned until {localized}. Wow...")
    ctx.server_ctx.set_ban(target.id, max(current_ban, time.time() + timer.seconds))

    # Tell them they're unbanned 1 second late to ensure any weird delays
    # will still make the logic sound
    await asyncio.sleep(timer.seconds + 1)
    logging.info(f"Check if {target.id} is still banned")

    # Since we're saving/loading file every time, we need to force a reload
    # to check if the user was already unbanned while we were sleeping
    ctx.server_ctx.reload()

    # got banned for *even longer* and we didn't know about it.
    # Check that the bantime is in the past and not -1 (unbanned early)
    # We check the bantime was in the past since we slept 1 more second
    bantime = ctx.server_ctx.bans[target.id]
    if bantime < time.time() and bantime != -1:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"<@{target.id}>: you have been unbanned.\n"
            f"I hope you learned your lesson, *{insult}*."
        )


async def unban(ctx: MessageContext, target: DiscordUser) -> None:
    """Unban a user immediately"""
    ctx.server_ctx.set_ban(target.id, -1)
    await ctx.channel.send(
        f"<@{target.id}> has been unbanned early.\n"
        "You should thank your benevolent savior.\n"
    )
