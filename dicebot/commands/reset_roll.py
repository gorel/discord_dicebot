#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.message_context import MessageContext


@register_command
@requires_admin
async def reset_roll(ctx: MessageContext, to: int) -> None:
    """Reset the next roll for this server to the given value"""
    ctx.guild.current_roll = to
    await ctx.session.commit()
    await ctx.channel.send(f"<@{ctx.author_id}> set the next roll to {to}")
