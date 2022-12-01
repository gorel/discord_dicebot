#!/usr/bin/env python3

from dicebot.core.register_command import register_command
from dicebot.data.types.message_context import MessageContext


@register_command
async def scoreboard(ctx: MessageContext) -> None:
    """Print out the roll scoreboard for this server"""

    msg = await ctx.guild.roll_scoreboard_str(ctx.client, ctx.session)
    await ctx.channel.send(msg)
