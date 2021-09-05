#!/usr/bin/env python3

import command
import db_helper
from message_context import MessageContext
from models import GreedyStr, Rename


async def rename(ctx: MessageContext, new_name: GreedyStr) -> None:
    """Rename either the server or chat channel (must be the most recent winner)"""
    location = None

    # Check for last loser
    record = db_helper.get_last_loser(ctx.db_conn, ctx.guild_id)
    if record["discord_id"] == ctx.discord_id and record["rename_used"] == 0:
        location = Rename.TEXT_CHAT

    # Check for last winner
    record = db_helper.get_last_winner(ctx.db_conn, ctx.guild_id)
    if record["discord_id"] == ctx.discord_id and record["rename_used"] == 0:
        location = Rename.SERVER

    # Resolve rename request
    if location == Rename.SERVER:
        await ctx.channel.send(f"Setting server name to: {new_name}")
        await ctx.message.guild.edit(name=new_name, reason="Dice roll")
    elif location == Rename.TEXT_CHAT:
        await ctx.channel.send(f"Setting chat name to: {new_name}")
        await ctx.channel.edit(name=new_name, reason="Dice roll")
    else:
        await ctx.channel.send(
            f"I can't let you do that, <@{ctx.discord_id}>\n"
            "This incident will be recorded."
        )
