#!/usr/bin/env python3

import asyncio
import datetime
import logging
import time

import dicebot.simple_utils
from dicebot.commands import timezone
from dicebot.data.db_models import Ban, DiscordUser
from dicebot.data.message_context import MessageContext
from dicebot.data.types.bot_param import BotParam
from dicebot.data.types.time import Time


async def ban(
    ctx: MessageContext,
    target: DiscordUser,
    timer: Time,
    ban_as_bot: BotParam[bool] = False,
    reason: BotParam[str] = "",
) -> None:
    """Ban a user for a given amount of time (bot will shame them)"""
    new_ban = int(time.time()) + timer.seconds
    new_ban_end_str = timezone.localize(new_ban, ctx.guild.timezone)
    banner_id = ctx.message.author.id

    if ban_as_bot:
        await ctx.channel.send(
            f"I have chosen to ban <@{target.discord_id}>. "
            f"The ban will end {new_ban_end_str}.\n"
            f"May God have mercy on your soul."
        )
        # Need to override banner's ID to denote "no real banner"
        banner_id = ctx.client.user.id
    else:
        reason = "Because they didn't like you"
        await ctx.channel.send(
            f"<@{ctx.discord_user_id}> has banned <@{target.discord_id}>. "
            f"The ban will end {new_ban_end_str}.\n"
            "May God have mercy on your soul."
        )

    # Record this ban in the db
    banned_until = datetime.datetime.fromtimestamp(time.time() + timer.seconds)
    ban = Ban(
        bannee_id=target.discord_id,
        banner_id=banner_id,
        reason=reason,
        banned_until=banned_until,
    )
    ctx.session.add(ban)
    await ctx.session.commit()

    # TODO: This is totally broken -- we need to get the max (unvoided) ban
    current_ban = await Ban.get_latest_unvoided_ban(
        ctx.session, ctx.guild_id, target.id
    )
    if current_ban.banned_until > new_ban.banned_until:
        localized = timezone.localize(current_ban, ctx.guild.timezone)
        await ctx.channel.send(f"Oh... you're already banned until {localized}. Wow...")

    # Tell them they're unbanned 1 second late to ensure any weird delays
    # will still make the logic sound
    # TODO: Put in a message queue instead
    await asyncio.sleep(timer.seconds + 1)
    logging.info(f"Check if {target.id} is still banned")

    # While we were sleeping, the target got banned for *even longer*
    # Check that the bantime is in the past and not -1 (unbanned early)
    # We check the bantime was in the past since we slept 1 more second
    current_ban = await Ban.get_latest_unvoided_ban(
        ctx.session, ctx.guild_id, target.id
    )
    if current_ban.banned_until < datetime.datetime.now():
        insult = dicebot.simple_utils.get_witty_insult()
        await ctx.channel.send(
            f"<@{target.id}>: you have been unbanned.\n"
            f"I hope you learned your lesson, *{insult}*."
        )


async def unban(ctx: MessageContext, target: DiscordUser) -> None:
    """Unban a user immediately"""
    await ctx.guild.unban(ctx.session, target)
    await ctx.session.commit()
    await ctx.channel.send(
        f"<@{target.discord_id}> has been unbanned early.\n"
        "You should thank your benevolent savior.\n"
    )


async def ban_leaderboard(ctx: MessageContext) -> None:
    """View the ban leaderboard"""

    leaderboard_str = await ctx.guild.ban_scoreboard_str(ctx.client, ctx.session)
    await ctx.channel.send(leaderboard_str)


async def turboban(
    ctx: MessageContext,
    reference_msg: MessageContext,
    target: DiscordUser,
    num_hours: int = 5,
) -> None:
    emojis = {e.name: f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
    turbo = ["T_", "U_", "R_", "B_", "O_"]
    turbo_str = "".join(emojis[s] for s in turbo)
    banned = ["B_", "A_", "N_", "N_", "E_", "D_"]
    banned_str = "".join(emojis[s] for s in banned)
    turbo_ban_msg = f"{turbo_str} {banned_str}"
    await reference_msg.channel.send(turbo_ban_msg, reference=reference_msg)
    await ban(
        ctx,
        target=target,
        timer=Time(f"{num_hours}hr"),
        ban_as_bot=True,
    )
