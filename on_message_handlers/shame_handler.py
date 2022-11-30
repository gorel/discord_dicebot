#!/usr/bin/env python3

import datetime
import logging

from data_infra.db_models import Ban
from data_infra.message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler


class ShameHandler(AbstractHandler):
    """If the user is banned, we react SHAME"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        latest_ban = await Ban.get_latest_unvoided_ban(
            ctx.session, ctx.guild, ctx.author
        )
        if latest_ban is None:
            return False
        else:
            return latest_ban.banned_until > datetime.datetime.now()

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
