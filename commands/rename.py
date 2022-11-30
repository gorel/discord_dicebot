#!/usr/bin/env python3

from data_infra.db_models import Rename
from data_infra.greedy_str import GreedyStr
from data_infra.message_context import MessageContext


async def rename(ctx: MessageContext, new_name: GreedyStr) -> None:
    """Rename either the server or chat channel (must be the most recent winner)"""
    last_winner = await Rename.get_last_winner(ctx.session, ctx.guild)
    last_loser = await Rename.get_last_loser(ctx.session, ctx.guild)

    if (
        last_winner is not None
        and last_winner.discord_user_id == ctx.author_id
        and not last_winner.rename_used
    ):
        await ctx.channel.send(f"Setting server name to: {new_name}")
        await ctx.message.guild.edit(name=new_name, reason="Dice roll")
        last_winner.rename_used = True
        await ctx.session.commit()
    elif (
        last_loser is not None
        and last_loser.discord_user_id == ctx.author_id
        and not last_loser.rename_used
    ):
        await ctx.channel.send(f"Setting chat name to: {new_name}")
        await ctx.channel.edit(name=new_name, reason="Dice roll")
        db_helper.record_rename_used_loser(
            ctx.db_conn, ctx.guild_id, ctx.discord_id, loser_record["roll"]
        )
    else:
        await ctx.channel.send(
            f"I can't let you do that, <@{ctx.discord_id}>\n"
            "This incident will be recorded."
        )
