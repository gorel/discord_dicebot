#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@register_command
@requires_admin
async def set_timeout(ctx: MessageContext, hours: int) -> None:
    """Set the roll timeout (how often you can roll) for this server"""
    ctx.guild.roll_timeout = hours
    await ctx.session.commit()
    await ctx.channel.send(f"Set the roll timeout to {hours} hours")
