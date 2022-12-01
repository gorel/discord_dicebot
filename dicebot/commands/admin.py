#!/usr/bin/env python3

import functools

from dicebot.data.db_models import User
from dicebot.data.message_context import MessageContext


def requires_admin(coro):
    """Utility decorator to mark that a function is only available to admins."""

    @functools.wraps(coro)
    async def wrapper(ctx: MessageContext, *args, **kwargs):
        if ctx.author.is_admin_of(ctx.guild):
            await coro(ctx, *args, **kwargs)
        else:
            await ctx.channel.send(
                "You're not an admin.\nThis incident will be recorded."
            )

    return wrapper


@requires_admin
async def add_admin(
    ctx: MessageContext,
    target: User,
) -> None:
    ctx.guild.admins.append(target)
    await ctx.session.commit()
    await ctx.channel.send(
        "{target.as_mention()} is now an admin.\n"
        '"*With great power comes great responsibility."* - Michael Scott'
    )


@requires_admin
async def remove_admin(
    ctx: MessageContext,
    target: User,
) -> None:
    if len(ctx.guild.admins) == 1:
        ctx.channel.send(
            "You can't leave a server with no admins.\n"
            f"Refusing to remove {target.as_mention()}"
        )
    else:
        ctx.guild.admins.remove(target)
        await ctx.session.commit()
        await ctx.channel.send("{target.as_mention()} is no longer an admin.")
