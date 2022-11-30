#!/usr/bin/env python3

import dicebot.simple_utils
from dicebot.data.message_context import MessageContext


async def set_turbo_ban_timing_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the turbo ban timing threshold (maximum number of seconds before a turbo banned is issued) for this server"""
    if dicebot.simple_utils.is_admin(ctx.message.author):
        ctx.guild.turboban_threshold = threshold
        await ctx.session.commit()
        await ctx.channel.send(
            f"<@{ctx.author_id}> set the turbo ban timing threshold to {threshold}"
        )
    else:
        await ctx.channel.send("You're not an admin.\nThis incident will be recorded.")
