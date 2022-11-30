#!/usr/bin/env python3

from data_infra.message_context import MessageContext


async def scoreboard(ctx: MessageContext) -> None:
    """Print out the roll scoreboard for this server"""

    msg = await ctx.guild.roll_scoreboard_str(ctx.client, ctx.session)
    await ctx.channel.send(msg)
