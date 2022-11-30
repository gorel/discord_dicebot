#!/usr/bin/env python3

import dicebot.simple_utils
from dicebot.data.message_context import MessageContext


async def set_timeout(ctx: MessageContext, hours: int) -> None:
    """Set the roll timeout (how often you can roll) for this server"""
    if dicebot.simple_utils.is_admin(ctx.message.author):
        ctx.guild.roll_timeout = hours
        await ctx.session.commit()
        await ctx.channel.send(
            f"<@{ctx.author_id}> set the roll timeout to {hours} hours"
        )
    else:
        await ctx.channel.send("You're not an admin.\nThis incident will be recorded.")
