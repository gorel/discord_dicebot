#!/usr/bin/env python3

from data_infra.message_context import MessageContext


async def reset_roll(ctx: MessageContext, to: int) -> None:
    """Reset the next roll for this server to the given value"""
    ctx.guild.current_roll = to
    await ctx.session.commit()
    await ctx.channel.send(f"<@{ctx.discord_id}> set the next roll to {to}")
