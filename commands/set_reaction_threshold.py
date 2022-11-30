#!/usr/bin/env python3

import simple_utils
from data_infra.message_context import MessageContext


async def set_reaction_threshold(ctx: MessageContext, threshold: int) -> None:
    """Set the reaction threshold (how many reactions before a reaction-reaction occurs) for this server"""
    if simple_utils.is_admin(ctx.message.author):
        ctx.guild.reaction_threshold = threshold
        await ctx.session.commit()
        await ctx.channel.send(
            f"<@{ctx.discord_id}> set the ban reaction threshold to {threshold}"
        )
    else:
        insult = simple_utils.get_witty_insult()
        await ctx.channel.send(
            f"You're not a diceboss.\nDon't try that shit again, {insult}."
        )
        await ctx.channel.send("You're not an admin.\nThis incident will be recorded.")
