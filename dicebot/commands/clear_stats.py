#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.message_context import MessageContext


@register_command
@requires_admin
async def clear_stats(ctx: MessageContext) -> None:
    """Clear all stats in the server's roll record (PERMANENT)"""
    await ctx.guild.clear_stats(ctx.session)
    await ctx.session.commit()

    await ctx.channel.send(
        "All winner/loser stats have been cleared for this server.\n"
        f"The next roll for this server has been reset to {ctx.guild.current_roll}"
    )
