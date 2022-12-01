#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@register_command
@requires_admin
async def set_reaction_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the reaction threshold (how many reactions before a reaction-reaction occurs) for this server"""
    ctx.guild.reaction_threshold = threshold
    await ctx.session.commit()
    await ctx.channel.send(f"Set the reaction threshold to {threshold}")
