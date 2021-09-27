#!/usr/bin/env python3

import command
from message_context import MessageContext


async def set_ban_reaction_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the ban reaction threshold (how many reactions before a ban occurs) for this server"""
    if command.has_diceboss_role(ctx.message.author):
        ctx.server_ctx.ban_reaction_threshold = threshold
        await ctx.channel.send(
            f"<@{ctx.discord_id}> set the ban reaction threshold to {threshold}"
        )
    else:
        insult = command.get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}."
        )
