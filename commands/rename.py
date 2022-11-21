#!/usr/bin/env python3

import command
import db_helper
from message_context import MessageContext
from models import GreedyStr, Rename


async def rename(ctx: MessageContext, new_name: GreedyStr) -> None:
    """Rename either the server or chat channel (must be the most recent winner)"""
    winner_record = db_helper.get_last_winner(ctx.db_conn, ctx.guild_id)
    loser_record = db_helper.get_last_loser(ctx.db_conn, ctx.guild_id)
    won_something = False

    if (
        winner_record["discord_id"] == ctx.discord_id
        and winner_record["rename_used"] == 0
    ):
        won_something = True
        await ctx.channel.send(f"Setting server name to: {new_name}")
        await ctx.message.guild.edit(name=new_name, reason="Dice roll")
        db_helper.record_rename_used_winner(
            ctx.db_conn, ctx.guild_id, ctx.discord_id, winner_record["roll"]
        )

    if (
        loser_record["discord_id"] == ctx.discord_id
        and loser_record["rename_used"] == 0
    ):
        won_something = True
        await ctx.channel.send(f"Setting chat name to: {new_name}")
        await ctx.channel.edit(name=new_name, reason="Dice roll")
        db_helper.record_rename_used_loser(
            ctx.db_conn, ctx.guild_id, ctx.discord_id, loser_record["roll"]
        )

    if not won_something:
        await ctx.channel.send(
            f"I can't let you do that, <@{ctx.discord_id}>\n"
            "This incident will be recorded."
        )
