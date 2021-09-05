#!/usr/bin/env python3

import command
from message_context import MessageContext


async def set_timeout(ctx: MessageContext, hours: int) -> None:
    """Set the roll timeout (how often you can roll) for this server"""
    if command.has_diceboss_role(ctx.message.author):
        ctx.server_ctx.roll_timeout_hours = hours
        await ctx.channel.send(f"<@{ctx.discord_id}> set the roll timeout to {hours} hours")
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}.")


