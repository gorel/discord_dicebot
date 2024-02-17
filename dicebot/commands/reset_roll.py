#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@requires_admin
@register_command
async def reset_roll(ctx: MessageContext, to: int) -> None:
    """Reset the next roll for this server to the given value"""
    ctx.guild.current_roll = to
    await ctx.session.commit()
    await ctx.send(f"<@{ctx.author_id}> set the next roll to {to}")
