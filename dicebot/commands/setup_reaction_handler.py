#!/usr/bin/env python3

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


@requires_admin
@register_command
async def setup_reaction_handler(
    ctx: MessageContext, reaction: str, gif_search: GreedyStr
) -> None:
    """Set up a reaction handler that will respond with a randomly searched GIF whenever
    the server's reaction threshold is met.
    """
    await ctx.guild.add_reaction_handler(
        ctx.session,
        reaction=reaction.strip(),
        gif_search=gif_search.strip(),
        author=ctx.author,
    )
    await ctx.quote_reply(f"Added reaction handler for {reaction}")
