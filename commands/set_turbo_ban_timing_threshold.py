#!/usr/bin/env python3

import command
from message_context import MessageContext


async def set_turbo_ban_timing_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the turbo ban timing threshold (maximum number of seconds before a turbo banned is issued) for this server"""
    if command.has_diceboss_role(ctx.message.author):
        ctx.server_ctx.turbo_ban_timing_threshold = threshold
        await ctx.channel.send(
            f"<@{ctx.discord_id}> set the turbo ban timing threshold to {threshold}"
        )
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}."
        )
