#!/usr/bin/env python3

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler


class HbdHandler(AbstractHandler):
    """Recognize someone's birthday with a heartfelt response"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return ctx.message.content.lower().startswith("hbd")

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        guild = ctx.message.guild
        # This should only ever be called from a guild context
        assert guild is not None

        guild_emojis = {e.name.lower(): e for e in guild.emojis}
        all_emojis = {e.name.lower(): e for e in ctx.client.emojis}
        if "this_tbh" in guild_emojis.keys():
            await ctx.message.add_reaction(guild_emojis["this_tbh"])
        elif "this_tbh" in all_emojis.keys():
            await ctx.message.add_reaction(all_emojis["this_tbh"])
        await ctx.send("^")
