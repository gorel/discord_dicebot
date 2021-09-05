#!/usr/bin/env python3

import db_helper
from message_context import MessageContext


async def scoreboard(ctx: MessageContext) -> None:
    """Print out the roll scoreboard for this server"""
    stats = db_helper.get_all_stats(ctx.db_conn, ctx.server_ctx.guild_id)
    sorted_stats = sorted(stats, key=lambda rec: rec["wins"] - rec["losses"])
    msg = "**Stats:**\n"
    for record in sorted_stats:
        user = ctx.client.get_user(record["discord_id"])
        if not user:
            user = await ctx.client.fetch_user(record["discord_id"])

        wins = record["wins"]
        losses = record["losses"]
        attempts = record["attempts"]
        msg += f"\t- {user.name}: {wins} wins, {losses} losses ({attempts} rolls)\n"
    await ctx.channel.send(msg)


