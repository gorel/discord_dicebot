#!/usr/bin/env python3

from dicebot.data.message_context import MessageContext


async def scoreboard(ctx: MessageContext) -> None:
    """Print out the roll scoreboard for this server"""

    msg = await ctx.guild.roll_scoreboard_str(ctx.client, ctx.session)
    await ctx.channel.send(msg)
