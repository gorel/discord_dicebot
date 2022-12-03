#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@requires_admin
@register_command
async def set_turbo_ban_timing_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the turbo ban timing threshold (maximum number of seconds before a turbo banned is issued) for this server"""
    ctx.guild.turboban_threshold = threshold
    await ctx.session.commit()
    await ctx.channel.send(f"Set the turbo ban timing threshold to {threshold}")
