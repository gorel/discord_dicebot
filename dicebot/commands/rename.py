#!/usr/bin/env python3

from discord import DMChannel

from dicebot.core.register_command import register_command
from dicebot.data.db.rename import Rename
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


class RenameError(ValueError):
    pass


@register_command
async def rename(ctx: MessageContext, new_name: GreedyStr) -> None:
    """Rename either the server or chat channel (must be the most recent winner)"""
    new_name_str = new_name.unwrap()
    last_winner = await Rename.get_last_winner(ctx.session, ctx.guild)
    last_loser = await Rename.get_last_loser(ctx.session, ctx.guild)

    if (
        last_winner is not None
        and last_winner.discord_user_id == ctx.author_id
        and not last_winner.rename_used
    ):
        if isinstance(ctx.channel, DMChannel) or ctx.discord_guild is None:
            raise RenameError("Renaming isn't supported here")
        await ctx.channel.send(f"Setting server name to: {new_name_str}")
        await ctx.discord_guild.edit(name=new_name_str, reason="Dice roll")
        last_winner.rename_used = True
        await ctx.session.commit()
    elif (
        last_loser is not None
        and last_loser.discord_user_id == ctx.author_id
        and not last_loser.rename_used
    ):
        if isinstance(ctx.channel, DMChannel) or ctx.discord_guild is None:
            raise RenameError("Renaming isn't supported here")
        await ctx.channel.send(f"Setting chat name to: {new_name_str}")
        await ctx.channel.edit(name=new_name_str, reason="Dice roll")
        last_loser.rename_used = True
        await ctx.session.commit()
    else:
        await ctx.channel.send(
            f"I can't let you do that, <@{ctx.author_id}>\n"
            "This incident will be recorded."
        )
