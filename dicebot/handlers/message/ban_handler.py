#!/usr/bin/env python3

import logging
import re

from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler


class BanHandler(AbstractHandler):
    """Easter egg if the bot detects 'ban' being said"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        # Don't use BanHandler if the user is invoking the ban command
        if ctx.message.content.startswith("!ban"):
            return False

        return (
            re.search(r"\b(ban)\b", ctx.message.content, flags=re.IGNORECASE)
            is not None
        )

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        guild = ctx.message.guild
        # This should only ever be called from a guild context
        assert guild is not None

        guild_emojis = {e.name.lower(): e for e in guild.emojis}
        all_emojis = {e.name.lower(): e for e in ctx.client.emojis}
        if "ban" in guild_emojis.keys():
            await ctx.message.add_reaction(guild_emojis["ban"])
        elif "ban" in all_emojis.keys():
            await ctx.message.add_reaction(all_emojis["ban"])
        else:
            logging.warning("No ban emoji found")
