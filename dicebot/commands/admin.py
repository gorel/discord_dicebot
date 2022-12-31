#!/usr/bin/env python3

import functools
import os

from dicebot.core.register_command import register_command
from dicebot.data.db.channel import Channel
from dicebot.data.db.user import User
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.set_message_subcommand import SetMessageSubcommand


def requires_owner(coro):
    """Utility decorator to mark that a function is only available to the bot owner."""

    @functools.wraps(coro)
    async def wrapper(ctx: MessageContext, *args, **kwargs) -> None:
        owner_discord_id = int(os.getenv("OWNER_DISCORD_ID", 0))
        if ctx.author_id == owner_discord_id:
            await coro(ctx, *args, **kwargs)
        else:
            await ctx.channel.send("This command is only callable by the bot owner.")

    return wrapper


def requires_admin(coro):
    """Utility decorator to mark that a function is only available to admins."""

    @functools.wraps(coro)
    async def wrapper(ctx: MessageContext, *args, **kwargs) -> None:
        if ctx.author.is_admin_of(ctx.guild):
            await coro(ctx, *args, **kwargs)
        else:
            await ctx.channel.send(
                "You're not an admin.\nThis incident will be recorded."
            )

    return wrapper


@requires_admin
@register_command
async def add_admin(
    ctx: MessageContext,
    target: User,
) -> None:
    ctx.guild.admins.append(target)
    await ctx.session.commit()
    await ctx.channel.send(
        f"{target.as_mention()} is now an admin.\n"
        '"*With great power comes great responsibility."* - Michael Scott'
    )


@requires_admin
@register_command
async def remove_admin(
    ctx: MessageContext,
    target: User,
) -> None:
    if len(ctx.guild.admins) == 1:
        await ctx.channel.send(
            "You can't leave a server with no admins.\n"
            f"Refusing to remove {target.as_mention()}"
        )
    else:
        ctx.guild.admins.remove(target)
        await ctx.session.commit()
        await ctx.channel.send(f"{target.as_mention()} is no longer an admin.")


@requires_admin
@register_command
async def set_msg(
    ctx: MessageContext,
    win_or_lose: SetMessageSubcommand,
    msg: GreedyStr,
) -> None:
    """Set the win/loss message in this server for critical success or failure"""
    msg_str = msg.unwrap()
    if win_or_lose is SetMessageSubcommand.WIN:
        ctx.guild.critical_success_msg = msg_str
        await ctx.session.commit()
        await ctx.channel.send(f"Set the win message to '{msg_str}'")
    else:
        ctx.guild.critical_failure_msg = msg_str
        await ctx.session.commit()
        await ctx.channel.send(f"Set the lose message to '{msg_str}'")


@requires_admin
@register_command
async def set_reaction_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the reaction threshold for this server. This is how many reactions
    are needed before a reaction-reaction occurs (like the bot reacting kekw)"""
    ctx.guild.reaction_threshold = threshold
    await ctx.session.commit()
    await ctx.channel.send(f"Set the reaction threshold to {threshold}")


@requires_admin
@register_command
async def set_timeout(ctx: MessageContext, hours: int) -> None:
    """Set the roll timeout (how often you can roll) for this server"""
    ctx.guild.roll_timeout = hours
    await ctx.session.commit()
    await ctx.channel.send(f"Set the roll timeout to {hours} hours")


@requires_admin
@register_command
async def set_turbo_ban_timing_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the turbo ban timing threshold for this server. This is the maximum number of
    seconds before a turbo banned will be issued instead of a regular ban"""
    ctx.guild.turboban_threshold = threshold
    await ctx.session.commit()
    await ctx.channel.send(f"Set the turbo ban timing threshold to {threshold}")


@requires_admin
@register_command
async def toggle_shame(ctx: MessageContext) -> None:
    """Toggle whether shame can be sent to a channel"""
    channel = await Channel.get_or_create(ctx.session, ctx.channel.id, ctx.guild_id)
    channel.shame = not channel.shame
    await ctx.session.commit()
    s = "**no longer** " if not channel.shame else ""
    await ctx.channel.send(f"Shame will now {s}be sent to this channel.")
