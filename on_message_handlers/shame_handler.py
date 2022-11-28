#!/usr/bin/env python3

import logging
import time

from message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler


class ShameHandler(AbstractHandler):
    """If the user is banned, we react SHAME"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return ctx.server_ctx.bans.get(ctx.discord_id, -1) > time.time()

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        logging.warning(f"{ctx.discord_id} is banned! Shame them.")
        await ctx.message.add_reaction("🇸")
        await ctx.message.add_reaction("🇭")
        await ctx.message.add_reaction("🇦")
        await ctx.message.add_reaction("🇲")
        await ctx.message.add_reaction("🇪")
