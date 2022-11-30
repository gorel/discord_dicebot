#!/usr/bin/env python3

import logging

from dicebot.data.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler


class ShameHandler(AbstractHandler):
    """If the user is banned, we react SHAME"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return ctx.author.is_currently_banned(ctx.session, ctx.guild)

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        logging.warning(f"{ctx.author_id} is banned! Shame them.")
        await ctx.message.add_reaction("🇸")
        await ctx.message.add_reaction("🇭")
        await ctx.message.add_reaction("🇦")
        await ctx.message.add_reaction("🇲")
        await ctx.message.add_reaction("🇪")
