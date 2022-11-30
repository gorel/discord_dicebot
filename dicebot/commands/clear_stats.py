#!/usr/bin/env python3

from sqlalchemy import delete

import dicebot.simple_utils
from dicebot.data.db_models import DEFAULT_START_ROLL, Rename, Roll
from dicebot.data.message_context import MessageContext


async def clear_stats(ctx: MessageContext) -> None:
    """Clear all stats in the server's roll record (PERMANENT)"""
    if dicebot.simple_utils.is_admin(ctx.message.author):
        await ctx.session.scalars(delete(Roll).where(Roll.guild_id == ctx.guild_id))
        await ctx.session.scalars(delete(Rename).where(Rename.guild_id == ctx.guild_id))
        ctx.guild.current_roll = DEFAULT_START_ROLL
        await ctx.session.commit()

        await ctx.channel.send(
            "All winner/loser stats have been cleared for this server.\n"
            f"The next roll for this server has been reset to {DEFAULT_START_ROLL}"
        )
    else:
        await ctx.channel.send("You're not an admin.\nThis incident will be recorded.")
