#!/usr/bin/env python3

import command
import db_helper
from message_context import MessageContext


async def clear_stats(ctx: MessageContext) -> None:
    """Clear all stats in the server's roll record (PERMANENT)"""
    if command.has_diceboss_role(ctx.message.author):
        db_helper.clear_all(ctx.db_conn, ctx.server_ctx.guild_id)
        ctx.server_ctx.current_roll = ctx.server_ctx.DEFAULT_CURRENT_ROLL
        await ctx.channel.send(
            "All winner/loser stats have been cleared for this server.\n"
            f"The next roll for this server has been reset to {ctx.server_ctx.current_roll}"
        )
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}.")


