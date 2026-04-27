#!/usr/bin/env python3

import datetime
import random
import time
from typing import Optional

from dicebot.commands import timezone
from dicebot.core.register_command import register_command
from dicebot.data.db.active_event import ActiveEvent, EventType
from dicebot.data.db.ban import Ban
from dicebot.data.db.ban_immunity import BanImmunity
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time
from dicebot.tasks.unban import unban as unban_task

VERY_BAD_THRESHOLD = 0.05
L_URL = "https://preview.redd.it/ulbdm5wicpha1.jpeg?width=1850&format=pjpg&auto=webp&s=37f7481b396e7966a02a77211e3fe0819ee3c913"


# Intentionally *not* a registered command
async def ban_internal(
    ctx: MessageContext,
    target: User,
    timer: Time,
    ban_as_bot: bool,
    reason: str,
    give_them_an_l: bool = False,
) -> None:
    """Ban a user for a given amount of time"""
    active_immunity = await BanImmunity.get_active(ctx.session, ctx.guild, target)
    if active_immunity is not None:
        localized = timezone.localize_dt(active_immunity.immune_until, ctx.guild.timezone)
        await ctx.send(
            f"{target.as_mention()} has ban immunity until {localized}. Nice try."
        )
        return
    active_event = await ActiveEvent.get_current(ctx.session, ctx.guild_id)
    if active_event is not None:
        if active_event.event_type_enum is EventType.DOUBLE_BAN:
            timer.seconds *= 2
        elif active_event.event_type_enum is EventType.LUCKY_HOUR:
            timer.seconds //= 2
            timer.seconds = max(timer.seconds, 1)  # don't allow 0-second bans
    if random.random() < VERY_BAD_THRESHOLD:
        msg = f"I have decided that {timer} is not enough.\n"
        msg += "Let's multiply that by 10."
        await ctx.send(msg)
        timer.seconds *= 10
    # "Why +1?"
    # There's a longstanding bug - https://github.com/gorel/discord_dicebot/issues/78
    # where the bot will say "the ban will end 59 minutes from now" because the
    # pretty-printer truncates down, meaning it thinks we're just *nanoseconds* away
    # from one hour, but since it uses strict comparison, it reports it as 59 minutes.
    # The easiest way to fix this is to just add one second now.
    # They probably deserved an extra second of ban anyway.
    new_ban = int(time.time()) + timer.seconds + 1
    new_ban_end_str = timezone.localize(new_ban, ctx.guild.timezone)
    banner_id = ctx.message.author.id

    if give_them_an_l:
        await ctx.send("This is for you.")
        await ctx.send(L_URL)

    if ban_as_bot:
        await ctx.send(
            f"I have chosen to ban <@{target.id}>. "
            f"The ban will end {new_ban_end_str}.\n"
            f"May God have mercy on your soul."
        )
        # Need to override banner's ID to denote "no real banner"
        assert ctx.client.user is not None
        banner_id = ctx.client.user.id
    else:
        await ctx.send(
            f"<@{banner_id}> has banned <@{target.id}>. "
            f"The ban will end {new_ban_end_str}.\n"
            "May God have mercy on your soul."
        )

    # Record this ban in the db
    banned_until = datetime.datetime.fromtimestamp(time.time() + timer.seconds)
    current_ban = await Ban.get_latest_unvoided_ban(ctx.session, ctx.guild, target)
    new_ban = Ban(
        guild_id=ctx.guild_id,
        bannee_id=target.id,
        banner_id=banner_id,
        reason=reason,
        banned_until=banned_until,
    )
    ctx.session.add(new_ban)
    await ctx.session.commit()

    if current_ban is not None and current_ban.banned_until > new_ban.banned_until:
        localized = timezone.localize_dt(current_ban.banned_until, ctx.guild.timezone)
        await ctx.send(f"Oh... you're already banned until {localized}. Wow...")
    else:
        await ctx.session.refresh(new_ban)
        unban_task.apply_async(
            (ctx.channel.id, ctx.guild_id, target.id, new_ban.id),
            countdown=timer.seconds + 1,
        )


@register_command
async def ban(ctx: MessageContext, target: User, timer: Time) -> None:
    """Ban a user for a given amount of time (bot will shame them)"""
    await ban_internal(
        ctx, target, timer, ban_as_bot=False, reason="Because they didn't like you"
    )


# Intentionally *not* a registered command
async def unban_internal(ctx: MessageContext, target: User, msg: str) -> None:
    await ctx.guild.unban(ctx.session, target)
    await ctx.session.commit()
    await ctx.send(msg)


@register_command
async def unban(ctx: MessageContext, target: User) -> None:
    """Unban a user immediately"""
    if ctx.message.author.id == target.id:
        await unban_internal(
            ctx,
            target,
            f"<@{target.id}> has been unbanned early.\n"
            "You should thank your benevolent sav -- Oh, unbanning _yourself_? Yikes.",
        )
    else:
        await unban_internal(
            ctx,
            target,
            f"<@{target.id}> has been unbanned early.\n"
            "You should thank your benevolent savior.\n",
        )


@register_command
async def ban_leaderboard(ctx: MessageContext) -> None:
    """View the ban leaderboard"""

    embed = await ctx.guild.ban_scoreboard_str(ctx.client, ctx.session)
    await ctx.send(embed=embed)


# Intentionally *not* a registered command
async def turboban(
    ctx: MessageContext,
    target: User,
    num_hours: int = 5,
    reason: Optional[str] = None,
) -> None:
    try:
        emojis = {e.name: f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
        turbo = ["T_", "U_", "R_", "B_", "O_"]
        turbo_str = "".join(emojis[s] for s in turbo)
        banned = ["B_", "A_", "N_", "N_", "E_", "D_"]
        banned_str = "".join(emojis[s] for s in banned)
        turbo_ban_msg = f"{turbo_str} {banned_str}"
    except KeyError:
        turbo_ban_msg = "**TURBO BANNED**"
    await ctx.quote_reply(turbo_ban_msg)

    if reason is None:
        reason = "Generic turboban"

    await ban_internal(
        ctx,
        target=target,
        timer=Time(f"{num_hours}hr"),
        ban_as_bot=True,
        reason=reason,
    )
